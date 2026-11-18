#!/usr/bin/env python3
"""Deterministic exact-fidelity extractor & Godot/Aseprite bundler for Drum (GBA source sheet)."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TOOLS_SHARPNESS = ROOT / "tools" / "art" / "measure_pixel_sharpness.py"
SKILL_SCRIPTS = ROOT / ".agent" / "skills" / "generate2dsprite" / "scripts"
BUILD_CLIPS = SKILL_SCRIPTS / "build_animation_clips.py"
EXPORT_ENGINE = SKILL_SCRIPTS / "export_engine.py"

UPLOAD_SRC = Path(
    "/home/codespace/.gemini/antigravity-cli/brain/"
    "c8e08543-6146-4d1d-9158-220fb30bfae3/.user_uploaded/uploaded_media_1794748948973.png"
)
CHAR_DIR = ROOT / "assets" / "drum"
SOURCE_DIR = CHAR_DIR / "source"
SOURCE_SHEET = SOURCE_DIR / "drum_sheet_src.png"
WALK_FRAMES_DIR = SOURCE_DIR / "walk_frames"
RAW_FRAMES_DIR = SOURCE_DIR / "raw_frames"
CLIPS_DIR = CHAR_DIR / "clips"
BUNDLE_DIR = CHAR_DIR / "godot_bundle"

BG_RGB = (146, 5, 167)  # #9205A7 exact indexed magenta key
CANVAS_W = 128
CANVAS_H = 96
FOOT_ANCHOR = [56, 84]
FX_PIVOT = [64, 48]


def measure_belt_center_x(rgba_arr: np.ndarray) -> float:
    """Measure median X of orange belt pixels; fallback to torso dark-pixel centroid."""
    r = rgba_arr[:, :, 0]
    g = rgba_arr[:, :, 1]
    b = rgba_arr[:, :, 2]
    a = rgba_arr[:, :, 3]
    belt_mask = (a > 0) & (r > 180) & (g > 60) & (g < 170) & (b < 60)
    xs = np.where(belt_mask)[1]
    if len(xs) >= 12:
        return float(np.median(xs))
    green_mask = (a > 0) & (g > 110) & (r < 120) & (b < 120)
    gxs = np.where(green_mask)[1]
    if len(gxs) >= 20:
        return float(np.median(gxs))
    vxs = np.where(a > 0)[1]
    return float(np.median(vxs))


def key_slot_exact(sheet_rgba: np.ndarray, rect: tuple[int, int, int, int]) -> np.ndarray:
    """Crop rect from sheet and zero ONLY exact BG_RGB pixels (100% original RGB preserved)."""
    x, y, w, h = rect
    crop = sheet_rgba[y : y + h, x : x + w].copy()
    is_bg = (
        (crop[:, :, 0] == BG_RGB[0])
        & (crop[:, :, 1] == BG_RGB[1])
        & (crop[:, :, 2] == BG_RGB[2])
    )
    crop[is_bg] = [0, 0, 0, 0]
    return crop


def place_on_canvas(
    crop: np.ndarray,
    *,
    align_mode: str = "ground_belt",
    y_offset: int = 0,
    x_shift: int = 0,
    fixed_cx: float | None = None,
) -> tuple[Image.Image, dict[str, Any]]:
    """Place cropped RGBA sprite onto fixed [128, 96] canvas preserving exact pixels."""
    h, w = crop.shape[:2]
    canvas = np.zeros((CANVAS_H, CANVAS_W, 4), dtype=np.uint8)

    if align_mode == "fx_center":
        cx = (w - 1) / 2.0
        cy = (h - 1) / 2.0
        dst_x = int(round(FX_PIVOT[0] - cx)) + x_shift
        dst_y = int(round(FX_PIVOT[1] - cy)) + y_offset
    elif align_mode == "center_bbox":
        cx = (w - 1) / 2.0 if fixed_cx is None else fixed_cx
        dst_x = int(round(FOOT_ANCHOR[0] - cx)) + x_shift
        dst_y = int(FOOT_ANCHOR[1] - h + y_offset)
    else:
        cx = measure_belt_center_x(crop) if fixed_cx is None else fixed_cx
        dst_x = int(round(FOOT_ANCHOR[0] - cx)) + x_shift
        dst_y = int(FOOT_ANCHOR[1] - h + y_offset)

    if dst_x < 0 or dst_y < 0 or dst_x + w > CANVAS_W or dst_y + h > CANVAS_H:
        raise ValueError(
            f"Crop {(w, h)} placed at {(dst_x, dst_y)} overflows canvas {(CANVAS_W, CANVAS_H)}"
        )

    canvas[dst_y : dst_y + h, dst_x : dst_x + w] = crop
    img = Image.fromarray(canvas, mode="RGBA")
    meta = {
        "crop_size": [w, h],
        "dst_top_left": [dst_x, dst_y],
        "center_x_measured": round(cx, 2),
    }
    return img, meta


def write_gdignore(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / ".gdignore").write_text("", encoding="utf-8")


def premul_visible_mae(img_a: Image.Image, img_b: Image.Image) -> float:
    """Measure premultiplied RGBA MAE over visible pixels matching build_animation_clips.py."""
    a = np.asarray(img_a, dtype=np.float32)
    b = np.asarray(img_b, dtype=np.float32)
    vis = (a[:, :, 3] > 0) | (b[:, :, 3] > 0)
    if not np.any(vis):
        return 0.0
    pa = np.concatenate([a[:, :, :3] * (a[:, :, 3:4] / 255.0), a[:, :, 3:4]], axis=2)
    pb = np.concatenate([b[:, :, :3] * (b[:, :, 3:4] / 255.0), b[:, :, 3:4]], axis=2)
    return float(np.mean(np.abs(pa[vis] - pb[vis])))


def count_enclosed_pockets(alpha: np.ndarray) -> int:
    """Count fully enclosed 0-alpha holes surrounded by visible pixels (not touching border)."""
    from collections import deque

    h, w = alpha.shape
    trans = alpha == 0
    seen = np.zeros_like(trans, dtype=bool)
    q: deque[tuple[int, int]] = deque()
    for y in range(h):
        for x in (0, w - 1):
            if trans[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((x, y))
    for x in range(w):
        for y in (0, h - 1):
            if trans[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((x, y))
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and trans[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((nx, ny))
    holes = trans & (~seen)
    return int(np.count_nonzero(holes))


def build() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    if UPLOAD_SRC.exists() and (
        not SOURCE_SHEET.exists() or SOURCE_SHEET.read_bytes() != UPLOAD_SRC.read_bytes()
    ):
        shutil.copy2(UPLOAD_SRC, SOURCE_SHEET)
    if not SOURCE_SHEET.exists():
        raise FileNotFoundError(f"Missing Drum source sheet: {SOURCE_SHEET}")

    write_gdignore(SOURCE_DIR)
    if RAW_FRAMES_DIR.exists():
        shutil.rmtree(RAW_FRAMES_DIR)
    RAW_FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    sheet_img = Image.open(SOURCE_SHEET).convert("RGBA")
    sheet_rgba = np.asarray(sheet_img, dtype=np.uint8)

    # Verify exact color palette from source sheet (minus magenta key)
    solid_mask = ~(
        (sheet_rgba[:, :, 0] == BG_RGB[0])
        & (sheet_rgba[:, :, 1] == BG_RGB[1])
        & (sheet_rgba[:, :, 2] == BG_RGB[2])
    )
    allowed_colors = {tuple(int(v) for v in c) for c in np.unique(sheet_rgba[solid_mask][:, :3], axis=0)}

    # Exact measured slots on uploaded_media_1794748948973.png (480x528)
    slots: dict[str, dict[str, Any]] = {
        # Row 0: idle (4) + jump (2)
        "idle_00": {"rect": (8, 14, 56, 50), "mode": "ground_belt", "y_off": 0},
        "idle_01": {"rect": (73, 17, 55, 48), "mode": "ground_belt", "y_off": 0},
        "idle_02": {"rect": (140, 19, 55, 47), "mode": "ground_belt", "y_off": 0},
        "idle_03": {"rect": (207, 19, 55, 48), "mode": "ground_belt", "y_off": 0},
        "jump_00": {"rect": (300, 5, 54, 48), "mode": "ground_belt", "y_off": -12},
        "jump_01": {"rect": (361, 5, 54, 48), "mode": "ground_belt", "y_off": -18},
        # Row 1: teleport (speed-vanish)
        "teleport_00": {"rect": (9, 81, 68, 48), "mode": "ground_belt", "y_off": 0},
        "teleport_01": {"rect": (84, 81, 73, 48), "mode": "center_bbox", "y_off": 0},
        "teleport_02": {"rect": (178, 80, 62, 48), "mode": "center_bbox", "y_off": 0},
        "teleport_03": {"rect": (249, 79, 54, 48), "mode": "ground_belt", "y_off": -4},
        # Row 2: attack_light (shoulder smash per Owner)
        "attack_light_00": {"rect": (12, 146, 38, 49), "mode": "ground_belt", "y_off": 0},
        "attack_light_01": {"rect": (65, 146, 48, 49), "mode": "ground_belt", "y_off": 0},
        "attack_light_02": {"rect": (120, 144, 45, 51), "mode": "ground_belt", "y_off": 0},
        "attack_light_03": {"rect": (175, 142, 72, 53), "mode": "ground_belt", "y_off": 0},
        "attack_light_04": {"rect": (262, 142, 72, 53), "mode": "ground_belt", "y_off": 0},
        "attack_light_05": {"rect": (340, 147, 66, 48), "mode": "ground_belt", "y_off": 0},
        # Row 3 prep + Row 4 + R5-C0: power_up (11 frames — preparation claw raise -> electric charge & cast)
        "power_up_00": {"rect": (10, 221, 54, 49), "mode": "ground_belt", "y_off": 0},   # R3-C0 prep windup
        "power_up_01": {"rect": (73, 220, 57, 50), "mode": "ground_belt", "y_off": 0},   # R3-C1 raise claw
        "power_up_02": {"rect": (139, 215, 52, 55), "mode": "ground_belt", "y_off": 0},  # R3-C2 high coil
        "power_up_03": {"rect": (206, 220, 69, 50), "mode": "ground_belt", "y_off": 0},  # R3-C3 lunge forward
        "power_up_04": {"rect": (284, 223, 71, 47), "mode": "ground_belt", "y_off": 0},  # R3-C4 arm extended
        "power_up_05": {"rect": (93, 284, 71, 47), "mode": "ground_belt", "y_off": 0},   # R3-C5/R4-C1 transition aim
        "power_up_06": {"rect": (171, 284, 79, 47), "mode": "ground_belt", "y_off": 0},  # R4-C2 gather sparks
        "power_up_07": {"rect": (9, 284, 75, 47), "mode": "ground_belt", "y_off": 0},    # R4-C0 charge glow
        "power_up_08": {"rect": (349, 284, 71, 47), "mode": "ground_belt", "y_off": 0},  # R4-C4 condensed orb on hand
        "power_up_09": {"rect": (259, 284, 82, 47), "mode": "ground_belt", "y_off": 0},  # R4-C3 peak white/cyan flash
        "power_up_10": {"rect": (9, 342, 78, 47), "mode": "ground_belt", "y_off": 0},    # R5-C0 spiky blast cast
        # Row 6-7: hit + ko + getup
        "hit_00": {"rect": (9, 411, 55, 49), "mode": "ground_belt", "y_off": 0},
        "hit_01": {"rect": (71, 411, 51, 50), "mode": "ground_belt", "y_off": 0},
        "hit_02": {"rect": (127, 419, 57, 42), "mode": "ground_belt", "y_off": 0},
        "ko_00": {"rect": (193, 412, 54, 49), "mode": "ground_belt", "y_off": -10},
        "ko_01": {"rect": (255, 412, 54, 49), "mode": "ground_belt", "y_off": -12},
        "ko_02": {"rect": (320, 425, 62, 36), "mode": "ground_belt", "y_off": -14},
        "ko_03": {"rect": (387, 423, 63, 33), "mode": "ground_belt", "y_off": -8},
        "ko_04": {"rect": (9, 478, 55, 31), "mode": "ground_belt", "y_off": -3},
        "ko_05": {"rect": (71, 480, 63, 31), "mode": "ground_belt", "y_off": -1},
        "ko_06": {"rect": (143, 487, 57, 27), "mode": "ground_belt", "y_off": 0},
        "getup_00": {"rect": (206, 482, 51, 32), "mode": "ground_belt", "y_off": 0},
        "getup_01": {"rect": (265, 472, 49, 42), "mode": "ground_belt", "y_off": 0},
        "getup_02": {"rect": (319, 469, 51, 45), "mode": "ground_belt", "y_off": 0},
        "getup_03": {"rect": (375, 470, 54, 45), "mode": "ground_belt", "y_off": 0},
        # Row 5 C1..C13: Independent electric FX
        "fx_orb_00": {"rect": (157, 355, 32, 32), "mode": "fx_center", "y_off": 0},
        "fx_orb_01": {"rect": (281, 358, 32, 32), "mode": "fx_center", "y_off": 0},
        "fx_ring_00": {"rect": (195, 359, 32, 32), "mode": "fx_center", "y_off": 0},
        "fx_ring_01": {"rect": (325, 359, 32, 32), "mode": "fx_center", "y_off": 0},
        "fx_spark_00": {"rect": (365, 369, 16, 11), "mode": "fx_center", "y_off": 0},
        "fx_spark_01": {"rect": (117, 370, 32, 15), "mode": "fx_center", "y_off": 0},
        "fx_spark_02": {"rect": (240, 362, 32, 24), "mode": "fx_center", "y_off": 0},
        "fx_spark_03": {"rect": (387, 368, 16, 14), "mode": "fx_center", "y_off": 0},
        "fx_spark_04": {"rect": (411, 367, 16, 16), "mode": "fx_center", "y_off": 0},
    }

    frame_entries: list[dict[str, str]] = []
    frame_imgs: dict[str, Image.Image] = {}
    placement_report: dict[str, Any] = {}

    for name, spec in slots.items():
        crop = key_slot_exact(sheet_rgba, spec["rect"])
        img, meta = place_on_canvas(
            crop,
            align_mode=spec["mode"],
            y_offset=spec.get("y_off", 0),
        )
        arr = np.asarray(img, dtype=np.uint8)
        vis = arr[:, :, 3] > 0
        # Enforce 100% color & alpha preservation check
        alphas = set(int(v) for v in np.unique(arr[:, :, 3]))
        if not alphas.issubset({0, 255}):
            raise AssertionError(f"{name}: non-binary alpha {alphas}")
        rgbs = {tuple(int(v) for v in c) for c in np.unique(arr[vis][:, :3], axis=0)}
        if not rgbs.issubset(allowed_colors):
            diff = rgbs - allowed_colors
            raise AssertionError(f"{name}: color drift vs source sheet: {diff}")
        pockets = count_enclosed_pockets(arr[:, :, 3])
        if pockets != 0 and not name.startswith(("teleport_", "fx_")):
            print(f"[INFO] {name}: transparent enclosed region px={pockets} (check visually)")

        out_path = RAW_FRAMES_DIR / f"{name}.png"
        img.save(out_path, optimize=True)
        frame_imgs[name] = img
        frame_entries.append({"name": name, "file": f"raw_frames/{name}.png"})
        placement_report[name] = {**meta, "enclosed_transparent_px": pockets}

    # Check ko_00 vs ko_01 premultiplied MAE
    ko_pair_mae = premul_visible_mae(frame_imgs["ko_00"], frame_imgs["ko_01"])
    ko_frames = ["ko_00", "ko_01", "ko_02", "ko_03", "ko_04", "ko_05", "ko_06"]
    ko_ticks = [5, 5, 5, 5, 5, 5, 10]
    if ko_pair_mae < 1.55:
        # Hold threshold trigger check
        print(f"[NOTE] ko_00 vs ko_01 premul MAE={ko_pair_mae:.3f}")

    # Measure cyan fist tip center on power_up_10 (R5-C0 spiky release)
    p5_arr = np.asarray(frame_imgs["power_up_10"], dtype=np.uint8)
    cyan_hand = (p5_arr[:, :, 3] > 0) & (p5_arr[:, :, 2] > 200) & (p5_arr[:, :, 0] < 120)
    cys, cxs = np.where(cyan_hand)
    cast_origin_px = [int(np.percentile(cxs, 85)), int(round(float(np.mean(cys))))]
    print(f"[INFO] power_up_10 release origin_canvas_px={cast_origin_px}")

    # Load verified 8-frame bipedal walk frames (strictly 12 idle palette colors + binary alpha + 0 pockets)
    walk_names: list[str] = []
    for wi in range(8):
        wname = f"walk_{wi:02d}"
        wsrc = WALK_FRAMES_DIR / f"{wname}.png"
        if not wsrc.exists():
            raise FileNotFoundError(f"Missing Drum walk frame: {wsrc}")
        wimg = Image.open(wsrc).convert("RGBA")
        if wimg.size != (CANVAS_W, CANVAS_H):
            raise AssertionError(f"{wname}: unexpected canvas {wimg.size}")
        warr = np.asarray(wimg, dtype=np.uint8)
        walphas = {int(v) for v in np.unique(warr[:, :, 3])}
        if not walphas.issubset({0, 255}):
            raise AssertionError(f"{wname}: non-binary alpha {walphas}")
        wvis = warr[:, :, 3] > 0
        wrgbs = {tuple(int(v) for v in c) for c in np.unique(warr[wvis][:, :3], axis=0)}
        if not wrgbs.issubset(allowed_colors):
            raise AssertionError(f"{wname}: walk color drift vs source sheet: {wrgbs - allowed_colors}")
        wpockets = count_enclosed_pockets(warr[:, :, 3])
        if wpockets != 0:
            raise AssertionError(f"{wname}: enclosed transparent pockets={wpockets}")
        wimg.save(RAW_FRAMES_DIR / f"{wname}.png", optimize=True)
        frame_imgs[wname] = wimg
        frame_entries.append({"name": wname, "file": f"raw_frames/{wname}.png"})
        walk_names.append(wname)
        placement_report[wname] = {"source": f"walk_frames/{wname}.png", "enclosed_transparent_px": 0}

    manifest = {
        "schema": "generate2dsprite.animation_clips.v2",
        "art_source": "host_image",
        "pixel_art": True,
        "sampling": "nearest",
        "body_height_px": 50,
        "anchor_px": FOOT_ANCHOR,
        "shadow": {"rx": 24, "ry": 3, "opacity": 0.32},
        "frames": frame_entries,
        "clips": {
            "idle": {
                "loop_policy": "cycle",
                "role": "player",
                "frames": ["idle_00", "idle_01", "idle_02", "idle_03"],
                "ticks": [10, 9, 10, 9],
            },
            "walk": {
                "loop_policy": "cycle",
                "role": "player",
                "frames": walk_names,
                "ticks": [6, 6, 6, 6, 6, 6, 6, 6],
            },
            "jump": {
                "loop_policy": "oneshot",
                "role": "player",
                "frames": ["jump_00", "jump_01"],
                "ticks": [8, 12],
            },
            "teleport": {
                "loop_policy": "oneshot",
                "role": "player",
                "frames": ["teleport_00", "teleport_01", "teleport_02", "teleport_03"],
                "ticks": [4, 4, 4, 6],
                "events": [
                    {"at": 2, "name": "custom:teleport_relocate"},
                    {"at": 3, "name": "end"},
                ],
            },
            "attack_light": {
                "loop_policy": "oneshot",
                "role": "player",
                "keys": {"wind_start": 0, "wind_peak": 1, "strike": 3, "recover": 5, "end": 5},
                "hitstop_ticks": 0,
                "frames": [
                    "attack_light_00",
                    "attack_light_01",
                    "attack_light_02",
                    "attack_light_03",
                    "attack_light_04",
                    "attack_light_05",
                ],
                "ticks": [5, 4, 3, 3, 4, 5],
                "events": [
                    {"at": 0, "name": "tell"},
                    {"at": 3, "name": "hit"},
                    {"at": 5, "name": "end"},
                ],
            },
            "power_up": {
                "loop_policy": "oneshot",
                "role": "player",
                "keys": {"wind_start": 0, "wind_peak": 9, "strike": 10, "recover": 10, "end": 10},
                "hitstop_ticks": 0,
                "frames": [
                    "power_up_00",
                    "power_up_01",
                    "power_up_02",
                    "power_up_03",
                    "power_up_04",
                    "power_up_05",
                    "power_up_06",
                    "power_up_07",
                    "power_up_08",
                    "power_up_09",
                    "power_up_10",
                ],
                "ticks": [5, 5, 4, 4, 4, 4, 5, 5, 4, 4, 8],
                "events": [
                    {"at": 10, "name": "custom:fireball_release"},
                    {"at": 10, "name": "end"},
                ],
            },
            "hit": {
                "loop_policy": "oneshot",
                "role": "player",
                "frames": ["hit_00", "hit_01", "hit_02"],
                "ticks": [5, 5, 6],
            },
            "ko": {
                "loop_policy": "oneshot",
                "role": "player",
                "frames": ko_frames,
                "ticks": ko_ticks,
            },
            "getup": {
                "loop_policy": "oneshot",
                "role": "player",
                "frames": ["getup_00", "getup_01", "getup_02", "getup_03"],
                "ticks": [5, 5, 5, 6],
            },
            "electric_orb_fx": {
                "loop_policy": "cycle",
                "role": "fx",
                "frames": ["fx_orb_00", "fx_orb_01"],
                "ticks": [4, 4],
            },
            "electric_ring_fx": {
                "loop_policy": "cycle",
                "role": "fx",
                "frames": [
                    "fx_ring_00",
                    "fx_ring_01",
                    "fx_spark_00",
                    "fx_spark_01",
                    "fx_spark_02",
                    "fx_spark_03",
                    "fx_spark_04",
                ],
                "ticks": [3, 3, 3, 3, 3, 3, 3],
            },
        },
        "states": {"idle": "idle", "walk": "walk", "jump": "jump", "attack": "attack_light"},
    }

    manifest_path = SOURCE_DIR / "clips-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Build clean clips/
    if CLIPS_DIR.exists():
        shutil.rmtree(CLIPS_DIR)
    cmd_clips = [
        sys.executable,
        str(BUILD_CLIPS),
        "--manifest",
        str(manifest_path),
        "--output-dir",
        str(CLIPS_DIR),
        "--preview-scale",
        "2",
        "--strict",
    ]
    res_clips = subprocess.run(cmd_clips, cwd=str(ROOT), capture_output=True, text=True)
    if res_clips.returncode != 0:
        print(res_clips.stdout)
        print(res_clips.stderr, file=sys.stderr)
        sys.exit(res_clips.returncode)
    write_gdignore(CLIPS_DIR)

    # Export clean godot_bundle/
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    cmd_export = [
        sys.executable,
        str(EXPORT_ENGINE),
        "--clips",
        str(CLIPS_DIR / "animation-clips.json"),
        "--target",
        "all",
        "--output-dir",
        str(BUNDLE_DIR),
        "--name",
        "drum",
        "--sampling",
        "nearest",
        "--godot-fps",
        "auto",
        "--ppu",
        "64",
    ]
    res_exp = subprocess.run(cmd_export, cwd=str(ROOT), capture_output=True, text=True)
    if res_exp.returncode != 0:
        print(res_exp.stdout)
        print(res_exp.stderr, file=sys.stderr)
        sys.exit(res_exp.returncode)

    # Embed canonical render_contract from assets/roster.json so server.py & Web preview stay 1:1 synced
    roster_path = ROOT / "assets" / "roster.json"
    if roster_path.is_file():
        roster_data = json.loads(roster_path.read_text(encoding="utf-8"))
        drum_entry = next(
            (c for c in roster_data.get("characters", []) if c.get("character_id") == "drum"),
            None,
        )
        if drum_entry and "render_contract" in drum_entry:
            export_json_path = BUNDLE_DIR / "engine-export.json"
            export_meta = json.loads(export_json_path.read_text(encoding="utf-8"))
            export_meta["render_contract"] = drum_entry["render_contract"]
            export_json_path.write_text(json.dumps(export_meta, indent=2) + "\n", encoding="utf-8")

    # Run official sharpness measurement tool on idle_00.png
    res_sharp = subprocess.run(
        [sys.executable, str(TOOLS_SHARPNESS), str(RAW_FRAMES_DIR / "idle_00.png")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    print(res_sharp.stdout)
    (SOURCE_DIR / "placement_report.json").write_text(
        json.dumps(
            {
                "cast_origin_px": cast_origin_px,
                "ko_00_01_premul_mae": round(ko_pair_mae, 4),
                "slots": placement_report,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("OK: drum bundle built cleanly.")


if __name__ == "__main__":
    build()
