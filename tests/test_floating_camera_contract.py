"""Contract & exact sheet fidelity tests for Floating Camera (70x74 1-Pass Nearest)."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_GIF = ROOT / "assets" / "floating_camera" / "source" / "FloatingCamera.gif"
RAW_DIR = ROOT / "assets" / "floating_camera" / "source" / "raw_frames"
TRES_PATH = ROOT / "assets" / "floating_camera" / "godot_bundle" / "godot" / "floating_camera.tres"
ATLAS_PATH = ROOT / "assets" / "floating_camera" / "godot_bundle" / "godot" / "floating_camera-atlas-00.png"
EXPORT_JSON = ROOT / "assets" / "floating_camera" / "godot_bundle" / "engine-export.json"
ROSTER_PATH = ROOT / "assets" / "roster.json"
BG_RGB = (4, 121, 188)


class FloatingCameraContractTests(unittest.TestCase):
    def test_exact_source_palette_and_alpha_hardness(self) -> None:
        with Image.open(SRC_GIF) as gif_im:
            sheet = np.asarray(gif_im.convert("RGBA"), dtype=np.uint8)
        solid_mask = ~(
            (sheet[:, :, 0] == BG_RGB[0])
            & (sheet[:, :, 1] == BG_RGB[1])
            & (sheet[:, :, 2] == BG_RGB[2])
        )
        allowed_palette = {tuple(int(v) for v in c) for c in np.unique(sheet[solid_mask][:, :3], axis=0)}
        self.assertGreaterEqual(len(allowed_palette), 13)
        frames = sorted(RAW_DIR.glob("*.png"))
        self.assertEqual(len(frames), 22)
        for p in frames:
            with Image.open(p) as fp_im:
                arr = np.asarray(fp_im.convert("RGBA"), dtype=np.uint8)
            self.assertEqual(arr.shape[:2], (160, 192), msg=f"{p.name} canvas mismatch")
            alphas = set(int(v) for v in np.unique(arr[:, :, 3]))
            self.assertTrue(alphas.issubset({0, 255}), msg=f"{p.name} soft alpha found: {alphas}")
            vis = arr[:, :, 3] > 0
            self.assertTrue(np.any(vis), msg=f"{p.name} is blank")
            rgbs = {tuple(int(v) for v in c) for c in np.unique(arr[vis][:, :3], axis=0)}
            self.assertTrue(
                rgbs.issubset(allowed_palette),
                msg=f"{p.name} introduced non-source colors: {rgbs - allowed_palette}",
            )
            key_px = int(
                np.count_nonzero(
                    vis
                    & (arr[:, :, 0] == BG_RGB[0])
                    & (arr[:, :, 1] == BG_RGB[1])
                    & (arr[:, :, 2] == BG_RGB[2])
                )
            )
            self.assertEqual(key_px, 0, msg=f"{p.name} leaked blue background key pixels")

        with Image.open(RAW_DIR / "flight-00.png") as f0_im:
            flight0 = np.asarray(f0_im.convert("RGBA"), dtype=np.uint8)
        f0_colors = {tuple(int(v) for v in c) for c in np.unique(flight0[flight0[:, :, 3] > 0][:, :3], axis=0)}
        self.assertEqual(len(f0_colors), 13)
        ys, xs = np.where(flight0[:, :, 3] > 0)
        self.assertEqual(int(xs.max() - xs.min() + 1), 70)
        self.assertEqual(int(ys.max() - ys.min() + 1), 74)

    def test_roster_and_engine_export_contract(self) -> None:
        roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
        fc = next((c for c in roster["characters"] if c["character_id"] == "floating_camera"), None)
        self.assertIsNotNone(fc)
        self.assertEqual(fc["status"], "finalized_owner_approved")
        self.assertEqual(fc["combat_role"], "monster")
        self.assertEqual(fc["map_sync_metrics"]["canvas_size_px"], [192, 160])
        self.assertEqual(fc["map_sync_metrics"]["foot_anchor_px"], [96, 112])
        self.assertEqual(fc["map_sync_metrics"]["body_only_bbox_px"], {"x": 61, "y": 38, "w": 70, "h": 74})
        self.assertEqual(fc["render_contract"]["locomotion"]["kind"], "flight")
        self.assertEqual(fc["render_contract"]["locomotion"]["default_scale"], 1.0)
        self.assertEqual(fc["render_contract"]["locomotion"]["screen_speed_px_per_second"], 150)
        self.assertEqual(fc["render_contract"]["locomotion"]["flight_default_y"], 300)
        self.assertTrue(fc["render_contract"]["locomotion"]["preserve_phase_on_idle_walk"])
        self.assertEqual(fc["render_contract"]["turning"]["method"], "instant_flip")
        self.assertEqual(fc["render_contract"]["projectile"]["projectile_clip"], "projectile_fx")
        self.assertEqual(fc["render_contract"]["projectile"]["origin_local_px"], [21, -6])
        self.assertEqual(
            fc["motion_quality"]["atlas_sha256"],
            hashlib.sha256(ATLAS_PATH.read_bytes()).hexdigest(),
        )

        export_data = json.loads(EXPORT_JSON.read_text(encoding="utf-8"))
        self.assertEqual(len(export_data["atlas"]["pages"]), 1)
        w, h = export_data["atlas"]["pages"][0]["size"]
        self.assertLessEqual(w, 4096)
        self.assertLessEqual(h, 4096)
        self.assertEqual(export_data["sampling"], "nearest")
        self.assertEqual(export_data["clips"]["idle"]["frames"], export_data["clips"]["walk"]["frames"])
        self.assertEqual(export_data["clips"]["idle"]["duration_ms"], export_data["clips"]["walk"]["duration_ms"])
        self.assertIn("attack_light", export_data["clips"])
        self.assertIn("projectile_fx", export_data["clips"])
        self.assertIn("hit", export_data["clips"])
        self.assertIn("ko", export_data["clips"])
        self.assertNotIn("power_up", export_data["clips"])


if __name__ == "__main__":
    unittest.main()
