#!/usr/bin/env python3
"""Build rocky_plateau 1:1 original-faithful terrain directly from rocky-plateau-bg.jpg.

- Keeps rocky-plateau-bg.jpg 100% intact for the main backdrop (no AI redraw).
- Generates crisp non-mirrored 20:9 side wings (wing_left.png, wing_right.png) for D1 expand.
- Extracts colors & textures directly from rocky-plateau-bg.jpg to build 1 seamless
  horizontal 32x32 side-view ground ledge (960x128 px -> 2x = 1920x256 @ y=824..1080, floor y=840)
  with 0 extra floating platforms.
- Generates 60Hz binary-alpha ground dust pixel FX matching the sandstone palette.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
MAP_DIR = ROOT / "assets" / "maps" / "rocky_plateau"
ORIG_JPG = MAP_DIR / "rocky-plateau-bg.jpg"
SOURCE_DIR = MAP_DIR / "source"
PARALLAX_DIR = MAP_DIR / "parallax"
TILES_DIR = MAP_DIR / "tiles"
FX_DIR = MAP_DIR / "fx"
REVIEW_DIR = SOURCE_DIR / "review"
TERRAIN_JSON = MAP_DIR / "terrain.json"

TILE_PX = 32
GAMEPLAY_SCALE = 2
GROUND_Y = 840
GROUND_SURFACE_OFFSET_Y_1X = 8  # y=824..1080 -> player feet y=840 sit squarely on sandstone top deck


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_gdignore(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    gi = folder / ".gdignore"
    if not gi.exists():
        gi.write_text("", encoding="utf-8")


def blend_join(a: np.ndarray, b: np.ndarray, overlap: int = 56) -> np.ndarray:
    """Horizontally cross-fade strip b onto the tail of strip a."""
    ah, _ = a.shape[:2]
    aw = a.shape[1]
    bw = b.shape[1]
    out = np.zeros((ah, aw + bw - overlap, 3), dtype=np.float32)
    out[:, : aw - overlap, :] = a[:, : aw - overlap, :]
    t = np.linspace(0.0, 1.0, overlap, dtype=np.float32)[None, :, None]
    s = t * t * (3.0 - 2.0 * t)
    out[:, aw - overlap : aw, :] = a[:, aw - overlap :, :] * (1.0 - s) + b[:, :overlap, :] * s
    out[:, aw:, :] = b[:, overlap:, :]
    return out


def build_seamless_wings(arr: np.ndarray, wing_w: int = 320) -> dict[str, Any]:
    """Extract sharp non-smeared seamless 20:9 side wings from outer rocky-plateau-bg.jpg."""
    PARALLAX_DIR.mkdir(parents=True, exist_ok=True)
    wings: dict[str, Any] = {}
    bridge_w = 40

    # Left wing: right column (x = wing_w - 1) matches arr[:, 0] seamlessly, outer width comes from non-mirrored cliff
    donor_l = arr[:, 100 : 100 + wing_w].astype(np.float32)
    tan_l = arr[:, 0:bridge_w][:, ::-1].astype(np.float32)
    t_l = np.linspace(0.0, 1.0, bridge_w, dtype=np.float32)[None, :, None]
    s_l = t_l * t_l * (3.0 - 2.0 * t_l)
    canvas_l = donor_l.copy()
    canvas_l[:, -bridge_w:, :] = donor_l[:, -bridge_w:, :] * (1.0 - s_l) + tan_l * s_l
    canvas_l[:, -1, :] = arr[:, 0, :]

    # Right wing: left column (x = 0) matches arr[:, -1] seamlessly
    donor_r = arr[:, -100 - wing_w : -100].astype(np.float32)
    tan_r = arr[:, -bridge_w:][:, ::-1].astype(np.float32)
    t_r = np.linspace(1.0, 0.0, bridge_w, dtype=np.float32)[None, :, None]
    s_r = t_r * t_r * (3.0 - 2.0 * t_r)
    canvas_r = donor_r.copy()
    canvas_r[:, :bridge_w, :] = donor_r[:, :bridge_w, :] * (1.0 - s_r) + tan_r * s_r
    canvas_r[:, 0, :] = arr[:, -1, :]

    for key, arr_rgb in (("wing_left", canvas_l), ("wing_right", canvas_r)):
        out_path = PARALLAX_DIR / f"{key}.jpg"
        img = Image.fromarray(np.clip(np.round(arr_rgb), 0, 255).astype(np.uint8), mode="RGB")
        img.save(out_path, format="JPEG", quality=94)
        wings[key] = {
            "path": out_path.relative_to(ROOT).as_posix(),
            "res_path": f"res://{out_path.relative_to(ROOT).as_posix()}",
            "web_path": "/" + out_path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(out_path),
            "size_px": list(img.size),
        }
    return wings


def build_ground_tileset(arr: np.ndarray) -> dict[str, Any]:
    """Extract 1 seamless horizontal 32x32 tileset (960x128 = 30x4 tiles) straight from rocky-plateau-bg.jpg."""
    target_w = 960  # 30 columns x 32px -> 2x = 1920px exact full stage before periodic wrap
    target_h = 128  # 4 rows x 32px -> 2x = 256px (y=824..1080)
    cols = target_w // TILE_PX
    rows = target_h // TILE_PX

    # 1. Extract cliff + green grass rim from the central horizontal span (x=230..760, y=550..675)
    region = arr[550:675, 230:760].copy()
    rh, rw = region.shape[:2]
    reg_f = region.astype(np.float32)
    grass_score = reg_f[:45, :, 1] - 0.72 * reg_f[:45, :, 0] - 0.15 * reg_f[:45, :, 2]
    brow_y = np.zeros(rw, dtype=np.float32)
    for x in range(rw):
        col = np.maximum(0.0, grass_score[:, x])
        brow_y[x] = float(np.sum(np.arange(len(col)) * col) / col.sum()) if col.sum() > 25.0 else 18.0
    win = 41
    smooth_brow = np.convolve(np.pad(brow_y, win // 2, mode="edge"), np.ones(win) / win, mode="valid")
    target_brow = 16.0
    rectified = np.zeros_like(region)
    for x in range(rw):
        shift = int(round(target_brow - smooth_brow[x]))
        col = region[:, x, :]
        if shift >= 0:
            rectified[shift:, x, :] = col[: rh - shift, :]
            rectified[:shift, x, :] = col[0:1, :]
        else:
            s = -shift
            rectified[: rh - s, x, :] = col[s:, :]
            rectified[rh - s :, x, :] = col[rh - 1 : rh, :]

    sA = rectified[:, 15:525, :].astype(np.float32)
    sB = rectified[:, 165:520, :].astype(np.float32)
    sC = rectified[:, 25:345, :].astype(np.float32)
    stitched = blend_join(blend_join(sA, sB, 56), sC, 56)
    ov = 64
    cliff_res = stitched[:, :target_w, :].copy()
    tail = stitched[:, target_w : target_w + ov, :]
    tw = np.linspace(0.0, 1.0, ov, dtype=np.float32)[None, :, None]
    cliff_res[:, :ov, :] = tail * (1.0 - tw) + cliff_res[:, :ov, :] * tw

    # 2. Extract flat cracked sandstone walking deck from original plateau (y=495..517, x=210..960)
    deck_raw = arr[495:517, 210:960]
    d_stitched = blend_join(deck_raw[:, :540, :].astype(np.float32), deck_raw[:, 180:720, :].astype(np.float32), 60)
    deck_res = d_stitched[:, :target_w, :].copy()
    d_tail = d_stitched[:, target_w : target_w + 60, :]
    d_tw = np.linspace(0.0, 1.0, 60, dtype=np.float32)[None, :, None]
    deck_res[:, :60, :] = d_tail * (1.0 - d_tw) + deck_res[:, :60, :] * d_tw

    # 3. Compose 960x128 horizontal tile slab preserving exact colors & textures of rocky-plateau-bg.jpg
    out_rgb = np.zeros((target_h, target_w, 3), dtype=np.float32)
    out_rgb[0:20] = deck_res[0:20]

    # Delicate crack-toned top rim defining the straight horizontal fighting plane cleanly against backdrop
    curb_shadow = np.array([124.0, 96.0, 68.0], dtype=np.float32)
    curb_lit = np.array([218.0, 189.0, 140.0], dtype=np.float32)
    out_rgb[0] = out_rgb[0] * 0.80 + curb_shadow * 0.20
    out_rgb[1] = out_rgb[1] * 0.84 + curb_lit * 0.16
    out_rgb[18] = 0.65 * deck_res[18] + 0.35 * cliff_res[6]
    out_rgb[19] = 0.35 * deck_res[19] + 0.65 * cliff_res[7]
    out_rgb[20:128] = cliff_res[7:115]

    rgba = np.zeros((target_h, target_w, 4), dtype=np.uint8)
    rgba[:, :, :3] = np.clip(np.round(out_rgb), 0, 255).astype(np.uint8)
    rgba[:, :, 3] = 255

    TILES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TILES_DIR / "ground_tileset.png"
    tileset_img = Image.fromarray(rgba, mode="RGBA")
    tileset_img.save(out_path, format="PNG")

    return {
        "path": out_path.relative_to(ROOT).as_posix(),
        "res_path": f"res://{out_path.relative_to(ROOT).as_posix()}",
        "web_path": "/" + out_path.relative_to(ROOT).as_posix(),
        "sha256": sha256_file(out_path),
        "tile_px": TILE_PX,
        "columns": cols,
        "rows": rows,
        "image_size_px": list(tileset_img.size),
        "alpha_hardness_pct": 100.0 * float(np.isin(rgba[:, :, 3], [0, 255]).mean()),
    }


def build_ground_dust_fx(arr: np.ndarray) -> dict[str, Any]:
    """Generate 6 crisp 32x20 pixel-art footstep/landing dust frames sampled from rocky-plateau-bg.jpg sandstone."""
    FX_DIR.mkdir(parents=True, exist_ok=True)
    fw, fh = 32, 20
    frames = 6
    sheet = Image.new("RGBA", (fw * frames, fh), (0, 0, 0, 0))

    # Sample sandstone dust ramps straight from rocky-plateau-bg.jpg deck tones
    deck_sample = arr[490:525, 360:720].astype(np.float32)
    base_sand = np.median(deck_sample.reshape(-1, 3), axis=0)
    c_dark = tuple(int(v) for v in np.clip(base_sand * 0.42, 0, 255)) + (255,)
    c_mid = tuple(int(v) for v in np.clip(base_sand * 0.72, 0, 255)) + (255,)
    c_sand = tuple(int(v) for v in np.clip(base_sand, 0, 255)) + (255,)
    c_hi = tuple(int(v) for v in np.clip(base_sand * 1.14, 0, 255)) + (255,)

    puffs_per_frame = [
        [(10, 15, 3), (21, 15, 3), (15, 16, 2)],
        [(8, 14, 4), (23, 14, 4), (12, 16, 2), (19, 16, 2)],
        [(6, 12, 4), (25, 12, 4), (10, 15, 3), (21, 15, 3)],
        [(4, 11, 3), (27, 11, 3), (8, 14, 2), (23, 14, 2)],
        [(3, 10, 2), (28, 10, 2), (7, 15, 1), (24, 15, 1)],
        [(2, 9, 1), (29, 9, 1)],
    ]

    for fi, puffs in enumerate(puffs_per_frame):
        tile = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        d = ImageDraw.Draw(tile)
        for px, py, r in puffs:
            d.ellipse((px - r - 1, py - r - 1, px + r + 1, py + r + 1), fill=c_dark)
        for px, py, r in puffs:
            d.ellipse((px - r, py - r, px + r, py + r), fill=c_mid if fi >= 3 else c_sand)
        if fi < 4:
            for px, py, r in puffs:
                if r >= 2:
                    d.rectangle((px - max(0, r - 2), py - r, px + max(0, r - 2), py - r + 1), fill=c_hi)
        sheet.paste(tile, (fi * fw, 0))

    out_path = FX_DIR / "ground_dust.png"
    sheet.save(out_path, format="PNG")
    return {
        "path": out_path.relative_to(ROOT).as_posix(),
        "res_path": f"res://{out_path.relative_to(ROOT).as_posix()}",
        "web_path": "/" + out_path.relative_to(ROOT).as_posix(),
        "sha256": sha256_file(out_path),
        "frame_size_1x_px": [fw, fh],
        "frame_count": frames,
        "tick_hz": 60,
        "ticks_per_frame": 3,
        "scale": GAMEPLAY_SCALE,
        "anchor_1x_px": [16, 17],
    }


def render_review_composite(terrain: dict[str, Any], orig_img: Image.Image) -> None:
    """Render an inspection sheet (1920x1080) with original JPG + 1 horizontal ledge + T-Rex + shadow."""
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    canvas = orig_img.resize((1920, 1080), Image.Resampling.LANCZOS).convert("RGBA")

    ts_cfg = terrain["tileset"]
    ts_img = Image.open(ROOT / ts_cfg["path"]).convert("RGBA")
    cols = ts_cfg["columns"]
    rows = ts_cfg["rows"]
    tile_2x = TILE_PX * GAMEPLAY_SCALE
    ground_top_y = terrain["ground"]["surface_top_y"]
    for tx in range(0, 1920, tile_2x):
        c_idx = (tx // tile_2x) % cols
        for r_idx in range(rows):
            t_crop = ts_img.crop((c_idx * TILE_PX, r_idx * TILE_PX, (c_idx + 1) * TILE_PX, (r_idx + 1) * TILE_PX))
            t_scaled = t_crop.resize((tile_2x, tile_2x), Image.Resampling.NEAREST)
            canvas.alpha_composite(t_scaled, (tx, ground_top_y + r_idx * tile_2x))

    trex_meta_path = ROOT / "assets" / "t_rex" / "godot_bundle" / "engine-export.json"
    if trex_meta_path.is_file():
        tmeta = json.loads(trex_meta_path.read_text(encoding="utf-8"))
        tatlas = Image.open(ROOT / "assets" / "t_rex" / "godot_bundle" / "godot" / "t_rex-atlas-00.png").convert("RGBA")
        tres = (ROOT / "assets" / "t_rex" / "godot_bundle" / "godot" / "t_rex.tres").read_text(encoding="utf-8")
        m = re.search(r"region = Rect2\((\d+), (\d+), (\d+), (\d+)\)", tres)
        if m:
            rx, ry, rw, rh = [int(v) for v in m.groups()]
            sc = 1.75
            t_crop = tatlas.crop((rx, ry, rx + rw, ry + rh)).resize(
                (int(round(rw * sc)), int(round(rh * sc))), Image.Resampling.NEAREST
            )
            ax, ay = tmeta["anchor_px"]
            d = ImageDraw.Draw(canvas)
            for px, py in ((560, GROUND_Y), (1360, GROUND_Y)):
                d.rectangle((px - 56, py - 4, px + 56, py + 4), fill=(35, 22, 16, 170))
                d.rectangle((px - 40, py - 6, px + 40, py + 6), fill=(26, 16, 11, 210))
            canvas.alpha_composite(t_crop, (int(round(560 - ax * sc)), int(round(GROUND_Y - ay * sc))))
            t_flip = t_crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            canvas.alpha_composite(t_flip, (int(round(1360 - (rw - ax) * sc)), int(round(GROUND_Y - ay * sc))))

    canvas.save(REVIEW_DIR / "rocky-plateau-tile-review.png", format="PNG")


def main() -> None:
    if not ORIG_JPG.is_file():
        raise FileNotFoundError(f"Missing original map image: {ORIG_JPG}")
    ensure_gdignore(SOURCE_DIR)
    ensure_gdignore(REVIEW_DIR)

    orig_img = Image.open(ORIG_JPG).convert("RGB")
    arr = np.array(orig_img)
    wings = build_seamless_wings(arr, wing_w=320)
    tileset = build_ground_tileset(arr)
    dust_fx = build_ground_dust_fx(arr)

    terrain_doc = {
        "schema": "dr7-studio.map_terrain.v2",
        "map_id": "rocky_plateau",
        "art_source": "original_jpg_extracted",
        "backdrop": {
            "mode": "original_jpg",
            "bg_path": ORIG_JPG.relative_to(ROOT).as_posix(),
            "bg_res_path": f"res://{ORIG_JPG.relative_to(ROOT).as_posix()}",
            "bg_web_path": "/" + ORIG_JPG.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(ORIG_JPG),
            "wing_left": wings["wing_left"],
            "wing_right": wings["wing_right"],
        },
        "viewport": {"width": 1920, "height": 1080, "ppu_reference": 64, "tile_px": TILE_PX},
        "ground": {
            "ground_y": GROUND_Y,
            "surface_top_y": GROUND_Y - GROUND_SURFACE_OFFSET_Y_1X * GAMEPLAY_SCALE,
            "render_scale": GAMEPLAY_SCALE,
        },
        "tileset": tileset,
        "platforms": [],
        "contact_shadow": {
            "style": "dynamic_pixel_rect",
            "ellipse_forbidden": True,
            "base_half_w_px": 56,
            "min_half_w_px": 18,
            "max_height_px": 320,
            "outer_rgba": [35, 22, 16, 165],
            "inner_rgba": [24, 14, 10, 215],
        },
        "dust_fx": dust_fx,
    }
    TERRAIN_JSON.write_text(json.dumps(terrain_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_review_composite(terrain_doc, orig_img)
    print(json.dumps({
        "status": "ok",
        "terrain_json": TERRAIN_JSON.relative_to(ROOT).as_posix(),
        "tileset_sha256": tileset["sha256"],
        "wing_left_sha256": wings["wing_left"]["sha256"],
        "wing_right_sha256": wings["wing_right"]["sha256"],
        "dust_fx_sha256": dust_fx["sha256"],
    }))


if __name__ == "__main__":
    main()
