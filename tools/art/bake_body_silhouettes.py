#!/usr/bin/env python3
"""Bake exact opaque-pixel body core center (tâm thân) and horizontal silhouette slices
for all characters (hero + monsters + NPC) from their canonical .tres + atlas PNGs."""
from __future__ import annotations

import json
import pathlib
import sys
import numpy as np
from PIL import Image

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "preview"))
import server as preview_server

ROSTER_JSON = REPO_ROOT / "assets" / "roster.json"
OUT_JSON = REPO_ROOT / "assets" / "body_silhouettes.json"
BAND_H_PX = 4


def bake_character_silhouette(entry: dict) -> dict | None:
    cid = str(entry.get("character_id", ""))
    if not cid:
        return None
    bundle_dir = REPO_ROOT / "assets" / cid / "godot_bundle"
    export_path = bundle_dir / "engine-export.json"
    godot_dir = bundle_dir / "godot"
    tres_path = godot_dir / f"{cid}.tres"
    if not export_path.is_file() or not tres_path.is_file():
        return None

    exp = json.loads(export_path.read_text(encoding="utf-8"))
    parsed = preview_server.parse_tres(tres_path)
    anims = parsed.get("animations", {})
    idle_frames = anims.get("idle", {}).get("frames", [])
    if not idle_frames:
        for adata in anims.values():
            if adata.get("frames"):
                idle_frames = adata["frames"]
                break
    if not idle_frames:
        return None

    anchor = exp.get("anchor_px", entry.get("map_sync_metrics", {}).get("foot_anchor_px", [0, 0]))
    ax, ay = float(anchor[0]), float(anchor[1])
    frame_size = exp.get("frame_size", [384, 256])
    fw, fh = int(frame_size[0]), int(frame_size[1])

    atlas_cache: dict[str, np.ndarray] = {}
    accum = np.zeros((fh, fw), dtype=np.int32)
    used = 0
    for fr in idle_frames:
        atlas_file = str(fr.get("atlas_file", f"{cid}-atlas-00.png"))
        if atlas_file not in atlas_cache:
            ap = godot_dir / atlas_file
            if not ap.is_file():
                continue
            atlas_cache[atlas_file] = np.array(Image.open(ap).convert("RGBA"))
        atlas = atlas_cache[atlas_file]
        rx, ry = int(round(fr["x"])), int(round(fr["y"]))
        rw, rh = int(round(fr["w"])), int(round(fr["h"]))
        if rw <= 0 or rh <= 0:
            continue
        crop = atlas[ry:ry + rh, rx:rx + rw, 3] >= 128
        ch, cw = min(fh, crop.shape[0]), min(fw, crop.shape[1])
        accum[:ch, :cw] += crop[:ch, :cw].astype(np.int32)
        used += 1

    if used == 0:
        return None

    thresh = max(1, used // 3)
    mask = accum >= thresh
    ys, xs = np.where(mask)
    if len(xs) == 0:
        mask = accum >= 1
        ys, xs = np.where(mask)
    if len(xs) == 0:
        return None

    core_x = float(xs.mean()) - ax
    core_y = float(ys.mean()) - ay

    y_min = int(ys.min())
    y_max = int(ys.max())
    bands = []
    for y0 in range(y_min, y_max + 1, BAND_H_PX):
        y1 = min(y_max + 1, y0 + BAND_H_PX)
        band_xs = np.where(mask[y0:y1, :].any(axis=0))[0]
        if len(band_xs) == 0:
            continue
        x_min = float(band_xs.min()) - ax
        x_max = float(band_xs.max() + 1) - ax
        bands.append([
            round(y0 - ay, 2),
            round(y1 - ay, 2),
            round(x_min, 2),
            round(x_max, 2),
        ])

    return {
        "character_id": cid,
        "anchor_px": [ax, ay],
        "core_offset_px": [round(core_x, 2), round(core_y, 2)],
        "bbox_local_px": [
            round(float(xs.min()) - ax, 2),
            round(float(ys.min()) - ay, 2),
            round(float(xs.max() + 1) - float(xs.min()), 2),
            round(float(ys.max() + 1) - float(ys.min()), 2),
        ],
        "bands": bands,
    }


def main() -> None:
    roster = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
    out = {"schema": "dr7-studio.body_silhouettes.v1", "characters": {}}
    for entry in roster.get("characters", []):
        baked = bake_character_silhouette(entry)
        if baked is not None:
            cid = baked["character_id"]
            out["characters"][cid] = baked
            print(f"  {cid:22s}: core={baked['core_offset_px']} bands={len(baked['bands'])}")
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] Baked {len(out['characters'])} silhouettes -> {OUT_JSON}")


if __name__ == "__main__":
    main()
