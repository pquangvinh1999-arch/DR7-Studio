"""Contract & exact sheet fidelity tests for Drum (PA-1 / H1 / Monster AI)."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_SHEET = ROOT / "assets" / "drum" / "source" / "drum_sheet_src.png"
RAW_DIR = ROOT / "assets" / "drum" / "source" / "raw_frames"
TRES_PATH = ROOT / "assets" / "drum" / "godot_bundle" / "godot" / "drum.tres"
ATLAS_PATH = ROOT / "assets" / "drum" / "godot_bundle" / "godot" / "drum-atlas-00.png"
EXPORT_JSON = ROOT / "assets" / "drum" / "godot_bundle" / "engine-export.json"
ROSTER_PATH = ROOT / "assets" / "roster.json"
BG_RGB = (146, 5, 167)


class DrumContractTests(unittest.TestCase):
    def test_exact_source_palette_and_alpha_hardness(self) -> None:
        sheet = np.asarray(Image.open(SRC_SHEET).convert("RGBA"), dtype=np.uint8)
        solid_mask = ~(
            (sheet[:, :, 0] == BG_RGB[0])
            & (sheet[:, :, 1] == BG_RGB[1])
            & (sheet[:, :, 2] == BG_RGB[2])
        )
        allowed_palette = {tuple(int(v) for v in c) for c in np.unique(sheet[solid_mask][:, :3], axis=0)}
        frames = sorted(RAW_DIR.glob("*.png"))
        self.assertGreaterEqual(len(frames), 50)
        for p in frames:
            arr = np.asarray(Image.open(p).convert("RGBA"), dtype=np.uint8)
            self.assertEqual(arr.shape[:2], (96, 128), msg=f"{p.name} canvas mismatch")
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
            self.assertEqual(key_px, 0, msg=f"{p.name} leaked magenta key pixels")

    def test_walk_size_parity_matches_canonical_idle(self) -> None:
        idle0 = np.asarray(Image.open(RAW_DIR / "idle_00.png").convert("RGBA"), dtype=np.uint8)
        iv = idle0[:, :, 3] > 0
        iys, ixs = np.where(iv)
        idle_w = int(ixs.max() - ixs.min() + 1)
        idle_h = int(iys.max() - iys.min() + 1)
        idle_area = int(np.count_nonzero(iv))
        for wi in range(8):
            wp = RAW_DIR / f"walk_{wi:02d}.png"
            self.assertTrue(wp.exists(), f"Missing {wp.name}")
            warr = np.asarray(Image.open(wp).convert("RGBA"), dtype=np.uint8)
            wv = warr[:, :, 3] > 0
            wys, wxs = np.where(wv)
            ww = int(wxs.max() - wxs.min() + 1)
            wh = int(wys.max() - wys.min() + 1)
            warea = int(np.count_nonzero(wv))
            self.assertGreaterEqual(ww, idle_w - 2, f"{wp.name} width {ww} shrunk vs idle_00 {idle_w}")
            self.assertLessEqual(ww, idle_w + 3, f"{wp.name} width {ww} bloated vs idle_00 {idle_w}")
            self.assertGreaterEqual(wh, idle_h - 2, f"{wp.name} height {wh} shrunk vs idle_00 {idle_h}")
            self.assertLessEqual(wh, idle_h + 2, f"{wp.name} height {wh} bloated vs idle_00 {idle_h}")
            self.assertGreaterEqual(warea, idle_area - 100, f"{wp.name} pixel area {warea} too small vs idle_00 {idle_area}")

    def test_roster_and_engine_export_contract(self) -> None:
        roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
        drum = next((c for c in roster["characters"] if c["character_id"] == "drum"), None)
        self.assertIsNotNone(drum)
        self.assertEqual(drum["combat_role"], "monster")
        self.assertEqual(drum["map_sync_metrics"]["canvas_size_px"], [128, 96])
        self.assertEqual(drum["map_sync_metrics"]["foot_anchor_px"], [56, 84])
        self.assertEqual(drum["render_contract"]["locomotion"]["default_scale"], 2.5)
        self.assertEqual(drum["render_contract"]["locomotion"]["screen_speed_px_per_second"], 140)
        self.assertEqual(drum["render_contract"]["locomotion"]["speed_px_per_second"], 56.0)
        self.assertEqual(drum["render_contract"]["turning"]["method"], "instant_flip")
        self.assertEqual(drum["render_contract"]["projectile"]["projectile_clip"], "electric_orb_fx")
        self.assertEqual(drum["render_contract"]["projectile"]["release_frame"], 10)
        self.assertEqual(drum["render_contract"]["locomotion"]["clip"], "walk")
        self.assertIn("walk", drum["present_clips"])
        self.assertNotIn("attack_heavy", drum["present_clips"])
        self.assertEqual(
            drum["motion_quality"]["atlas_sha256"],
            hashlib.sha256(ATLAS_PATH.read_bytes()).hexdigest(),
        )

        export_data = json.loads(EXPORT_JSON.read_text(encoding="utf-8"))
        self.assertEqual(len(export_data["atlas"]["pages"]), 1)
        w, h = export_data["atlas"]["pages"][0]["size"]
        self.assertLessEqual(w, 4096)
        self.assertLessEqual(h, 4096)
        self.assertEqual(export_data["sampling"], "nearest")
        self.assertIn("walk", export_data["clips"])
        self.assertEqual(len(export_data["clips"]["walk"]["frames"]), 8)
        self.assertIn("teleport", export_data["clips"])
        self.assertIn("attack_light", export_data["clips"])
        self.assertNotIn("attack_heavy", export_data["clips"])
        self.assertIn("power_up", export_data["clips"])
        self.assertEqual(len(export_data["clips"]["power_up"]["frames"]), 11)
        self.assertIn("electric_orb_fx", export_data["clips"])
        self.assertEqual(
            export_data["render_contract"]["locomotion"]["default_scale"],
            2.5,
        )
        self.assertEqual(
            export_data["render_contract"]["locomotion"]["screen_speed_px_per_second"],
            140,
        )
        self.assertEqual(
            export_data["render_contract"]["locomotion"]["speed_px_per_second"],
            56.0,
        )
        tres = TRES_PATH.read_text(encoding="utf-8")
        self.assertIn('ExtResource("1_atlas00")', tres)
        self.assertIn('&"walk"', tres)
        self.assertIn('&"teleport"', tres)
        self.assertIn('&"electric_orb_fx"', tres)


if __name__ == "__main__":
    unittest.main()
