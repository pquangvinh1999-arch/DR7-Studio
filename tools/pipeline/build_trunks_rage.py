#!/usr/bin/env python3
"""DR7-Studio — Official 1-Layer Combined Atlas Extraction & Registration Pipeline for Trunks Rage.

Tuân thủ tuyệt đối Hiến pháp AGENTS.md & bài học kỹ thuật lerning.md (LRN-001..LRN-007):
1. Kiến trúc duy nhất: Gộp Chung 1 Lớp Nguyên Bản (Combined 1-Layer, Zero AI Redraw) — bảo toàn 100% chi tiết gốc từ sheet Pixel Art nguyên bản không nén (1340×2261, nền #2B3772).
2. Phân tách cụm 2D theo mặt nạ sở hữu liên thông (2D Component Ownership Masking):
   - Loại bỏ sạch header/footer, khung viền tím/xanh, vạch phân cách '-', chữ 'WIN' và ảnh mặt cắt (cut-in).
   - Ngăn chặn 100% hiện tượng mũi kiếm chéo hoặc tia chưởng hàng dưới lọt vào khung cắt.
   - Gom chính xác các tia sét, vòm hào quang rời, vệt tốc biến RGB và bụi nhảy vào đúng frame chủ.
3. Tách nền xanh tím than #2B3772 (RGB 43, 55, 114) chuẩn xác:
   - Với sheet Pixel Art nguyên bản không nội suy (1340×2261): tách chính xác tuyệt đối 100% pixel #2B3772 (cả nền ngoài lẫn 100% hốc kín giữa tay/chân/kiếm/hào quang) mà giữ nguyên 100% RGB gốc + độ cứng biên alpha 100.0%.
   - Kèm bộ khử viền dự phòng 2 giai đoạn (Pocket-First + Edge/Olive Unmixing) nếu nguồn đầu vào từng qua thu phóng.
4. Căn tâm gốc chuẩn xác (Shared Row Ground Baseline + Dark-Outline/Scarf Torso Centroid) trên khung Canvas 320×256, anchor_px = [96, 220], đóng gói 1 trang PNG Atlas duy nhất (<= 4096×4096).
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = REPO_ROOT / "assets" / "trunks_rage"
SOURCE_DIR = ASSET_ROOT / "source"
FRAMES_DIR = SOURCE_DIR / "frames"
CLIPS_DIR = ASSET_ROOT / "clips"
BUNDLE_DIR = ASSET_ROOT / "godot_bundle"

SKILL_SCRIPTS = REPO_ROOT / ".agents" / "skills" / "generate2dsprite" / "scripts"

CANVAS_W = 320
CANVAS_H = 256
ANCHOR_X = 96
ANCHOR_Y = 220

BG_RGB_U8 = (43, 55, 114)
BG_RGB = np.array([43.0, 55.0, 114.0], dtype=np.float32)


def is_lossless_navy_sheet(raw_rgba: np.ndarray) -> bool:
    """Detect whether the input sheet has pure 1:1 lossless #2B3772 background with zero resampling blur."""
    rgb = raw_rgba[:, :, :3]
    exact_bg = (
        (rgb[:, :, 0] == BG_RGB_U8[0])
        & (rgb[:, :, 1] == BG_RGB_U8[1])
        & (rgb[:, :, 2] == BG_RGB_U8[2])
    )
    adj = ndimage.binary_dilation(exact_bg, structure=np.ones((3, 3))) & (~exact_bg)
    if not np.any(adj):
        return False
    dist_adj = np.sqrt(((rgb[adj].astype(np.float32) - BG_RGB) ** 2).sum(axis=-1))
    return int((dist_adj <= 18.0).sum()) == 0


def key_navy_crop(
    rgba_crop: np.ndarray,
    ownership_mask: np.ndarray | None = None,
    lossless_exact: bool = True,
) -> np.ndarray:
    """Key #2B3772 background cleanly (100% bit-exact for lossless pixel art; 2-stage unmix fallback if resampled)."""
    out = rgba_crop.copy()
    if lossless_exact:
        r, g, b = out[:, :, 0], out[:, :, 1], out[:, :, 2]
        bg_mask = (r == BG_RGB_U8[0]) & (g == BG_RGB_U8[1]) & (b == BG_RGB_U8[2])
        if ownership_mask is not None:
            bg_mask |= ~ownership_mask
        out[:, :, 3] = np.where(bg_mask, 0, 255).astype(np.uint8)
        out[bg_mask] = 0
        return out

    if ownership_mask is not None:
        out[~ownership_mask] = [43, 55, 114, 255]

    rgb = out[:, :, :3].astype(np.float32)
    h, w, _ = rgb.shape
    dist = np.sqrt(((rgb - BG_RGB) ** 2).sum(axis=-1))
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

    # Stage 1: Punch all enclosed #2B3772 pockets FIRST
    indigo_pocket_seed = (dist <= 22.0) | (
        (dist <= 31.0)
        & ((b - g) >= 42.0)
        & ((b - r) >= 52.0)
        & (b >= 82.0)
        & (b <= 144.0)
    )
    border = np.zeros((h, w), dtype=bool)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True

    passable_bg = (dist <= 29.5) | (
        ((b - g) >= 38.0) & ((b - r) >= 48.0) & (dist <= 37.0)
    )
    seeds = (border & passable_bg) | indigo_pocket_seed
    bg_mask = ndimage.binary_propagation(seeds, mask=passable_bg, structure=np.ones((3, 3)))
    if ownership_mask is not None:
        bg_mask |= ~ownership_mask

    alpha = np.where(bg_mask, 0.0, 255.0).astype(np.float32)

    # Stage 2A: 1px silhouette boundary indigo/purple fringe unmixing
    adj_bg = ndimage.binary_dilation(bg_mask, structure=np.ones((3, 3))) & (~bg_mask)
    indigo_fringe = (
        adj_bg
        & (dist < 60.0)
        & ((b - g) >= 22.0)
        & ((b - r) >= 24.0)
        & (g < 138.0)
    )
    if np.any(indigo_fringe):
        a_est = np.clip((dist - 25.0) / 35.0, 0.0, 1.0)
        kill = indigo_fringe & (a_est < 0.42)
        keep = indigo_fringe & (~kill)
        alpha[kill] = 0.0
        bg_mask[kill] = True
        if np.any(keep):
            ae = a_est[keep][:, None]
            rgb[keep] = np.clip(
                (rgb[keep] - (1.0 - ae) * BG_RGB[None, :]) / np.maximum(ae, 0.42),
                0.0,
                255.0,
            )
            snapped = np.where(a_est[keep] >= 0.72, 255.0, np.round(a_est[keep] * 255.0))
            alpha[keep] = snapped

    # Stage 2B: Unmix 1px yellow-aura + navy-bg olive blend
    bright_yellow = (alpha > 0) & (r > 210.0) & (g > 190.0) & (b < 90.0)
    near_yellow = ndimage.binary_dilation(bright_yellow, structure=np.ones((3, 3)))
    adj_bg2 = ndimage.binary_dilation(alpha == 0, structure=np.ones((3, 3))) & (alpha > 0)
    olive_fringe = (
        adj_bg2
        & near_yellow
        & (r >= 70.0)
        & (r <= 205.0)
        & (g >= 80.0)
        & (g <= 210.0)
        & (b >= 45.0)
        & (b <= 125.0)
        & (np.abs(r - g) <= 32.0)
    )
    if np.any(olive_fringe):
        w_yel = np.clip((114.0 - b) / 99.0, 0.0, 1.0)
        kill_ol = olive_fringe & (w_yel < 0.48)
        keep_ol = olive_fringe & (~kill_ol)
        alpha[kill_ol] = 0.0
        if np.any(keep_ol):
            wy = w_yel[keep_ol][:, None]
            rgb[keep_ol] = np.clip(
                (rgb[keep_ol] - (1.0 - wy) * BG_RGB[None, :]) / np.maximum(wy, 0.48),
                0.0,
                255.0,
            )
            alpha[keep_ol] = 255.0

    out[:, :, :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    out[:, :, 3] = np.clip(np.round(alpha), 0, 255).astype(np.uint8)
    out[out[:, :, 3] == 0] = 0
    return out


def extract_row_components(
    raw_rgba: np.ndarray,
    y0: int,
    y1: int,
    x0: int,
    x1: int,
    extra_exclusions: list[tuple[int, int, int, int]] | None = None,
    merge_overlap_ratio: float = 0.45,
    merge_min_px_overlap: int | None = None,
    merge_thin_teleports: bool = False,
    lossless_exact: bool = True,
) -> list[dict]:
    """Extract ordered 2D sprite components in a row with exact pixel-ownership masks."""
    sub_rgba = raw_rgba[y0 : y1 + 1, x0 : x1 + 1]
    rgb_u8 = sub_rgba[:, :, :3]
    if lossless_exact:
        core_fg = ~(
            (rgb_u8[:, :, 0] == BG_RGB_U8[0])
            & (rgb_u8[:, :, 1] == BG_RGB_U8[1])
            & (rgb_u8[:, :, 2] == BG_RGB_U8[2])
        )
    else:
        dist = np.sqrt(((rgb_u8.astype(np.float32) - BG_RGB) ** 2).sum(axis=-1))
        core_fg = dist > 28.0

    if extra_exclusions:
        for ex0, ey0, ex1, ey1 in extra_exclusions:
            rx0 = max(0, ex0 - x0)
            ry0 = max(0, ey0 - y0)
            rx1 = min(x1 - x0 + 1, ex1 - x0 + 1)
            ry1 = min(y1 - y0 + 1, ey1 - y0 + 1)
            if rx1 > rx0 and ry1 > ry0:
                core_fg[ry0:ry1, rx0:rx1] = False

    lbl, n = ndimage.label(core_fg, structure=np.ones((3, 3)))
    raw_items: list[dict] = []
    sparks: list[dict] = []

    for cid in range(1, n + 1):
        ys, xs = np.where(lbl == cid)
        bx0, bx1 = int(xs.min()), int(xs.max())
        by0, by1 = int(ys.min()), int(ys.max())
        bw, bh = bx1 - bx0 + 1, by1 - by0 + 1
        area = int(len(xs))
        # Filter horizontal green/grey separator dashes '-'
        if bh <= 9 and 7 <= bw <= 35 and area < 240:
            continue
        item = {
            "cids": [cid],
            "lx0": bx0,
            "ly0": by0,
            "lx1": bx1,
            "ly1": by1,
            "area": area,
        }
        is_teleport_streak = merge_thin_teleports and bh >= 20 and bw <= 10 and area >= 25
        if not is_teleport_streak and area < 145 and (bw < 32 or bh < 21):
            sparks.append(item)
        else:
            raw_items.append(item)

    raw_items.sort(key=lambda c: 0.5 * (c["lx0"] + c["lx1"]))

    # Merge vertically aligned multi-part poses (aura arch, blade tip, RGB teleport speed-lines, attached beam)
    merged: list[dict] = []
    for item in raw_items:
        if not merged:
            merged.append(item)
            continue
        prev = merged[-1]
        pw = prev["lx1"] - prev["lx0"] + 1
        iw = item["lx1"] - item["lx0"] + 1
        ov = min(prev["lx1"], item["lx1"]) - max(prev["lx0"], item["lx0"]) + 1
        min_w = max(1, min(pw, iw))
        gap_x = item["lx0"] - prev["lx1"]
        thin_pair = merge_thin_teleports and (pw <= 30 and iw <= 30 and gap_x <= 7)
        px_ov_match = merge_min_px_overlap is not None and ov >= merge_min_px_overlap
        if (ov / min_w) >= merge_overlap_ratio or thin_pair or px_ov_match:
            prev["cids"].extend(item["cids"])
            prev["lx0"] = min(prev["lx0"], item["lx0"])
            prev["ly0"] = min(prev["ly0"], item["ly0"])
            prev["lx1"] = max(prev["lx1"], item["lx1"])
            prev["ly1"] = max(prev["ly1"], item["ly1"])
            prev["area"] += item["area"]
        else:
            merged.append(item)

    # Attach small sparks / dust puffs / lightning streaks to nearest main pose
    for sp in sparks:
        max_dist = 14.0 if (merge_thin_teleports and (sp["ly1"] - sp["ly0"] + 1) >= 24) else 28.0
        best_idx = None
        best_d = 1e9
        for idx, m in enumerate(merged):
            dx = max(0, m["lx0"] - sp["lx1"], sp["lx0"] - m["lx1"])
            dy = max(0, m["ly0"] - sp["ly1"], sp["ly0"] - m["ly1"])
            d = math.hypot(dx * 1.6, dy * 0.7)
            if d < best_d:
                best_d = d
                best_idx = idx
        if best_idx is not None and best_d <= max_dist:
            t = merged[best_idx]
            t["cids"].extend(sp["cids"])
            t["lx0"] = min(t["lx0"], sp["lx0"])
            t["ly0"] = min(t["ly0"], sp["ly0"])
            t["lx1"] = max(t["lx1"], sp["lx1"])
            t["ly1"] = max(t["ly1"], sp["ly1"])
            t["area"] += sp["area"]

    # Materialize clean keyed RGBA crops with 2D component ownership mask (zero neighbor bleed!)
    results: list[dict] = []
    pad = 0 if lossless_exact else 2
    sub_h, sub_w = lbl.shape
    for m in merged:
        cx0 = max(0, m["lx0"] - pad)
        cy0 = max(0, m["ly0"] - pad)
        cx1 = min(sub_w - 1, m["lx1"] + pad)
        cy1 = min(sub_h - 1, m["ly1"] + pad)

        lbl_win = lbl[cy0 : cy1 + 1, cx0 : cx1 + 1]
        own_core = np.isin(lbl_win, m["cids"])
        if lossless_exact:
            own_mask = own_core
        else:
            other_core = (lbl_win > 0) & (~own_core)
            own_mask = ndimage.binary_dilation(own_core, structure=np.ones((5, 5))) & (~other_core)

        rgba_win = sub_rgba[cy0 : cy1 + 1, cx0 : cx1 + 1]
        keyed = key_navy_crop(rgba_win, ownership_mask=own_mask, lossless_exact=lossless_exact)

        ays, axs = np.where(keyed[:, :, 3] > 0)
        if len(axs) == 0:
            continue
        tx0, tx1 = int(axs.min()), int(axs.max())
        ty0, ty1 = int(ays.min()), int(ays.max())
        tight_rgba = keyed[ty0 : ty1 + 1, tx0 : tx1 + 1]

        results.append(
            {
                "rgba": tight_rgba,
                "sheet_x0": x0 + cx0 + tx0,
                "sheet_y0": y0 + cy0 + ty0,
                "sheet_x1": x0 + cx0 + tx1,
                "sheet_y1": y0 + cy0 + ty1,
                "w": tx1 - tx0 + 1,
                "h": ty1 - ty0 + 1,
            }
        )
    return results


def detect_body_center_x(crop_rgba: np.ndarray) -> float:
    """Locate Trunks's horizontal pelvis/torso center while ignoring wide beams/sword arcs."""
    vis = crop_rgba[:, :, 3] > 128
    if not np.any(vis):
        return crop_rgba.shape[1] * 0.5

    r = crop_rgba[:, :, 0].astype(np.int32)
    g = crop_rgba[:, :, 1].astype(np.int32)
    b = crop_rgba[:, :, 2].astype(np.int32)

    # 1. Dark character outline pixels (hair/jacket/pants/boots outline; excludes cyan/yellow/purple FX)
    dark_outline = vis & (r < 44) & (g < 46) & (b < 58)
    _, dx = np.where(dark_outline)
    if len(dx) >= 35:
        return float(np.median(dx))

    # 2. Red scarf fallback
    scarf = vis & (r > 115) & ((r - g) > 50) & ((r - b) > 45) & (g < 85)
    _, sx = np.where(scarf)
    if len(sx) >= 4:
        return float(np.median(sx))

    # 3. Full visible silhouette fallback (e.g. pure aura/teleport/sphere frames)
    _, vx = np.where(vis)
    return float(np.median(vx))


def detect_boot_bottom_y(crop: dict, default_row_ground_y: int) -> int:
    """Locate Trunks's dark boot ground line when surrounded by spiky downward aura."""
    rgba = crop["rgba"]
    vis = rgba[:, :, 3] > 128
    r = rgba[:, :, 0].astype(np.int32)
    g = rgba[:, :, 1].astype(np.int32)
    b = rgba[:, :, 2].astype(np.int32)
    dark = vis & (r < 45) & (g < 48) & (b < 60)
    dy, _ = np.where(dark)
    if len(dy) >= 25:
        return crop["sheet_y0"] + int(dy.max())
    return default_row_ground_y


def place_on_canvas(
    crop: dict,
    row_ground_y: int | None = None,
    align_bottom_direct: bool = False,
    center_x_box: bool = False,
    dx_nudge: int = 0,
    dy_nudge: int = 0,
) -> np.ndarray:
    """Composite a keyed sprite onto the shared 320x256 RGBA canvas at anchor_px=[96, 220]."""
    canvas = np.zeros((CANVAS_H, CANVAS_W, 4), dtype=np.uint8)
    rgba = crop["rgba"]
    h, w, _ = rgba.shape

    cx_local = (w * 0.5) if center_x_box else detect_body_center_x(rgba)
    dst_x = int(round(ANCHOR_X - cx_local)) + dx_nudge

    if align_bottom_direct or row_ground_y is None:
        dst_y = ANCHOR_Y - h + 1 + dy_nudge
    else:
        offset_from_ground = crop["sheet_y1"] - row_ground_y
        dst_y = ANCHOR_Y - h + 1 + offset_from_ground + dy_nudge

    if dst_x < 2:
        dst_x = 2
    if dst_x + w > CANVAS_W - 2:
        dst_x = CANVAS_W - 2 - w
    if dst_y < 2:
        dst_y = 2
    if dst_y + h > CANVAS_H - 2:
        dst_y = CANVAS_H - 2 - h

    canvas[dst_y : dst_y + h, dst_x : dst_x + w] = rgba
    return canvas


def composite_fx_ahead(
    body_crop: dict,
    fx_crop: dict,
    row_ground_y: int,
    fx_x_start: int,
    fx_ground_align: bool = False,
    fx_center_y: int | None = None,
) -> np.ndarray:
    """Composite a detached sheet projectile/impact FX in front of Trunks on the shared 1-Layer 320x256 canvas."""
    canvas = place_on_canvas(body_crop, row_ground_y=row_ground_y)
    fx = fx_crop["rgba"]
    fh, fw, _ = fx.shape
    dst_x = max(2, min(CANVAS_W - fw - 2, fx_x_start))
    if fx_ground_align:
        dst_y = max(2, min(CANVAS_H - fh - 2, ANCHOR_Y - fh + 4))
    else:
        cy = (ANCHOR_Y - 28) if fx_center_y is None else fx_center_y
        dst_y = max(2, min(CANVAS_H - fh - 2, cy - fh // 2))
    sub_dst = canvas[dst_y : dst_y + fh, dst_x : dst_x + fw]
    mask = fx[:, :, 3:4] > 0
    sub_dst[:] = np.where(mask, fx, sub_dst)
    return canvas


def strip_beam_dividers(p: np.ndarray) -> np.ndarray:
    """Strip 1px dark modular tile divider columns on left/right of beam segments if present."""
    out = p.copy()
    for _ in range(2):
        if out.shape[1] <= 4:
            break
        left_rgb = out[:, 0, :3].astype(np.int32)
        left_dark = (out[:, 0, 3] > 0) & (left_rgb[:, 0] < 45) & (left_rgb[:, 1] < 45) & (left_rgb[:, 2] < 45)
        if left_dark.sum() > out.shape[0] * 0.30:
            out = out[:, 1:, :]
        right_rgb = out[:, -1, :3].astype(np.int32)
        right_dark = (out[:, -1, 3] > 0) & (right_rgb[:, 0] < 45) & (right_rgb[:, 1] < 45) & (right_rgb[:, 2] < 45)
        if right_dark.sum() > out.shape[0] * 0.30:
            out = out[:, :-1, :]
    return out


def stitch_final_flash_beam(body_crop: dict, beam_parts: list[dict], row_ground_y: int) -> np.ndarray:
    """Seamlessly stitch Trunks firing pose + 3-part Final Flash beam without 1px divider lines, preserving full rounded tip."""
    canvas = place_on_canvas(body_crop, row_ground_y=row_ground_y)
    _, vis_x = np.where(canvas[:, :, 3] > 0)
    hand_right_x = int(vis_x.max())
    hand_center_y = int(round(ANCHOR_Y - 29))

    cleaned_parts = [strip_beam_dividers(part["rgba"]) for part in beam_parts]
    cur_x = hand_right_x + 1
    max_avail = (CANVAS_W - 2) - cur_x
    total_w = sum(p.shape[1] for p in cleaned_parts)

    # If modular 3-part beam (head | straight middle | rounded tip) slightly exceeds 320px canvas width,
    # trim only the uniform straight repeating middle segment so 100% of the rounded beam tip stays intact!
    if total_w > max_avail and len(cleaned_parts) >= 3:
        overflow = total_w - max_avail
        mid = cleaned_parts[1]
        if mid.shape[1] > overflow + 16:
            cleaned_parts[1] = mid[:, : mid.shape[1] - overflow, :]

    for p in cleaned_parts:
        ph, pw, _ = p.shape
        dst_y = max(2, min(CANVAS_H - ph - 2, hand_center_y - ph // 2))
        avail_w = min(pw, CANVAS_W - 2 - cur_x)
        if avail_w <= 0:
            break
        sub_dst = canvas[dst_y : dst_y + ph, cur_x : cur_x + avail_w]
        sub_src = p[:, :avail_w]
        mask = sub_src[:, :, 3:4] > 0
        sub_dst[:] = np.where(mask, sub_src, sub_dst)
        cur_x += avail_w
    return canvas


def compute_matte_and_sharpness_qa(frames_list: list[np.ndarray]) -> dict:
    """Measure exact matte cleanliness and Sobel acutance across all exported frames."""
    opaque_key_px = 0
    enclosed_pockets = 0
    ring_spill_px = 0
    ring_total_px = 0
    hard_alpha_px = 0
    vis_alpha_px = 0
    sobel_vals: list[float] = []

    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    ky = kx.T

    for f in frames_list:
        rgb = f[:, :, :3].astype(np.float32)
        a = f[:, :, 3]
        vis = a > 0
        if not np.any(vis):
            continue
        dist = np.sqrt(((rgb - BG_RGB) ** 2).sum(axis=-1))
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

        is_key_color = (a >= 200) & (dist <= 18.0) & ((b - g) >= 44.0) & ((b - r) >= 54.0)
        opaque_key_px += int(is_key_color.sum())

        border = np.zeros_like(vis)
        border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
        ext_trans = ndimage.binary_propagation(border & (~vis), mask=(~vis), structure=np.ones((3, 3)))
        if np.any(is_key_color):
            adj_ext = ndimage.binary_dilation(ext_trans, structure=np.ones((3, 3)))
            enclosed_pockets += int((is_key_color & (~adj_ext)).sum())

        adj_trans = ndimage.binary_dilation(~vis, structure=np.ones((3, 3))) & vis
        ring_total_px += int(adj_trans.sum())
        spill = adj_trans & (dist <= 18.0) & ((b - g) >= 36.0) & ((b - r) >= 46.0)
        ring_spill_px += int(spill.sum())

        vis_alpha_px += int(vis.sum())
        hard_alpha_px += int((a >= 245).sum())

        ys, xs = np.where(vis)
        luma = (
            0.299 * rgb[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1, 0]
            + 0.587 * rgb[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1, 1]
            + 0.114 * rgb[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1, 2]
        )
        gx = ndimage.convolve(luma, kx, mode="nearest")
        gy = ndimage.convolve(luma, ky, mode="nearest")
        mag = np.hypot(gx, gy)
        edge_m = mag > 25.0
        if np.any(edge_m):
            sobel_vals.append(float(mag[edge_m].mean()))

    return {
        "opaque_key_px": opaque_key_px,
        "enclosed_key_pockets": enclosed_pockets,
        "outer_ring_spill_fraction": round(ring_spill_px / max(1, ring_total_px), 4),
        "alpha_hardness_pct": round(hard_alpha_px * 100.0 / max(1, vis_alpha_px), 1),
        "edge_acutance_sobel": round(float(np.mean(sobel_vals)) if sobel_vals else 0.0, 2),
    }


def main() -> None:
    raw_copy_path = SOURCE_DIR / "raw_trunks_rage_atlas.png"
    if not raw_copy_path.exists():
        raise FileNotFoundError(f"Missing canonical raw sheet: {raw_copy_path}")

    raw_bytes = raw_copy_path.read_bytes()
    shutil.rmtree(ASSET_ROOT)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    (SOURCE_DIR / ".gdignore").write_text("", encoding="utf-8")
    raw_copy_path.write_bytes(raw_bytes)

    raw_im = Image.open(raw_copy_path).convert("RGBA")
    raw_arr = np.array(raw_im)
    lossless = is_lossless_navy_sheet(raw_arr)
    print(f"Loaded raw sheet {raw_im.size} | lossless_exact_pixel_art={lossless}")

    # 1. Extract all clean row groups on the 1340x2261 lossless Pixel-Art sheet
    r01 = extract_row_components(
        raw_arr, 188, 327, 14, 902, merge_overlap_ratio=0.45, lossless_exact=lossless
    )
    r02 = extract_row_components(raw_arr, 348, 413, 17, 401, lossless_exact=lossless)
    r03 = extract_row_components(raw_arr, 415, 500, 17, 684, lossless_exact=lossless)
    r04 = extract_row_components(raw_arr, 504, 566, 17, 831, lossless_exact=lossless)
    r05 = extract_row_components(
        raw_arr,
        570,
        651,
        17,
        1227,
        extra_exclusions=[(17, 643, 535, 651)],
        lossless_exact=lossless,
    )
    r06 = extract_row_components(raw_arr, 643, 708, 17, 531, lossless_exact=lossless)
    r07 = extract_row_components(
        raw_arr,
        717,
        816,
        17,
        814,
        merge_overlap_ratio=0.35,
        merge_min_px_overlap=8,
        lossless_exact=lossless,
    )
    r08 = extract_row_components(
        raw_arr, 825, 900, 23, 503, merge_min_px_overlap=6, lossless_exact=lossless
    )
    r09 = extract_row_components(
        raw_arr, 916, 1008, 17, 907, merge_overlap_ratio=0.60, lossless_exact=lossless
    )
    r10 = extract_row_components(
        raw_arr,
        1020,
        1117,
        17,
        556,
        extra_exclusions=[(17, 1099, 362, 1117)],
        merge_overlap_ratio=0.35,
        merge_thin_teleports=True,
        lossless_exact=lossless,
    )
    r13 = extract_row_components(
        raw_arr, 1618, 1698, 79, 1186, merge_overlap_ratio=0.55, lossless_exact=lossless
    )
    r14 = extract_row_components(
        raw_arr,
        1693,
        1878,
        23,
        1253,
        extra_exclusions=[(23, 1693, 1185, 1700), (1012, 1859, 1125, 1878)],
        merge_overlap_ratio=0.45,
        lossless_exact=lossless,
    )
    r15 = extract_row_components(
        raw_arr,
        1862,
        2012,
        9,
        1122,
        extra_exclusions=[(9, 1862, 452, 1883), (9, 2008, 95, 2012)],
        merge_overlap_ratio=0.42,
        lossless_exact=lossless,
    )
    r16 = extract_row_components(raw_arr, 2026, 2087, 9, 247, lossless_exact=lossless)

    print(
        "Extracted counts:",
        f"R01={len(r01)} R02={len(r02)} R03={len(r03)} R04={len(r04)} R05={len(r05)} "
        f"R06={len(r06)} R07={len(r07)} R08={len(r08)} R09={len(r09)} R10={len(r10)} "
        f"R13={len(r13)} R14={len(r14)} R15={len(r15)} R16={len(r16)}",
    )

    # 2. Register every sequence onto shared 320x256 canvas at foot_anchor_px = [96, 220]
    registered_frames: list[np.ndarray] = []
    frame_names: list[str] = []

    def add_frame(tag: str, canvas_arr: np.ndarray) -> int:
        idx = len(registered_frames)
        fname = f"frames/frame_{idx:03d}_{tag}.png"
        Image.fromarray(canvas_arr).save(SOURCE_DIR / fname)
        registered_frames.append(canvas_arr)
        frame_names.append(fname)
        return idx

    # Clip 1: idle & combat_ready (R02[0], R02[1])
    f_idle = add_frame("idle_0", place_on_canvas(r02[0], row_ground_y=408))
    f_ready = add_frame("ready_0", place_on_canvas(r02[1], row_ground_y=408))

    # Clip 2: walk (R03[9..14] — 6-frame walking stride cycle)
    walk_ids = [
        add_frame(f"walk_{k}", place_on_canvas(c, row_ground_y=495))
        for k, c in enumerate(r03[9:15])
    ]

    # Clip 3: run / high-speed dash (R03[0..2])
    run_ids = [
        add_frame(f"run_{k}", place_on_canvas(c, row_ground_y=495))
        for k, c in enumerate(r03[0:3])
    ]

    # Clip 4: jump (R03[3..8] — preserves exact 30px jump trajectory relative to y_ground=495)
    jump_ids = [
        add_frame(f"jump_{k}", place_on_canvas(c, row_ground_y=495))
        for k, c in enumerate(r03[3:9])
    ]

    # Clip 5: guard (R06[7..9] — standing, crouching, aerial guard)
    guard_ids = [
        add_frame(f"guard_{k}", place_on_canvas(c, row_ground_y=703))
        for k, c in enumerate(r06[7:10])
    ]

    # Clip 6: attack_light (ready stance + R04[0..8] rapid melee flurry)
    atk_light_ids = [f_ready] + [
        add_frame(f"atk_light_{k}", place_on_canvas(c, row_ground_y=561))
        for k, c in enumerate(r04[0:9])
    ]

    # Clip 7: attack_heavy (R04[9..16] smash punch -> crescent kick -> axe kick -> ground slam)
    atk_heavy_ids = [
        add_frame(f"atk_heavy_{k}", place_on_canvas(c, row_ground_y=561))
        for k, c in enumerate(r04[9:17])
    ]

    # Clip 8: spin_kick (R05[0..7] tornado spin & double crescent somersault kick)
    spin_kick_ids = [
        add_frame(f"spin_kick_{k}", place_on_canvas(c, row_ground_y=632))
        for k, c in enumerate(r05[0:8])
    ]

    # Clip 9: sword_combo (R05[8..18] cyan Ki-blade combo + Ki sword burst)
    sword_combo_ids = [
        add_frame(f"sword_combo_{k}", place_on_canvas(c, row_ground_y=635))
        for k, c in enumerate(r05[8:19])
    ]

    # Clip 10: burning_sword (R13[0..15] 16-hit golden sword combo + R13[16] X-slash burst composited in front of R13[15]!)
    burning_sword_ids = [
        add_frame(f"burn_sword_{k}", place_on_canvas(c, row_ground_y=1680))
        for k, c in enumerate(r13[0:16])
    ]
    if len(r13) >= 17:
        burning_sword_ids.append(
            add_frame(
                "burn_sword_xslash",
                composite_fx_ahead(
                    r13[15],
                    r13[16],
                    row_ground_y=1680,
                    fx_x_start=ANCHOR_X + 34,
                    fx_center_y=ANCHOR_Y - 28,
                ),
            )
        )

    # Clip 11: power_up (R01 — Base blue-hair Trunks -> Super Saiyan Rage transformation!)
    power_up_ids = []
    for k, c in enumerate(r01):
        boot_y = detect_boot_bottom_y(c, default_row_ground_y=c["sheet_y1"] - 4)
        power_up_ids.append(
            add_frame(f"power_up_{k}", place_on_canvas(c, row_ground_y=boot_y))
        )

    # Clip 12 & 13: aura_loop & ki_blast (R07)
    # Merge R07[3] + overlapping right-side lightning wing R07[4] on sheet coordinates so aura_loop_c has full bilateral lightning!
    ux0 = min(r07[3]["sheet_x0"], r07[4]["sheet_x0"])
    uy0 = min(r07[3]["sheet_y0"], r07[4]["sheet_y0"])
    ux1 = max(r07[3]["sheet_x1"], r07[4]["sheet_x1"])
    uy1 = max(r07[3]["sheet_y1"], r07[4]["sheet_y1"])
    aura_c_union = np.zeros((uy1 - uy0 + 1, ux1 - ux0 + 1, 4), dtype=np.uint8)
    for part_c in (r07[3], r07[4]):
        py0, px0 = part_c["sheet_y0"] - uy0, part_c["sheet_x0"] - ux0
        ph, pw, _ = part_c["rgba"].shape
        dst_s = aura_c_union[py0 : py0 + ph, px0 : px0 + pw]
        m_s = part_c["rgba"][:, :, 3:4] > 0
        dst_s[:] = np.where(m_s, part_c["rgba"], dst_s)
    r07_aura_c = {
        "rgba": aura_c_union,
        "sheet_x0": ux0,
        "sheet_y0": uy0,
        "sheet_x1": ux1,
        "sheet_y1": uy1,
        "w": ux1 - ux0 + 1,
        "h": uy1 - uy0 + 1,
    }

    aura_charge_0 = add_frame("aura_start", place_on_canvas(r07[0], row_ground_y=794))
    aura_loop_a = add_frame("aura_loop_a", place_on_canvas(r07[1], row_ground_y=793))
    aura_loop_b = add_frame("aura_loop_b", place_on_canvas(r07[2], row_ground_y=793))
    aura_loop_c = add_frame("aura_loop_c", place_on_canvas(r07_aura_c, row_ground_y=794))
    aura_loop_ids = [aura_loop_a, aura_loop_b, aura_loop_c, aura_loop_b]

    # R07[5..7] = 3 Ki-blast firing stances; R07[8] = muzzle burst; R07[9] = flying Ki bolt; R07[10..11] = Ki explosion!
    ki_blast_ids = [
        aura_charge_0,
        add_frame("ki_blast_0", place_on_canvas(r07[5], row_ground_y=793)),
        add_frame(
            "ki_blast_fire",
            composite_fx_ahead(
                r07[6], r07[8], row_ground_y=793, fx_x_start=ANCHOR_X + 26, fx_center_y=ANCHOR_Y - 28
            ),
        ),
        add_frame(
            "ki_blast_bolt",
            composite_fx_ahead(
                r07[7], r07[9], row_ground_y=793, fx_x_start=ANCHOR_X + 70, fx_center_y=ANCHOR_Y - 32
            ),
        ),
        add_frame(
            "ki_blast_hit_0",
            composite_fx_ahead(
                r07[7], r07[10], row_ground_y=793, fx_x_start=ANCHOR_X + 116, fx_center_y=ANCHOR_Y - 22
            ),
        ),
        add_frame(
            "ki_blast_hit_1",
            composite_fx_ahead(
                r07[5], r07[11], row_ground_y=793, fx_x_start=ANCHOR_X + 122, fx_center_y=ANCHOR_Y - 22
            ),
        ),
    ]

    # Clip 14: galick_gun (R08: 0..5 charge & thrust -> 7 full purple Galick Gun beam -> 6 cooldown!)
    gg_raw = [
        add_frame(f"galick_{k}", place_on_canvas(c, row_ground_y=888))
        for k, c in enumerate(r08[0:8])
    ]
    galick_gun_ids = [gg_raw[0], gg_raw[1], gg_raw[2], gg_raw[3], gg_raw[4], gg_raw[5], gg_raw[7], gg_raw[6]]

    # Clip 15: final_flash (R09: 0..5 golden aura charge -> stitched seamless pulsing beam A & B -> cooldown)
    ff_charge_ids = [
        add_frame(f"ff_charge_{k}", place_on_canvas(c, row_ground_y=987))
        for k, c in enumerate(r09[0:6])
    ]
    ff_thrust_id = add_frame("ff_thrust", place_on_canvas(r09[6], row_ground_y=987))
    beam_a_parts = [c for c in r09[7:] if c["sheet_x0"] < 675]
    beam_b_parts = [c for c in r09[7:] if c["sheet_x0"] >= 675]
    ff_beam_a = add_frame("ff_beam_a", stitch_final_flash_beam(r09[6], beam_a_parts, row_ground_y=987))
    ff_beam_b = add_frame("ff_beam_b", stitch_final_flash_beam(r09[6], beam_b_parts, row_ground_y=987))
    final_flash_ids = ff_charge_ids + [ff_thrust_id, ff_beam_a, ff_beam_b, ff_beam_a, ff_beam_b, ff_thrust_id]

    # Clip 16: vanish_blitz (R10: draw sword -> RGB speed-line vanish -> sheathe click -> delayed cross starburst!)
    vanish_blitz_ids = []
    for k, c in enumerate(r10):
        is_streak = c["w"] <= 32 and c["h"] >= 45
        vanish_blitz_ids.append(
            add_frame(
                f"vanish_{k}",
                place_on_canvas(c, row_ground_y=1092, center_x_box=is_streak),
            )
        )

    # Clip 17: ultimate_spirit_sword (R14 Sword of Hope Genki Sphere + R15 Giant Sword of Hope Cleave & Pillar!)
    spirit_ids = []
    for k, c in enumerate(r14):
        center_sphere = c["w"] >= 115 and c["h"] >= 105
        spirit_ids.append(
            add_frame(
                f"spirit_p1_{k}",
                place_on_canvas(c, row_ground_y=1860, center_x_box=center_sphere),
            )
        )
    for k, c in enumerate(r15):
        is_pillar = c["sheet_x0"] >= 1010
        if is_pillar:
            # Composite giant Sword of Hope pillar erupting directly in front of Trunks's downward cleave!
            cleave_pose = r15[5] if len(r15) > 5 else r15[-2]
            spirit_ids.append(
                add_frame(
                    f"spirit_p2_{k}",
                    composite_fx_ahead(
                        cleave_pose,
                        c,
                        row_ground_y=2002,
                        fx_x_start=ANCHOR_X + 46,
                        fx_ground_align=True,
                    ),
                )
            )
        else:
            spirit_ids.append(
                add_frame(
                    f"spirit_p2_{k}",
                    place_on_canvas(c, row_ground_y=2002),
                )
            )

    # Clip 18 & 19: hit (R06[0..2]) & ko (R06[3..6] airborne knockback -> ground downed -> stand up recovery)
    hit_ids = [
        add_frame(f"hit_{k}", place_on_canvas(c, row_ground_y=703))
        for k, c in enumerate(r06[0:3])
    ]
    ko_air_0 = add_frame("ko_air_0", place_on_canvas(r06[3], row_ground_y=703))
    ko_air_1 = add_frame("ko_air_1", place_on_canvas(r06[4], row_ground_y=703))
    ko_down = add_frame("ko_down", place_on_canvas(r06[5], align_bottom_direct=True))
    ko_stand = add_frame("ko_stand", place_on_canvas(r06[6], row_ground_y=703))
    ko_ids = [ko_air_0, ko_air_1, ko_down, ko_stand]

    # Clip 20: win (R16[0..3] — Ki blade dissipates cleanly into steel sword victory pose)
    win_ids = [
        add_frame(f"win_{k}", place_on_canvas(c, row_ground_y=2085))
        for k, c in enumerate(r16[0:4])
    ]

    # 3. Compute verified QA metrics across all registered frames
    qa = compute_matte_and_sharpness_qa(registered_frames)
    print("Matte & Pixel Sharpness QA:", json.dumps(qa, indent=2))
    assert qa["opaque_key_px"] == 0, f"Remaining opaque #2B3772 key pixels: {qa['opaque_key_px']}"
    assert qa["enclosed_key_pockets"] == 0, f"Remaining enclosed pockets: {qa['enclosed_key_pockets']}"

    # Measure exact character bounding boxes on shared 320x256 canvas for Map Sync Metrics
    idle_arr = registered_frames[f_idle]
    iy, ix = np.where(idle_arr[:, :, 3] > 0)
    body_bbox = {
        "x": int(ix.min()),
        "y": int(iy.min()),
        "w": int(ix.max() - ix.min() + 1),
        "h": int(iy.max() - iy.min() + 1),
    }

    union_vis = np.zeros((CANVAS_H, CANVAS_W), dtype=bool)
    for f in registered_frames:
        union_vis |= f[:, :, 3] > 0
    uy, ux = np.where(union_vis)
    full_fx_bbox = {
        "x": int(ux.min()),
        "y": int(uy.min()),
        "w": int(ux.max() - ux.min() + 1),
        "h": int(uy.max() - uy.min() + 1),
    }

    # 4. Write v2 animation-clips manifest (60Hz tick grid)
    clips_manifest = {
        "schema": "generate2dsprite.animation_clips.v2",
        "frames": frame_names,
        "anchor_px": [ANCHOR_X, ANCHOR_Y],
        "clips": {
            "idle": {
                "frames": [f_idle],
                "duration_ms": 500,
                "loop": True,
            },
            "walk": {
                "frames": walk_ids,
                "ticks": [6] * len(walk_ids),
                "loop_policy": "cycle",
                "role": "player",
            },
            "run": {
                "frames": [run_ids[1], run_ids[2]] if len(run_ids) >= 3 else run_ids,
                "ticks": [5, 5],
                "loop_policy": "cycle",
                "role": "player",
            },
            "jump": {
                "frames": jump_ids,
                "ticks": [4, 5, 7, 6, 5, 5][: len(jump_ids)],
                "loop_policy": "oneshot",
                "role": "player",
            },
            "guard": {
                "frames": guard_ids,
                "ticks": [8, 8, 8][: len(guard_ids)],
                "loop_policy": "oneshot",
                "role": "player",
            },
            "attack_light": {
                "frames": atk_light_ids,
                "ticks": [4] * len(atk_light_ids),
                "loop_policy": "oneshot",
                "role": "player",
                "hitstop_ticks": 3,
                "events": [
                    {"at": 0, "name": "tell"},
                    {"at": 2, "name": "hit", "data": {"damage": 90}},
                    {"at": len(atk_light_ids) - 2, "name": "impact", "data": {"damage": 120}},
                    {"at": len(atk_light_ids) - 1, "name": "end"},
                ],
            },
            "attack_heavy": {
                "frames": atk_heavy_ids,
                "ticks": [5, 4, 4, 4, 5, 5, 6, 7][: len(atk_heavy_ids)],
                "loop_policy": "oneshot",
                "role": "player",
                "hitstop_ticks": 4,
                "events": [
                    {"at": 0, "name": "tell"},
                    {"at": 3, "name": "hit", "data": {"damage": 160}},
                    {"at": len(atk_heavy_ids) - 2, "name": "impact", "data": {"damage": 220}},
                    {"at": len(atk_heavy_ids) - 1, "name": "end"},
                ],
            },
            "spin_kick": {
                "frames": spin_kick_ids,
                "ticks": [4, 4, 4, 4, 5, 5, 5, 6][: len(spin_kick_ids)],
                "loop_policy": "oneshot",
                "role": "player",
                "events": [
                    {"at": 0, "name": "tell"},
                    {"at": 4, "name": "hit", "data": {"damage": 180}},
                    {"at": len(spin_kick_ids) - 1, "name": "end"},
                ],
            },
            "sword_combo": {
                "frames": sword_combo_ids,
                "ticks": [5, 4, 4, 4, 5, 4, 4, 4, 4, 6, 7][: len(sword_combo_ids)],
                "loop_policy": "oneshot",
                "role": "player",
                "hitstop_ticks": 5,
                "events": [
                    {"at": 0, "name": "tell"},
                    {"at": 3, "name": "hit", "data": {"damage": 210}},
                    {"at": len(sword_combo_ids) - 2, "name": "impact", "data": {"damage": 320}},
                    {"at": len(sword_combo_ids) - 1, "name": "end"},
                ],
            },
            "burning_sword": {
                "frames": burning_sword_ids,
                "ticks": [4] * (len(burning_sword_ids) - 1) + [6],
                "loop_policy": "oneshot",
                "role": "player",
                "hitstop_ticks": 5,
                "events": [
                    {"at": 0, "name": "tell"},
                    {"at": 6, "name": "hit", "data": {"damage": 240}},
                    {"at": len(burning_sword_ids) - 2, "name": "impact", "data": {"damage": 360}},
                    {"at": len(burning_sword_ids) - 1, "name": "end"},
                ],
            },
            "power_up": {
                "frames": power_up_ids,
                "ticks": [6] * len(power_up_ids),
                "loop_policy": "oneshot",
                "role": "player",
                "hitstop_ticks": 4,
                "events": [
                    {"at": 0, "name": "tell"},
                    {"at": 3, "name": "impact"},
                    {"at": 6, "name": "hit", "data": {"damage": 250}},
                    {"at": len(power_up_ids) - 1, "name": "end"},
                ],
            },
            "aura_loop": {
                "frames": aura_loop_ids,
                "ticks": [5, 5, 5, 5],
                "loop_policy": "cycle",
                "role": "player",
            },
            "ki_blast": {
                "frames": ki_blast_ids,
                "ticks": [5] * len(ki_blast_ids),
                "loop_policy": "oneshot",
                "role": "player",
            },
            "galick_gun": {
                "frames": galick_gun_ids,
                "ticks": [5, 5, 5, 5, 5, 4, 18, 7],
                "loop_policy": "oneshot",
                "role": "player",
                "hitstop_ticks": 6,
                "events": [
                    {"at": 0, "name": "tell"},
                    {"at": 6, "name": "hit", "data": {"damage": 380}},
                    {"at": 7, "name": "end"},
                ],
            },
            "final_flash": {
                "frames": final_flash_ids,
                "ticks": [5, 5, 5, 5, 5, 5, 4, 6, 6, 6, 6, 7],
                "loop_policy": "oneshot",
                "role": "player",
                "hitstop_ticks": 6,
                "events": [
                    {"at": 0, "name": "tell"},
                    {"at": 7, "name": "hit", "data": {"damage": 480}},
                    {"at": 11, "name": "end"},
                ],
            },
            "vanish_blitz": {
                "frames": vanish_blitz_ids,
                "ticks": [5] * len(vanish_blitz_ids),
                "loop_policy": "oneshot",
                "role": "player",
                "hitstop_ticks": 5,
                "events": [
                    {"at": 0, "name": "tell"},
                    {"at": len(vanish_blitz_ids) - 2, "name": "hit", "data": {"damage": 420}},
                    {"at": len(vanish_blitz_ids) - 1, "name": "end"},
                ],
            },
            "ultimate_spirit_sword": {
                "frames": spirit_ids,
                "ticks": [5] * len(spirit_ids),
                "loop_policy": "oneshot",
                "role": "player",
                "hitstop_ticks": 8,
                "events": [
                    {"at": 0, "name": "tell"},
                    {"at": len(r14) + 4, "name": "hit", "data": {"damage": 650}},
                    {"at": len(spirit_ids) - 1, "name": "impact", "data": {"damage": 800}},
                ],
            },
            "hit": {
                "frames": hit_ids,
                "ticks": [5, 6, 6][: len(hit_ids)],
                "loop_policy": "oneshot",
                "role": "player",
            },
            "ko": {
                "frames": ko_ids,
                "ticks": [6, 6, 20, 8],
                "loop_policy": "oneshot",
                "role": "player",
            },
            "win": {
                "frames": win_ids,
                "ticks": [7, 7, 7, 18][: len(win_ids)],
                "loop_policy": "oneshot",
                "role": "player",
            },
        },
        "states": {
            "idle": "idle",
            "moving": "walk",
            "running": "run",
            "jumping": "jump",
            "charge": "aura_loop",
            "skill": "ultimate_spirit_sword",
        },
        "sampling": "nearest",
        "pixel_art": True,
        "art_source": "existing",
        "body_height_px": body_bbox["h"],
        "shadow": {"rx": 18, "ry": 5, "opacity": 0.38},
    }

    manifest_path = SOURCE_DIR / "clips.json"
    manifest_path.write_text(json.dumps(clips_manifest, indent=2) + "\n", encoding="utf-8")

    # 5. Invoke official Forge tools: build_animation_clips.py -> export_engine.py
    subprocess.run(
        [
            sys.executable,
            str(SKILL_SCRIPTS / "build_animation_clips.py"),
            "--manifest",
            str(manifest_path),
            "--output-dir",
            str(CLIPS_DIR),
            "--tick-hz",
            "60",
            "--preview-scale",
            "2",
        ],
        check=True,
    )
    (CLIPS_DIR / ".gdignore").write_text("", encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            str(SKILL_SCRIPTS / "export_engine.py"),
            "--clips",
            str(CLIPS_DIR / "animation-clips.json"),
            "--target",
            "all",
            "--output-dir",
            str(BUNDLE_DIR),
            "--name",
            "trunks_rage",
            "--sampling",
            "nearest",
            "--max-atlas-size",
            "4096",
        ],
        check=True,
    )
    for sub_ignore in ("aseprite", "godot-sprite3d"):
        sub_dir = BUNDLE_DIR / sub_ignore
        if sub_dir.is_dir():
            (sub_dir / ".gdignore").write_text("", encoding="utf-8")

    atlas_im = Image.open(BUNDLE_DIR / "godot" / "trunks_rage-atlas-00.png")
    summary = {
        "character_id": "trunks_rage",
        "raw_sheet_size_px": list(raw_im.size),
        "lossless_exact_pixel_art": lossless,
        "unique_frames": len(registered_frames),
        "clip_count": len(clips_manifest["clips"]),
        "clips": list(clips_manifest["clips"].keys()),
        "atlas_size_px": list(atlas_im.size),
        "canvas_size_px": [CANVAS_W, CANVAS_H],
        "foot_anchor_px": [ANCHOR_X, ANCHOR_Y],
        "body_only_bbox_px": body_bbox,
        "full_fx_bbox_px": full_fx_bbox,
        "qa": qa,
    }
    (SOURCE_DIR / "build_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print("BUILD_SUMMARY:", json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
