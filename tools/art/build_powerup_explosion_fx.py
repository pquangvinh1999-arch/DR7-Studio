#!/usr/bin/env python3
"""Build small PowerUp impact explosion SpriteFrames from `/workspaces/DR7-Studio/image copy 7.png`."""
from __future__ import annotations

import pathlib
from collections import deque
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, label

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC_PNG = REPO_ROOT / "image copy 7.png"
OUT_DIR = REPO_ROOT / "assets" / "fx" / "powerup_explosion"
ATLAS_PNG = OUT_DIR / "powerup_explosion-atlas-00.png"
TRES_PATH = OUT_DIR / "powerup_explosion.tres"

FRAME_W = 80
FRAME_H = 80
TICKS = [3, 4, 4, 4, 4, 4]
X_SLICES = [
    (0, 58),
    (64, 142),
    (144, 218),
    (220, 298),
    (299, 378),
    (379, 457),
]


def key_dark_navy_fx(crop_rgba: np.ndarray) -> np.ndarray:
    out = crop_rgba.copy()
    rgb = out[:, :, :3].astype(np.float32)
    bg = np.array([22.0, 24.0, 39.0], dtype=np.float32)
    dist = np.linalg.norm(rgb - bg, axis=-1)

    # Flood-fill background from border so interior smoke puffs stay intact
    h, w = dist.shape
    is_bg_cand = dist <= 16.0
    visited = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        for y in (0, h - 1):
            if is_bg_cand[y, x] and not visited[y, x]:
                visited[y, x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_bg_cand[y, x] and not visited[y, x]:
                visited[y, x] = True
                q.append((x, y))
    while q:
        cx, cy = q.popleft()
        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx] and is_bg_cand[ny, nx]:
                visited[ny, nx] = True
                q.append((nx, ny))

    # Any enclosed pure-bg pockets inside smoke ring
    visited |= (dist <= 9.0)
    out[visited, 3] = 0

    # Soft FX alpha on 1-2px outer border mixed with dark navy bg
    ring = binary_dilation(visited, iterations=2) & (~visited)
    for py, px in zip(*np.where(ring)):
        d = float(dist[py, px])
        if d < 42.0:
            a = float(np.clip((d - 12.0) / 30.0, 0.0, 1.0))
            if a <= 0.02:
                out[py, px, 3] = 0
            else:
                unmixed = np.clip((rgb[py, px] - (1.0 - a) * bg) / a, 0.0, 255.0)
                out[py, px, :3] = unmixed.astype(np.uint8)
                out[py, px, 3] = int(round(a * 255.0))
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src = np.array(Image.open(SRC_PNG).convert("RGBA"))
    atlas = Image.new("RGBA", (FRAME_W * len(X_SLICES), FRAME_H), (0, 0, 0, 0))

    # Determine common center Y from frame 2 (peak burst)
    peak_crop = key_dark_navy_fx(src[:, X_SLICES[2][0]:X_SLICES[2][1], :])
    pys, pxs = np.where(peak_crop[:, :, 3] > 24)
    common_cy = float(pys.min() + pys.max()) * 0.5

    for idx, (x0, x1) in enumerate(X_SLICES):
        cleaned = key_dark_navy_fx(src[:, x0:x1, :])
        if idx <= 3:
            # Remove tiny <= 4px isolated JPEG compression specks outside the main burst
            lbl, n_lbl = label(cleaned[:, :, 3] > 16)
            if n_lbl > 1:
                counts = np.bincount(lbl.ravel())
                for k in range(1, len(counts)):
                    if counts[k] <= 6:
                        cleaned[lbl == k, 3] = 0
        ys, xs = np.where(cleaned[:, :, 3] > 16)
        if len(xs) == 0:
            continue
        bx0, bx1 = int(xs.min()), int(xs.max()) + 1
        by0, by1 = int(ys.min()), int(ys.max()) + 1
        sub = Image.fromarray(cleaned[by0:by1, bx0:bx1], "RGBA")
        # Keep within 76x76 so it stays crisp inside 80x80 cell
        scale = min(1.0, 74.0 / max(sub.width, sub.height))
        if scale < 1.0:
            nw = max(1, int(round(sub.width * scale)))
            nh = max(1, int(round(sub.height * scale)))
            sub = sub.resize((nw, nh), Image.Resampling.NEAREST)
        cx_local = (bx0 + bx1) * 0.5
        paste_x = idx * FRAME_W + (FRAME_W - sub.width) // 2
        paste_y = int(round((FRAME_H * 0.5) - ((common_cy - by0) * scale)))
        paste_y = max(0, min(FRAME_H - sub.height, paste_y))
        atlas.paste(sub, (paste_x, paste_y), sub)

    atlas.save(ATLAS_PNG)

    # Write Godot 4 SpriteFrames .tres
    sub_res = []
    frame_entries = []
    for i, dur in enumerate(TICKS):
        sid = f"AtlasTexture_exp_{i}"
        sub_res.append(
            f'[sub_resource type="AtlasTexture" id="{sid}"]\n'
            f'atlas = ExtResource("1_atlas")\n'
            f'region = Rect2({i * FRAME_W}, 0, {FRAME_W}, {FRAME_H})\n'
        )
        frame_entries.append(
            f'{{\n"duration": {float(dur):.1f},\n"texture": SubResource("{sid}")\n}}'
        )

    tres_text = (
        '[gd_resource type="SpriteFrames" load_steps=8 format=3]\n\n'
        '[ext_resource type="Texture2D" path="res://assets/fx/powerup_explosion/powerup_explosion-atlas-00.png" id="1_atlas"]\n\n'
        + "\n".join(sub_res)
        + '\n[resource]\nanimations = [{\n'
        '"frames": [' + ", ".join(frame_entries) + '],\n'
        '"loop": false,\n'
        '"name": &"explode",\n'
        '"speed": 60.0\n}]\n'
    )
    TRES_PATH.write_text(tres_text, encoding="utf-8")
    print(f"[OK] Built {ATLAS_PNG} ({atlas.size}) and {TRES_PATH}")


if __name__ == "__main__":
    main()
