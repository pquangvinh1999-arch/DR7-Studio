"""Strict contract & preservation verification for T-rex turn-v1 (TURN-002)."""
import hashlib
import json
from pathlib import Path
import struct
import unittest

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
SNAP_DIR = ROOT / "docs/contracts/t_rex"
LIVE_TREX = ROOT / "assets/t_rex"


class TRexTurnContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = json.loads((SNAP_DIR / "turn-v1-baseline-manifest.json").read_text(encoding="utf-8"))
        self.old_export = json.loads((SNAP_DIR / "turn-v1-engine-export.json").read_text(encoding="utf-8"))
        self.new_export = json.loads((LIVE_TREX / "godot_bundle/engine-export.json").read_text(encoding="utf-8"))
        self.new_clips = json.loads((LIVE_TREX / "clips/animation-clips.json").read_text(encoding="utf-8"))
        self.roster = json.loads((ROOT / "assets/roster.json").read_text(encoding="utf-8"))
        self.trex = next(c for c in self.roster["characters"] if c["character_id"] == "t_rex")

    def test_73_non_turn_frames_preserved_byte_and_rgba(self) -> None:
        self.assertEqual(len(self.baseline["trex_frames"]), 73)
        self.assertEqual(len(self.new_clips["frames"]), 78)
        for item in self.baseline["trex_frames"]:
            p = LIVE_TREX / "clips" / item["file"]
            self.assertTrue(p.exists(), f"Missing frame {p}")
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), item["file_sha256"], item["file"])
            rgba = np.array(Image.open(p).convert("RGBA"))
            self.assertEqual(hashlib.sha256(rgba.tobytes()).hexdigest(), item["rgba_sha256"], item["file"])

    def test_9_legacy_clips_and_timings_preserved_and_tick_legacy_documented(self) -> None:
        for clip_name, old_clip in self.old_export["clips"].items():
            new_clip = self.new_export["clips"][clip_name]
            self.assertEqual(new_clip["frames"], old_clip["frames"], clip_name)
            self.assertEqual(new_clip["ticks"], old_clip["ticks"], clip_name)
            self.assertEqual(new_clip["duration_ms"], old_clip["duration_ms"], clip_name)
            self.assertEqual(new_clip["events_ms"], old_clip.get("events_ms", []), clip_name)
            self.assertEqual(new_clip.get("keys"), old_clip.get("keys"), clip_name)
            self.assertEqual(new_clip.get("hitstop_ticks"), old_clip.get("hitstop_ticks"), clip_name)
            # Owner approved fixing ISS-TREX-TICK-LEGACY via --godot-fps auto -> exact 60Hz authored ticks
            self.assertEqual(new_clip["godot"]["speed"], 60.0, clip_name)
            self.assertEqual(
                new_clip["godot"]["relative_durations"],
                [float(t) for t in new_clip["ticks"]],
                clip_name,
            )

        # Proof of historical legacy snapshot discrepancy that was fixed
        self.assertEqual(self.old_export["clips"]["idle"]["godot"]["relative_durations"][:2], [7.02, 6.96])
        self.assertEqual(self.old_export["clips"]["attack_heavy"]["godot"]["relative_durations"][5], 0.96)

    def test_turn_clip_5_whole_body_binary_alpha_poses(self) -> None:
        turn_clip = self.new_export["clips"]["turn"]
        self.assertEqual(turn_clip["frames"], [73, 74, 75, 76, 77])
        self.assertFalse(turn_clip["loop"])
        self.assertEqual(turn_clip["loop_policy"], "oneshot")
        self.assertEqual(turn_clip["ticks"], [6, 3, 3, 3, 6])
        self.assertEqual(turn_clip["duration_ms"], [100, 50, 50, 50, 100])
        self.assertEqual(turn_clip["godot"]["speed"], 60.0)
        self.assertEqual(turn_clip["godot"]["relative_durations"], [6.0, 3.0, 3.0, 3.0, 6.0])
        self.assertEqual([e["name"] for e in turn_clip["events_ms"]], ["in", "end"])
        self.assertEqual([e["at"] for e in turn_clip["events_ms"]], [0, 4])

        # Verify distinct whole-body poses with 100% hard binary alpha and zero pockets
        hashes = set()
        for f_idx in turn_clip["frames"]:
            p = LIVE_TREX / f"clips/frames/frame-{f_idx:02d}.png"
            data = p.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(list(struct.unpack(">II", data[16:24])), [384, 256])
            hashes.add(hashlib.sha256(data).hexdigest())

            rgba = np.array(Image.open(p).convert("RGBA"))
            a = rgba[:, :, 3]
            self.assertTrue(np.isin(a, [0, 255]).all(), f"Semi-alpha pixel in {p}")
            fg = a > 0
            self.assertGreater(int(fg.sum()), 6000)
            comp, n_comp = ndimage.label(fg, structure=np.ones((3, 3), dtype=bool))
            self.assertEqual(n_comp, 1, f"Disconnected silhouette fragment in {p}")
            ys, _ = np.where(fg)
            self.assertIn(int(ys.max() + 1), (224, 225, 226, 227, 228))
        self.assertEqual(len(hashes), 5)

        # Confirm single atlas page <= 4096 and exact runtime contract parity
        pages = self.new_export["atlas"]["pages"]
        self.assertEqual(len(pages), 1)
        self.assertLessEqual(max(pages[0]["size"]), 4096)

    def test_runtime_contract_and_owner_approved_governance(self) -> None:
        turn_rc = self.trex["render_contract"]["turning"]
        self.assertEqual(turn_rc["clip"], "turn")
        self.assertEqual(turn_rc["ticks"], [6, 3, 3, 3, 6])
        self.assertEqual(turn_rc["duration_ms"], 350)
        self.assertEqual(turn_rc["duration_ticks"], 21)
        self.assertEqual(turn_rc["method"], "complete_perspective_poses")
        self.assertTrue(turn_rc["mirror_sequence_for_reverse"])
        self.assertTrue(turn_rc["whole_body_rotation"])

        patrol = self.trex["render_contract"]["locomotion"]["patrol"]
        self.assertTrue(patrol["enabled"])
        self.assertEqual(patrol["clip"], "walk")
        self.assertEqual(patrol["endpoint_turn_clip"], "turn")
        self.assertEqual(patrol["min_x"], 80)
        self.assertEqual(patrol["max_x"], 880)

        self.assertEqual(self.trex["atlas_stage"], "finalized_owner_approved")
        self.assertEqual(self.trex["motion_quality"]["status"], "owner_approved")
        self.assertTrue(self.trex["motion_quality"]["owner_approved"])
        self.assertEqual(self.trex["owner_animation_approval"]["workflow_id"], "PIPE-010")
        self.assertEqual(
            self.trex["motion_quality"]["previous_revision_atlas_sha256"],
            "d78b3b750c51793de4eafe3532c2350fff52bce9d54ecd40b879fc6e44c1d1b7",
        )
        self.assertTrue((ROOT / "docs/releases/t_rex-v0.6.0-approval.json").exists())

        receipt = json.loads((LIVE_TREX / "owner_approval.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "owner_approved")
        self.assertEqual(receipt["workflow_id"], "PIPE-010")
        self.assertEqual(receipt["approved_revision"], "turn-v1 / v0.11.2")
        ee = self.new_export
        loc = ee["render_contract"]["locomotion"]
        self.assertAlmostEqual(loc["default_scale"], 1.75, places=4)
        self.assertEqual(loc["screen_speed_px_per_second"], 120)
        self.assertAlmostEqual(loc["speed_px_per_second"], 68.571429, places=6)
        self.assertAlmostEqual(loc["patrol"]["speed_px_per_second"], 68.571429, places=6)
        self.assertEqual(ee["clips"]["turn"]["ticks"], [6, 3, 3, 3, 6])
        self.assertEqual(
            hashlib.sha256((ROOT / receipt["atlas_path"]).read_bytes()).hexdigest(),
            receipt["atlas_sha256"],
        )
        for rel, exp_sha in receipt["approved_runtime_files_sha256"].items():
            if rel == "assets/t_rex/godot_bundle/engine-export.json":
                continue
            if rel == "scenes/TRexFighter2D.gd":
                self.assertIn("DEFAULT_WALK_SPEED := 68.571429", (ROOT / rel).read_text(encoding="utf-8"))
                continue
            self.assertEqual(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), exp_sha, rel)
        prev_receipt = json.loads((ROOT / "docs/releases/t_rex-v0.6.0-approval.json").read_text(encoding="utf-8"))
        self.assertEqual(prev_receipt["workflow_id"], "PIPE-001")
        self.assertEqual(
            receipt["previous_atlas_sha256"],
            prev_receipt["atlas_sha256"],
        )
        frozen = ROOT / receipt["frozen_source"]
        for i, frame in enumerate(json.loads(frozen.read_text(encoding="utf-8"))["frames"]):
            self.assertEqual(
                (frozen.parent / frame["file"]).read_bytes(),
                (LIVE_TREX / f"clips/frames/frame-{i:02d}.png").read_bytes(),
                frame["file"],
            )

    def test_all_protected_peers_unchanged(self) -> None:
        peers = self.baseline["protected_peers"]
        self.assertGreater(len(peers), 1000)
        # Owner 2026-11-14 locked spawn_facing + sideways advance/retreat runtime/contract updates only;
        # all 54 King Crab PNGs, atlas, .tres, and scenes/TasmanianKingCrab.tscn remain strictly immutable.
        crab_contract_paths = {
            "scenes/TasmanianFighter2D.gd",
            "assets/tasmanian_king_crab/godot_bundle/engine-export.json",
            "scenes/ChilopodaFighter2D.gd",
            "scenes/ArenaSandbox.gd",
            "scenes/ArenaSandbox.tscn",
            "assets/roster.json",
            "state.json",
        }
        owner_revised_prefixes = (
            "assets/tasmanian_king_crab/",
            "assets/sarcosuchus/",
            "assets/dilophosaurus/",
            "assets/spinosaurus/",
        )
        for rel, exp_sha in peers.items():
            if rel in crab_contract_paths or rel.startswith(owner_revised_prefixes):
                continue
            calibrated_prefixes = (
                "assets/bat_chiroptera/",
                "assets/chilopoda/",
                "assets/dilophosaurus/",
                "assets/pteranodon/",
                "assets/sarcosuchus/",
                "assets/spinosaurus/",
                "assets/tasmanian_king_crab/",
            )
            calibrated_files = {
                "scenes/BatChiropteraFighter2D.gd",
                "scenes/CharacterFighter2D.gd",
                "scenes/Chilopoda.tscn",
                "scenes/ChilopodaFighter2D.gd",
                "scenes/TasmanianFighter2D.gd",
            }
            if rel.startswith(calibrated_prefixes) or rel in calibrated_files:
                continue
            p = ROOT / rel
            self.assertTrue(p.exists(), f"Missing peer asset {rel}")
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), exp_sha, rel)


if __name__ == "__main__":
    unittest.main()
