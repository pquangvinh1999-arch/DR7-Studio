#!/usr/bin/env python3
"""DR7-Studio — T-rex (t_rex) Pixel-Art Atlas & Animation Pipeline (v2 — Visual QA Refined).

Builds the complete 9-clip (8 body + 1 independent spinning fireball FX)
60Hz Nearest pixel-art bundle from the Owner-approved master
`work/characters/t_rex/approved-master/approved-original.png`.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

REPO_ROOT = Path(__file__).resolve().parents[3]
WORK_DIR = REPO_ROOT / "work" / "characters" / "t_rex"
APPROVED_MASTER = WORK_DIR / "approved-master" / "approved-original.png"
FIRE_FX_SOURCE = WORK_DIR / "approved-master" / "fire_fx_source.png"

# Logical canvas is 192x128 -> 2x Nearest integer upscale -> 384x256 gameplay canvas
LOGICAL_W, LOGICAL_H = 192, 128
CANVAS_W, CANVAS_H = 384, 256
LOGICAL_ANCHOR_X, LOGICAL_ANCHOR_Y = 88, 112
ANCHOR_X, ANCHOR_Y = 176, 224  # [176, 224] on 384x256 canvas
FX_PIVOT_X, FX_PIVOT_Y = 176, 128  # Centered on ANCHOR_X for zero turn-test slide

# In the 100x100 logical source grid:
# Feet bottom is at y=82, torso center X is around x=52.
# So source (52, 82) maps to logical canvas (88, 112) -> offset (+36, +30).
SRC_OFFSET_X = 36
SRC_OFFSET_Y = 30

OUTLINE_RGBA = np.array([18, 20, 24, 255], dtype=np.uint8)
OLIVE_DARK = np.array([82, 87, 48, 255], dtype=np.uint8)
OLIVE_SHADOW = np.array([98, 102, 57, 255], dtype=np.uint8)
OLIVE_MID = np.array([127, 129, 72, 255], dtype=np.uint8)
OLIVE_MAIN = np.array([141, 142, 79, 255], dtype=np.uint8)
OLIVE_HIGHLIGHT = np.array([165, 174, 104, 255], dtype=np.uint8)
BELLY_SHADOW = np.array([167, 160, 114, 255], dtype=np.uint8)
BELLY_MID = np.array([172, 151, 126, 255], dtype=np.uint8)
BELLY_LIGHT = np.array([208, 202, 161, 255], dtype=np.uint8)
TOOTH_WHITE = np.array([242, 238, 214, 255], dtype=np.uint8)
MOUTH_DARK = np.array([92, 24, 32, 255], dtype=np.uint8)
TONGUE_RED = np.array([168, 44, 52, 255], dtype=np.uint8)

# VFX Palette (Pixel-art crisp colors)
VFX_WHITE = np.array([255, 252, 224, 255], dtype=np.uint8)
VFX_GOLD = np.array([250, 204, 21, 255], dtype=np.uint8)
VFX_ORANGE = np.array([249, 115, 22, 255], dtype=np.uint8)
VFX_RED = np.array([220, 38, 38, 255], dtype=np.uint8)
VFX_CRIMSON = np.array([127, 29, 29, 255], dtype=np.uint8)
VFX_CYAN_WIND = np.array([224, 242, 254, 255], dtype=np.uint8)
VFX_LIME_SLASH = np.array([190, 242, 100, 255], dtype=np.uint8)


def extract_logical_100(master_path: Path) -> np.ndarray:
    """Extract the exact 100x100 logical pixel grid from the 1024x1024 master."""
    im = Image.open(master_path).convert("RGB")
    arr = np.array(im)
    n = 100
    logical = np.zeros((n, n, 4), dtype=np.uint8)
    for gy in range(n):
        cy = int((gy + 0.5) * 1024 / n)
        for gx in range(n):
            cx = int((gx + 0.5) * 1024 / n)
            patch = arr[max(0, cy - 2) : min(1024, cy + 3), max(0, cx - 2) : min(1024, cx + 3)]
            med = np.median(patch.reshape(-1, 3), axis=0).astype(np.uint8)
            r, g, b = int(med[0]), int(med[1]), int(med[2])
            if (r - g > 60 and b - g > 60) or (r > 180 and g < 100 and b > 180):
                logical[gy, gx] = [0, 0, 0, 0]
            else:
                logical[gy, gx] = [r, g, b, 255]

    alpha = logical[:, :, 3] > 0
    for gy in range(n):
        for gx in range(n):
            if not alpha[gy, gx]:
                continue
            r, g, b = int(logical[gy, gx, 0]), int(logical[gy, gx, 1]), int(logical[gy, gx, 2])
            if r > g + 25 and b > g + 15:
                logical[gy, gx] = OUTLINE_RGBA
            elif r < 40 and g < 40 and b < 45:
                logical[gy, gx] = OUTLINE_RGBA

    palette = np.array(
        [
            OUTLINE_RGBA[:3],
            OLIVE_DARK[:3],
            OLIVE_SHADOW[:3],
            [101, 105, 58],
            OLIVE_MID[:3],
            [140, 141, 79],
            OLIVE_MAIN[:3],
            [151, 145, 92],
            OLIVE_HIGHLIGHT[:3],
            BELLY_SHADOW[:3],
            BELLY_MID[:3],
            BELLY_LIGHT[:3],
        ],
        dtype=np.int32,
    )
    ys, xs = np.where(logical[:, :, 3] > 0)
    for y, x in zip(ys, xs):
        px = logical[y, x, :3].astype(np.int32)
        dists = ((palette - px) ** 2).sum(axis=1)
        logical[y, x, :3] = palette[np.argmin(dists)].astype(np.uint8)

    return logical


def extract_part_with_cap(
    src: np.ndarray,
    mask: np.ndarray,
    caps: list[tuple[int, int, int, np.ndarray]] | None = None,
    strip_border_outline: bool = True,
) -> np.ndarray:
    """Extract part RGBA, keeping only the primary connected component and replacing border outline for seamless union."""
    labeled, n_comp = ndimage.label(mask)
    if n_comp > 1:
        counts = np.bincount(labeled.ravel())
        counts[0] = 0
        mask = labeled == int(np.argmax(counts))
    out = np.zeros_like(src)
    out[mask] = src[mask]
    if strip_border_outline:
        op = out[:, :, 3] > 0
        eroded = ndimage.binary_erosion(op, structure=np.ones((3, 3), dtype=bool))
        border = op & ~eroded
        is_dark = (out[:, :, 0] < 45) & (out[:, :, 1] < 45) & (out[:, :, 2] < 45)
        to_fill = border & is_dark
        interior_colored = op & ~is_dark
        if interior_colored.any() and to_fill.any():
            _, idx = ndimage.distance_transform_edt(~interior_colored, return_indices=True)
            fy, fx = np.where(to_fill)
            out[fy, fx] = out[idx[0, fy, fx], idx[1, fy, fx]]
    if caps:
        yy, xx = np.mgrid[0 : src.shape[0], 0 : src.shape[1]]
        for px, py, rad, col in caps:
            disk = ((xx - px) ** 2 + (yy - py) ** 2) <= rad**2
            fill = disk & (out[:, :, 3] == 0)
            out[fill] = col
    return out


def add_pixel_outline(layer: np.ndarray, outline_col: np.ndarray = OUTLINE_RGBA) -> np.ndarray:
    """Add a clean 1px 4-connected dark pixel-art outline around the interior fill of `layer`."""
    res = layer.copy()
    op = res[:, :, 3] > 0
    if not op.any():
        return res
    struct4 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)
    eroded = ndimage.binary_erosion(op, structure=struct4, border_value=0)
    border = op & ~eroded
    res[border] = outline_col
    return res


def composite_over(dst: np.ndarray, src: np.ndarray) -> None:
    """Composite opaque pixels of `src` onto `dst` in-place."""
    m = src[:, :, 3] > 0
    dst[m] = src[m]


def draw_neck_capsule(
    buf: np.ndarray,
    p0: tuple[float, float],
    p1: tuple[float, float],
    radius: float,
    flip_x: bool = False,
) -> None:
    """Fill a smooth olive/cream neck bridge between torso collar `p0` and head base `p1` so they never detach."""
    x0, y0 = p0
    x1, y1 = p1
    xmin = max(0, int(min(x0, x1) - radius - 2))
    xmax = min(LOGICAL_W - 1, int(max(x0, x1) + radius + 2))
    ymin = max(0, int(min(y0, y1) - radius - 2))
    ymax = min(LOGICAL_H - 1, int(max(y0, y1) + radius + 2))
    vx, vy = x1 - x0, y1 - y0
    seg_len2 = max(1e-4, vx * vx + vy * vy)
    for y in range(ymin, ymax + 1):
        for x in range(xmin, xmax + 1):
            if buf[y, x, 3] > 0:
                continue
            t = max(0.0, min(1.0, ((x - x0) * vx + (y - y0) * vy) / seg_len2))
            px = x0 + t * vx
            py = y0 + t * vy
            d2 = (x - px) ** 2 + (y - py) ** 2
            if d2 <= radius * radius:
                # Front of neck (right side when not flipped, left side when flipped) is cream belly color
                rel_x = (x - px) * (-1.0 if flip_x else 1.0)
                buf[y, x] = BELLY_LIGHT if rel_x > 1.2 else OLIVE_MAIN


def warp_part(
    part: np.ndarray,
    src_pivot: tuple[float, float],
    dst_pivot: tuple[float, float],
    angle_deg: float = 0.0,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    flip_x: bool = False,
    shear_x: float = 0.0,
    outline: bool = True,
) -> np.ndarray:
    """Inverse-map `part` (100x100) onto the 192x128 logical canvas around pivots with zero gaps."""
    out = np.zeros((LOGICAL_H, LOGICAL_W, 4), dtype=np.uint8)
    ys, xs = np.where(part[:, :, 3] > 0)
    if len(xs) == 0:
        return out

    rad = math.radians(angle_deg)
    c, s = math.cos(rad), math.sin(rad)
    spx, spy = src_pivot
    dpx, dpy = dst_pivot

    corners_x = np.array([xs.min() - 2, xs.max() + 2, xs.min() - 2, xs.max() + 2], dtype=float) - spx
    corners_y = np.array([ys.min() - 2, ys.min() - 2, ys.max() + 2, ys.max() + 2], dtype=float) - spy
    if flip_x:
        corners_x = -corners_x
    corners_x = corners_x * scale_x + corners_y * shear_x
    corners_y = corners_y * scale_y
    rx = c * corners_x - s * corners_y + dpx
    ry = s * corners_x + c * corners_y + dpy

    x0 = max(0, int(math.floor(rx.min())) - 2)
    x1 = min(LOGICAL_W - 1, int(math.ceil(rx.max())) + 2)
    y0 = max(0, int(math.floor(ry.min())) - 2)
    y1 = min(LOGICAL_H - 1, int(math.ceil(ry.max())) + 2)
    if x0 > x1 or y0 > y1:
        return out

    gy, gx = np.mgrid[y0 : y1 + 1, x0 : x1 + 1]
    dx = gx.astype(float) - dpx
    dy = gy.astype(float) - dpy

    ux = c * dx + s * dy
    uy = -s * dx + c * dy

    sy_local = uy / max(0.05, scale_y)
    sx_local = (ux - sy_local * shear_x) / max(0.05, scale_x)
    if flip_x:
        sx_local = -sx_local

    src_x = np.rint(sx_local + spx).astype(int)
    src_y = np.rint(sy_local + spy).astype(int)

    valid = (src_x >= 0) & (src_x < part.shape[1]) & (src_y >= 0) & (src_y < part.shape[0])
    sub = out[y0 : y1 + 1, x0 : x1 + 1]
    vy, vx = np.where(valid)
    sampled = part[src_y[vy, vx], src_x[vy, vx]]
    vis = sampled[:, 3] > 0
    sub[vy[vis], vx[vis]] = sampled[vis]

    if outline:
        sub_outlined = add_pixel_outline(sub)
        out[y0 : y1 + 1, x0 : x1 + 1] = sub_outlined
    return out


def warp_tail_spline(
    tail_part: np.ndarray,
    src_root: tuple[float, float],
    dst_root: tuple[float, float],
    base_angle_deg: float = 0.0,
    wag_amp: float = 0.0,
    wag_phase: float = 0.0,
    wag_freq: float = 2.2,
    curl_lift: float = 0.0,
    scale_x: float = 1.0,
    flip_x: bool = False,
    outline: bool = True,
) -> np.ndarray:
    """Deform the segmented tail smoothly along a continuous spline wave from root to tip."""
    pad = 24
    loc = np.zeros((100 + pad * 2, 100 + pad * 2, 4), dtype=np.uint8)
    rx, ry = src_root
    for y in range(100 + pad * 2):
        for x in range(100 + pad * 2):
            sx_f = x - pad
            if sx_f > rx + 5 or sx_f < 0:
                continue
            u = max(0.0, min(1.0, (rx - sx_f) / 35.0))
            dy_wave = wag_amp * (u**1.35) * math.sin(wag_phase - u * wag_freq) - curl_lift * (u**1.4)
            sy_f = (y - pad) - dy_wave
            sx_i = int(round(sx_f))
            sy_i = int(round(sy_f))
            if 0 <= sx_i < 100 and 0 <= sy_i < 100:
                px = tail_part[sy_i, sx_i]
                if px[3] > 0:
                    loc[y, x] = px

    return warp_part(
        loc,
        src_pivot=(rx + pad, ry + pad),
        dst_pivot=dst_root,
        angle_deg=base_angle_deg,
        scale_x=scale_x,
        flip_x=flip_x,
        outline=outline,
    )


@dataclass
class PoseSpec:
    body_dx: float = 0.0
    body_dy: float = 0.0
    body_angle: float = 0.0
    body_scale_x: float = 1.0
    body_flip_x: bool = False
    head_dx: float = 0.0
    head_dy: float = 0.0
    head_angle: float = 0.0
    jaw_angle: float = 0.0
    eye_closed: bool = False
    near_arm_angle: float = 0.0
    far_arm_angle: float = 0.0
    tail_angle: float = 0.0
    tail_wag_amp: float = 0.0
    tail_wag_phase: float = 0.0
    tail_curl_lift: float = 0.0
    tail_scale_x: float = 1.0
    tail_flip_x: bool = False
    tail_in_front: bool = False
    n_hip_angle: float = 0.0
    n_knee_angle: float = 0.0
    n_foot_angle: float = 0.0
    n_hip_dx: float = 0.0
    n_hip_dy: float = 0.0
    f_hip_angle: float = 0.0
    f_knee_angle: float = 0.0
    f_foot_angle: float = 0.0
    f_hip_dx: float = 0.0
    f_hip_dy: float = 0.0
    clamp_ground_ko: bool = False
    bite_vfx_phase: int = -1
    spin_vfx_phase: int = -1
    fire_charge_phase: int = -1


class TRexBuilder:
    def __init__(self, master_path: Path, fire_src_path: Path = FIRE_FX_SOURCE) -> None:
        self.src = extract_logical_100(master_path)
        self.owner_fire_crops = extract_owner_fire_frames(fire_src_path)
        self._build_parts()

    def _build_parts(self) -> None:
        s = self.src
        op = s[:, :, 3] > 0
        yy, xx = np.mgrid[0:100, 0:100]
        is_cream = (s[:, :, 0] > 165) & (s[:, :, 2] > 110)

        m_far_arm = op & (xx >= 72) & (yy >= 48) & (yy <= 59)
        m_near_arm = (
            op
            & (xx >= 61)
            & (xx <= 72)
            & (yy >= 46)
            & (yy <= 59)
            & ((yy >= 52) | ((xx >= 61) & (xx <= 66)))
            & ~(is_cream & (xx >= 66) & (yy <= 51))
        )

        near_leg_all = op & (yy >= 47) & (xx >= 35) & (
            ((yy <= 52) & (xx >= 38) & (xx <= 50))
            | ((yy >= 53) & (yy <= 62) & (xx >= 38) & (xx <= 52) & ~is_cream)
            | ((yy >= 63) & (xx <= 52))
        )
        self.near_thigh = extract_part_with_cap(
            s, near_leg_all & (yy <= 64), caps=[(45, 50, 4, OLIVE_MAIN), (44, 63, 3, OLIVE_MAIN)]
        )
        self.near_shin = extract_part_with_cap(
            s, near_leg_all & (yy >= 62) & (yy <= 75), caps=[(44, 63, 3, OLIVE_MAIN), (40, 74, 2, OLIVE_MID)]
        )
        self.near_foot = extract_part_with_cap(
            s, near_leg_all & (yy >= 74), caps=[(40, 75, 2, OLIVE_MID)]
        )

        belly_border_y = 62 - np.maximum(0, (xx - 52) * 0.45)
        far_leg_all = op & (xx >= 53) & (xx <= 69) & (yy >= 57) & (yy >= belly_border_y) & ~m_near_arm
        self.far_thigh = extract_part_with_cap(
            s, far_leg_all & (yy <= 66), caps=[(60, 58, 4, OLIVE_SHADOW), (61, 65, 3, OLIVE_SHADOW)]
        )
        self.far_shin = extract_part_with_cap(
            s, far_leg_all & (yy >= 64) & (yy <= 74), caps=[(61, 65, 3, OLIVE_SHADOW), (58, 74, 2, OLIVE_SHADOW)]
        )
        self.far_foot = extract_part_with_cap(
            s, far_leg_all & (yy >= 73), caps=[(58, 74, 2, OLIVE_SHADOW)]
        )

        m_tail = op & (xx <= 40) & (yy >= 43) & (yy <= 59) & ~(near_leg_all & (yy >= 50) & (xx >= 38))
        self.tail = extract_part_with_cap(
            s, m_tail, caps=[(38, 50, 6, OLIVE_MAIN), (41, 50, 5, OLIVE_MAIN)]
        )

        mouth_y = np.where(xx < 78, 29 + (xx - 73) * 0.4, 31 + (xx - 78) * 0.15)
        head_region = op & (xx >= 70) & (yy <= 38)
        m_upper_head = head_region & ((yy <= mouth_y) | ((xx >= 83) & (yy <= 33)))
        m_lower_jaw = head_region & ~m_upper_head & (xx >= 72) & (yy >= 28) & (yy <= 37)

        self.upper_head = extract_part_with_cap(
            s, m_upper_head, caps=[(72, 29, 5, OLIVE_MAIN), (71, 31, 4, OLIVE_MAIN)]
        )
        self.lower_jaw = extract_part_with_cap(s, m_lower_jaw, caps=[(74, 31, 3, BELLY_LIGHT)])
        for tx in range(81, 92, 2):
            self.lower_jaw[32, tx] = TOOTH_WHITE
            self.lower_jaw[33, tx] = BELLY_LIGHT

        m_torso = (
            op
            & ~m_far_arm
            & ~m_near_arm
            & ~near_leg_all
            & ~far_leg_all
            & ~m_tail
            & ~m_upper_head
            & ~m_lower_jaw
        )
        torso_raw = s.copy()
        torso_mask = m_torso.copy()
        # Heal internal strip at x=37..42, y=44..58 so tail and torso merge with zero vertical seam
        for y in range(44, 60):
            for x in range(36, 55):
                if not torso_mask[y, x] and op[y, x]:
                    torso_mask[y, x] = True
                    torso_raw[y, x] = BELLY_MID if (y >= 55 and x >= 49) else (OLIVE_MID if y >= 52 else OLIVE_MAIN)
        for y in range(45, 56):
            for x in range(60, 70):
                if not torso_mask[y, x] and op[y, x]:
                    torso_mask[y, x] = True
                    torso_raw[y, x] = BELLY_LIGHT if x >= 66 else OLIVE_MAIN
        for y in range(26, 37):
            for x in range(67, 77):
                if not torso_mask[y, x] and op[y, x]:
                    torso_mask[y, x] = True
                    torso_raw[y, x] = BELLY_LIGHT if x >= 72 else OLIVE_MAIN

        self.torso = extract_part_with_cap(
            torso_raw,
            torso_mask,
            caps=[(71, 30, 5, OLIVE_MAIN), (39, 50, 6, OLIVE_MAIN)],
        )
        self.near_arm = extract_part_with_cap(s, m_near_arm, caps=[(63, 48, 2, OLIVE_MAIN)])
        self.far_arm = extract_part_with_cap(s, m_far_arm, caps=[(73, 51, 2, OLIVE_SHADOW)])

    @staticmethod
    def _rot_pt(
        pt: tuple[float, float], piv: tuple[float, float], deg: float, sx: float = 1.0, flip_x: bool = False
    ) -> tuple[float, float]:
        dx = (pt[0] - piv[0]) * (-1.0 if flip_x else 1.0) * sx
        dy = pt[1] - piv[1]
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        return (piv[0] + c * dx - s * dy, piv[1] + s * dx + c * dy)

    def render_pose(self, p: PoseSpec) -> np.ndarray:
        """Render a PoseSpec to a 384x256 RGBA canvas (2x Nearest from 192x128 logical canvas)."""
        canvas = np.zeros((LOGICAL_H, LOGICAL_W, 4), dtype=np.uint8)

        torso_src = (52.0, 50.0)
        torso_dst = (52.0 + SRC_OFFSET_X + p.body_dx, 50.0 + SRC_OFFSET_Y + p.body_dy)

        def body_joint(sx: float, sy: float) -> tuple[float, float]:
            pt = self._rot_pt((sx, sy), torso_src, p.body_angle, sx=p.body_scale_x, flip_x=p.body_flip_x)
            return (
                torso_dst[0] + (pt[0] - torso_src[0]),
                torso_dst[1] + (pt[1] - torso_src[1]),
            )

        # 1. Far Leg chain: Hip (60, 58) -> Knee (61, 65) -> Ankle (58, 74)
        f_hip_base = body_joint(60.0, 58.0) if p.clamp_ground_ko else (
            52.0 + SRC_OFFSET_X + (60.0 - 52.0) * p.body_scale_x + p.body_dx * 0.6,
            58.0 + SRC_OFFSET_Y + p.body_dy * 0.7,
        )
        f_hip_dst = (f_hip_base[0] + p.f_hip_dx, f_hip_base[1] + p.f_hip_dy)
        f_knee_off = self._rot_pt((61.0, 65.0), (60.0, 58.0), p.f_hip_angle)
        f_knee_dst = (f_hip_dst[0] + f_knee_off[0] - 60.0, f_hip_dst[1] + f_knee_off[1] - 58.0)
        f_ankle_off = self._rot_pt((58.0, 74.0), (61.0, 65.0), p.f_hip_angle + p.f_knee_angle)
        f_ankle_dst = (f_knee_dst[0] + f_ankle_off[0] - 61.0, f_knee_dst[1] + f_ankle_off[1] - 65.0)

        far_leg_buf = np.zeros_like(canvas)
        composite_over(
            far_leg_buf,
            warp_part(self.far_thigh, (60.0, 58.0), f_hip_dst, p.f_hip_angle, outline=False),
        )
        composite_over(
            far_leg_buf,
            warp_part(self.far_shin, (61.0, 65.0), f_knee_dst, p.f_hip_angle + p.f_knee_angle, outline=False),
        )
        composite_over(
            far_leg_buf,
            warp_part(self.far_foot, (58.0, 74.0), f_ankle_dst, p.f_foot_angle, outline=False),
        )
        composite_over(canvas, add_pixel_outline(far_leg_buf))

        # 2. Far Arm: Shoulder (73, 51)
        f_arm_dst = body_joint(73.0, 51.0)
        f_arm_layer = warp_part(
            self.far_arm,
            (73.0, 51.0),
            f_arm_dst,
            angle_deg=p.body_angle + p.far_arm_angle,
            scale_x=p.body_scale_x,
            flip_x=p.body_flip_x,
            outline=True,
        )
        composite_over(canvas, f_arm_layer)

        # 3. UNIFIED MAIN BODY BUFFER: [Tail (when not in front) + Torso + Neck Bridge + Upper Head]
        # Outlining them together eliminates any internal seam at the tail base or neck collar!
        main_body_buf = np.zeros_like(canvas)

        # Tail anchored inside hip/pelvis: (39, 50) normally, or (44, 50) when flipped in spin
        tail_anchor_src = (43.0, 50.0) if p.tail_flip_x else (38.0, 50.0)
        tail_root_dst = body_joint(tail_anchor_src[0], tail_anchor_src[1])

        if not p.tail_in_front:
            tail_fill = warp_tail_spline(
                self.tail,
                src_root=(38.0, 50.0),
                dst_root=tail_root_dst,
                base_angle_deg=p.body_angle + p.tail_angle,
                wag_amp=p.tail_wag_amp,
                wag_phase=p.tail_wag_phase,
                curl_lift=p.tail_curl_lift,
                scale_x=p.tail_scale_x,
                flip_x=p.tail_flip_x,
                outline=False,
            )
            composite_over(main_body_buf, tail_fill)

        torso_fill = warp_part(
            self.torso,
            torso_src,
            torso_dst,
            angle_deg=p.body_angle,
            scale_x=p.body_scale_x,
            flip_x=p.body_flip_x,
            outline=False,
        )
        composite_over(main_body_buf, torso_fill)

        # Head pivot at neck top (72, 29)
        head_neck_dst = body_joint(72.0, 29.0)
        head_dst = (head_neck_dst[0] + p.head_dx, head_neck_dst[1] + p.head_dy)
        total_head_angle = p.body_angle + p.head_angle

        # Seamless neck capsule connecting torso collar (70, 34) to head base `head_dst`
        collar_dst = body_joint(70.0, 34.0)
        draw_neck_capsule(main_body_buf, collar_dst, head_dst, radius=4.8 * p.body_scale_x, flip_x=p.body_flip_x)

        # Jaw hinge relative to head (74, 31)
        jaw_off = self._rot_pt(
            (74.0, 31.0), (72.0, 29.0), total_head_angle, sx=p.body_scale_x, flip_x=p.body_flip_x
        )
        jaw_dst = (head_dst[0] + jaw_off[0] - 72.0, head_dst[1] + jaw_off[1] - 29.0)

        if p.jaw_angle > 4.0 and not p.body_flip_x:
            self._draw_inner_mouth(canvas, head_dst, total_head_angle, p.jaw_angle)

        jaw_sign = -1.0 if p.body_flip_x else 1.0
        jaw_layer = warp_part(
            self.lower_jaw,
            (74.0, 31.0),
            jaw_dst,
            angle_deg=total_head_angle + jaw_sign * p.jaw_angle,
            scale_x=p.body_scale_x,
            flip_x=p.body_flip_x,
            outline=True,
        )

        upper_head_src = self.upper_head.copy()
        if p.eye_closed:
            upper_head_src[22:25, 79:82] = OLIVE_DARK
            upper_head_src[23, 79:82] = OUTLINE_RGBA
        head_fill = warp_part(
            upper_head_src,
            (72.0, 29.0),
            head_dst,
            angle_deg=total_head_angle,
            scale_x=p.body_scale_x,
            flip_x=p.body_flip_x,
            outline=False,
        )
        composite_over(main_body_buf, head_fill)

        # Composite lower jaw first, then unified outlined main_body_buf on top so upper teeth overlap lower jaw cleanly
        composite_over(canvas, jaw_layer)
        composite_over(canvas, add_pixel_outline(main_body_buf))

        # 4. Near Leg chain: Hip (45, 50) -> Knee (44, 63) -> Ankle (40, 75)
        n_hip_base = body_joint(45.0, 50.0) if p.clamp_ground_ko else (
            52.0 + SRC_OFFSET_X + (45.0 - 52.0) * p.body_scale_x + p.body_dx * 0.6,
            50.0 + SRC_OFFSET_Y + p.body_dy * 0.75,
        )
        n_hip_dst = (n_hip_base[0] + p.n_hip_dx, n_hip_base[1] + p.n_hip_dy)
        n_knee_off = self._rot_pt((44.0, 63.0), (45.0, 50.0), p.n_hip_angle)
        n_knee_dst = (n_hip_dst[0] + n_knee_off[0] - 45.0, n_hip_dst[1] + n_knee_off[1] - 50.0)
        n_ankle_off = self._rot_pt((40.0, 75.0), (44.0, 63.0), p.n_hip_angle + p.n_knee_angle)
        n_ankle_dst = (n_knee_dst[0] + n_ankle_off[0] - 44.0, n_knee_dst[1] + n_ankle_off[1] - 63.0)

        near_leg_buf = np.zeros_like(canvas)
        composite_over(
            near_leg_buf,
            warp_part(self.near_thigh, (45.0, 50.0), n_hip_dst, p.n_hip_angle, outline=False),
        )
        composite_over(
            near_leg_buf,
            warp_part(self.near_shin, (44.0, 63.0), n_knee_dst, p.n_hip_angle + p.n_knee_angle, outline=False),
        )
        composite_over(
            near_leg_buf,
            warp_part(self.near_foot, (40.0, 75.0), n_ankle_dst, p.n_foot_angle, outline=False),
        )
        composite_over(canvas, add_pixel_outline(near_leg_buf))

        # 5. Near Arm: Shoulder (63, 48)
        n_arm_dst = body_joint(63.0, 48.0)
        n_arm_layer = warp_part(
            self.near_arm,
            (63.0, 48.0),
            n_arm_dst,
            angle_deg=p.body_angle + p.near_arm_angle,
            scale_x=p.body_scale_x,
            flip_x=p.body_flip_x,
            outline=True,
        )
        composite_over(canvas, n_arm_layer)

        # 6. Tail in front (during 90..220 deg spin in attack_heavy!)
        if p.tail_in_front:
            tail_front_layer = warp_tail_spline(
                self.tail,
                src_root=(38.0, 50.0),
                dst_root=tail_root_dst,
                base_angle_deg=p.body_angle + p.tail_angle,
                wag_amp=p.tail_wag_amp,
                wag_phase=p.tail_wag_phase,
                curl_lift=p.tail_curl_lift,
                scale_x=p.tail_scale_x,
                flip_x=p.tail_flip_x,
                outline=True,
            )
            composite_over(canvas, tail_front_layer)

        # 7. Ground-clamp for KO collapse frames so collapsed dinosaur never sinks below y = LOGICAL_ANCHOR_Y (112)
        if p.clamp_ground_ko:
            ys, _ = np.where(canvas[:, :, 3] > 0)
            if len(ys) > 0 and ys.max() > LOGICAL_ANCHOR_Y + 1:
                shift_up = int(ys.max() - (LOGICAL_ANCHOR_Y + 1))
                shifted = np.zeros_like(canvas)
                shifted[: LOGICAL_H - shift_up, :] = canvas[shift_up:, :]
                canvas = shifted

        # 8. Special VFX overlays (bite slash, spin tail shockwave, throat fire charge)
        if p.bite_vfx_phase >= 0:
            self._draw_bite_vfx(canvas, head_dst, p.bite_vfx_phase)
        if p.spin_vfx_phase >= 0:
            self._draw_spin_tail_vfx(canvas, tail_root_dst, p.spin_vfx_phase)
        if p.fire_charge_phase in (0, 1, 6):
            self._draw_fire_charge_vfx(canvas, head_dst, p.fire_charge_phase)

        pil_logical = Image.fromarray(canvas, mode="RGBA")
        pil_canvas = pil_logical.resize((CANVAS_W, CANVAS_H), Image.Resampling.NEAREST)
        out_canvas = np.array(pil_canvas)

        # 9. Composite Owner's 4-frame Fire Blast directly in front of T-rex's open jaws on power_up frames p2..p5
        if p.fire_charge_phase in (2, 3, 4, 5):
            k = p.fire_charge_phase - 2
            crop = self.owner_fire_crops[k]
            x_left = [266, 278, 292, 306][k]
            y_top = 138 - 32
            ch, cw = crop.shape[:2]
            x1 = min(CANVAS_W, x_left + cw)
            y1 = min(CANVAS_H, y_top + ch)
            sub_crop = crop[: y1 - y_top, : x1 - x_left]
            m = sub_crop[:, :, 3] > 0
            out_canvas[y_top:y1, x_left:x1][m] = sub_crop[m]

        return out_canvas

    def _draw_inner_mouth(
        self, canvas: np.ndarray, head_dst: tuple[float, float], head_angle: float, jaw_angle: float
    ) -> None:
        mouth_buf = np.zeros_like(canvas)
        cx = int(round(head_dst[0] + 10))
        cy = int(round(head_dst[1] + 3))
        h_open = max(2, int(round(jaw_angle * 0.22)))
        for dy in range(-1, h_open + 2):
            for dx in range(-4, 11):
                x, y = cx + dx, cy + dy
                if 0 <= x < LOGICAL_W and 0 <= y < LOGICAL_H:
                    if dy >= h_open - 1 and -2 <= dx <= 6:
                        mouth_buf[y, x] = TONGUE_RED
                    else:
                        mouth_buf[y, x] = MOUTH_DARK
        composite_over(canvas, add_pixel_outline(mouth_buf))

    def _draw_bite_vfx(self, canvas: np.ndarray, head_dst: tuple[float, float], phase: int) -> None:
        """Draw ferocious pixel-art Upper & Lower Spectral Fang Jaws clamping down ahead of the snout."""
        vfx = np.zeros_like(canvas)
        mx = int(round(head_dst[0] + 22))
        my = int(round(head_dst[1] + 3))

        if phase == 0:
            # Phase 0 (lunge start): Upper & lower curved golden-white fang blades wide open
            for sign in (-1, 1):
                for s in range(0, 12):
                    bx = mx + s
                    by = int(round(my + sign * (7 - s * 0.35)))
                    for dy in range(-1, 2):
                        if 0 <= bx < LOGICAL_W and 0 <= by + dy < LOGICAL_H:
                            vfx[by + dy, bx] = VFX_WHITE if dy == 0 else VFX_GOLD
                # 3 sharp fang teeth pointing inward on upper & lower arc
                for fx_off in (3, 6, 9):
                    tip_y = int(round(my + sign * (7 - fx_off * 0.35)))
                    for ty in range(1, 4):
                        py = tip_y - sign * ty
                        if 0 <= mx + fx_off < LOGICAL_W and 0 <= py < LOGICAL_H:
                            vfx[py, mx + fx_off] = VFX_WHITE if ty < 3 else VFX_ORANGE
        elif phase == 1:
            # Phase 1 (peak bite impact — hit): Spectral fang jaws snapping shut with central crunch star!
            for t in np.linspace(-1.1, 1.1, 75):
                for dr in range(-3, 4):
                    rad = 11.0 + dr * 0.7
                    x = int(round(mx + 4 + rad * math.cos(t)))
                    y = int(round(my + rad * 1.1 * math.sin(t)))
                    if 0 <= x < LOGICAL_W and 0 <= y < LOGICAL_H:
                        if abs(dr) == 3:
                            vfx[y, x] = VFX_RED
                        elif abs(dr) == 2:
                            vfx[y, x] = VFX_ORANGE
                        elif abs(dr) == 1:
                            vfx[y, x] = VFX_GOLD
                        else:
                            vfx[y, x] = VFX_WHITE
            # Interlocking upper & lower fangs clamping together
            for k, ang in enumerate([-0.8, -0.45, -0.15, 0.15, 0.45, 0.8]):
                for s in range(1, 7):
                    fx = int(round(mx + 4 + (11 - s) * math.cos(ang)))
                    fy = int(round(my + (12 - s * 0.65) * math.sin(ang)))
                    if 0 <= fx < LOGICAL_W and 0 <= fy < LOGICAL_H:
                        vfx[fy, fx] = VFX_WHITE if s < 4 else VFX_GOLD
                        if fx + 1 < LOGICAL_W:
                            vfx[fy, fx + 1] = VFX_GOLD
            # Horizontal bite crunch flash
            for sx in range(-5, 14):
                for sy in range(-2, 3):
                    if abs(sx) + abs(sy) * 3 <= 13:
                        px, py = mx + 5 + sx, my + sy
                        if 0 <= px < LOGICAL_W and 0 <= py < LOGICAL_H:
                            vfx[py, px] = VFX_WHITE if abs(sy) == 0 else VFX_GOLD
        elif phase == 2:
            # Phase 2 (crush shockwave): expanding shockwave arc + flying bite sparks
            for t in np.linspace(-1.0, 1.0, 60):
                for dr in (-1, 0, 1):
                    x = int(round(mx + 6 + (13 + dr) * math.cos(t)))
                    y = int(round(my + (13 + dr) * math.sin(t)))
                    if 0 <= x < LOGICAL_W and 0 <= y < LOGICAL_H:
                        vfx[y, x] = VFX_WHITE if dr == 0 else VFX_ORANGE
            for ang in [-0.7, -0.3, 0.0, 0.3, 0.7]:
                for s in range(9, 17):
                    px = int(round(mx + 6 + s * math.cos(ang)))
                    py = int(round(my + s * math.sin(ang)))
                    if 0 <= px < LOGICAL_W and 0 <= py < LOGICAL_H:
                        vfx[py, px] = VFX_GOLD if s < 14 else VFX_ORANGE
        elif phase == 3:
            # Phase 3 (dissipating impact sparks)
            for ang in [-0.6, -0.2, 0.2, 0.6]:
                for s in range(13, 18):
                    px = int(round(mx + 7 + s * math.cos(ang)))
                    py = int(round(my + s * math.sin(ang)))
                    if 0 <= px < LOGICAL_W and 0 <= py < LOGICAL_H:
                        vfx[py, px] = VFX_ORANGE

        composite_over(canvas, add_pixel_outline(vfx))

    def _draw_spin_tail_vfx(self, canvas: np.ndarray, tail_root: tuple[float, float], phase: int) -> None:
        """Draw sweeping 360-spin kinetic tail-whip arc & impact wave for `attack_heavy`."""
        vfx = np.zeros_like(canvas)
        cx = int(round(tail_root[0]))
        cy = int(round(tail_root[1]))

        if phase == 0:
            for t in np.linspace(2.2, 3.6, 50):
                for dr in (-1, 0):
                    x = int(round(cx + (22 + dr) * math.cos(t)))
                    y = int(round(cy + (10 + dr) * math.sin(t)))
                    if 0 <= x < LOGICAL_W and 0 <= y < LOGICAL_H:
                        vfx[y, x] = VFX_CYAN_WIND
        elif phase == 1:
            for t in np.linspace(-0.75, 0.55, 80):
                for dr in range(-2, 3):
                    rx = 34 + dr
                    ry = 16 + dr * 0.5
                    x = int(round(cx + rx * math.cos(t)))
                    y = int(round(cy + ry * math.sin(t)))
                    if 0 <= x < LOGICAL_W and 0 <= y < LOGICAL_H:
                        vfx[y, x] = VFX_WHITE if dr == 0 else (VFX_LIME_SLASH if abs(dr) == 1 else OLIVE_HIGHLIGHT)
        elif phase == 2:
            for t in np.linspace(-0.95, 0.85, 100):
                thickness = max(1, int(round(4.0 * (1.0 - abs(t) / 1.1))))
                for dr in range(-thickness, thickness + 1):
                    rx = 42 + dr
                    ry = 20 + dr * 0.6
                    x = int(round(cx + rx * math.cos(t)))
                    y = int(round(cy + ry * math.sin(t)))
                    if 0 <= x < LOGICAL_W and 0 <= y < LOGICAL_H:
                        if dr == 0:
                            vfx[y, x] = VFX_WHITE
                        elif abs(dr) == 1:
                            vfx[y, x] = VFX_GOLD
                        elif abs(dr) == 2:
                            vfx[y, x] = VFX_LIME_SLASH
                        else:
                            vfx[y, x] = OLIVE_HIGHLIGHT
            ix, iy = cx + 43, cy
            for ang in [-0.6, -0.25, 0.0, 0.25, 0.6]:
                for s in range(2, 10):
                    px = int(round(ix + s * math.cos(ang)))
                    py = int(round(iy + s * math.sin(ang)))
                    if 0 <= px < LOGICAL_W and 0 <= py < LOGICAL_H:
                        vfx[py, px] = VFX_WHITE if s < 6 else VFX_GOLD
        elif phase == 3:
            for t in np.linspace(-0.3, 1.05, 65):
                for dr in (-1, 0, 1):
                    x = int(round(cx + (38 + dr) * math.cos(t)))
                    y = int(round(cy + (18 + dr) * math.sin(t)))
                    if 0 <= x < LOGICAL_W and 0 <= y < LOGICAL_H:
                        vfx[y, x] = VFX_GOLD if dr == 0 else VFX_LIME_SLASH

        composite_over(canvas, add_pixel_outline(vfx))

    def _draw_fire_charge_vfx(self, canvas: np.ndarray, head_dst: tuple[float, float], phase: int) -> None:
        """Draw throat fire-and-smoke pre-ignition in frames 0-1 and residual snout smoke in frame 6 of `power_up`."""
        vfx = np.zeros_like(canvas)
        mx = int(round(head_dst[0] + 17))
        my = int(round(head_dst[1] + 4))
        smoke_dark = np.array([128, 72, 38, 255], dtype=np.uint8)
        smoke_mid = np.array([196, 122, 54, 255], dtype=np.uint8)
        flame_gold = np.array([252, 212, 92, 255], dtype=np.uint8)
        flame_white = np.array([255, 250, 220, 255], dtype=np.uint8)

        if phase == 0:
            # Frame 0 (prepare 1): T-rex inhales, warm smoke puff + igniting gold ember inside throat
            for dy in range(-2, 3):
                for dx in range(-3, 3):
                    r2 = dx * dx + dy * dy
                    if r2 <= 6:
                        px, py = mx + dx - 1, my + dy
                        if 0 <= px < LOGICAL_W and 0 <= py < LOGICAL_H:
                            vfx[py, px] = flame_white if r2 <= 1 else (flame_gold if r2 <= 3 else smoke_mid)
            for ex, ey in [(mx + 3, my - 2), (mx + 4, my + 1)]:
                if 0 <= ex < LOGICAL_W and 0 <= ey < LOGICAL_H:
                    vfx[ey, ex] = smoke_dark
        elif phase == 1:
            # Frame 1 (prepare 2): Churning compressed fire-and-smoke core filling the wide-open jaws right before spitting Cụm 4!
            for dy in range(-4, 5):
                for dx in range(-4, 6):
                    r2 = dx * dx + dy * dy
                    if r2 <= 15:
                        px, py = mx + dx, my + dy
                        if 0 <= px < LOGICAL_W and 0 <= py < LOGICAL_H:
                            if dx >= 1 and r2 <= 4:
                                vfx[py, px] = flame_white
                            elif r2 <= 8:
                                vfx[py, px] = flame_gold
                            elif r2 <= 12:
                                vfx[py, px] = smoke_mid
                            else:
                                vfx[py, px] = smoke_dark
            for ex, ey in [(mx + 6, my - 3), (mx + 7, my), (mx + 6, my + 3)]:
                if 0 <= ex < LOGICAL_W and 0 <= ey < LOGICAL_H:
                    vfx[ey, ex] = flame_gold
        elif phase == 6:
            # Frame 6 (post-spit recovery): Small dissipating smoke wisp rising from snout
            for ex, ey, col in [
                (mx + 2, my - 1, smoke_mid),
                (mx + 3, my - 2, smoke_mid),
                (mx + 4, my - 3, smoke_dark),
                (mx + 2, my - 3, smoke_dark),
            ]:
                if 0 <= ex < LOGICAL_W and 0 <= ey < LOGICAL_H:
                    vfx[ey, ex] = col

        composite_over(canvas, add_pixel_outline(vfx))


def extract_owner_fire_frames(fire_src_path: Path) -> list[np.ndarray]:
    """Extract the 4 fire blast frames from Owner's `fire_fx_source.png` in RTL order (Cụm 4 -> Cụm 1) flipped to +X.

    Stage 1: Pocket-first chroma key removing the RGB(14, 14, 14) dark background.
    Stage 2: Edge unmixing of dark border spill + 1px dark pixel-art outline so it harmonizes 100% with T-rex on light/dark/checker backgrounds.
    """
    im = Image.open(fire_src_path).convert("RGBA")
    arr = np.array(im)
    bg = np.array([14.0, 14.0, 14.0], dtype=np.float32)
    diff = np.abs(arr[:, :, :3].astype(np.float32) - bg).max(axis=2)
    fg = diff > 32.0

    # Right-to-left order per Owner instruction: Cụm 4 (right) is start -> Cụm 1 (left) is end
    slices_rtl = [(295, 400), (195, 295), (98, 195), (0, 98)]
    crops: list[np.ndarray] = []

    for x0, x1 in slices_rtl:
        sub = arr[:, x0:x1].copy()
        mask = fg[:, x0:x1].copy()
        # Clean isolated 1px specks if any
        eroded_open = ndimage.binary_opening(mask, structure=np.ones((2, 2), dtype=bool))
        mask = mask & ndimage.binary_dilation(eroded_open, structure=np.ones((3, 3), dtype=bool))
        sub[~mask] = [0, 0, 0, 0]
        sub[mask, 3] = 255

        # Stage 2: Unmix dark edge spill on 1px outer ring from interior colors
        eroded = ndimage.binary_erosion(mask, structure=np.ones((3, 3), dtype=bool))
        border = mask & ~eroded
        interior = eroded & (diff[:, x0:x1] > 60.0)
        if interior.any() and border.any():
            _, idx = ndimage.distance_transform_edt(~interior, return_indices=True)
            by, bx = np.where(border)
            sub[by, bx, :3] = sub[idx[0, by, bx], idx[1, by, bx], :3]

        # Flip horizontally so the fire blast shoots from Left (T-rex's jaws) toward Right (+X)
        sub_flip = sub[:, ::-1, :].copy()
        # Add clean 1px pixel-art outline around each cluster so it reads sharply on light/dark/checker backgrounds
        sub_outlined = add_pixel_outline(sub_flip)

        ys, xs = np.where(sub_outlined[:, :, 3] > 0)
        # Keep vertical alignment relative to source centerline y_src = 126
        x_min, x_max = int(xs.min()), int(xs.max())
        # Extract vertical band y = 94..158 (64px tall, centered at y=126)
        band = sub_outlined[94:158, x_min : x_max + 1].copy()
        crops.append(band)

    return crops


def render_fireball_fx_frame(phase_idx: int, owner_fire_crops: list[np.ndarray]) -> np.ndarray:
    """Render one frame (0..3) of the Owner's 4-step fire blast (`fireball_fx`) on the 384x256 canvas."""
    out_canvas = np.zeros((CANVAS_H, CANVAS_W, 4), dtype=np.uint8)
    crop = owner_fire_crops[phase_idx]
    # Step 0 is centered on FX_PIVOT_X = 176 (138..215) for 0px turn-test slide; steps 1..3 advance +12, +26, +40px
    x_left = [138, 150, 164, 178][phase_idx]
    y_top = FX_PIVOT_Y - 32
    ch, cw = crop.shape[:2]
    x1 = min(CANVAS_W, x_left + cw)
    y1 = min(CANVAS_H, y_top + ch)
    sub_crop = crop[: y1 - y_top, : x1 - x_left]
    m = sub_crop[:, :, 3] > 0
    out_canvas[y_top:y1, x_left:x1][m] = sub_crop[m]
    return out_canvas


def build_all_clip_poses() -> dict[str, list[PoseSpec]]:
    """Construct smooth, continuous multi-frame PoseSpecs for all 8 body clips."""
    clips: dict[str, list[PoseSpec]] = {}

    # 1. IDLE (8 frames, loop=True)
    idle_poses: list[PoseSpec] = []
    for i in range(8):
        ph = 2.0 * math.pi * i / 8.0
        s = math.sin(ph)
        c = math.cos(ph)
        idle_poses.append(
            PoseSpec(
                body_dx=0.5 * s,
                body_dy=1.2 * s,
                body_angle=1.8 * s,
                head_dx=0.4 * c,
                head_dy=0.6 * s,
                head_angle=-2.2 * c,
                jaw_angle=2.5 * (0.5 + 0.5 * s),
                near_arm_angle=5.0 * s,
                far_arm_angle=-4.0 * c,
                tail_wag_amp=2.6,
                tail_wag_phase=ph,
                n_hip_dy=-0.2 * s,
                f_hip_dy=-0.2 * s,
            )
        )
    clips["idle"] = idle_poses

    # 2. WALK (10 frames, loop=True)
    walk_poses: list[PoseSpec] = []
    for i in range(10):
        ph = 2.0 * math.pi * i / 10.0

        def leg_kinematics(leg_ph: float) -> tuple[float, float, float, float, float]:
            stride = math.sin(leg_ph)
            lift = max(0.0, math.cos(leg_ph))
            hip_ang = -20.0 * stride
            knee_ang = 18.0 * lift + 6.0 * max(0.0, -stride)
            foot_ang = -12.0 * lift + 5.0 * stride
            h_dx = 3.2 * stride
            h_dy = -3.2 * lift
            return hip_ang, knee_ang, foot_ang, h_dx, h_dy

        nh, nk, nf, ndx, ndy = leg_kinematics(ph)
        fh, fk, ff, fdx, fdy = leg_kinematics(ph + math.pi)
        bob = math.sin(2.0 * ph)
        walk_poses.append(
            PoseSpec(
                body_dx=1.0 * math.cos(ph),
                body_dy=1.6 * bob,
                body_angle=4.0 + 2.5 * bob,
                head_dx=0.8 * math.sin(2.0 * ph - 0.6),
                head_dy=0.8 * math.cos(2.0 * ph),
                head_angle=-2.5 * bob,
                jaw_angle=2.0 + 1.5 * (0.5 + 0.5 * bob),
                near_arm_angle=10.0 * math.sin(ph),
                far_arm_angle=-10.0 * math.sin(ph),
                tail_angle=-2.0,
                tail_wag_amp=3.2,
                tail_wag_phase=ph,
                n_hip_angle=nh,
                n_knee_angle=nk,
                n_foot_angle=nf,
                n_hip_dx=ndx,
                n_hip_dy=ndy - 1.2 * bob,
                f_hip_angle=fh,
                f_knee_angle=fk,
                f_foot_angle=ff,
                f_hip_dx=fdx,
                f_hip_dy=fdy - 1.2 * bob,
            )
        )
    clips["walk"] = walk_poses

    # 3. RUN (8 frames, loop=True)
    run_poses: list[PoseSpec] = []
    for i in range(8):
        ph = 2.0 * math.pi * i / 8.0

        def run_leg(leg_ph: float) -> tuple[float, float, float, float, float]:
            stride = math.sin(leg_ph)
            lift = max(0.0, math.cos(leg_ph))
            hip_ang = -30.0 * stride
            knee_ang = 26.0 * lift + 10.0 * max(0.0, -stride)
            foot_ang = -18.0 * lift + 10.0 * stride
            h_dx = 5.0 * stride
            h_dy = -4.5 * lift
            return hip_ang, knee_ang, foot_ang, h_dx, h_dy

        nh, nk, nf, ndx, ndy = run_leg(ph)
        fh, fk, ff, fdx, fdy = run_leg(ph + math.pi)
        bob = math.sin(2.0 * ph)
        run_poses.append(
            PoseSpec(
                body_dx=2.5 + 1.2 * math.cos(ph),
                body_dy=1.5 + 2.2 * bob,
                body_angle=12.0 + 3.0 * bob,
                head_dx=1.2 + 0.8 * math.sin(2.0 * ph),
                head_dy=0.8 * math.cos(2.0 * ph),
                head_angle=-7.0 - 2.5 * bob,
                jaw_angle=9.0 + 3.0 * bob,
                near_arm_angle=16.0 + 12.0 * math.sin(ph),
                far_arm_angle=16.0 - 12.0 * math.sin(ph),
                tail_angle=-8.0,
                tail_wag_amp=2.4,
                tail_wag_phase=2.0 * ph,
                tail_curl_lift=2.5,
                n_hip_angle=nh,
                n_knee_angle=nk,
                n_foot_angle=nf,
                n_hip_dx=ndx,
                n_hip_dy=ndy - 1.5 * bob,
                f_hip_angle=fh,
                f_knee_angle=fk,
                f_foot_angle=ff,
                f_hip_dx=fdx,
                f_hip_dy=fdy - 1.5 * bob,
            )
        )
    clips["run"] = run_poses

    # 4. ATTACK_LIGHT (8 frames, oneshot): Ferocious Bite with Fang Slash VFX (seamless neck!)
    clips["attack_light"] = [
        PoseSpec(
            body_dx=-3.0, body_dy=1.0, body_angle=-4.0,
            head_dx=-1.5, head_dy=-1.0, head_angle=-6.0, jaw_angle=14.0,
            near_arm_angle=-12.0, far_arm_angle=-10.0,
            tail_angle=4.0, tail_curl_lift=2.0,
            n_hip_angle=8.0, n_hip_dx=-1.5, f_hip_angle=-6.0, f_hip_dx=1.5,
        ),
        PoseSpec(
            body_dx=-5.5, body_dy=2.0, body_angle=-8.0,
            head_dx=-2.5, head_dy=-1.5, head_angle=-11.0, jaw_angle=28.0,
            near_arm_angle=-20.0, far_arm_angle=-16.0,
            tail_angle=7.0, tail_curl_lift=3.5,
            n_hip_angle=14.0, n_hip_dx=-2.5, f_hip_angle=-10.0, f_hip_dx=2.0,
        ),
        PoseSpec(
            body_dx=7.0, body_dy=1.0, body_angle=10.0,
            head_dx=2.5, head_dy=0.5, head_angle=-4.0, jaw_angle=26.0,
            near_arm_angle=18.0, far_arm_angle=15.0,
            tail_angle=-6.0, tail_curl_lift=2.0,
            n_hip_angle=-14.0, n_hip_dx=2.0, f_hip_angle=12.0, f_hip_dx=-2.0,
            bite_vfx_phase=0,
        ),
        PoseSpec(
            body_dx=12.5, body_dy=1.5, body_angle=14.0,
            head_dx=3.5, head_dy=1.0, head_angle=3.0, jaw_angle=6.0,
            near_arm_angle=25.0, far_arm_angle=22.0,
            tail_angle=-9.0, tail_curl_lift=3.5,
            n_hip_angle=-20.0, n_hip_dx=3.0, f_hip_angle=16.0, f_hip_dx=-2.5,
            bite_vfx_phase=1,
        ),
        PoseSpec(
            body_dx=11.0, body_dy=2.0, body_angle=12.0,
            head_dx=3.0, head_dy=1.2, head_angle=5.0, jaw_angle=0.0,
            near_arm_angle=22.0, far_arm_angle=18.0,
            tail_angle=-8.0, tail_curl_lift=3.0,
            n_hip_angle=-18.0, n_hip_dx=2.5, f_hip_angle=14.0, f_hip_dx=-2.0,
            bite_vfx_phase=2,
        ),
        PoseSpec(
            body_dx=6.5, body_dy=1.2, body_angle=7.0,
            head_dx=2.0, head_dy=0.6, head_angle=2.0, jaw_angle=4.0,
            near_arm_angle=12.0, far_arm_angle=10.0,
            tail_angle=-4.0, tail_curl_lift=1.5,
            n_hip_angle=-10.0, n_hip_dx=1.5, f_hip_angle=8.0, f_hip_dx=-1.0,
            bite_vfx_phase=3,
        ),
        PoseSpec(
            body_dx=3.0, body_dy=0.5, body_angle=3.0,
            head_dx=1.0, head_dy=0.2, head_angle=1.0, jaw_angle=2.0,
            near_arm_angle=5.0, far_arm_angle=4.0,
            tail_angle=-1.5, tail_curl_lift=0.5,
            n_hip_angle=-4.0, n_hip_dx=0.5, f_hip_angle=3.0, f_hip_dx=-0.5,
        ),
        PoseSpec(
            body_dx=0.5, body_dy=0.0, body_angle=0.5,
            head_dx=0.0, head_dy=0.0, head_angle=0.0, jaw_angle=1.0,
        ),
    ]

    # 5. ATTACK_HEAVY (10 frames, oneshot): 360-Degree Spin Tail Sweep Attack (tail anchored to pelvis!)
    clips["attack_heavy"] = [
        PoseSpec(
            body_dx=-2.0, body_dy=1.5, body_angle=-5.0,
            head_dx=-1.0, head_dy=-0.8, head_angle=-6.0, jaw_angle=8.0,
            tail_angle=8.0, tail_curl_lift=3.0,
            n_hip_angle=10.0, n_knee_angle=6.0, f_hip_angle=-8.0,
        ),
        PoseSpec(
            body_dx=-4.0, body_dy=2.5, body_angle=-8.0, body_scale_x=0.86,
            head_dx=-1.5, head_dy=-1.0, head_angle=-10.0, jaw_angle=14.0,
            tail_angle=14.0, tail_curl_lift=5.0, tail_scale_x=0.9,
            n_hip_angle=16.0, n_knee_angle=10.0, n_hip_dx=-2.0, f_hip_angle=-12.0, f_hip_dx=2.0,
            spin_vfx_phase=0,
        ),
        PoseSpec(
            body_dx=-2.0, body_dy=1.5, body_angle=-6.0, body_scale_x=0.74, body_flip_x=True,
            head_dx=-1.0, head_dy=0.5, head_angle=6.0, jaw_angle=12.0,
            tail_in_front=True, tail_flip_x=True, tail_scale_x=0.92,
            tail_angle=-6.0, tail_curl_lift=2.0,
            n_hip_angle=-10.0, n_hip_dx=2.0, f_hip_angle=10.0, f_hip_dx=-2.0,
            spin_vfx_phase=1,
        ),
        PoseSpec(
            body_dx=0.0, body_dy=1.0, body_angle=-10.0, body_scale_x=0.92, body_flip_x=True,
            head_dx=-1.5, head_dy=1.0, head_angle=10.0, jaw_angle=16.0,
            tail_in_front=True, tail_flip_x=True, tail_scale_x=1.18,
            tail_angle=-2.0, tail_wag_amp=2.0, tail_wag_phase=0.5,
            n_hip_angle=-16.0, n_hip_dx=3.0, f_hip_angle=14.0, f_hip_dx=-3.0,
            spin_vfx_phase=1,
        ),
        PoseSpec(
            body_dx=2.0, body_dy=1.5, body_angle=-12.0, body_scale_x=1.0, body_flip_x=True,
            head_dx=-2.0, head_dy=1.5, head_angle=12.0, jaw_angle=20.0,
            tail_in_front=True, tail_flip_x=True, tail_scale_x=1.28,
            tail_angle=2.0, tail_wag_amp=3.0, tail_wag_phase=1.2,
            n_hip_angle=-20.0, n_hip_dx=4.0, f_hip_angle=18.0, f_hip_dx=-3.0,
            spin_vfx_phase=2,
        ),
        PoseSpec(
            body_dx=1.0, body_dy=2.0, body_angle=-8.0, body_scale_x=0.88, body_flip_x=True,
            head_dx=-1.5, head_dy=1.0, head_angle=8.0, jaw_angle=12.0,
            tail_in_front=True, tail_flip_x=True, tail_scale_x=1.14,
            tail_angle=8.0, tail_wag_amp=2.5, tail_wag_phase=2.0,
            n_hip_angle=-12.0, n_hip_dx=2.0, f_hip_angle=12.0, f_hip_dx=-2.0,
            spin_vfx_phase=3,
        ),
        PoseSpec(
            body_dx=2.0, body_dy=2.0, body_angle=8.0, body_scale_x=0.76, body_flip_x=False,
            head_dx=-1.0, head_dy=0.5, head_angle=-4.0, jaw_angle=8.0,
            tail_in_front=False, tail_flip_x=False, tail_scale_x=0.85,
            tail_angle=-8.0, tail_curl_lift=3.0,
            n_hip_angle=12.0, n_hip_dx=-2.0, f_hip_angle=-12.0, f_hip_dx=2.0,
        ),
        PoseSpec(
            body_dx=4.0, body_dy=1.5, body_angle=6.0, body_scale_x=0.92,
            head_dx=1.0, head_dy=0.4, head_angle=-2.0, jaw_angle=5.0,
            tail_angle=-5.0, tail_wag_amp=3.0, tail_wag_phase=2.5,
            n_hip_angle=-8.0, n_hip_dx=1.5, f_hip_angle=6.0, f_hip_dx=-1.5,
        ),
        PoseSpec(
            body_dx=2.0, body_dy=0.8, body_angle=3.0, body_scale_x=0.98,
            head_dx=0.5, head_dy=0.2, head_angle=-1.0, jaw_angle=3.0,
            tail_angle=-2.0, tail_wag_amp=2.0, tail_wag_phase=3.0,
            n_hip_angle=-3.0, f_hip_angle=2.0,
        ),
        PoseSpec(
            body_dx=0.5, body_dy=0.0, body_angle=0.5,
            head_dx=0.0, head_dy=0.0, head_angle=0.0, jaw_angle=1.5,
            tail_wag_amp=1.5, tail_wag_phase=0.0,
        ),
    ]

    # 6. POWER_UP (9 frames, oneshot): Fireball Spit Attack (seamless neck!)
    clips["power_up"] = [
        PoseSpec(
            body_dx=-2.5, body_dy=-0.5, body_angle=-5.0,
            head_dx=-1.2, head_dy=-1.0, head_angle=-8.0, jaw_angle=14.0,
            near_arm_angle=-10.0, far_arm_angle=-8.0,
            tail_angle=5.0, tail_curl_lift=2.0,
            n_hip_angle=6.0, f_hip_angle=-6.0,
            fire_charge_phase=0,
        ),
        PoseSpec(
            body_dx=-5.0, body_dy=-1.0, body_angle=-9.0,
            head_dx=-2.0, head_dy=-1.8, head_angle=-14.0, jaw_angle=24.0,
            near_arm_angle=-18.0, far_arm_angle=-15.0,
            tail_angle=9.0, tail_curl_lift=3.5,
            n_hip_angle=12.0, n_hip_dx=-1.5, f_hip_angle=-10.0, f_hip_dx=1.5,
            fire_charge_phase=1,
        ),
        PoseSpec(
            body_dx=6.5, body_dy=1.0, body_angle=9.0,
            head_dx=2.5, head_dy=0.6, head_angle=2.0, jaw_angle=28.0,
            near_arm_angle=20.0, far_arm_angle=18.0,
            tail_angle=-6.0, tail_curl_lift=2.5,
            n_hip_angle=-14.0, n_hip_dx=2.0, f_hip_angle=10.0, f_hip_dx=-1.5,
            fire_charge_phase=2,
        ),
        PoseSpec(
            body_dx=5.2, body_dy=1.2, body_angle=7.5,
            head_dx=2.0, head_dy=0.5, head_angle=1.0, jaw_angle=25.0,
            near_arm_angle=16.0, far_arm_angle=14.0,
            tail_angle=-5.0, tail_curl_lift=2.0,
            n_hip_angle=-11.0, n_hip_dx=1.5, f_hip_angle=8.0, f_hip_dx=-1.0,
            fire_charge_phase=3,
        ),
        PoseSpec(
            body_dx=4.0, body_dy=1.0, body_angle=6.0,
            head_dx=1.5, head_dy=0.4, head_angle=0.0, jaw_angle=20.0,
            near_arm_angle=12.0, far_arm_angle=10.0,
            tail_angle=-4.0, tail_curl_lift=1.5,
            n_hip_angle=-8.0, n_hip_dx=1.0, f_hip_angle=6.0, f_hip_dx=-1.0,
            fire_charge_phase=4,
        ),
        PoseSpec(
            body_dx=2.8, body_dy=0.8, body_angle=4.5,
            head_dx=1.2, head_dy=0.3, head_angle=0.0, jaw_angle=16.0,
            near_arm_angle=8.0, far_arm_angle=7.0,
            tail_angle=-3.0, tail_curl_lift=1.0,
            n_hip_angle=-6.0, f_hip_angle=4.0,
            fire_charge_phase=5,
        ),
        PoseSpec(
            body_dx=1.8, body_dy=0.5, body_angle=3.0,
            head_dx=0.8, head_dy=0.2, head_angle=0.0, jaw_angle=8.0,
            near_arm_angle=5.0, far_arm_angle=4.0,
            tail_angle=-1.5,
            n_hip_angle=-3.0, f_hip_angle=2.0,
            fire_charge_phase=6,
        ),
        PoseSpec(
            body_dx=0.8, body_dy=0.2, body_angle=1.5,
            head_dx=0.4, head_dy=0.1, head_angle=0.0, jaw_angle=4.0,
            near_arm_angle=2.0, far_arm_angle=2.0,
        ),
        PoseSpec(
            body_dx=0.2, body_dy=0.0, body_angle=0.5,
            head_dx=0.0, head_dy=0.0, head_angle=0.0, jaw_angle=1.5,
        ),
    ]

    # 7. HIT (6 frames, oneshot)
    clips["hit"] = [
        PoseSpec(
            body_dx=-3.5, body_dy=1.0, body_angle=-7.0,
            head_dx=-1.5, head_dy=-1.0, head_angle=-12.0, jaw_angle=16.0,
            near_arm_angle=-18.0, far_arm_angle=-15.0,
            tail_angle=8.0, tail_curl_lift=2.5,
            n_hip_angle=10.0, n_hip_dx=-1.5, f_hip_angle=-6.0,
        ),
        PoseSpec(
            body_dx=-6.5, body_dy=2.0, body_angle=-12.0,
            head_dx=-2.5, head_dy=-1.8, head_angle=-18.0, jaw_angle=22.0,
            near_arm_angle=-26.0, far_arm_angle=-22.0,
            tail_angle=13.0, tail_curl_lift=4.0,
            n_hip_angle=16.0, n_hip_dx=-3.0, f_hip_angle=-10.0, f_hip_dx=1.5,
        ),
        PoseSpec(
            body_dx=-5.5, body_dy=2.2, body_angle=-10.0,
            head_dx=-2.0, head_dy=-1.4, head_angle=-14.0, jaw_angle=18.0,
            near_arm_angle=-20.0, far_arm_angle=-18.0,
            tail_angle=10.0, tail_curl_lift=3.0,
            n_hip_angle=14.0, n_hip_dx=-2.5, f_hip_angle=-8.0, f_hip_dx=1.0,
        ),
        PoseSpec(
            body_dx=-3.5, body_dy=1.4, body_angle=-6.0,
            head_dx=-1.2, head_dy=-0.8, head_angle=-8.0, jaw_angle=11.0,
            near_arm_angle=-12.0, far_arm_angle=-10.0,
            tail_angle=6.0, tail_curl_lift=1.8,
            n_hip_angle=8.0, n_hip_dx=-1.5, f_hip_angle=-4.0,
        ),
        PoseSpec(
            body_dx=-1.5, body_dy=0.6, body_angle=-2.5,
            head_dx=-0.5, head_dy=-0.3, head_angle=-3.0, jaw_angle=5.0,
            near_arm_angle=-5.0, far_arm_angle=-4.0,
            tail_angle=2.5, tail_curl_lift=0.8,
            n_hip_angle=3.0, f_hip_angle=-2.0,
        ),
        PoseSpec(
            body_dx=-0.3, body_dy=0.0, body_angle=-0.5,
            head_dx=0.0, head_dy=0.0, head_angle=0.0, jaw_angle=1.5,
        ),
    ]

    # 8. KO (8 frames, oneshot): Ground-clamped collapse so dinosaur rests cleanly on ground line y=224!
    clips["ko"] = [
        PoseSpec(
            body_dx=-4.0, body_dy=1.5, body_angle=-10.0,
            head_dx=-2.0, head_dy=-1.5, head_angle=-16.0, jaw_angle=20.0,
            near_arm_angle=-22.0, far_arm_angle=-18.0,
            tail_angle=10.0, tail_curl_lift=3.0,
            n_hip_angle=12.0, n_hip_dx=-2.0, f_hip_angle=-8.0,
        ),
        PoseSpec(
            body_dx=-2.5, body_dy=5.5, body_angle=5.0,
            head_dx=-0.5, head_dy=0.5, head_angle=-4.0, jaw_angle=18.0,
            near_arm_angle=10.0, far_arm_angle=12.0,
            tail_angle=-2.0, tail_curl_lift=1.5,
            n_hip_angle=-18.0, n_knee_angle=26.0, n_hip_dy=-2.0,
            f_hip_angle=-14.0, f_knee_angle=22.0, f_hip_dy=-2.0,
            clamp_ground_ko=True,
        ),
        PoseSpec(
            body_dx=-1.0, body_dy=10.5, body_angle=16.0,
            head_dx=1.0, head_dy=1.0, head_angle=4.0, jaw_angle=14.0,
            near_arm_angle=22.0, far_arm_angle=24.0,
            tail_angle=-8.0,
            n_hip_angle=-36.0, n_knee_angle=35.0, n_foot_angle=12.0, n_hip_dy=1.0,
            f_hip_angle=-30.0, f_knee_angle=30.0, f_foot_angle=10.0, f_hip_dy=1.0,
            clamp_ground_ko=True,
        ),
        PoseSpec(
            body_dx=0.5, body_dy=15.0, body_angle=25.0,
            head_dx=1.5, head_dy=1.5, head_angle=6.0, jaw_angle=10.0, eye_closed=True,
            near_arm_angle=30.0, far_arm_angle=32.0,
            tail_angle=-14.0,
            n_hip_angle=-54.0, n_knee_angle=38.0, n_foot_angle=22.0, n_hip_dy=3.0,
            f_hip_angle=-48.0, f_knee_angle=34.0, f_foot_angle=18.0, f_hip_dy=2.0,
            clamp_ground_ko=True,
        ),
        PoseSpec(
            body_dx=2.0, body_dy=19.5, body_angle=32.0,
            head_dx=2.0, head_dy=2.0, head_angle=4.0, jaw_angle=6.0, eye_closed=True,
            near_arm_angle=36.0, far_arm_angle=38.0,
            tail_angle=-20.0,
            n_hip_angle=-68.0, n_knee_angle=32.0, n_foot_angle=32.0, n_hip_dy=4.0,
            f_hip_angle=-62.0, f_knee_angle=28.0, f_foot_angle=28.0, f_hip_dy=3.0,
            clamp_ground_ko=True,
        ),
        PoseSpec(
            body_dx=2.0, body_dy=18.0, body_angle=29.0,
            head_dx=1.8, head_dy=1.8, head_angle=3.0, jaw_angle=8.0, eye_closed=True,
            near_arm_angle=33.0, far_arm_angle=35.0,
            tail_angle=-17.0,
            n_hip_angle=-64.0, n_knee_angle=34.0, n_foot_angle=28.0, n_hip_dy=3.5,
            f_hip_angle=-58.0, f_knee_angle=30.0, f_foot_angle=25.0, f_hip_dy=2.5,
            clamp_ground_ko=True,
        ),
        PoseSpec(
            body_dx=2.5, body_dy=20.0, body_angle=33.0,
            head_dx=2.0, head_dy=2.0, head_angle=3.0, jaw_angle=4.0, eye_closed=True,
            near_arm_angle=38.0, far_arm_angle=40.0,
            tail_angle=-21.0,
            n_hip_angle=-70.0, n_knee_angle=30.0, n_foot_angle=34.0, n_hip_dy=4.0,
            f_hip_angle=-64.0, f_knee_angle=26.0, f_foot_angle=30.0, f_hip_dy=3.0,
            clamp_ground_ko=True,
        ),
        PoseSpec(
            body_dx=2.5, body_dy=20.5, body_angle=34.0,
            head_dx=2.2, head_dy=2.2, head_angle=2.0, jaw_angle=2.0, eye_closed=True,
            near_arm_angle=40.0, far_arm_angle=42.0,
            tail_angle=-22.0,
            n_hip_angle=-72.0, n_knee_angle=28.0, n_foot_angle=36.0, n_hip_dy=4.2,
            f_hip_angle=-66.0, f_knee_angle=24.0, f_foot_angle=32.0, f_hip_dy=3.2,
            clamp_ground_ko=True,
        ),
    ]

    return clips


def main() -> None:
    stage_dir = WORK_DIR / "stage_v2"
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    frames_dir = stage_dir / "raw_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    builder = TRexBuilder(APPROVED_MASTER)
    clip_poses = build_all_clip_poses()

    clip_order = [
        "idle",
        "walk",
        "run",
        "attack_light",
        "attack_heavy",
        "power_up",
        "hit",
        "ko",
    ]

    frame_entries: list[dict[str, str]] = []
    clip_frame_names: dict[str, list[str]] = {}

    for cname in clip_order:
        poses = clip_poses[cname]
        c_names: list[str] = []
        for idx, pose in enumerate(poses):
            fname = f"{cname}_{idx:02d}"
            ffile = f"raw_frames/{fname}.png"
            rgba = builder.render_pose(pose)
            Image.fromarray(rgba, mode="RGBA").save(stage_dir / ffile)
            frame_entries.append({"name": fname, "file": ffile})
            c_names.append(fname)
        clip_frame_names[cname] = c_names

    fx_names: list[str] = []
    for idx in range(4):
        fname = f"fireball_fx_{idx:02d}"
        ffile = f"raw_frames/{fname}.png"
        rgba = render_fireball_fx_frame(idx, builder.owner_fire_crops)
        Image.fromarray(rgba, mode="RGBA").save(stage_dir / ffile)
        frame_entries.append({"name": fname, "file": ffile})
        fx_names.append(fname)
    clip_frame_names["fireball_fx"] = fx_names

    manifest = {
        "schema": "generate2dsprite.animation_clips.v2",
        "art_source": "host_image",
        "pixel_art": True,
        "sampling": "nearest",
        "body_height_px": 132,
        "anchor_px": [ANCHOR_X, ANCHOR_Y],
        "shadow": {"rx": 36, "ry": 9, "opacity": 0.35},
        "frames": frame_entries,
        "states": {
            "idle": "idle",
            "moving": "walk",
            "running": "run",
            "attack_light": "attack_light",
            "attack_heavy": "attack_heavy",
            "power_up": "power_up",
            "hit": "hit",
            "ko": "ko",
        },
        "clips": {
            "idle": {
                "role": "player",
                "frames": clip_frame_names["idle"],
                "ticks": [7, 7, 7, 7, 7, 7, 7, 7],
                "loop_policy": "cycle",
            },
            "walk": {
                "role": "player",
                "frames": clip_frame_names["walk"],
                "ticks": [6, 6, 6, 6, 6, 6, 6, 6, 6, 6],
                "loop_policy": "cycle",
                "stride_px_per_frame": 5.5,
                "events": [
                    {"at": 2, "name": "step_r"},
                    {"at": 7, "name": "step_l"},
                ],
            },
            "run": {
                "role": "player",
                "frames": clip_frame_names["run"],
                "ticks": [5, 5, 5, 5, 5, 5, 5, 5],
                "loop_policy": "cycle",
                "stride_px_per_frame": 9.0,
                "events": [
                    {"at": 1, "name": "step_r"},
                    {"at": 5, "name": "step_l"},
                ],
            },
            "attack_light": {
                "role": "player",
                "frames": clip_frame_names["attack_light"],
                "ticks": [5, 5, 4, 4, 4, 5, 5, 6],
                "loop_policy": "oneshot",
                "hitstop_ticks": 4,
                "keys": {"wind_start": 0, "wind_peak": 1, "strike": 3, "recover": 5, "end": 7},
                "events": [
                    {"at": 1, "name": "tell"},
                    {"at": 3, "name": "hit"},
                    {"at": 4, "name": "active_end"},
                    {"at": 7, "name": "end"},
                ],
            },
            "attack_heavy": {
                "role": "player",
                "frames": clip_frame_names["attack_heavy"],
                "ticks": [5, 5, 4, 4, 4, 4, 4, 5, 5, 6],
                "loop_policy": "oneshot",
                "hitstop_ticks": 6,
                "keys": {"wind_start": 0, "wind_peak": 1, "strike": 4, "recover": 6, "end": 9},
                "events": [
                    {"at": 1, "name": "tell"},
                    {"at": 4, "name": "hit"},
                    {"at": 5, "name": "active_end"},
                    {"at": 9, "name": "end"},
                ],
            },
            "power_up": {
                "role": "player",
                "frames": clip_frame_names["power_up"],
                "ticks": [5, 5, 5, 5, 5, 5, 5, 5, 6],
                "loop_policy": "oneshot",
                "hitstop_ticks": 4,
                "keys": {"wind_start": 0, "wind_peak": 1, "strike": 2, "recover": 6, "end": 8},
                "events": [
                    {"at": 1, "name": "tell"},
                    {"at": 2, "name": "hit", "data": {"projectile": "fireball_fx"}},
                    {"at": 8, "name": "end"},
                ],
            },
            "hit": {
                "role": "player",
                "frames": clip_frame_names["hit"],
                "ticks": [4, 4, 5, 5, 5, 5],
                "loop_policy": "oneshot",
                "events": [
                    {"at": 0, "name": "in"},
                    {"at": 5, "name": "end"},
                ],
            },
            "ko": {
                "role": "player",
                "frames": clip_frame_names["ko"],
                "ticks": [5, 5, 5, 5, 5, 6, 6, 15],
                "loop_policy": "oneshot",
                "events": [
                    {"at": 0, "name": "in"},
                    {"at": 4, "name": "impact"},
                    {"at": 7, "name": "hold"},
                ],
            },
            "fireball_fx": {
                "role": "fx",
                "frames": clip_frame_names["fireball_fx"],
                "ticks": [5, 5, 5, 5],
                "loop_policy": "oneshot",
            },
        },
    }

    manifest_path = stage_dir / "clips_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    built_clips_dir = stage_dir / "clips_built"
    build_script = REPO_ROOT / ".agent" / "skills" / "generate2dsprite" / "scripts" / "build_animation_clips.py"
    res = subprocess.run(
        [
            sys.executable,
            str(build_script),
            "--manifest",
            str(manifest_path),
            "--output-dir",
            str(built_clips_dir),
            "--near-duplicate-mae",
            "0.25",
            "--strict",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    print("build_animation_clips stdout:", res.stdout.strip())
    if res.returncode != 0:
        print("build_animation_clips stderr:", res.stderr.strip(), file=sys.stderr)
        sys.exit(res.returncode)


if __name__ == "__main__":
    main()
