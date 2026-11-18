#!/usr/bin/env python3
"""Extract the Owner's Floating Camera sheet at 70x74 without redrawing or blurring its pixels."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/art"))
import measure_pixel_sharpness as mps  # noqa: E402

SOURCE = ROOT / "assets/floating_camera/source/FloatingCamera.gif"
FALLBACK_SOURCE = ROOT / "FloatingCamera.gif"
OUT = ROOT / "work/characters/floating_camera/size70x74"
BODY_SIZE = (70, 74)
CANVAS = (192, 160)
ANCHOR = (96, 112)
SOURCE_BODY_SIZE = (20, 24)
SX = BODY_SIZE[0] / SOURCE_BODY_SIZE[0]
SY = BODY_SIZE[1] / SOURCE_BODY_SIZE[1]
FX_PIVOT = (96, 70)
ORIGIN_LOCAL_PX = [round(6 * SX), round(-2 * SY)]

# Atlas-gốc Rect(x0,y0,x1,y1); the source file remains untouched.
SLOTS = {
    "flight": [
        (7, 5, 27, 29), (35, 6, 55, 29), (63, 7, 83, 29),
        (88, 6, 108, 29), (119, 5, 139, 29), (146, 5, 166, 29),
        (174, 5, 194, 29), (202, 5, 222, 29), (227, 5, 247, 29),
    ],
    "attack_body": [(7, 43, 36, 70), (42, 44, 67, 79)],
    "projectile": [(83, 57, 91, 65), (98, 57, 106, 65),
                   (115, 57, 123, 65), (130, 57, 138, 65)],
    "hit": [(4, 94, 24, 118)],
    "explosion": [(31, 101, 47, 117), (54, 94, 78, 121),
                  (85, 94, 111, 121), (116, 96, 144, 120),
                  (151, 101, 175, 118), (186, 106, 196, 114)],
}

# Centers/baselines were measured on the body, excluding the muzzle flash.
BODY_REFERENCE = {
    "flight": [(r[0] + 10, 29) for r in SLOTS["flight"]],
    "attack_body": [(17, 68), (52, 69)],
    "hit": [(14, 118)],
}


def _check_frame_cleanliness(arr: np.ndarray, key: tuple[int, int, int]) -> dict:
    alpha = arr[:, :, 3]
    mask = alpha > 0
    rgb = arr[:, :, :3]
    is_key_rgb = np.all(rgb == np.array(key, dtype=np.uint8), axis=-1)
    opaque_key_px = int((mask & is_key_rgb).sum())
    # Enclosed background pockets: opaque key-colored pixels inside silhouette holes (alpha==0 holes are clean)
    filled = ndimage.binary_fill_holes(mask)
    transparent_holes_px = int((filled & ~mask).sum())
    enclosed_key_pockets = int((filled & mask & is_key_rgb).sum())
    # 1px inner visible boundary ring spill check (partial alpha or key RGB on visible boundary pixels)
    boundary = mask & ~ndimage.binary_erosion(mask)
    bnd_px = int(boundary.sum())
    partial_alpha = int((~np.isin(alpha, [0, 255])).sum())
    ring_spill = int((boundary & ((alpha < 255) | is_key_rgb)).sum())
    return {
        "opaque_key_px": opaque_key_px,
        "enclosed_key_pockets": enclosed_key_pockets,
        "transparent_interior_holes_px": transparent_holes_px,
        "partial_alpha_px": partial_alpha,
        "outer_ring_spill_fraction": round(ring_spill / max(1, bnd_px), 6),
    }


def build() -> None:
    src_path = SOURCE if SOURCE.is_file() else FALLBACK_SOURCE
    if not src_path.is_file():
        raise FileNotFoundError(SOURCE)
    OUT.mkdir(parents=True, exist_ok=True)
    frame_dir = OUT / "frames"
    frame_dir.mkdir(exist_ok=True)
    source = Image.open(src_path).convert("RGB")
    if source.size != (261, 123):
        raise ValueError(f"Unexpected source size: {source.size}")
    key = source.getpixel((0, 0))
    if key != (4, 121, 188):
        raise ValueError(f"Unexpected background RGB: {key}")

    entries = []
    source_map = []
    groups: dict[str, list[int]] = {}
    runtime_union = np.zeros((CANVAS[1], CANVAS[0]), dtype=bool)
    max_opaque_key = 0
    max_pockets = 0
    max_partial = 0
    max_spill = 0.0

    for group, rects in SLOTS.items():
        groups[group] = []
        for index, rect in enumerate(rects):
            crop = source.crop(rect).convert("RGBA")
            crop.putdata([(0, 0, 0, 0) if (r, g, b) == key else (r, g, b, 255)
                          for r, g, b, _ in crop.getdata()])
            target = (round(crop.width * SX), round(crop.height * SY))
            scaled = crop.resize(target, Image.Resampling.NEAREST)
            if group in BODY_REFERENCE:
                center_x, bottom_y = BODY_REFERENCE[group][index]
                x = round(ANCHOR[0] + (rect[0] - center_x) * SX)
                y = round(ANCHOR[1] + (rect[1] - bottom_y) * SY)
            else:
                x = round(ANCHOR[0] - scaled.width / 2)
                y = round(FX_PIVOT[1] - scaled.height / 2)
            if x < 0 or y < 0 or x + scaled.width > CANVAS[0] or y + scaled.height > CANVAS[1]:
                raise ValueError(f"Frame outside canvas: {group}-{index} {(x, y, *target)}")
            canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
            canvas.paste(scaled, (x, y))
            name = f"{group}-{index:02}.png"
            dest = frame_dir / name
            canvas.save(dest)

            arr = np.array(canvas)
            cstats = _check_frame_cleanliness(arr, key)
            max_opaque_key = max(max_opaque_key, cstats["opaque_key_px"])
            max_pockets = max(max_pockets, cstats["enclosed_key_pockets"])
            max_partial = max(max_partial, cstats["partial_alpha_px"])
            max_spill = max(max_spill, cstats["outer_ring_spill_fraction"])

            if not (group == "flight" and index == 8):
                mask = arr[:, :, 3] > 0
                if group == "projectile":
                    # Composite projectile at its muzzle spawn position for full_fx_bbox_px
                    dx = (ANCHOR[0] + ORIGIN_LOCAL_PX[0]) - FX_PIVOT[0]
                    dy = (ANCHOR[1] + ORIGIN_LOCAL_PX[1]) - FX_PIVOT[1]
                    ys, xs = np.nonzero(mask)
                    pxs = np.clip(xs + dx, 0, CANVAS[0] - 1)
                    pys = np.clip(ys + dy, 0, CANVAS[1] - 1)
                    runtime_union[pys, pxs] = True
                else:
                    runtime_union |= mask

            groups[group].append(len(entries))
            entries.append(f"frames/{name}")
            source_map.append({
                "name": name, "source_rect_xyxy": list(rect),
                "canvas_rect_xywh": [x, y, *target],
                "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                "qa": cstats,
            })

    f0_metrics = mps.measure(frame_dir / "flight-00.png")
    body_x, body_y, body_w, body_h = f0_metrics["body_bbox_px"]
    if (body_w, body_h) != BODY_SIZE:
        raise ValueError(f"Body bbox {(body_w, body_h)} != {BODY_SIZE}")

    uys, uxs = np.nonzero(runtime_union)
    fx_x0, fx_y0 = int(uxs.min()), int(uys.min())
    fx_x1, fx_y1 = int(uxs.max()) + 1, int(uys.max()) + 1
    full_fx_bbox = {"x": fx_x0, "y": fx_y0, "w": fx_x1 - fx_x0, "h": fx_y1 - fx_y0}

    # Timing is a review draft. Movement speed and spawn height are fixed by Owner.
    clips = {
        "idle": {"frames": groups["flight"][:-1], "ticks": 4, "loop_policy": "cycle", "role": "enemy"},
        "walk": {"frames": groups["flight"][:-1], "ticks": 4, "loop_policy": "cycle", "role": "enemy"},
        "attack_light": {"frames": groups["attack_body"], "ticks": [12, 8], "loop_policy": "oneshot", "role": "enemy",
                         "events": [{"at": 1, "name": "custom:launch", "data": {"projectile": "projectile_fx"}}]},
        "projectile_fx": {"frames": groups["projectile"], "ticks": 4, "loop_policy": "cycle", "role": "fx"},
        "hit": {"frames": groups["hit"], "ticks": 8, "loop_policy": "oneshot", "role": "enemy"},
        "ko": {"frames": groups["explosion"], "ticks": [4, 4, 5, 6, 5, 4], "loop_policy": "oneshot", "role": "enemy"},
    }
    manifest = {
        "schema": "generate2dsprite.animation_clips.v2",
        "frames": entries, "anchor_px": list(ANCHOR), "clips": clips,
        "states": {"idle": "idle", "moving": "walk", "attack": "attack_light", "hurt": "hit", "dead": "ko"},
        "sampling": "nearest", "pixel_art": True, "art_source": "existing",
        "body_height_px": BODY_SIZE[1],
    }
    (OUT / "clips-input.json").write_text(json.dumps(manifest, indent=2) + "\n")
    evidence = {
        "source": str(src_path.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(src_path.read_bytes()).hexdigest(),
        "source_size_px": list(source.size), "source_background_rgb": list(key),
        "body_target_px": list(BODY_SIZE),
        "body_only_bbox_px": {"x": body_x, "y": body_y, "w": body_w, "h": body_h},
        "full_fx_bbox_px": full_fx_bbox,
        "canvas_px": list(CANVAS),
        "anchor_px": list(ANCHOR), "fx_pivot_px": list(FX_PIVOT),
        "origin_local_px": ORIGIN_LOCAL_PX,
        "horizontal_scale": SX, "vertical_scale": SY,
        "screen_speed_px_per_second": 150, "flight_default_y": 300,
        "source_forward": "right (+X); muzzle flash is to the right of the body in source row 2",
        "art_method": "source crop; exact blue key; 1-pass direct nearest resize from 20x24; no redraw; no blur",
        "timing_status": "review_draft",
        "idle_contract": "same 8 source poses and 60Hz ticks as walk; seamless phase continuity; no world-position translation",
        "sharpness_metrics": {
            "edge_acutance_sobel": f0_metrics["edge_acutance_sobel"],
            "alpha_hardness_pct": f0_metrics["alpha_hardness_pct"],
            "visible_alpha_hardness_pct": f0_metrics["visible_alpha_hardness_pct"],
            "rgb_colors": f0_metrics["rgb_colors"],
            "enclosed_key_pockets": max_pockets,
            "opaque_key_px": max_opaque_key,
            "partial_alpha_px": max_partial,
            "outer_ring_spill_fraction": max_spill,
        },
        "slots": source_map,
    }
    (OUT / "source-map.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({
        "output": str(OUT), "frames": len(entries),
        "body_only_bbox_px": evidence["body_only_bbox_px"],
        "full_fx_bbox_px": full_fx_bbox,
        "origin_local_px": ORIGIN_LOCAL_PX,
        "sharpness_metrics": evidence["sharpness_metrics"],
    }))


if __name__ == "__main__":
    build()
