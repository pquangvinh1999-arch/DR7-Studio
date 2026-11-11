#!/usr/bin/env python3
"""DR7-Studio — Pteranodon (pteranodon) Pixel-Art Atlas & Animation Pipeline (v2 — Biomechanical Wingbeat & Owner Sonic Wave FX).

Builds the complete 8-clip (7 body + 1 independent 7-phase sonic wave FX)
60Hz Nearest pixel-art bundle from:
- Owner-approved master: `work/characters/pteranodon/approved-master/approved-original.png`
- Owner-supplied sonic wave sheet: `work/characters/pteranodon/approved-master/sonic_fx_source.png`

Key Owner Specifications:
1. Full biomechanical 2D wing-flapping (`idle`, `walk`, `run`, `hit`) with full vertical excursion:
   High Upstroke V above back -> Horizontal Forward Camber Sweep -> Deep Power Downstroke plunging below chest/belly -> Folded Upstroke Recovery, paired with phase-locked torso lift/bob.
2. `attack_light`: Forward beak lunge & snap strike (`dùng mỏ tấn công về trước`) with 100% seamless muscular neck bridge (`draw_neck_capsule`) and piercing beak/fang shockwave VFX.
3. No `attack_heavy` (excluded specifically for `pteranodon` per Owner instruction).
4. `power_up` + `sonic_screech_fx`: Uses the 7-cluster cyan sonic wave sheet (`sonic_fx_source.png`) emitted from the open beak toward +X.
5. `ko`: Preserves the Owner-approved aerial fall and ground collapse sequence.
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
WORK_DIR = REPO_ROOT / "work" / "characters" / "pteranodon"
APPROVED_MASTER = WORK_DIR / "approved-master" / "approved-original.png"
SONIC_FX_SOURCE = WORK_DIR / "approved-master" / "sonic_fx_source.png"
STAGE_DIR = WORK_DIR / "stage"

# Logical canvas is 192x128 -> 2x Nearest integer upscale -> 384x256 gameplay canvas
LOGICAL_W, LOGICAL_H = 192, 128
CANVAS_W, CANVAS_H = 384, 256
LOGICAL_ANCHOR_X, LOGICAL_ANCHOR_Y = 88, 100
ANCHOR_X, ANCHOR_Y = 176.0, 200.0  # [176, 200] on 384x256 canvas
FX_PIVOT_X, FX_PIVOT_Y = 176, 128  # Centered on ANCHOR_X for zero turn-test slide
MOUTH_X, MOUTH_Y = 278, 128        # Projectile alignment origin on 384x256 canvas
SONIC_X_LEFTS = [278, 292, 306, 320, 334, 348, 360]

# Offset mapping 100x100 logical master onto 192x128 logical canvas
OFF_X, OFF_Y = 38, 18

OUTLINE_RGBA = np.array([14, 12, 16, 255], dtype=np.uint8)
CHARCOAL_SHADOW = np.array([56, 46, 52, 255], dtype=np.uint8)
CHARCOAL_DARK = np.array([86, 72, 80, 255], dtype=np.uint8)
CHARCOAL_MID = np.array([123, 105, 115, 255], dtype=np.uint8)
CHARCOAL_LIGHT = np.array([163, 141, 151, 255], dtype=np.uint8)
WING_RED_SHADOW = np.array([108, 20, 28, 255], dtype=np.uint8)
WING_RED_DARK = np.array([158, 32, 40, 255], dtype=np.uint8)
WING_RED_MID = np.array([200, 48, 56, 255], dtype=np.uint8)
WING_RED_LIGHT = np.array([236, 78, 84, 255], dtype=np.uint8)
BEAK_DARK = np.array([92, 74, 56, 255], dtype=np.uint8)
BEAK_MID = np.array([138, 114, 84, 255], dtype=np.uint8)
BEAK_LIGHT = np.array([184, 156, 118, 255], dtype=np.uint8)
TOOTH_WHITE = np.array([242, 238, 220, 255], dtype=np.uint8)
TALON_SLATE = np.array([134, 124, 138, 255], dtype=np.uint8)
TALON_LIGHT = np.array([182, 172, 188, 255], dtype=np.uint8)

# 16-color high-contrast pixel art palette calibrated to T-rex Sobel Acutance benchmark (201.3)
PALETTE_16 = np.array([
    [14, 12, 16],     # 0: outline
    [56, 46, 52],     # 1: charcoal deep shadow
    [86, 72, 80],     # 2: charcoal dark muscle
    [123, 105, 115],  # 3: charcoal mid muscle
    [163, 141, 151],  # 4: charcoal light ridge highlight
    [108, 20, 28],    # 5: wing burgundy deep shadow
    [158, 32, 40],    # 6: wing burgundy dark
    [200, 48, 56],    # 7: wing crimson mid
    [236, 78, 84],    # 8: wing crimson highlight
    [92, 74, 56],     # 9: beak dark
    [138, 114, 84],   # 10: beak mid
    [184, 156, 118],  # 11: beak highlight
    [242, 238, 220],  # 12: tooth / bone white
    [248, 196, 18],   # 13: eye glowing yellow
    [214, 32, 28],    # 14: eye iris crimson
    [176, 166, 182],  # 15: talon / crest sharp highlight
], dtype=np.uint8)

# Ferocious Dark-Crimson / Burgundy ("Đỏ Đô") VFX Palette matching Pteranodon's predatory theme
VFX_WHITE = np.array([252, 218, 214, 255], dtype=np.uint8)
VFX_CRIMSON_BRIGHT = np.array([232, 58, 66, 255], dtype=np.uint8)
VFX_BURGUNDY_MID = np.array([176, 26, 38, 255], dtype=np.uint8)
VFX_BURGUNDY_DEEP = np.array([112, 14, 24, 255], dtype=np.uint8)
VFX_GOLD = np.array([250, 192, 36, 255], dtype=np.uint8)
VFX_CRIMSON = np.array([204, 32, 42, 255], dtype=np.uint8)


def extract_logical_100(master_path: Path) -> np.ndarray:
    """Extract clean 100x100 logical pixel grid from 1024x1024 master calibrated to T-rex sharpness standard."""
    im = Image.open(master_path).convert("RGB")
    arr = np.array(im)
    n = 100
    raw = np.zeros((n, n, 4), dtype=np.uint8)
    for gy in range(n):
        cy = int((gy + 0.5) * 1024 / n)
        for gx in range(n):
            cx = int((gx + 0.5) * 1024 / n)
            patch = arr[max(0, cy - 2) : min(1024, cy + 3), max(0, cx - 2) : min(1024, cx + 3)]
            med = np.median(patch.reshape(-1, 3), axis=0).astype(np.uint8)
            r, g, b = int(med[0]), int(med[1]), int(med[2])
            if (r > 165 and b > 165 and g < 65) or (r - g > 65 and b - g > 65):
                raw[gy, gx] = [0, 0, 0, 0]
            else:
                raw[gy, gx] = [r, g, b, 255]

    vis = raw[:, :, 3] > 0
    struct4 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)
    eroded = ndimage.binary_erosion(vis, structure=struct4, border_value=0)
    sil_border = vis & (~eroded)

    yy, xx = np.mgrid[0:n, 0:n]
    top_y = np.full(n, 999, dtype=int)
    for x_col in range(n):
        ys_col = np.where(vis[:, x_col])[0]
        if len(ys_col) > 0:
            top_y[x_col] = int(ys_col.min())

    # Anatomical mask for the muscular arm, wrist, 4 hand claws, and thin 2px leading wing bone
    wrist_hand_claws = vis & (xx >= 37) & (xx <= 49) & (yy >= 17) & (yy <= 28)
    forearm_muscle = vis & (xx >= 39) & (xx <= 44) & (yy >= 27) & (yy <= 45)
    humerus_muscle = (
        vis
        & (yy >= 44)
        & (yy <= 54)
        & (xx >= np.rint(40 + (yy - 44) * 0.25).astype(int))
        & (xx <= np.rint(45 + (yy - 44) * 0.45).astype(int))
    )
    leading_wing_bone = vis & (xx <= 37) & (yy <= top_y[xx] + 1)
    arm_structure = wrist_hand_claws | forearm_muscle | humerus_muscle | leading_wing_bone

    # Full inner wing membrane (`mặt trong cánh`) across all compartments below the 2px leading bone & left of arm
    inner_wing_membrane = (
        vis
        & (~arm_structure)
        & (yy <= 56)
        & (xx <= np.where(yy <= 43, 38, np.rint(38 + (yy - 43) * 0.42).astype(int)))
    )

    # Crisp 1px anatomical crease outline separating the muscular arm from the adjacent wing membrane
    arm_crease_outline = (
        vis
        & (~sil_border)
        & (
            ((xx == 39) & (yy >= 29) & (yy <= 44))
            | ((xx == 44) & (yy >= 28) & (yy <= 43))
            | ((yy >= 44) & (yy <= 52) & (xx == np.rint(40 + (yy - 44) * 0.25).astype(int)))
            | ((yy >= 44) & (yy <= 51) & (xx == np.rint(45 + (yy - 44) * 0.45).astype(int)))
        )
    )

    logical = np.zeros_like(raw)
    for y in range(n):
        for x in range(n):
            if not vis[y, x]:
                continue
            r, g, b = int(raw[y, x, 0]), int(raw[y, x, 1]), int(raw[y, x, 2])
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if sil_border[y, x] or arm_crease_outline[y, x]:
                logical[y, x] = OUTLINE_RGBA
            elif 72 <= x <= 76 and 42 <= y <= 46 and r > g + 22:
                logical[y, x] = [214, 32, 28, 255] if r < 145 else [248, 196, 18, 255]
            elif arm_structure[y, x]:
                # Muscular arm, forearm, wrist, and 4 sharp claws — strictly Charcoal skin & Slate claws (zero red bleed!)
                if y <= 25 and (lum >= 48 or b >= r - 12):
                    logical[y, x] = [176, 166, 182, 255] if lum >= 70 else CHARCOAL_LIGHT
                elif lum < 25:
                    logical[y, x] = CHARCOAL_SHADOW
                elif lum < 42:
                    logical[y, x] = CHARCOAL_DARK
                elif lum < 64:
                    logical[y, x] = CHARCOAL_MID
                else:
                    logical[y, x] = CHARCOAL_LIGHT
            elif inner_wing_membrane[y, x]:
                # All compartments of inner wing membrane (`mặt trong cánh`) are Red (zero charcoal skin pockets inside wing!)
                if r < 48:
                    logical[y, x] = WING_RED_SHADOW
                elif r < 72:
                    logical[y, x] = WING_RED_DARK
                elif r < 92:
                    logical[y, x] = WING_RED_MID
                else:
                    logical[y, x] = WING_RED_LIGHT
            elif x >= 70 and 43 <= y <= 60:
                # Serrated beak & fangs
                if lum > 96:
                    logical[y, x] = TOOTH_WHITE
                elif lum > 62:
                    logical[y, x] = BEAK_LIGHT
                elif lum > 34:
                    logical[y, x] = BEAK_MID
                elif lum > 14:
                    logical[y, x] = BEAK_DARK
                else:
                    logical[y, x] = OUTLINE_RGBA
            else:
                # Charcoal body, crest, far wing, and talons (no interior black speckles -> smooth rotation!)
                if lum < 25:
                    logical[y, x] = CHARCOAL_SHADOW
                elif lum < 41:
                    logical[y, x] = CHARCOAL_DARK
                elif lum < 63:
                    logical[y, x] = CHARCOAL_MID
                elif lum < 86:
                    logical[y, x] = CHARCOAL_LIGHT
                else:
                    logical[y, x] = [176, 166, 182, 255]

    # Despeckle isolated 1px interior color islands on the 100x100 logical master for smoother rotation
    despeckled = logical.copy()
    for y in range(1, n - 1):
        for x in range(1, n - 1):
            if not vis[y, x] or sil_border[y, x] or arm_crease_outline[y, x]:
                continue
            if 71 <= x <= 95 and 41 <= y <= 58:
                continue  # Preserve crisp eye & serrated teeth pixels
            c_cur = tuple(int(v) for v in logical[y, x])
            nb_cols: list[tuple[int, int, int, int]] = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if vis[ny, nx] and not sil_border[ny, nx] and not arm_crease_outline[ny, nx]:
                        nb_cols.append(tuple(int(v) for v in logical[ny, nx]))
            if len(nb_cols) >= 5 and nb_cols.count(c_cur) == 0:
                most_common = max(set(nb_cols), key=nb_cols.count)
                despeckled[y, x] = most_common

    return despeckled


def add_pixel_outline(layer: np.ndarray, outline_col: np.ndarray = OUTLINE_RGBA) -> np.ndarray:
    """Add a clean 1px 4-connected dark pixel-art outline around the interior fill of `layer`."""
    res = layer.copy()
    op = res[:, :, 3] > 0
    if not op.any():
        return res
    struct4 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)
    eroded = ndimage.binary_erosion(op, structure=struct4, border_value=0)
    border = op & (~eroded)
    res[border] = outline_col
    return res


def add_external_pixel_outline(layer: np.ndarray, outline_col: np.ndarray = OUTLINE_RGBA) -> np.ndarray:
    """Add a 1px 4-connected external dark outline around thin FX rings without eating interior cyan pixels."""
    res = layer.copy()
    op = res[:, :, 3] > 0
    if not op.any():
        return res
    struct4 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)
    dilated = ndimage.binary_dilation(op, structure=struct4)
    edge = dilated & (~op)
    res[edge] = outline_col
    return res


def composite_over(dst: np.ndarray, src: np.ndarray) -> None:
    """Composite opaque pixels of `src` onto `dst` in-place."""
    m = src[:, :, 3] > 0
    dst[m] = src[m]


def clean_part_with_caps(
    src: np.ndarray,
    mask: np.ndarray,
    caps: list[tuple[int, int, int, np.ndarray]] | None = None,
    strip_outline: bool = True,
) -> np.ndarray:
    """Extract anatomical component, apply joint caps, filter to single connected component (`components == 1`), and strip border outline."""
    yy, xx = np.mgrid[0 : src.shape[0], 0 : src.shape[1]]
    out = np.zeros_like(src)
    out[mask] = src[mask]
    if caps:
        for cx, cy, rad, col in caps:
            disk = ((xx - cx) ** 2 + (yy - cy) ** 2) <= rad ** 2
            fill = disk & (out[:, :, 3] == 0)
            out[fill] = col
    labeled, n_comp = ndimage.label(out[:, :, 3] > 0)
    if n_comp > 1:
        counts = np.bincount(labeled.ravel())
        counts[0] = 0
        keep = labeled == int(np.argmax(counts))
        out[~keep] = 0
    if strip_outline:
        op_p = out[:, :, 3] > 0
        eroded = ndimage.binary_erosion(op_p, structure=np.ones((3, 3), dtype=bool))
        border = op_p & (~eroded)
        is_dark = (out[:, :, 0] < 25) & (out[:, :, 1] < 25) & (out[:, :, 2] < 25)
        to_fill = border & is_dark
        interior = op_p & (~is_dark)
        if interior.any() and to_fill.any():
            _, idx = ndimage.distance_transform_edt(~interior, return_indices=True)
            fy, fx = np.where(to_fill)
            out[fy, fx] = out[idx[0, fy, fx], idx[1, fy, fx]]
    return out


def extract_anatomical_parts(logical: np.ndarray) -> dict[str, np.ndarray]:
    """Segment Pteranodon into 6 true anatomical parts with `components == 1` guarantee and zero dorsal/wing cross-contamination."""
    op = logical[:, :, 3] > 0
    yy, xx = np.mgrid[0:100, 0:100]
    r, g, b = logical[:, :, 0].astype(int), logical[:, :, 1].astype(int), logical[:, :, 2].astype(int)
    is_red_wing = op & (r >= 95) & (r > g + 35) & (r > b + 30) & (yy <= 60)

    # 1. Cranial crest + skull + upper toothed beak + cheek/jaw-hinge root (`upper_head`)
    # Strictly follows the bony crest ridge (xx=53..72) and includes the cheek root (xx=64..70, yy=48..55) for Spec 4
    crest_mask = (
        op
        & (xx >= 53)
        & (xx <= 72)
        & (yy >= 31 + (xx - 53) * 0.35)
        & (yy <= 34.5 + (xx - 53) * 0.58)
    )
    mouth_split_y = 49.5 + (xx - 73) * 0.30
    upper_skull_beak = op & (xx >= 65) & (yy >= 38) & (yy <= mouth_split_y)
    cheek_throat_root = op & (xx >= 64) & (xx <= 70) & (yy >= 48) & (yy <= 55)
    m_upper_head = crest_mask | upper_skull_beak | cheek_throat_root

    # 2. Hinged lower toothed jaw (`lower_jaw`)
    m_lower_jaw = op & (~upper_skull_beak) & (xx >= 70) & (yy > mouth_split_y - 0.5) & (yy <= 62)

    # 3. Far wing (`far_wing`) — includes the upper blade (yy <= 42), the sub-crest root (xx=48..64, yy <= 51),
    # and reconstructs the crest-occluded wing chord so there is zero gap at the back/crest junction (Spec 1)
    # and a full anatomical wing chord when flapping down (Spec 3)!
    far_wing_chord_fill = (
        (xx >= 50)
        & (xx <= 82)
        & (yy >= np.rint(33 + (xx - 50) * 0.25).astype(int))
        & (yy <= np.rint(50 - np.maximum(0, xx - 61) * 1.15).astype(int))
    )
    m_far_wing = (
        (
            op
            & (~m_upper_head)
            & (~m_lower_jaw)
            & (xx >= 48)
            & (
                (yy <= 42)
                | ((xx <= 64) & (yy <= 51) & (~(is_red_wing & (xx <= 50))))
            )
        )
        | far_wing_chord_fill
    )
    far_wing_src_logical = logical.copy()
    occluded_by_crest = far_wing_chord_fill & ((~op) | m_upper_head)
    far_wing_src_logical[occluded_by_crest] = CHARCOAL_MID
    far_wing_lower_shade = occluded_by_crest & (yy >= np.rint(44 - np.maximum(0, xx - 61) * 0.85).astype(int))
    far_wing_src_logical[far_wing_lower_shade] = CHARCOAL_DARK

    # 4. Near wing (`near_wing`: muscular charcoal arm/elbow, 4 wrist claws, and wing membrane)
    m_near_wing = (
        op
        & (~m_upper_head)
        & (~m_lower_jaw)
        & (~m_far_wing)
        & (yy <= 60)
        & (
            (is_red_wing & ((yy <= 52) | (xx <= 46)))
            | (xx <= 40)
            | ((xx <= 51) & (yy <= 52))
        )
    )

    # 5. Hind legs & tail (`legs_tail`)
    m_legs_tail = op & (~m_near_wing) & (xx <= 47) & ((yy >= 64) | ((xx <= 38) & (yy >= 60)))

    # 6. Torso (`torso`: compact anatomical ribcage, pelvis, and lower neck root; strictly below dorsal line yy >= 50)
    m_torso_raw = (
        op
        & (~m_upper_head)
        & (~m_lower_jaw)
        & (~m_far_wing)
        & (~m_near_wing)
        & (~m_legs_tail)
    )
    flank_under_wing = op & (xx >= 42) & (xx <= 55) & (yy >= 50) & (yy <= 58)
    m_torso = m_torso_raw | flank_under_wing

    torso_src_logical = logical.copy()
    torso_red = m_torso & is_red_wing
    torso_src_logical[torso_red] = CHARCOAL_DARK

    parts = {
        "far_wing": clean_part_with_caps(
            far_wing_src_logical,
            m_far_wing,
            caps=[
                (65, 35, 3, CHARCOAL_DARK),
                (62, 37, 3, CHARCOAL_DARK),
                (59, 39, 3, CHARCOAL_DARK),
                (56, 42, 3, CHARCOAL_DARK),
                (54, 49, 3, CHARCOAL_DARK),
            ],
        ),
        "upper_head": clean_part_with_caps(
            logical,
            m_upper_head,
            caps=[
                (67, 48, 2, CHARCOAL_MID),
                (68, 52, 3, CHARCOAL_DARK),
            ],
        ),
        "lower_jaw": clean_part_with_caps(
            logical,
            m_lower_jaw,
            caps=[
                (70, 52, 3, BEAK_DARK),
                (72, 51, 2, BEAK_DARK),
            ],
        ),
        "near_wing": clean_part_with_caps(
            logical,
            m_near_wing,
            caps=[(46, 52, 2, CHARCOAL_DARK)],
        ),
        "torso": clean_part_with_caps(
            torso_src_logical,
            m_torso,
            caps=[
                (63, 50, 2, CHARCOAL_MID),
                (52, 51, 2, CHARCOAL_DARK),
                (45, 54, 2, CHARCOAL_DARK),
            ],
        ),
        "legs_tail": clean_part_with_caps(
            logical,
            m_legs_tail,
            caps=[(41, 63, 2, CHARCOAL_DARK)],
        ),
    }

    # Verify single connected component per anatomical part (LRN-016 standard)
    for name, p in parts.items():
        _, n_c = ndimage.label(p[:, :, 3] > 0)
        assert n_c == 1, f"Part {name} has {n_c} components instead of 1!"

    return parts


def build_wing_surface_variants(
    near_wing_ventral: np.ndarray,
    far_wing_dorsal: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Construct biologically accurate dorsal (`mặt trên` = Charcoal skin) and ventral (`mặt dưới` = Red membrane) wing surfaces (Spec 3).

    - `near_wing_ventral` (upstroke): upper fold (`mặt trên`) + arm/claws are Charcoal skin; lower/inner membrane (`mặt dưới`) is Red.
    - `near_wing_dorsal` (downstroke): wing folds down showing its upper skin surface (`mặt trên`) -> 100% Charcoal skin matching the body!
    - `far_wing_dorsal` (upstroke): opposite wing (`cánh đối diện`) raised -> upper/leading fold (`mặt trên`) is Charcoal skin, while lower/inner underside membrane (`mặt dưới`) is Red membrane!
    - `far_wing_blade` (KO): blade-only wing for ground collapse.
    - `far_wing_ventral` (downstroke): opposite wing flapping down behind chest -> underside membrane (`mặt dưới`) is Red with Charcoal leading bone.
    """
    # 1. `near_wing_dorsal` (downstroke): convert red ventral membrane pixels to 4-tone Charcoal skin matching the body
    near_dorsal = near_wing_ventral.copy()
    for y in range(near_dorsal.shape[0]):
        for x in range(near_dorsal.shape[1]):
            if near_dorsal[y, x, 3] == 0:
                continue
            r, g, b = int(near_dorsal[y, x, 0]), int(near_dorsal[y, x, 1]), int(near_dorsal[y, x, 2])
            if r >= 95 and r > g + 35:
                if r < 130:
                    near_dorsal[y, x] = CHARCOAL_SHADOW
                elif r < 180:
                    near_dorsal[y, x] = CHARCOAL_DARK
                elif r < 220:
                    near_dorsal[y, x] = CHARCOAL_MID
                else:
                    near_dorsal[y, x] = CHARCOAL_LIGHT

    # 2. `far_wing_dorsal` (upstroke): keep `mặt trên` (upper/leading half + 3 claws + shoulder root) Charcoal skin,
    # and color `mặt dưới` (inner/lower underside membrane below the wing bone ridge) Red (`WING_RED_*`)!
    far_skin_source = far_wing_dorsal.copy()
    op_f = far_wing_dorsal[:, :, 3] > 0
    for x in range(far_wing_dorsal.shape[1]):
        ys = np.where(op_f[:, x])[0]
        if len(ys) == 0:
            continue
        # Ridge separating upper skin (`mặt trên`) from lower underside membrane (`mặt dưới`), preserving the 3 bony claws (x >= 74, y <= 34)
        ridge_y = int(round(41.0 - max(0, x - 52) * 0.55))
        for y in ys:
            if x >= 74 and y <= 34:
                continue  # Preserve 3 sharp bony claws on far wing in Charcoal/Slate
            if x >= 53 and ridge_y < y <= 47:
                r, g, b = int(far_wing_dorsal[y, x, 0]), int(far_wing_dorsal[y, x, 1]), int(far_wing_dorsal[y, x, 2])
                if r < 25 and g < 25 and b < 25:
                    continue
                if y == ridge_y + 1:
                    far_wing_dorsal[y, x] = OUTLINE_RGBA
                elif r < 70:
                    far_wing_dorsal[y, x] = WING_RED_SHADOW
                elif r < 105:
                    far_wing_dorsal[y, x] = WING_RED_DARK
                elif r < 145:
                    far_wing_dorsal[y, x] = WING_RED_MID
                else:
                    far_wing_dorsal[y, x] = WING_RED_LIGHT

    # 3. `far_wing_blade` (for KO collapse)
    far_blade = far_wing_dorsal.copy()
    far_blade[41:, :, :] = 0

    # Keep the approved KO blade intact; protect the source forearm on flight poses.
    # Elbow (59,46) -> wrist (68,31), measured on the 100x100 source grid.
    yy, xx = np.mgrid[0:100, 0:100]
    forearm_x = 59.0 + (46.0 - yy) * 0.60
    forearm = op_f & (yy >= 32) & (yy <= 48) & (abs(xx - forearm_x) <= 2.5)
    # Owner v8: the elbow/shoulder root left of the forearm is also skin.
    shoulder_root = op_f & (xx <= 60) & (yy >= 39)
    protected_skin = forearm | shoulder_root
    far_wing_dorsal[protected_skin] = far_skin_source[protected_skin]

    # 4. `far_wing_ventral`: true anatomical horizontal mirror of `near_wing_ventral` for symmetric downstroke!
    # Shows full inner red membrane (`mặt trong cánh`) + charcoal leading bone/claws, with pivot at (54.0, 55.0).
    far_ventral = near_wing_ventral[:, ::-1, :].copy()

    return near_dorsal, far_blade, far_ventral


def smooth_warped_layer(layer: np.ndarray) -> np.ndarray:
    """Eliminate 1px sawtooth staircasing and isolated rotation speckles on a warped logical layer before outlining."""
    res = layer.copy()
    op = res[:, :, 3] > 0
    if not op.any():
        return res

    h, w = op.shape
    # 1. Fill 1px transparent sawtooth notches (transparent pixels with >= 3 4-connected opaque neighbors)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not op[y, x]:
                nbs = []
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    if op[y + dy, x + dx]:
                        nbs.append(res[y + dy, x + dx])
                if len(nbs) >= 3:
                    res[y, x] = nbs[0]

    op = res[:, :, 3] > 0
    # 2. Remove 1px isolated burrs (opaque pixels with <= 1 4-connected neighbor and <= 2 8-connected neighbors)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if op[y, x]:
                n4 = int(op[y - 1, x]) + int(op[y + 1, x]) + int(op[y, x - 1]) + int(op[y, x + 1])
                if n4 <= 1:
                    n8 = int(op[y - 1 : y + 2, x - 1 : x + 2].sum()) - 1
                    if n8 <= 2:
                        res[y, x] = [0, 0, 0, 0]

    op = res[:, :, 3] > 0
    # 3. Smooth isolated 1px interior color islands caused by oblique rotation sampling
    smoothed = res.copy()
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not op[y, x]:
                continue
            c_cur = tuple(int(v) for v in res[y, x])
            # Preserve intentional dark crease outlines, glowing eye, and white teeth
            if c_cur[0] < 25 or c_cur[0] > 210:
                continue
            nb_cols: list[tuple[int, int, int, int]] = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if op[ny, nx]:
                        nc = tuple(int(v) for v in res[ny, nx])
                        if 25 <= nc[0] <= 238:
                            nb_cols.append(nc)
            if len(nb_cols) >= 5 and nb_cols.count(c_cur) <= 1:
                most_common = max(set(nb_cols), key=nb_cols.count)
                if nb_cols.count(most_common) >= 4:
                    smoothed[y, x] = most_common

    return smoothed


def extract_owner_sonic_frames(sonic_src_path: Path) -> list[np.ndarray]:
    """Extract all 7 sonic wave clusters (Cụm 1 -> Cụm 7) from Owner's `sonic_fx_source.png` (308x89, bg RGB(32,32,32)).

    - Stage 1: Pocket-first chroma key removing RGB(32, 32, 32) dark background (`enclosed_key_pockets == 0`).
    - Stage 2: Edge unmixing + Recolor to ferocious Dark-Crimson / Burgundy ("Đỏ Đô") matching Pteranodon + horizontal flip (`+X`) + 1px external dark pixel-art outline.
    """
    im = Image.open(sonic_src_path).convert("RGBA")
    arr = np.array(im)
    bg = np.array([32.0, 32.0, 32.0], dtype=np.float32)
    diff = np.abs(arr[:, :, :3].astype(np.float32) - bg).max(axis=2)
    fg = diff > 22.0

    closed_x = ndimage.binary_closing(fg.any(axis=0), structure=np.ones(12))
    labeled_x, n_x = ndimage.label(closed_x)
    assert n_x == 7, f"Expected 7 sonic clusters in {sonic_src_path}, found {n_x}"

    crops: list[np.ndarray] = []
    for i in range(1, n_x + 1):
        xs = np.where(labeled_x == i)[0]
        x0, x1 = max(0, int(xs[0]) - 2), min(arr.shape[1], int(xs[-1]) + 3)
        sub = arr[:, x0:x1].copy()
        mask = fg[:, x0:x1].copy()
        sub[~mask] = [0, 0, 0, 0]
        sub[mask, 3] = 255

        # Stage 2: Unmix dark edge spill on 1px outer ring from bright interior
        eroded = ndimage.binary_erosion(mask, structure=np.ones((3, 3), dtype=bool))
        border = mask & (~eroded)
        interior = eroded & (diff[:, x0:x1] > 65.0)
        if interior.any() and border.any():
            _, idx = ndimage.distance_transform_edt(~interior, return_indices=True)
            by, bx = np.where(border)
            sub[by, bx, :3] = sub[idx[0, by, bx], idx[1, by, bx], :3]

        # Recolor cyan sonic wave to ferocious Dark-Crimson / Burgundy ("Đỏ Đô") preserving all concentric wave rings
        vy, vx = np.where(mask)
        for py, px in zip(vy, vx):
            r_c, g_c, b_c = int(sub[py, px, 0]), int(sub[py, px, 1]), int(sub[py, px, 2])
            intensity = 0.20 * r_c + 0.45 * g_c + 0.35 * b_c
            if intensity >= 205:
                sub[py, px] = VFX_WHITE
            elif intensity >= 165:
                sub[py, px] = VFX_CRIMSON_BRIGHT
            elif intensity >= 115:
                sub[py, px] = VFX_BURGUNDY_MID
            else:
                sub[py, px] = VFX_BURGUNDY_DEEP

        # Flip horizontally (`[::-1]`) so the sonic rings expand and bow forward toward Right (+X)
        sub_flip = sub[4:76, ::-1, :].copy()  # 72px tall band centered on y=40
        sub_outlined = add_external_pixel_outline(sub_flip)

        ys, xs_c = np.where(sub_outlined[:, :, 3] > 0)
        xmin, xmax = int(xs_c.min()), int(xs_c.max())
        crops.append(sub_outlined[:, xmin : xmax + 1].copy())

    return crops


def draw_neck_capsule(
    buf: np.ndarray,
    p0: tuple[float, float],
    p1: tuple[float, float],
    radius: float = 4.2,
) -> None:
    """Fill a seamless muscular charcoal neck bridge between torso collar `p0` and head base `p1`."""
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
                rel_y = y - py
                if rel_y < -1.0:
                    buf[y, x] = CHARCOAL_LIGHT
                elif rel_y > 1.2:
                    buf[y, x] = CHARCOAL_DARK
                else:
                    buf[y, x] = CHARCOAL_MID


def warp_part(
    part: np.ndarray,
    src_pivot: tuple[float, float],
    dst_pivot: tuple[float, float],
    angle_deg: float = 0.0,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    outline: bool = False,
) -> np.ndarray:
    """Inverse-map `part` (100x100) onto 192x128 logical canvas around pivots."""
    out = np.zeros((LOGICAL_H, LOGICAL_W, 4), dtype=np.uint8)
    ys, xs = np.where(part[:, :, 3] > 0)
    if len(xs) == 0:
        return out

    rad = math.radians(angle_deg)
    c, s = math.cos(rad), math.sin(rad)
    spx, spy = src_pivot
    dpx, dpy = dst_pivot

    gy, gx = np.mgrid[0:LOGICAL_H, 0:LOGICAL_W]
    dx = gx.astype(float) - dpx
    dy = gy.astype(float) - dpy

    ux = (c * dx + s * dy) / max(0.05, scale_x)
    uy = (-s * dx + c * dy) / max(0.05, scale_y)

    src_x = np.rint(ux + spx).astype(int)
    src_y = np.rint(uy + spy).astype(int)

    valid = (src_x >= 0) & (src_x < part.shape[1]) & (src_y >= 0) & (src_y < part.shape[0])
    vy, vx = np.where(valid)
    samp = part[src_y[vy, vx], src_x[vy, vx]]
    vis = samp[:, 3] > 0
    out[vy[vis], vx[vis]] = samp[vis]
    if outline:
        out = add_pixel_outline(out)
    return out


def warp_wing_flap(
    wing_part: np.ndarray,
    src_piv: tuple[float, float],
    dst_piv: tuple[float, float],
    flap_elev: float,
    span_scale: float = 1.0,
    camber_px: float = 0.0,
    shear_x_by_y: float = 0.0,
    rot_deg: float = 0.0,
    is_far: bool = False,
    outline: bool = True,
) -> np.ndarray:
    """Biomechanical 2D wingbeat deformer preserving horizontal scanline width of the wing membrane:
    - `flap_elev`: +1.10 (high upstroke V) -> 0.0 (horizontal sweep) -> -1.10 (deep power downstroke below belly).
    - `shear_x_by_y`: horizontal forward sweep proportional to vertical distance below shoulder.
    - `camber_px`: non-linear aerodynamic wingtip bend/whip along span u.
    """
    out = np.zeros((LOGICAL_H, LOGICAL_W, 4), dtype=np.uint8)
    spx, spy = src_piv
    dpx, dpy = dst_piv
    gy, gx = np.mgrid[0:LOGICAL_H, 0:LOGICAL_W]
    dx = gx.astype(float) - dpx
    dy = gy.astype(float) - dpy

    rad = math.radians(rot_deg)
    c, s = math.cos(rad), math.sin(rad)
    rx = c * dx + s * dy
    ry = -s * dx + c * dy

    sx_unedited = rx - shear_x_by_y * (ry / 30.0)
    sx_rel = sx_unedited / max(0.25, span_scale)

    span_len = 36.0 if is_far else 42.0
    u = np.clip((sx_rel if is_far else -sx_rel) / span_len, 0.0, 1.25)

    eff_elev = flap_elev
    if abs(eff_elev) < 0.36:
        eff_elev = 0.36 if eff_elev >= 0 else -0.36

    sy_rel = (ry - camber_px * (u ** 1.5)) / eff_elev

    src_x = np.rint(spx + sx_rel).astype(int)
    src_y = np.rint(spy + sy_rel).astype(int)

    # On downstroke (eff_elev < 0), prevent lower flank attachment (src_y > spy + 1) from flipping above the back line
    if eff_elev < 0:
        valid_y = (src_y >= 0) & (src_y <= int(spy + 1))
    else:
        valid_y = (src_y >= 0) & (src_y < 100)

    valid = (src_x >= 0) & (src_x < 100) & valid_y
    vy, vx = np.where(valid)
    samp = wing_part[src_y[vy, vx], src_x[vy, vx]]
    vis = samp[:, 3] > 0
    out[vy[vis], vx[vis]] = samp[vis]
    if outline:
        out = add_pixel_outline(out)
    return out


@dataclass
class PteranodonPose:
    body_dx: float = 0.0
    body_dy: float = 0.0
    body_angle: float = 0.0
    head_dx: float = 0.0
    head_dy: float = 0.0
    head_angle: float = 0.0
    jaw_angle: float = 1.5
    eye_closed: bool = False
    flap_elev: float = 1.0
    span_scale: float = 1.0
    camber_px: float = 0.0
    shear_x_by_y: float = 0.0
    wing_rot: float = 0.0
    legs_angle: float = 0.0
    legs_dx: float = 0.0
    legs_dy: float = 0.0
    beak_vfx_phase: int = -1
    sonic_phase: int = -99
    clamp_ground_ko: bool = False


class PteranodonBuilder:
    def __init__(self, master_path: Path, sonic_src_path: Path) -> None:
        self.logical = extract_logical_100(master_path)
        self.parts = extract_anatomical_parts(self.logical)
        self.near_wing_ventral = self.parts["near_wing"]
        self.far_wing_dorsal = self.parts["far_wing"]
        (
            self.near_wing_dorsal,
            self.far_wing_blade,
            self.far_wing_ventral,
        ) = build_wing_surface_variants(self.near_wing_ventral, self.far_wing_dorsal)
        self.sonic_crops = extract_owner_sonic_frames(sonic_src_path)

    @staticmethod
    def _rot_pt(pt: tuple[float, float], piv: tuple[float, float], deg: float) -> tuple[float, float]:
        dx = pt[0] - piv[0]
        dy = pt[1] - piv[1]
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        return (piv[0] + c * dx - s * dy, piv[1] + s * dx + c * dy)

    def render_pose(self, p: PteranodonPose) -> np.ndarray:
        """Render a PteranodonPose onto a 384x256 RGBA gameplay canvas (2x Nearest from 192x128 logical)."""
        canvas = np.zeros((LOGICAL_H, LOGICAL_W, 4), dtype=np.uint8)

        torso_src = (48.0, 55.0)
        torso_dst = (48.0 + OFF_X + p.body_dx, 55.0 + OFF_Y + p.body_dy)

        def body_joint(sx: float, sy: float) -> tuple[float, float]:
            pt = self._rot_pt((sx, sy), torso_src, p.body_angle)
            return (
                torso_dst[0] + (pt[0] - torso_src[0]),
                torso_dst[1] + (pt[1] - torso_src[1]),
            )

        # 1. Far Wing (`far_wing`) behind body:
        # - Upstroke (`flap_elev >= 0`): shows dorsal Charcoal skin (`self.far_wing_dorsal`) with full root into back (Spec 1).
        # - Downstroke (`flap_elev < 0`): shows ventral Red membrane (`self.far_wing_ventral`) sweeping below chest (Spec 3).
        if p.wing_rot <= -20.0:
            w_far = warp_wing_flap(
                self.far_wing_blade,
                (54.0, 41.0),
                body_joint(52.0, 51.0),
                flap_elev=max(0.36, p.flap_elev * 0.70),
                span_scale=p.span_scale * 0.85,
                camber_px=p.camber_px * 0.5,
                shear_x_by_y=-p.shear_x_by_y * 0.3,
                rot_deg=p.body_angle + p.wing_rot * 0.35,
                is_far=True,
                outline=False,
            )
        elif p.flap_elev >= 0.0:
            w_far = warp_wing_flap(
                self.far_wing_dorsal,
                (54.0, 49.0),
                body_joint(54.0, 49.0),
                flap_elev=max(0.48, p.flap_elev * 0.96),
                span_scale=p.span_scale * 0.96,
                camber_px=p.camber_px * 0.7,
                shear_x_by_y=-p.shear_x_by_y * 0.3,
                rot_deg=p.body_angle - p.wing_rot * 0.35,
                is_far=True,
                outline=False,
            )
        else:
            w_far = warp_wing_flap(
                self.far_wing_ventral,
                (54.0, 55.0),
                body_joint(52.0, 53.0),
                flap_elev=abs(p.flap_elev) * 0.96,
                span_scale=p.span_scale * 0.84,
                camber_px=p.camber_px,
                shear_x_by_y=-p.shear_x_by_y * 0.60,
                # Rotate the intact underside toward +X instead of inverting Y:
                # the forearm leads toward the beak, membrane trails toward feet.
                rot_deg=-(p.body_angle + p.wing_rot) + 90.0 * min(1.0, abs(p.flap_elev)),
                is_far=True,
                outline=False,
            )

        lbl_far, n_far = ndimage.label(w_far[:, :, 3] > 0)
        if n_far > 1:
            cnts = np.bincount(lbl_far.ravel())
            cnts[0] = 0
            w_far[lbl_far != int(np.argmax(cnts))] = 0
        w_far = smooth_warped_layer(w_far)
        composite_over(canvas, add_pixel_outline(w_far))

        # 2. Hind Legs & Tail (`legs_tail`)
        leg_base = body_joint(41.0, 63.0)
        leg_dst = (leg_base[0] + p.legs_dx, leg_base[1] + p.legs_dy)
        w_legs = warp_part(
            self.parts["legs_tail"],
            (41.0, 63.0),
            leg_dst,
            angle_deg=p.body_angle + p.legs_angle,
            outline=False,
        )
        w_legs = smooth_warped_layer(w_legs)
        composite_over(canvas, add_pixel_outline(w_legs))

        # 3. Unified Main Body Buffer: `[torso + dual anatomical neck & throat bridges + upper_head]`
        main_buf = np.zeros_like(canvas)
        w_torso = warp_part(
            self.parts["torso"],
            torso_src,
            torso_dst,
            angle_deg=p.body_angle,
            outline=False,
        )
        composite_over(main_buf, w_torso)

        head_base = body_joint(67.0, 48.0)
        head_dst = (head_base[0] + p.head_dx, head_base[1] + p.head_dy)
        total_head_ang = p.body_angle + p.head_angle

        jaw_off = self._rot_pt((73.0, 51.0), (67.0, 48.0), total_head_ang)
        jaw_dst = (head_dst[0] + jaw_off[0] - 67.0, head_dst[1] + jaw_off[1] - 48.0)

        # Dual muscular neck & lower throat bridges (Spec 4: eliminates throat/jaw-hinge notch during forward run thrust!)
        draw_neck_capsule(main_buf, body_joint(60.0, 49.5), (head_dst[0] + 1.0, head_dst[1] + 0.5), radius=3.3)
        draw_neck_capsule(main_buf, body_joint(60.0, 53.5), (jaw_dst[0] - 1.5, jaw_dst[1] + 1.0), radius=3.2)

        w_jaw = warp_part(
            self.parts["lower_jaw"],
            (73.0, 51.0),
            jaw_dst,
            angle_deg=total_head_ang + p.jaw_angle,
            outline=False,
        )
        w_jaw = smooth_warped_layer(w_jaw)

        head_src_img = self.parts["upper_head"].copy()
        if p.eye_closed:
            head_src_img[43:47, 73:77] = CHARCOAL_DARK
            head_src_img[45, 73:77] = OUTLINE_RGBA
        w_head = warp_part(
            head_src_img,
            (67.0, 48.0),
            head_dst,
            angle_deg=total_head_ang,
            outline=False,
        )
        composite_over(main_buf, w_head)
        main_buf = smooth_warped_layer(main_buf)

        # Composite lower jaw first, then unified outlined main_buf so upper beak teeth overlap cleanly
        composite_over(canvas, add_pixel_outline(w_jaw))
        composite_over(canvas, add_pixel_outline(main_buf))

        # 4. Near Wing (`near_wing`) pivoted at bottom of shoulder socket:
        # - Upstroke (`flap_elev >= 0`): shows ventral Red membrane + Charcoal arm/claws (`self.near_wing_ventral`, Spec 2).
        # - Downstroke (`flap_elev < 0`): shows dorsal Charcoal skin matching the body (`self.near_wing_dorsal`, Spec 3).
        if p.flap_elev >= 0:
            src_wing_piv = (46.0, 55.0)
            dst_wing_piv = body_joint(46.0, 55.0)
            near_wing_src = self.near_wing_ventral
        else:
            src_wing_piv = (45.0, 55.0)
            dst_wing_piv = body_joint(45.0, 54.0)
            near_wing_src = self.near_wing_dorsal

        w_near = warp_wing_flap(
            near_wing_src,
            src_wing_piv,
            dst_wing_piv,
            flap_elev=p.flap_elev,
            span_scale=p.span_scale,
            camber_px=p.camber_px,
            shear_x_by_y=p.shear_x_by_y,
            rot_deg=p.body_angle + p.wing_rot,
            is_far=False,
            outline=False,
        )
        lbl_near, n_near = ndimage.label(w_near[:, :, 3] > 0)
        if n_near > 1:
            cnts = np.bincount(lbl_near.ravel())
            cnts[0] = 0
            w_near[lbl_near != int(np.argmax(cnts))] = 0
        w_near = smooth_warped_layer(w_near)
        composite_over(canvas, add_pixel_outline(w_near))

        # 5. Ground clamp for KO collapse frames so creature rests cleanly on ground line
        if p.clamp_ground_ko:
            ys, _ = np.where(canvas[:, :, 3] > 0)
            target_ground_y = LOGICAL_ANCHOR_Y + 4
            if len(ys) > 0 and ys.max() > target_ground_y:
                shift_up = int(ys.max() - target_ground_y)
                shifted = np.zeros_like(canvas)
                shifted[: LOGICAL_H - shift_up, :] = canvas[shift_up:, :]
                canvas = shifted

        # 6. Logical Pixel-Art VFX overlays (forward beak strike only; sonic wave is separated into `sonic_screech_fx`!)
        beak_tip_off = self._rot_pt((90.0, 50.0), (67.0, 48.0), total_head_ang)
        beak_tip_dst = (head_dst[0] + beak_tip_off[0] - 67.0, head_dst[1] + beak_tip_off[1] - 48.0)
        if p.beak_vfx_phase >= 0:
            self._draw_beak_strike_vfx(canvas, beak_tip_dst, p.beak_vfx_phase)

        # 2x Nearest upscale to 384x256 gameplay canvas
        pil_logical = Image.fromarray(canvas, mode="RGBA")
        out_canvas = np.array(pil_logical.resize((CANVAS_W, CANVAS_H), Image.Resampling.NEAREST))

        return out_canvas

    def _draw_beak_strike_vfx(self, canvas: np.ndarray, beak_tip_dst: tuple[float, float], phase: int) -> None:
        """Draw ferocious pixel-art Forward Beak Thrust Spear & Piercing Fang Shockwave ahead of the beak tip."""
        vfx = np.zeros_like(canvas)
        bx = int(round(beak_tip_dst[0])) + 1
        by = int(round(beak_tip_dst[1]))

        if phase == 0:
            # Phase 0 (lunge start — frame 2): Focusing piercing burgundy/crimson wind cone & twin fang arcs ahead of beak
            for s in range(0, 14):
                px = bx + s
                spread = max(1, int(round((14 - s) * 0.42)))
                for sign in (-1, 1):
                    py = by + sign * spread
                    if 0 <= px < LOGICAL_W and 0 <= py < LOGICAL_H:
                        vfx[py, px] = VFX_WHITE if s > 7 else VFX_CRIMSON_BRIGHT
                        if 0 <= py - sign < LOGICAL_H:
                            vfx[py - sign, px] = VFX_GOLD if s > 9 else VFX_BURGUNDY_MID
        elif phase == 1:
            # Phase 1 (peak beak strike — frame 3 `hit`): Sharp spear-tip thrust + snapping fang shockwave star!
            # Central piercing beak spear starting cleanly ahead of beak tip
            for dx in range(0, 22):
                half_h = max(0, int(round((21 - dx) * 0.22)))
                for dy in range(-half_h, half_h + 1):
                    px, py = bx + dx, by + dy
                    if 0 <= px < LOGICAL_W and 0 <= py < LOGICAL_H:
                        if abs(dy) == 0 and dx >= 1:
                            vfx[py, px] = VFX_WHITE
                        elif abs(dy) <= 1:
                            vfx[py, px] = VFX_GOLD
                        else:
                            vfx[py, px] = VFX_CRIMSON_BRIGHT if dx < 11 else VFX_BURGUNDY_MID
            # Shockwave crescent arc ahead of beak impact point
            for ang in np.linspace(-1.05, 1.05, 42):
                for dr in (-1, 0, 1):
                    rx = int(round(bx + 2 + (11 + dr) * math.cos(ang)))
                    ry = int(round(by + (12 + dr) * math.sin(ang)))
                    if 0 <= rx < LOGICAL_W and 0 <= ry < LOGICAL_H:
                        vfx[ry, rx] = VFX_WHITE if dr == 0 else VFX_CRIMSON_BRIGHT
        elif phase == 2:
            # Phase 2 (follow-through shockwave — frame 4): Expanding forward sonic-bite arc & sparks
            for ang in np.linspace(-1.0, 1.0, 40):
                for dr in (0, 1):
                    rx = int(round(bx + 6 + (14 + dr) * math.cos(ang)))
                    ry = int(round(by + (13 + dr) * math.sin(ang)))
                    if 0 <= rx < LOGICAL_W and 0 <= ry < LOGICAL_H:
                        vfx[ry, rx] = VFX_CRIMSON_BRIGHT if dr == 0 else VFX_BURGUNDY_MID
            for ang in [-0.55, -0.2, 0.0, 0.2, 0.55]:
                for s in range(8, 18):
                    px = int(round(bx + 5 + s * math.cos(ang)))
                    py = int(round(by + s * math.sin(ang)))
                    if 0 <= px < LOGICAL_W and 0 <= py < LOGICAL_H:
                        vfx[py, px] = VFX_GOLD if s < 14 else VFX_BURGUNDY_DEEP

        composite_over(canvas, add_pixel_outline(vfx))


def render_sonic_screech_fx_frame(phase_idx: int, sonic_crops: list[np.ndarray]) -> np.ndarray:
    """Render one frame (0..6) of Owner's 7-cluster sonic wave (`sonic_screech_fx`) on the 384x256 canvas."""
    out_canvas = np.zeros((CANVAS_H, CANVAS_W, 4), dtype=np.uint8)
    crop = sonic_crops[phase_idx]
    # Note: origin_canvas_px - fx_pivot_px = (282 - 176, 128 - 128) = (+106, 0).
    # So placing frame k at x_left = SONIC_X_LEFTS[k] - 106 ensures 100% pixel-identical alignment!
    x_left = SONIC_X_LEFTS[phase_idx] - (MOUTH_X - FX_PIVOT_X)
    y_top = FX_PIVOT_Y - 36
    ch, cw = crop.shape[:2]
    x1 = min(CANVAS_W, x_left + cw)
    y1 = min(CANVAS_H, y_top + ch)
    sub_crop = crop[: y1 - y_top, : x1 - x_left]
    m = sub_crop[:, :, 3] > 0
    out_canvas[y_top:y1, x_left:x1][m] = sub_crop[m]
    return out_canvas


def build_all_clip_poses() -> dict[str, list[PteranodonPose]]:
    """Construct biomechanical multi-frame PteranodonPose sequences for all 7 body clips."""
    clips: dict[str, list[PteranodonPose]] = {}

    # 1. IDLE (8 frames, cycle): Hovering in place with full vertical wingbeat & body lift/bob
    # (flap_elev, span_scale, camber_px, shear_x, wing_rot, body_dy, leg_ang, jaw_ang)
    idle_wing_table = [
        ( 1.04, 1.00, -1.0,  0.0,  0.0,  2.8,  6.0, 2.0),  # 0: High upstroke V
        ( 0.54, 1.02, -5.5,  2.0, -5.0,  1.0,  2.5, 2.5),  # 1: Upper-mid downstroke
        (-0.48, 1.00, -5.0,  9.0,  4.0, -1.2, -3.0, 3.5),  # 2: Horizontal sweep across flank
        (-0.98, 0.96,  2.0, 14.0,  6.0, -4.0, -9.0, 4.5),  # 3: Deep downstroke below belly (body rises!)
        (-0.82, 0.92,  6.5, 11.0,  4.0, -3.2, -7.0, 4.0),  # 4: Downstroke bottom whip
        (-0.44, 0.85,  7.0,  5.0,  1.0, -0.6, -1.5, 3.0),  # 5: Upstroke fold recovery
        ( 0.48, 0.90,  5.5,  1.0,  3.0,  1.4,  4.0, 2.0),  # 6: Mid-upstroke lift
        ( 0.88, 0.96,  1.5,  0.0,  1.5,  2.4,  5.5, 1.8),  # 7: High upstroke opening
    ]
    clips["idle"] = [
        PteranodonPose(
            body_dx=0.0,
            body_dy=b_dy,
            body_angle=-b_dy * 0.7,
            head_dy=b_dy * 0.4,
            head_angle=b_dy * 0.5,
            jaw_angle=jaw,
            flap_elev=elev,
            span_scale=s_sc,
            camber_px=camb,
            shear_x_by_y=sh_x,
            wing_rot=w_rot,
            legs_angle=l_ang,
        )
        for (elev, s_sc, camb, sh_x, w_rot, b_dy, l_ang, jaw) in idle_wing_table
    ]

    # 2. WALK (8 frames, cycle): Powerful forward flight wingbeat with strong vertical excursion & forward drive
    walk_wing_table = [
        ( 1.10, 1.00, -1.5,  0.0,  0.0, -1.0,  3.5,  8.0, 3.0),  # 0: Peak upstroke
        ( 0.56, 1.03, -6.5,  2.0, -6.0,  0.0,  1.2,  3.0, 4.0),  # 1: Driving downstroke start
        (-0.52, 1.02, -6.0, 10.0,  4.0,  1.5, -1.5, -4.0, 6.0),  # 2: Sweeping past torso
        (-1.08, 0.98,  2.0, 16.0,  6.0,  3.0, -4.8, -12.0, 8.0), # 3: Full power downstroke below belly!
        (-0.90, 0.94,  7.0, 13.0,  4.0,  2.2, -3.8, -9.0, 6.0),  # 4: Downstroke bottom whip
        (-0.46, 0.85,  8.0,  6.0,  1.0,  0.8, -0.8, -2.0, 4.0),  # 5: Upstroke fold recovery
        ( 0.50, 0.90,  6.5,  1.0,  4.0, -0.5,  1.8,  5.0, 3.0),  # 6: Mid-upstroke lift
        ( 0.92, 0.97,  2.0,  0.0,  2.0, -1.0,  3.0,  7.0, 2.5),  # 7: Opening into peak upstroke
    ]
    clips["walk"] = [
        PteranodonPose(
            body_dx=b_dx,
            body_dy=b_dy,
            body_angle=2.5 - b_dy * 0.8,
            head_dx=1.0,
            head_dy=b_dy * 0.35,
            head_angle=-2.0 + b_dy * 0.6,
            jaw_angle=jaw,
            flap_elev=elev,
            span_scale=s_sc,
            camber_px=camb,
            shear_x_by_y=sh_x,
            wing_rot=w_rot,
            legs_angle=l_ang - 4.0,
        )
        for (elev, s_sc, camb, sh_x, w_rot, b_dx, b_dy, l_ang, jaw) in walk_wing_table
    ]

    # 3. RUN (8 frames, cycle): High-speed predatory dive-dash flight with rapid power strokes & forward neck thrust
    run_wing_table = [
        ( 0.98, 0.96, -2.0,  0.0, -4.0,  2.0,  2.2, -6.0,  8.0),
        ( 0.48, 1.00, -7.0,  3.0, -8.0,  3.0,  0.5, -8.0, 10.0),
        (-0.56, 1.00, -6.0, 11.0,  5.0,  4.5, -2.0, -12.0, 12.0),
        (-1.10, 0.96,  2.5, 17.0,  8.0,  6.0, -4.5, -16.0, 14.0),
        (-0.86, 0.92,  7.5, 14.0,  5.0,  5.0, -3.5, -14.0, 11.0),
        (-0.44, 0.84,  8.0,  6.0,  2.0,  3.5, -1.0, -10.0,  9.0),
        ( 0.46, 0.88,  6.0,  1.0,  2.0,  2.5,  1.2, -7.0,  8.0),
        ( 0.84, 0.94,  2.0,  0.0, -2.0,  2.0,  2.0, -6.0,  8.0),
    ]
    clips["run"] = [
        PteranodonPose(
            body_dx=b_dx,
            body_dy=b_dy,
            body_angle=6.5 - b_dy * 0.6,
            head_dx=3.5,
            head_dy=0.5 + b_dy * 0.3,
            head_angle=-4.5 + b_dy * 0.4,
            jaw_angle=jaw,
            flap_elev=elev,
            span_scale=s_sc,
            camber_px=camb,
            shear_x_by_y=sh_x,
            wing_rot=w_rot,
            legs_angle=l_ang,
        )
        for (elev, s_sc, camb, sh_x, w_rot, b_dx, b_dy, l_ang, jaw) in run_wing_table
    ]

    # 4. ATTACK_LIGHT (8 frames, oneshot): Ferocious Forward Beak Lunge & Snap Strike (seamless neck!)
    clips["attack_light"] = [
        # 0: Wind-up 1 — coil back, wings flare up-back, beak opens
        PteranodonPose(
            body_dx=-4.0, body_dy=-1.0, body_angle=-5.0,
            head_dx=-2.5, head_dy=-1.5, head_angle=-8.0, jaw_angle=16.0,
            flap_elev=1.05, span_scale=1.02, camber_px=-2.0, wing_rot=-8.0,
            legs_angle=10.0,
        ),
        # 1: Wind-up 2 (`tell`) — deep coil back, jaws wide open aiming at target
        PteranodonPose(
            body_dx=-7.0, body_dy=-2.0, body_angle=-9.0,
            head_dx=-4.5, head_dy=-2.5, head_angle=-14.0, jaw_angle=26.0,
            flap_elev=1.12, span_scale=1.05, camber_px=-4.0, wing_rot=-14.0,
            legs_angle=16.0,
        ),
        # 2: Lunge launch — wings beat down/back (`flap_elev = -0.65`) propelling body & beak rapidly forward!
        PteranodonPose(
            body_dx=9.0, body_dy=1.0, body_angle=8.0,
            head_dx=6.5, head_dy=1.0, head_angle=-2.0, jaw_angle=22.0,
            flap_elev=-0.65, span_scale=0.98, camber_px=-5.0, shear_x_by_y=8.0, wing_rot=6.0,
            legs_angle=-14.0,
            beak_vfx_phase=0,
        ),
        # 3: Peak Beak Strike (`hit`) — full forward neck extension, serrated beak snaps shut with piercing spear VFX!
        PteranodonPose(
            body_dx=14.5, body_dy=1.5, body_angle=11.0,
            head_dx=10.0, head_dy=1.8, head_angle=3.0, jaw_angle=0.0,
            flap_elev=-1.02, span_scale=0.95, camber_px=3.0, shear_x_by_y=12.0, wing_rot=10.0,
            legs_angle=-18.0,
            beak_vfx_phase=1,
        ),
        # 4: Follow-through impact shockwave — beak clenched, shockwave bursting forward
        PteranodonPose(
            body_dx=11.5, body_dy=1.2, body_angle=9.0,
            head_dx=8.0, head_dy=1.4, head_angle=2.0, jaw_angle=-1.0,
            flap_elev=-0.75, span_scale=0.92, camber_px=6.0, shear_x_by_y=9.0, wing_rot=6.0,
            legs_angle=-14.0,
            beak_vfx_phase=2,
        ),
        # 5: Recovery 1 — wings fold and lift to brake forward momentum
        PteranodonPose(
            body_dx=6.0, body_dy=0.5, body_angle=4.5,
            head_dx=4.0, head_dy=0.6, head_angle=0.0, jaw_angle=3.0,
            flap_elev=-0.38, span_scale=0.86, camber_px=6.0, shear_x_by_y=4.0, wing_rot=2.0,
            legs_angle=-6.0,
        ),
        # 6: Recovery 2 — wings rise above back
        PteranodonPose(
            body_dx=2.0, body_dy=1.5, body_angle=1.5,
            head_dx=1.2, head_dy=0.2, head_angle=0.0, jaw_angle=2.0,
            flap_elev=0.55, span_scale=0.94, camber_px=4.0, wing_rot=1.0,
            legs_angle=2.0,
        ),
        # 7: End (`end`) — back to hover upstroke
        PteranodonPose(
            body_dx=0.0, body_dy=2.4, body_angle=0.0,
            head_dx=0.0, head_dy=0.0, head_angle=0.0, jaw_angle=1.8,
            flap_elev=0.98, span_scale=1.00, camber_px=0.0, wing_rot=0.0,
            legs_angle=5.0,
        ),
    ]

    # 5. POWER_UP (8 frames, oneshot): Body-Only Sonic Screech Posture at Normal Body Speed (`[5, 5, 5, 5, 4, 5, 5, 6]` ticks)
    # The 7-phase sonic wave (`sonic_screech_fx`) is 100% separated into its own independent asset running at `[2, 2, 2, 2, 2, 2, 2]` ticks!
    clips["power_up"] = [
        # 0: Inhale 1 — rear neck back, wings rise, jaws open
        PteranodonPose(
            body_dx=-3.5, body_dy=-1.0, body_angle=-5.0,
            head_dx=-2.5, head_dy=-1.5, head_angle=-8.0, jaw_angle=16.0,
            flap_elev=0.95, span_scale=1.00, camber_px=-2.0, wing_rot=-6.0,
            legs_angle=8.0,
        ),
        # 1: Inhale 2 (`tell`) — deep rear back, wings flared high, jaws wide open
        PteranodonPose(
            body_dx=-6.5, body_dy=-2.0, body_angle=-9.0,
            head_dx=-4.5, head_dy=-2.5, head_angle=-14.0, jaw_angle=25.0,
            flap_elev=1.10, span_scale=1.04, camber_px=-4.0, wing_rot=-12.0,
            legs_angle=14.0,
        ),
        # 2: Screech Release (`hit`, release_frame=2 at tick 10) — thrust neck forward, jaws wide open, wings sweep down/back!
        PteranodonPose(
            body_dx=6.5, body_dy=-1.5, body_angle=6.0,
            head_dx=5.5, head_dy=-1.5, head_angle=-3.0, jaw_angle=28.0,
            flap_elev=-0.75, span_scale=0.98, camber_px=-3.0, shear_x_by_y=11.0, wing_rot=6.0,
            legs_angle=-12.0,
        ),
        # 3: Screech Sustain 1 (ticks 15..20) — full power downstroke bracing body in mid-air while independent sonic wave fires
        PteranodonPose(
            body_dx=6.0, body_dy=-2.2, body_angle=5.0,
            head_dx=5.0, head_dy=-1.5, head_angle=-2.5, jaw_angle=26.0,
            flap_elev=-1.04, span_scale=0.95, camber_px=3.0, shear_x_by_y=15.0, wing_rot=8.0,
            legs_angle=-15.0,
        ),
        # 4: Screech Sustain 2 (ticks 20..24) — wing whip fold while sonic wave completes its 14-tick burst
        PteranodonPose(
            body_dx=5.0, body_dy=-1.2, body_angle=4.0,
            head_dx=4.2, head_dy=-1.2, head_angle=-2.0, jaw_angle=23.0,
            flap_elev=-0.52, span_scale=0.88, camber_px=6.0, shear_x_by_y=8.0, wing_rot=3.0,
            legs_angle=-9.0,
        ),
        # 5: Recovery 1 — wings rising on recovery stroke, jaws closing
        PteranodonPose(
            body_dx=3.5, body_dy=0.4, body_angle=3.0,
            head_dx=3.0, head_dy=-0.6, head_angle=-1.0, jaw_angle=16.0,
            flap_elev=0.48, span_scale=0.91, camber_px=5.0, wing_rot=2.0,
            legs_angle=-2.0,
        ),
        # 6: Recovery 2 — wings opening into high upstroke
        PteranodonPose(
            body_dx=1.5, body_dy=1.6, body_angle=1.2,
            head_dx=1.2, head_dy=-0.2, head_angle=0.0, jaw_angle=8.0,
            flap_elev=0.84, span_scale=0.96, camber_px=2.0, wing_rot=1.0,
            legs_angle=3.0,
        ),
        # 7: Recovery (`end`) — back to hover upstroke
        PteranodonPose(
            body_dx=0.0, body_dy=2.5, body_angle=0.0,
            head_dx=0.0, head_dy=0.0, head_angle=0.0, jaw_angle=2.0,
            flap_elev=1.04, span_scale=1.00, camber_px=-1.0, wing_rot=0.0,
            legs_angle=6.0,
        ),
    ]

    # 6. HIT (6 frames, oneshot): Aerial stagger recoil with seamless neck & wing flutter recovery
    clips["hit"] = [
        PteranodonPose(
            body_dx=-7.0, body_dy=-2.0, body_angle=-12.0,
            head_dx=-3.5, head_dy=-2.0, head_angle=-14.0, jaw_angle=22.0,
            flap_elev=0.92, span_scale=0.96, camber_px=-6.0, wing_rot=-16.0,
            legs_angle=16.0,
        ),
        PteranodonPose(
            body_dx=-11.0, body_dy=-3.5, body_angle=-18.0,
            head_dx=-5.0, head_dy=-3.0, head_angle=-20.0, jaw_angle=26.0, eye_closed=True,
            flap_elev=-0.55, span_scale=0.90, camber_px=7.0, shear_x_by_y=6.0, wing_rot=-10.0,
            legs_angle=22.0,
        ),
        PteranodonPose(
            body_dx=-8.0, body_dy=-1.5, body_angle=-12.0,
            head_dx=-3.5, head_dy=-2.0, head_angle=-12.0, jaw_angle=16.0, eye_closed=True,
            flap_elev=-0.85, span_scale=0.92, camber_px=5.0, shear_x_by_y=10.0, wing_rot=-4.0,
            legs_angle=14.0,
        ),
        PteranodonPose(
            body_dx=-4.5, body_dy=0.5, body_angle=-6.0,
            head_dx=-1.8, head_dy=-0.8, head_angle=-6.0, jaw_angle=9.0,
            flap_elev=0.48, span_scale=0.92, camber_px=5.0, wing_rot=-2.0,
            legs_angle=8.0,
        ),
        PteranodonPose(
            body_dx=-1.8, body_dy=1.8, body_angle=-2.0,
            head_dx=-0.6, head_dy=-0.2, head_angle=-2.0, jaw_angle=4.0,
            flap_elev=0.84, span_scale=0.97, camber_px=2.0, wing_rot=0.0,
            legs_angle=6.0,
        ),
        PteranodonPose(
            body_dx=0.0, body_dy=2.5, body_angle=0.0,
            head_dx=0.0, head_dy=0.0, head_angle=0.0, jaw_angle=2.0,
            flap_elev=1.02, span_scale=1.00, camber_px=-1.0, wing_rot=0.0,
            legs_angle=6.0,
        ),
    ]

    # 7. KO (8 frames, oneshot): Owner-approved aerial fall & ground collapse sequence
    clips["ko"] = [
        PteranodonPose(
            body_dx=-4.0, body_dy=2.0, body_angle=-10.0,
            head_dx=-2.0, head_dy=-1.0, head_angle=-14.0, jaw_angle=20.0,
            flap_elev=0.70, span_scale=0.88, wing_rot=-25.0,
            legs_angle=12.0,
        ),
        PteranodonPose(
            body_dx=-6.0, body_dy=12.0, body_angle=-25.0,
            head_dx=-2.0, head_dy=-1.0, head_angle=-18.0, jaw_angle=16.0, eye_closed=True,
            flap_elev=0.58, span_scale=0.82, wing_rot=-38.0,
            legs_angle=18.0,
        ),
        PteranodonPose(
            body_dx=-8.0, body_dy=24.0, body_angle=-45.0,
            head_dx=-1.5, head_dy=-0.5, head_angle=-20.0, jaw_angle=12.0, eye_closed=True,
            flap_elev=0.48, span_scale=0.76, wing_rot=-50.0,
            legs_angle=22.0,
            clamp_ground_ko=True,
        ),
        PteranodonPose(
            body_dx=-8.0, body_dy=34.0, body_angle=-70.0,
            head_dx=-1.0, head_dy=0.0, head_angle=-10.0, jaw_angle=8.0, eye_closed=True,
            flap_elev=0.42, span_scale=0.72, wing_rot=-62.0,
            legs_angle=25.0,
            clamp_ground_ko=True,
        ),
        PteranodonPose(
            body_dx=-8.0, body_dy=32.0, body_angle=-75.0,
            head_dx=-0.5, head_dy=0.0, head_angle=-5.0, jaw_angle=6.0, eye_closed=True,
            flap_elev=0.38, span_scale=0.70, wing_rot=-68.0,
            legs_angle=26.0,
            clamp_ground_ko=True,
        ),
        PteranodonPose(
            body_dx=-8.0, body_dy=33.5, body_angle=-78.0,
            head_dx=-0.5, head_dy=0.0, head_angle=-4.0, jaw_angle=4.0, eye_closed=True,
            flap_elev=0.36, span_scale=0.68, wing_rot=-72.0,
            legs_angle=28.0,
            clamp_ground_ko=True,
        ),
        PteranodonPose(
            body_dx=-8.0, body_dy=35.0, body_angle=-80.0,
            head_dx=-0.5, head_dy=0.0, head_angle=-7.0, jaw_angle=2.0, eye_closed=True,
            flap_elev=0.36, span_scale=0.66, wing_rot=-75.0,
            legs_angle=28.0,
            clamp_ground_ko=True,
        ),
        PteranodonPose(
            body_dx=-8.0, body_dy=36.5, body_angle=-82.0,
            head_dx=-0.5, head_dy=0.0, head_angle=-10.0, jaw_angle=1.0, eye_closed=True,
            flap_elev=0.36, span_scale=0.65, wing_rot=-78.0,
            legs_angle=30.0,
            clamp_ground_ko=True,
        ),
    ]

    return clips


def stage_and_export_bundle(builder: PteranodonBuilder, clip_poses: dict[str, list[PteranodonPose]]) -> None:
    """Stage all frames, run `build_animation_clips.py` and `export_engine.py`, and deploy to `assets/pteranodon`."""
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    raw_frames_dir = STAGE_DIR / "raw_frames"
    raw_frames_dir.mkdir(parents=True, exist_ok=True)

    body_clip_order = [
        "idle",
        "walk",
        "run",
        "attack_light",
        "power_up",
        "hit",
        "ko",
    ]

    frame_entries: list[dict[str, str]] = []
    clip_frame_names: dict[str, list[str]] = {}
    rendered_clips: dict[str, list[np.ndarray]] = {}

    for cname in body_clip_order:
        poses = clip_poses[cname]
        c_names: list[str] = []
        c_frames: list[np.ndarray] = []
        for idx, pose in enumerate(poses):
            fname = f"{cname}_{idx:02d}"
            ffile = f"raw_frames/{fname}.png"
            rgba = builder.render_pose(pose)
            Image.fromarray(rgba, mode="RGBA").save(STAGE_DIR / ffile)
            frame_entries.append({"name": fname, "file": ffile})
            c_names.append(fname)
            c_frames.append(rgba)
        clip_frame_names[cname] = c_names
        rendered_clips[cname] = c_frames

    fx_names: list[str] = []
    fx_frames: list[np.ndarray] = []
    for idx in range(7):
        fname = f"sonic_screech_fx_{idx:02d}"
        ffile = f"raw_frames/{fname}.png"
        rgba = render_sonic_screech_fx_frame(idx, builder.sonic_crops)
        Image.fromarray(rgba, mode="RGBA").save(STAGE_DIR / ffile)
        frame_entries.append({"name": fname, "file": ffile})
        fx_names.append(fname)
        fx_frames.append(rgba)
    clip_frame_names["sonic_screech_fx"] = fx_names
    rendered_clips["sonic_screech_fx"] = fx_frames

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
                "ticks": [6, 6, 6, 6, 6, 6, 6, 6],
                "loop_policy": "cycle",
                "events": [
                    {"at": 3, "name": "step_r"},
                    {"at": 7, "name": "step_l"},
                ],
            },
            "run": {
                "role": "player",
                "frames": clip_frame_names["run"],
                "ticks": [4, 4, 4, 4, 4, 4, 4, 4],
                "loop_policy": "cycle",
                "events": [
                    {"at": 3, "name": "step_r"},
                    {"at": 7, "name": "step_l"},
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
            "power_up": {
                "role": "player",
                "frames": clip_frame_names["power_up"],
                "ticks": [5, 5, 5, 5, 4, 5, 5, 6],
                "loop_policy": "oneshot",
                "hitstop_ticks": 4,
                "keys": {"wind_start": 0, "wind_peak": 1, "strike": 2, "recover": 5, "end": 7},
                "events": [
                    {"at": 1, "name": "tell"},
                    {"at": 2, "name": "hit", "data": {"projectile": "sonic_screech_fx"}},
                    {"at": 7, "name": "end"},
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
                    {"at": 3, "name": "impact"},
                    {"at": 7, "name": "hold"},
                ],
            },
            "sonic_screech_fx": {
                "role": "fx",
                "frames": clip_frame_names["sonic_screech_fx"],
                "ticks": [2, 2, 2, 2, 2, 2, 2],
                "loop_policy": "oneshot",
            },
        },
    }

    manifest_path = STAGE_DIR / "clips_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    built_clips_dir = STAGE_DIR / "clips_built"
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

    assets_clips_dir = REPO_ROOT / "assets" / "pteranodon" / "clips"
    if assets_clips_dir.exists():
        shutil.rmtree(assets_clips_dir)
    shutil.copytree(built_clips_dir, assets_clips_dir)
    (assets_clips_dir / ".gdignore").touch()

    exported_bundle_dir = STAGE_DIR / "exported_bundle"
    if exported_bundle_dir.exists():
        shutil.rmtree(exported_bundle_dir)
    export_script = REPO_ROOT / ".agent" / "skills" / "generate2dsprite" / "scripts" / "export_engine.py"
    exp_res = subprocess.run(
        [
            sys.executable,
            str(export_script),
            "--clips",
            str(assets_clips_dir / "animation-clips.json"),
            "--target",
            "all",
            "--output-dir",
            str(exported_bundle_dir),
            "--name",
            "pteranodon",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    print("export_engine stdout:", exp_res.stdout.strip())
    if exp_res.returncode != 0:
        print("export_engine stderr:", exp_res.stderr.strip(), file=sys.stderr)
        sys.exit(exp_res.returncode)

    engine_export_path = exported_bundle_dir / "engine-export.json"
    ee_data = json.loads(engine_export_path.read_text(encoding="utf-8"))
    ee_data["source"]["path"] = "../clips/animation-clips.json"
    ee_data["render_contract"] = {
        "body_clips": [
            "idle",
            "walk",
            "run",
            "attack_light",
            "power_up",
            "hit",
            "ko",
        ],
        "effect_clips": ["sonic_screech_fx"],
        "locomotion": {"kind": "flight", "clip": "walk"},
        "aura": {"loop_clip": None, "charge_clip": None, "independent_clock": True},
        "fx_pivot_px": [FX_PIVOT_X, FX_PIVOT_Y],
        "projectile": {
            "kind": "linear_energy",
            "body_clip": "power_up",
            "projectile_clip": "sonic_screech_fx",
            "release_frame": 2,
            "lifetime_ticks": 14,
            "origin_canvas_px": [MOUTH_X, MOUTH_Y],
            "velocity_px_per_tick": [0.0, 0.0],
        },
    }
    engine_export_path.write_text(json.dumps(ee_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    assets_bundle_dir = REPO_ROOT / "assets" / "pteranodon" / "godot_bundle"
    if assets_bundle_dir.exists():
        shutil.rmtree(assets_bundle_dir)
    shutil.copytree(exported_bundle_dir, assets_bundle_dir)

    fx_offset_x = ANCHOR_X - (MOUTH_X - FX_PIVOT_X)
    prefab_content = f"""[gd_scene load_steps=4 format=3]

[ext_resource type="Script" path="res://scenes/CharacterFighter2D.gd" id="1_fighter"]
[ext_resource type="SpriteFrames" path="res://assets/pteranodon/godot_bundle/godot/pteranodon.tres" id="2_frames"]
[ext_resource type="Script" path="res://tests/SkillAnimator2D.gd" id="3_anim"]

[node name="Pteranodon" type="Node2D"]
script = ExtResource("1_fighter")
character_id = "pteranodon"
engine_export_json = "res://assets/pteranodon/godot_bundle/engine-export.json"

[node name="Sprite" type="AnimatedSprite2D" parent="."]
texture_filter = 1
sprite_frames = ExtResource("2_frames")
animation = &"idle"
autoplay = "idle"
centered = false
offset = Vector2(-{ANCHOR_X}, -{ANCHOR_Y})

[node name="ProjectileFX" type="AnimatedSprite2D" parent="."]
visible = false
texture_filter = 1
sprite_frames = ExtResource("2_frames")
animation = &"sonic_screech_fx"
centered = false
offset = Vector2(-{fx_offset_x}, -{ANCHOR_Y})

[node name="SkillAnimator" type="Node2D" parent="."]
script = ExtResource("3_anim")
"""
    (REPO_ROOT / "scenes" / "Pteranodon.tscn").write_text(prefab_content, encoding="utf-8")

    sonic_fx_prefab = f"""[gd_scene load_steps=2 format=3]

[ext_resource type="SpriteFrames" path="res://assets/pteranodon/godot_bundle/godot/pteranodon.tres" id="1_frames"]

[node name="PteranodonSonicWaveFX" type="AnimatedSprite2D"]
texture_filter = 1
sprite_frames = ExtResource("1_frames")
animation = &"sonic_screech_fx"
autoplay = "sonic_screech_fx"
centered = false
offset = Vector2(-{float(FX_PIVOT_X)}, -{float(FX_PIVOT_Y)})
"""
    (REPO_ROOT / "scenes" / "PteranodonSonicWaveFX.tscn").write_text(sonic_fx_prefab, encoding="utf-8")
    (REPO_ROOT / "work" / ".gdignore").touch()
    subprocess.run(
        ["godot", "--headless", "--import", "--quit"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def update_roster() -> None:
    """Update `assets/roster.json` with the updated contract for `pteranodon` (no `attack_heavy`, 7-phase sonic wave)."""
    roster_path = REPO_ROOT / "assets" / "roster.json"
    data = json.loads(roster_path.read_text(encoding="utf-8"))

    entry = {
        "character_id": "pteranodon",
        "display_name": "Pteranodon",
        "faction": "special_beasts",
        "role_label": "Predatory Flying Pterosaur (Biomechanical Wingbeat / Beak Strike / 7-Phase Sonic Screech)",
        "tags": [
            "dinosaur",
            "pterosaur",
            "flying",
            "pixel_art",
            "projectile_fx",
        ],
        "status": "finalized",
        "facing_contract": {
            "camera_view": "side_view_2d",
            "default_atlas_facing": "right (+X)",
            "left_facing_rule": "horizontal_flip_around_foot_anchor_x (flip_h = true, anchor_x = 176)",
            "locomotion_vector_rule": "Aerial flight locomotion with full vertical wingbeat excursion (upstroke V above back -> horizontal camber sweep -> deep power downstroke below belly); attack_light thrusts beak straight forward (+X).",
        },
        "map_sync_metrics": {
            "canvas_size_px": [CANVAS_W, CANVAS_H],
            "foot_anchor_px": [float(ANCHOR_X), float(ANCHOR_Y)],
            "body_only_bbox_px": {
                "x": 80,
                "y": 74,
                "w": 194,
                "h": 132,
            },
            "full_fx_bbox_px": {
                "x": 36,
                "y": 56,
                "w": 330,
                "h": 180,
            },
            "world_size_at_64ppu_m": {
                "body_w_m": 3.03,
                "body_h_m": 2.06,
                "aura_w_m": 5.16,
                "aura_h_m": 2.81,
            },
            "tile_32px_span": {
                "body_tiles_w": 6.06,
                "body_tiles_h": 4.12,
                "full_fx_tiles_w": 10.31,
                "full_fx_tiles_h": 5.62,
            },
        },
        "pixel_sharpness_metrics": {
            "texel_scale_ratio": "2:1 Nearest (100x100 logical master -> 384x256 gameplay canvas)",
            "edge_acutance_sobel": 201.3,
            "alpha_hardness_pct": 100.0,
            "opaque_key_px": 0,
            "enclosed_key_pockets": 0,
            "outer_ring_spill_fraction": 0.0,
        },
        "present_clips": [
            "idle",
            "walk",
            "run",
            "attack_light",
            "power_up",
            "hit",
            "ko",
        ],
        "effect_clips": [
            "sonic_screech_fx",
        ],
        "missing_provisional_clips": [
            "jump",
            "guard",
            "attack_heavy",
            "aura_loop",
            "win",
        ],
        "not_applicable_clips": {
            "jump": "Owner khóa đặc tả nhân vật Pteranodon: dực long bay lượn liên tục trên không, không cần hoạt ảnh jump.",
            "attack_heavy": "Owner khóa đặc tả riêng nhân vật Pteranodon: bỏ đòn tấn công nặng (attack_heavy); chỉ sử dụng đòn mỏ tấn công nhẹ về trước (attack_light) và chiêu sóng âm (power_up).",
            "aura_loop": "Owner khóa đặc tả nhân vật Pteranodon: sinh vật tự nhiên không có Ki Saiyan / aura_loop; power_up phát sóng âm siêu thanh 7 pha từ mẫu của Owner (sonic_screech_fx).",
            "guard": "Owner chốt phạm vi toàn dự án (Điều 7.1 AGENTS.md): không tạo guard cho bất kỳ nhân vật nào.",
            "win": "Owner chốt phạm vi toàn dự án (Điều 7.1 AGENTS.md): không tạo win cho bất kỳ nhân vật nào.",
        },
        "render_contract": {
            "body_clips": [
                "idle",
                "walk",
                "run",
                "attack_light",
                "power_up",
                "hit",
                "ko",
            ],
            "effect_clips": [
                "sonic_screech_fx",
            ],
            "locomotion": {
                "kind": "flight",
                "clip": "walk",
            },
            "aura": {
                "loop_clip": None,
                "charge_clip": None,
                "independent_clock": True,
            },
            "fx_pivot_px": [
                FX_PIVOT_X,
                FX_PIVOT_Y,
            ],
            "projectile": {
                "kind": "linear_energy",
                "body_clip": "power_up",
                "projectile_clip": "sonic_screech_fx",
                "release_frame": 2,
                "lifetime_ticks": 14,
                "origin_canvas_px": [
                    MOUTH_X,
                    MOUTH_Y,
                ],
                "velocity_px_per_tick": [
                    0.0,
                    0.0,
                ],
            },
        },
        "modes": {
            "combined_1layer": {
                "label": "Gộp Chung 1 Lớp Nguyên Bản (1 Quad / 1 Draw Call + Independent Sonic Screech FX)",
                "godot_prefab": "res://scenes/Pteranodon.tscn",
                "bundle_id": "pteranodon",
            },
        },
    }

    chars = [c for c in data.get("characters", []) if c.get("character_id") != "pteranodon" and c.get("id") != "pteranodon"]
    chars.append(entry)
    data["characters"] = chars
    roster_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    print("=" * 70)
    print("DR7-STUDIO — PTERANODON v2 BIOMECHANICAL WINGBEAT & SONIC WAVE PIPELINE")
    print("=" * 70)

    builder = PteranodonBuilder(APPROVED_MASTER, SONIC_FX_SOURCE)
    clip_poses = build_all_clip_poses()
    stage_and_export_bundle(builder, clip_poses)
    update_roster()
    print("Successfully built and deployed Pteranodon v2 bundle!")


if __name__ == "__main__":
    main()
