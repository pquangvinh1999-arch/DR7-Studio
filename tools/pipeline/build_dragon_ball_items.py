#!/usr/bin/env python3
"""Deterministic 1x (32x32) game-item extractor & shared-atlas packager for Dragon Balls 1..7."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
SOURCE_CANDIDATES = [
    ROOT / "assets" / "rituals" / "shenron_summon" / "source" / "owner-1.png",
    ROOT / "image copy.png",
]
EXPECTED_SOURCE_SHA256 = "0368f9a6c20f634b391dc893d70cc70757e14204b4feade4817b6e861cfbe876"
MEASURE_TOOL = ROOT / "tools" / "art" / "measure_pixel_sharpness.py"

ITEMS_DIR = ROOT / "assets" / "items"
CATALOG_JSON = ITEMS_DIR / "catalog.json"
ITEM_DIR = ITEMS_DIR / "dragon_balls"
SOURCE_DIR = ITEM_DIR / "source"
RAW_SOURCE_DIR = SOURCE_DIR / "source_crops"
ITEM_1X_DIR = SOURCE_DIR / "frames_1x"
CLIPS_DIR = ITEM_DIR / "clips"
REVIEW_DIR = CLIPS_DIR / "review"
GODOT_DIR = ITEM_DIR / "godot"
QA_DOC = ROOT / "docs" / "items" / "dragon-balls-v1-qa.json"

FRAME_W = 32
FRAME_H = 32
BAG_ANCHOR_PX = [16, 16]
SPARKLE_ANCHOR_TOP_LEFT_PX = [6, 5]
TICK_HZ = 60

# Diagonal full-body shine sweep across 7 active frames + 1 calm rest pause = 72 ticks (1.20s cycle @ 60Hz)
SPARKLE_FRAME_TICKS = [3, 3, 3, 3, 3, 3, 4, 50]
SHEEN_CENTERS_U = [13.0, 19.0, 25.0, 31.0, 37.0, 43.0, 49.0]

DROP_PHYSICS = {
    "jump_height_px": 10.0,
    "rise_ticks": 10,
    "fall_min_ticks": 12,
    "fall_gravity_px_per_s2": 1800.0,
    "arc_dx_px": 8.0,
    "roll_distance_px": 10.0,
    "roll_ticks": 18,
    "roll_angle_rad": 0.625,
    "start_sheen_after_roll": True,
}

PICKUP_PHYSICS = {
    "duration_ticks": 30,
    "start_scale": 1.0,
    "end_scale": 0.05,
    "arc_lift_px": 18.0,
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_gdignore(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / ".gdignore").write_text("", encoding="utf-8")


def count_enclosed_pockets(alpha: np.ndarray) -> int:
    h, w = alpha.shape
    trans = alpha == 0
    seen = np.zeros_like(trans, dtype=bool)
    q: deque[tuple[int, int]] = deque()
    for y in range(h):
        for x in (0, w - 1):
            if trans[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    for x in range(w):
        for y in (0, h - 1):
            if trans[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and trans[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))
    return int(np.sum(trans & ~seen))


def extract_clean_source_ball(rgb_crop: np.ndarray, comp_mask: np.ndarray) -> Image.Image:
    """Extract a single Dragon Ball cleanly from pure-white background without stray rim speckles."""
    owned = ndimage.binary_fill_holes(comp_mask)
    lbl, nl = ndimage.label(owned)
    if nl > 1:
        sizes = np.bincount(lbl.ravel())
        sizes[0] = 0
        owned = lbl == int(sizes.argmax())

    c = rgb_crop.astype(np.float32)
    inner = ndimage.binary_erosion(owned, iterations=2)
    inner_idx = ndimage.distance_transform_edt(~inner, return_distances=False, return_indices=True)
    fg_rgb = c[tuple(inner_idx)]
    bg_rgb = np.array([255.0, 255.0, 255.0], dtype=np.float32)
    v = bg_rgb - fg_rgb
    alpha = np.clip(
        np.sum((bg_rgb - c) * v, axis=2) / np.maximum(1.0, np.sum(v * v, axis=2)),
        0.0,
        1.0,
    )

    rgba = np.zeros((*rgb_crop.shape[:2], 4), dtype=np.uint8)
    core = ndimage.binary_erosion(owned, iterations=1)
    rgba[core, :3] = rgb_crop[core]
    rgba[core, 3] = 255

    rim = owned & ~core
    a_rim = alpha[rim]
    keep = a_rim >= 0.20
    rim_y, rim_x = np.where(rim)
    ky = rim_y[keep]
    kx = rim_x[keep]
    ka = a_rim[keep, None]
    unmixed = np.clip((c[ky, kx] - 255.0 * (1.0 - ka)) / np.maximum(ka, 1e-4), 0.0, 255.0)
    rgba[ky, kx, :3] = unmixed.round().astype(np.uint8)
    rgba[ky, kx, 3] = (a_rim[keep] * 255.0).round().astype(np.uint8)

    yy, xx = np.where(rgba[:, :, 3] > 0)
    return Image.fromarray(rgba, mode="RGBA").crop(
        (int(xx.min()), int(yy.min()), int(xx.max() + 1), int(yy.max() + 1))
    )


def premultiplied_box_1x(src_im: Image.Image, target_w: int = FRAME_W, target_h: int = FRAME_H) -> Image.Image:
    """Single-step premultiplied BOX area downsample to exact 1x hard-alpha 0/255 sprite."""
    side = max(src_im.width, src_im.height)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(src_im, ((side - src_im.width) // 2, (side - src_im.height) // 2))

    arr = np.asarray(square, dtype=np.float32) / 255.0
    alpha = arr[:, :, 3]
    red_a = np.asarray(
        Image.fromarray(alpha, mode="F").resize((target_w, target_h), Image.Resampling.BOX)
    )
    out = np.zeros((target_h, target_w, 4), dtype=np.uint8)
    solid = red_a >= 0.50
    for ch in range(3):
        pre = np.asarray(
            Image.fromarray(arr[:, :, ch] * alpha, mode="F").resize((target_w, target_h), Image.Resampling.BOX)
        )
        out[:, :, ch] = np.where(
            solid,
            np.clip(pre / np.maximum(red_a, 1e-8) * 255.0, 0.0, 255.0).round(),
            0,
        ).astype(np.uint8)
    out[:, :, 3] = solid.astype(np.uint8) * 255

    # Keep only single connected component & guarantee zero enclosed transparent pockets
    lbl, nl = ndimage.label(out[:, :, 3] > 0)
    if nl > 1:
        sizes = np.bincount(lbl.ravel())
        sizes[0] = 0
        keep = lbl == int(sizes.argmax())
        out[~keep] = [0, 0, 0, 0]
    assert count_enclosed_pockets(out[:, :, 3]) == 0, "Enclosed transparent pocket detected!"
    return Image.fromarray(out, mode="RGBA")


def build_sparkle_frames(common_mask: np.ndarray) -> list[Image.Image]:
    """Generate crisp 8-frame diagonal full-body shine sweep strictly inside common sphere mask."""
    yy, xx = np.indices((FRAME_H, FRAME_W))
    u = xx.astype(np.float32) + yy.astype(np.float32)
    r_from_center = np.hypot(xx.astype(np.float32) - 15.5, yy.astype(np.float32) - 15.5)
    rim_weight = np.where(r_from_center >= 14.8, 0.45, 1.0)

    frames: list[Image.Image] = []
    for uc in SHEEN_CENTERS_U:
        arr = np.zeros((FRAME_H, FRAME_W, 4), dtype=np.uint8)
        dist_main = np.abs(u - float(uc))
        dist_sub = np.abs(u - (float(uc) - 4.8))
        alpha_main = np.clip(1.0 - np.maximum(0.0, dist_main - 0.6) / 1.9, 0.0, 1.0)
        alpha_sub = np.clip(1.0 - dist_sub / 1.35, 0.0, 1.0) * 0.45
        alpha = np.maximum(alpha_main * 0.84, alpha_sub)
        final_a = (alpha * rim_weight * 255.0).round().astype(np.uint8)
        valid = common_mask & (final_a > 12)
        arr[valid, 0] = 255
        arr[valid, 1] = np.where(alpha_main[valid] > 0.5, 255, 248)
        arr[valid, 2] = np.where(alpha_main[valid] > 0.5, 236, 185)
        arr[valid, 3] = final_a[valid]
        frames.append(Image.fromarray(arr, mode="RGBA"))

    frames.append(Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0)))
    return frames


def checker_tile(w: int, h: int, cell: int = 4) -> Image.Image:
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    yy, xx = np.indices((h, w))
    even = ((xx // cell) + (yy // cell)) % 2 == 0
    arr[even] = [204, 210, 218, 255]
    arr[~even] = [148, 156, 168, 255]
    return Image.fromarray(arr, mode="RGBA")


def build_review_sheets(balls: list[Image.Image], sparkles: list[Image.Image]) -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    rocky_bg_path = ROOT / "assets" / "maps" / "rocky_plateau" / "rocky-plateau-bg.jpg"
    rocky = Image.open(rocky_bg_path).convert("RGBA").resize((1920, 1080))
    rock_tile = rocky.crop((680, 808, 680 + FRAME_W, 808 + FRAME_H))

    # 1. Filmstrip 3+1 backgrounds (Dark / Light / Checker / Rocky) across 7 balls + 6 sparkle phases
    zoom = 4
    cw, ch = FRAME_W * zoom, FRAME_H * zoom
    pad = 8
    bgs = [
        ("Dark", Image.new("RGBA", (FRAME_W, FRAME_H), (11, 14, 23, 255))),
        ("Light", Image.new("RGBA", (FRAME_W, FRAME_H), (229, 231, 235, 255))),
        ("Checker", checker_tile(FRAME_W, FRAME_H, 4)),
        ("Rocky", rock_tile),
    ]
    sheet = Image.new(
        "RGBA",
        (8 * (cw + pad) + pad + 72, len(bgs) * (ch + pad) + pad + 26),
        (15, 23, 42, 255),
    )
    draw = ImageDraw.Draw(sheet)
    for col in range(8):
        draw.text((76 + col * (cw + pad) + 4, 6), f"Ball {min(col + 1, 7)} + F{col}", fill=(226, 232, 240, 255))
    for row, (label, bg) in enumerate(bgs):
        y0 = 26 + pad + row * (ch + pad)
        draw.text((8, y0 + ch // 2 - 6), label, fill=(253, 224, 71, 255))
        for col in range(8):
            sp = sparkles[col]
            ball_im = balls[col % 7]
            comp = bg.copy()
            comp.alpha_composite(ball_im)
            comp.alpha_composite(sp)
            big = comp.resize((cw, ch), Image.Resampling.NEAREST)
            x0 = 72 + pad + col * (cw + pad)
            sheet.paste(big, (x0, y0))
    sheet.save(REVIEW_DIR / "filmstrip-3bg.png")

    # 2. Map Drop (1x vs 2x next to Drum) visual sheet
    map_cmp = rocky.copy()
    drum_atlas = Image.open(ROOT / "assets/drum/godot_bundle/godot/drum-atlas-00.png").convert("RGBA")
    drum_idle0 = drum_atlas.crop((3, 3, 131, 99)).resize((320, 240), Image.Resampling.NEAREST)
    map_cmp.alpha_composite(drum_idle0, (420, 630))
    for i, b in enumerate(balls):
        bx = 710 + i * 44
        map_cmp.alpha_composite(b, (bx, 840 - 32))
        map_cmp.alpha_composite(sparkles[min(i, 6)], (bx, 840 - 32))
        comp2 = b.copy()
        comp2.alpha_composite(sparkles[min(i, 6)])
        b2 = comp2.resize((64, 64), Image.Resampling.NEAREST)
        map_cmp.alpha_composite(b2, (1045 + i * 74, 840 - 64))
    bag_crop = map_cmp.crop((400, 560, 1600, 910))
    bag_crop.save(REVIEW_DIR / "map-vs-bag-preview.png")


def build_godot_tres_and_atlas(
    balls: list[Image.Image],
    sparkles: list[Image.Image],
) -> tuple[Path, Path, dict[str, list[int]], dict[str, Any]]:
    GODOT_DIR.mkdir(parents=True, exist_ok=True)
    atlas_path = GODOT_DIR / "dragon_balls-atlas-00.png"
    tres_path = GODOT_DIR / "dragon_balls.tres"

    # 15 cells of 32x32 with 1px extrude + 2px outer pad cleanly placed into single page (304x80)
    pad = 2
    extrude = 1
    cols = 8
    cell_step = FRAME_W + 2 * extrude + pad
    atlas_w = pad + cols * cell_step
    atlas_h = pad + 2 * cell_step
    # Round up cleanly to multiple of 16
    atlas_w = ((atlas_w + 15) // 16) * 16
    atlas_h = ((atlas_h + 15) // 16) * 16

    atlas_img = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
    ordered_frames: list[tuple[str, Image.Image]] = [
        *(("ball_%02d" % (i + 1), balls[i]) for i in range(7)),
        *(("sparkle_%02d" % j, sparkles[j]) for j in range(len(sparkles))),
    ]

    regions: dict[str, list[int]] = {}
    sub_ids: list[str] = []
    sub_blocks: list[str] = []

    for idx, (key, im) in enumerate(ordered_frames):
        col = idx % cols
        row = idx // cols
        rx = pad + extrude + col * cell_step
        ry = pad + extrude + row * cell_step
        atlas_img.paste(im, (rx, ry))
        # Clamp-to-edge 1px extrude for safe texture sampling
        arr = np.asarray(im, dtype=np.uint8)
        patch = np.zeros((FRAME_H + 2, FRAME_W + 2, 4), dtype=np.uint8)
        patch[1:-1, 1:-1] = arr
        patch[0, 1:-1] = arr[0, :]
        patch[-1, 1:-1] = arr[-1, :]
        patch[:, 0] = patch[:, 1]
        patch[:, -1] = patch[:, -2]
        atlas_img.paste(Image.fromarray(patch, mode="RGBA"), (rx - 1, ry - 1))

        regions[key] = [rx, ry, FRAME_W, FRAME_H]
        sid = f"AtlasTexture_{key}"
        sub_ids.append(sid)
        sub_blocks.append(
            f'[sub_resource type="AtlasTexture" id="{sid}"]\n'
            f'atlas = ExtResource("1_atlas00")\n'
            f"region = Rect2({rx}, {ry}, {FRAME_W}, {FRAME_H})\n"
            f"filter_clip = true\n"
        )

    atlas_img.save(atlas_path)

    anim_defs: list[str] = []
    # 7 Dragon Ball static item animations: ball_01 .. ball_07
    for i in range(7):
        key = f"ball_{i + 1:02d}"
        sid = f"AtlasTexture_{key}"
        anim_defs.append(
            "{\n"
            '"frames": [{\n'
            '"duration": 6.0,\n'
            f'"texture": SubResource("{sid}")\n'
            "}],\n"
            '"loop": false,\n'
            f'"name": &"{key}",\n'
            '"speed": 60.0\n'
            "}"
        )

    # Shared independent top-left sparkle_fx loop animation (60Hz ticks)
    sparkle_frames_str = ", ".join(
        '{\n"duration": %.1f,\n"texture": SubResource("AtlasTexture_sparkle_%02d")\n}'
        % (float(SPARKLE_FRAME_TICKS[j]), j)
        for j in range(len(sparkles))
    )
    anim_defs.append(
        "{\n"
        f'"frames": [{sparkle_frames_str}],\n'
        '"loop": true,\n'
        '"name": &"sparkle_fx",\n'
        '"speed": 60.0\n'
        "}"
    )

    load_steps = len(ordered_frames) + 2
    tres_txt = (
        f'[gd_resource type="SpriteFrames" load_steps={load_steps} format=3]\n\n'
        '[ext_resource type="Texture2D" path="dragon_balls-atlas-00.png" id="1_atlas00"]\n\n'
        + "\n".join(sub_blocks)
        + "\n[resource]\n"
        "animations = ["
        + ", ".join(anim_defs)
        + "]\n"
    )
    tres_path.write_text(tres_txt, encoding="utf-8")

    atlas_meta = {
        "pages": 1,
        "size": [atlas_w, atlas_h],
        "padding": pad,
        "extrude": extrude,
        "cells": len(ordered_frames),
    }
    return atlas_path, tres_path, regions, atlas_meta


def run_sharpness_tool(path: Path) -> dict[str, Any]:
    res = subprocess.run(
        [sys.executable, str(MEASURE_TOOL), str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(res.stdout)


def resolve_source_image() -> Path:
    for cand in SOURCE_CANDIDATES:
        if cand.is_file():
            return cand
    raise FileNotFoundError(f"Missing owner source image in candidates: {SOURCE_CANDIDATES}")


def build() -> None:
    source_image = resolve_source_image()
    src_sha = sha256_file(source_image)
    if src_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"Source SHA mismatch: {src_sha} != {EXPECTED_SOURCE_SHA256}")

    write_gdignore(SOURCE_DIR)
    write_gdignore(CLIPS_DIR)
    RAW_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    ITEM_1X_DIR.mkdir(parents=True, exist_ok=True)
    GODOT_DIR.mkdir(parents=True, exist_ok=True)
    QA_DOC.parent.mkdir(parents=True, exist_ok=True)

    rgb = np.array(Image.open(source_image).convert("RGB"))
    bg_dist = np.linalg.norm(rgb.astype(np.float32) - 255.0, axis=2)
    fg = bg_dist > 14.0
    labels, n_labels = ndimage.label(fg)
    sizes = np.bincount(labels.ravel())

    extracted_src: dict[int, Image.Image] = {}
    extracted_boxes: dict[int, list[int]] = {}

    for lbl in range(1, n_labels + 1):
        if sizes[lbl] < 5000:
            continue
        comp = labels == lbl
        yy, xx = np.where(comp)
        x0 = max(0, int(xx.min()) - 4)
        y0 = max(0, int(yy.min()) - 4)
        x1 = min(rgb.shape[1], int(xx.max()) + 5)
        y1 = min(rgb.shape[0], int(yy.max()) + 5)
        im_src = extract_clean_source_ball(rgb[y0:y1, x0:x1], comp[y0:y1, x0:x1])

        arr = np.asarray(im_src)
        v = arr[:, :, :3].astype(int)
        stars = (arr[:, :, 3] > 128) & (v[:, :, 0] > 90) & (v[:, :, 0] < 210) & (v[:, :, 1] < 80) & (
            v[:, :, 0] - v[:, :, 1] > 55
        )
        sl, _ = ndimage.label(stars)
        star_count = len([sz for sz in np.bincount(sl.ravel())[1:] if sz > 150])
        assert star_count in range(1, 8) and star_count not in extracted_src, f"Bad star count {star_count}"
        extracted_src[star_count] = im_src
        extracted_boxes[star_count] = [x0, y0, x1, y1]
        im_src.save(RAW_SOURCE_DIR / f"dragon_ball_{star_count:02d}_src.png")

    assert set(extracted_src.keys()) == set(range(1, 8)), "Must detect all 7 Dragon Balls (1..7 stars)"

    balls_1x: list[Image.Image] = []
    sharpness_per_ball: dict[str, Any] = {}
    ball_entries: list[dict[str, Any]] = []
    bottom_rows: list[int] = []

    for num in range(1, 8):
        im1x = premultiplied_box_1x(extracted_src[num], FRAME_W, FRAME_H)
        out_path = ITEM_1X_DIR / f"dragon_ball_{num:02d}.png"
        im1x.save(out_path)
        balls_1x.append(im1x)

        metrics = run_sharpness_tool(out_path)
        arr = np.asarray(im1x)
        assert metrics["alpha_hardness_pct"] == 100.0, f"ball_{num:02d} must have 100% hard alpha"
        assert metrics["visible_alpha_hardness_pct"] == 100.0
        assert count_enclosed_pockets(arr[:, :, 3]) == 0
        yy = np.where(arr[:, :, 3] > 0)[0]
        bottom_y = int(yy.max()) + 1
        bottom_rows.append(bottom_y)
        sharpness_per_ball[f"ball_{num:02d}"] = metrics

    # Consistent resting baseline across all 7 balls on map ground_y
    map_anchor_y = max(bottom_rows)
    map_anchor_px = [16, map_anchor_y]

    common_mask = np.ones((FRAME_H, FRAME_W), dtype=bool)
    for b_im in balls_1x:
        common_mask &= np.asarray(b_im)[:, :, 3] > 0

    sparkles = build_sparkle_frames(common_mask)
    for p_old in ITEM_1X_DIR.glob("sparkle_*.png"):
        p_old.unlink()
    for j, sf in enumerate(sparkles):
        sf.save(ITEM_1X_DIR / f"sparkle_{j:02d}.png")

    atlas_path, tres_path, regions, atlas_meta = build_godot_tres_and_atlas(balls_1x, sparkles)
    build_review_sheets(balls_1x, sparkles)

    atlas_sha = sha256_file(atlas_path)
    tres_sha = sha256_file(tres_path)

    for num in range(1, 8):
        key = f"ball_{num:02d}"
        ball_entries.append({
            "number": num,
            "item_id": f"dragon_ball_{num:02d}",
            "display_name": f"Ngọc Rồng {num} Sao",
            "clip": key,
            "region": regions[key],
            "file_1x": f"assets/items/dragon_balls/source/frames_1x/dragon_ball_{num:02d}.png",
            "source_box_xyxy": extracted_boxes[num],
            "body_bbox_px": sharpness_per_ball[key]["body_bbox_px"],
            "edge_acutance_sobel": sharpness_per_ball[key]["edge_acutance_sobel"],
            "alpha_hardness_pct": sharpness_per_ball[key]["alpha_hardness_pct"],
        })

    item_export = {
        "schema": "dr7-studio.item_export.v1",
        "item_set_id": "dragon_balls",
        "display_name": "Bộ 7 Viên Ngọc Rồng (Item 1×)",
        "category": "quest_consumable_item",
        "source_isolation": "Extracted read-only from canonical owner-1 source; assets/rituals/shenron_summon/* untouched.",
        "source_image": {
            "file": str(source_image.relative_to(ROOT)),
            "sha256": src_sha,
            "size": [int(rgb.shape[1]), int(rgb.shape[0])],
        },
        "frame_size": [FRAME_W, FRAME_H],
        "sampling": "nearest",
        "pixel_art": True,
        "alpha_mode": "hard_0_255_body_with_fx_overlay",
        "bag_anchor_px": BAG_ANCHOR_PX,
        "map_anchor_px": map_anchor_px,
        "map_drop_test_scales": [1.0, 1.5, 2.0, 3.0],
        "default_map_test_scale": 1.0,
        "default_bag_scale": 1.0,
        "sparkle_fx": {
            "clip": "sparkle_fx",
            "style": "diagonal_body_sheen",
            "position_zone": "full_sphere_diagonal_sweep",
            "independent_overlay": True,
            "shared_across_variants": True,
            "show_on_map_after_roll": True,
            "show_in_bag": False,
            "tick_hz": TICK_HZ,
            "ticks": SPARKLE_FRAME_TICKS,
            "total_ticks": sum(SPARKLE_FRAME_TICKS),
            "frames": [regions[f"sparkle_{j:02d}"] for j in range(len(sparkles))],
        },
        "drop_physics": DROP_PHYSICS,
        "pickup_physics": PICKUP_PHYSICS,
        "atlas": {
            **atlas_meta,
            "file": "assets/items/dragon_balls/godot/dragon_balls-atlas-00.png",
            "sha256": atlas_sha,
        },
        "godot": {
            "prefab": "res://scenes/items/DragonBallItem2D.tscn",
            "script": "res://scenes/items/DragonBallItem2D.gd",
            "frames_tres": "res://assets/items/dragon_balls/godot/dragon_balls.tres",
            "frames_tres_sha256": tres_sha,
            "texture_filter": "nearest",
        },
        "variants": ball_entries,
        "qa": {
            "status": "owner_approved",
            "owner_approved": True,
            "body_alpha_hardness_pct": 100.0,
            "enclosed_key_pockets": 0,
            "opaque_key_px": 0,
            "review_sheets": [
                "assets/items/dragon_balls/clips/review/filmstrip-3bg.png",
                "assets/items/dragon_balls/clips/review/map-vs-bag-preview.png",
            ],
        },
    }

    export_path = ITEM_DIR / "item-export.json"
    export_path.write_text(json.dumps(item_export, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    catalog = {
        "schema": "dr7-studio.item_catalog.v1",
        "items": [
            {
                "item_set_id": "dragon_balls",
                "display_name": "Bộ 7 Viên Ngọc Rồng (1× = 32×32)",
                "category": "quest_consumable_item",
                "status": "owner_approved",
                "frame_size": [FRAME_W, FRAME_H],
                "default_map_test_scale": 1.0,
                "default_bag_scale": 1.0,
                "export_json": "assets/items/dragon_balls/item-export.json",
                "export_sha256": sha256_file(export_path),
                "godot_prefab": "res://scenes/items/DragonBallItem2D.tscn",
                "godot_tres": "res://assets/items/dragon_balls/godot/dragon_balls.tres",
                "atlas_path": "assets/items/dragon_balls/godot/dragon_balls-atlas-00.png",
                "atlas_sha256": atlas_sha,
                "variant_count": 7,
            }
        ],
    }
    CATALOG_JSON.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    qa_report = {
        "schema": "dr7-studio.item_qa.v1",
        "item_set_id": "dragon_balls",
        "status": "owner_approved",
        "atlas_sha256": atlas_sha,
        "tres_sha256": tres_sha,
        "export_sha256": sha256_file(export_path),
        "frame_size": [FRAME_W, FRAME_H],
        "map_anchor_px": map_anchor_px,
        "bag_anchor_px": BAG_ANCHOR_PX,
        "sparkle_total_ticks": sum(SPARKLE_FRAME_TICKS),
        "sharpness_by_ball": sharpness_per_ball,
    }
    QA_DOC.write_text(json.dumps(qa_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    clips_manifest = {
        "schema": "dr7-studio.item_clips.v1",
        "item_set_id": "dragon_balls",
        "frame_size": [FRAME_W, FRAME_H],
        "tick_hz": TICK_HZ,
        "variants": {f"ball_{i:02d}": {"frame_1x": f"source/frames_1x/dragon_ball_{i:02d}.png"} for i in range(1, 8)},
        "fx": {
            "sparkle_fx": {
                "ticks": SPARKLE_FRAME_TICKS,
                "loop": True,
                "frames": [f"source/frames_1x/sparkle_{j:02d}.png" for j in range(len(sparkles))],
            }
        },
    }
    (CLIPS_DIR / "item-clips.json").write_text(
        json.dumps(clips_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "ok": True,
        "item_set_id": "dragon_balls",
        "frame_size": [FRAME_W, FRAME_H],
        "map_anchor_px": map_anchor_px,
        "atlas_size": atlas_meta["size"],
        "atlas_sha256": atlas_sha,
        "tres_sha256": tres_sha,
        "variant_count": 7,
    }, ensure_ascii=False))


if __name__ == "__main__":
    build()
