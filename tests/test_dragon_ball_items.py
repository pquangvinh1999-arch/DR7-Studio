import hashlib
import io
import json
import pathlib
import sys
import unittest
import zipfile

import numpy as np
from PIL import Image
from scipy import ndimage

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "preview"))
import server as preview_server  # noqa: E402


class DragonBallItemTests(unittest.TestCase):
    def test_catalog_and_godot_atlas_parity(self) -> None:
        parity = preview_server.verify_engine_localhost_parity()
        self.assertTrue(parity["ok"], msg=f"Parity errors: {parity['errors']}")

        items = preview_server.load_items()
        self.assertIn("dragon_balls", items["by_id"])
        db = items["by_id"]["dragon_balls"]
        self.assertEqual(db["frame_size"], [32, 32])
        self.assertEqual(db["map_anchor_px"], [16, 32])
        self.assertEqual(db["bag_anchor_px"], [16, 16])
        self.assertEqual(db["default_map_test_scale"], 1.0)
        self.assertEqual(db["atlas"]["pages"], 1)
        self.assertEqual(db["sparkle_fx"]["style"], "diagonal_body_sheen")
        self.assertFalse(db["sparkle_fx"]["show_in_bag"])
        self.assertTrue(db["sparkle_fx"]["show_on_map_after_roll"])
        self.assertEqual(db["drop_physics"]["jump_height_px"], 10.0)
        self.assertEqual(db["drop_physics"]["roll_distance_px"], 10.0)
        self.assertEqual(db["pickup_physics"]["duration_ticks"], 30)
        self.assertLess(db["pickup_physics"]["end_scale"], 0.1)

        # Standalone character discovery must NOT confuse items with roster fighters
        fighter_ids = {b["id"] for b in preview_server.discover_bundles()}
        self.assertNotIn("dragon_balls", fighter_ids)

        # Check 1..7 static variants + shared 60Hz diagonal sheen clip in .tres
        for n in range(1, 8):
            key = f"ball_{n:02d}"
            self.assertIn(key, db["animations"])
            self.assertEqual(len(db["animations"][key]["frames"]), 1)
            self.assertEqual(db["animations"][key]["speed_hz"], 60.0)
        self.assertIn("sparkle_fx", db["animations"])
        sp = db["animations"]["sparkle_fx"]
        self.assertTrue(sp["loop"])
        self.assertEqual(sp["speed_hz"], 60.0)
        self.assertEqual([f["duration_ticks"] for f in sp["frames"]], [3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 4.0, 50.0])

    def test_item_constitution_gate_rejects_incomplete_item(self) -> None:
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            tmp_items = tmp_path / "items"
            tmp_items.mkdir()
            shutil.copytree(REPO_ROOT / "assets" / "items" / "dragon_balls", tmp_items / "dragon_balls")
            bad_export = tmp_items / "dragon_balls" / "item-export.json"
            cat = json.loads((REPO_ROOT / "assets" / "items" / "catalog.json").read_text(encoding="utf-8"))
            cat["items"][0]["export_json"] = str(bad_export.relative_to(tmp_path))
            cat["items"][0]["atlas_path"] = str((tmp_items / "dragon_balls" / "godot" / "dragon_balls-atlas-00.png").relative_to(tmp_path))
            cat["items"][0]["godot_tres"] = str((tmp_items / "dragon_balls" / "godot" / "dragon_balls.tres").relative_to(tmp_path))
            cat["items"][0]["godot_prefab"] = ""

            orig_root, orig_cat = preview_server.REPO_ROOT, preview_server.CATALOG_JSON
            try:
                preview_server.REPO_ROOT = tmp_path
                preview_server.CATALOG_JSON = tmp_items / "catalog.json"
                base_export = json.loads(bad_export.read_text(encoding="utf-8"))
                cases = [
                    ("hide FX in bag", lambda d: d["sparkle_fx"].__setitem__("show_in_bag", True)),
                    ("diagonal_body_sheen", lambda d: d["sparkle_fx"].__setitem__("style", "sparkle")),
                    ("drop jump/roll", lambda d: d["drop_physics"].__setitem__("jump_height_px", 0.0)),
                    ("pickup physics", lambda d: d["pickup_physics"].__setitem__("end_scale", 1.5)),
                ]
                for err_substr, mutate in cases:
                    d = json.loads(json.dumps(base_export))
                    mutate(d)
                    bad_export.write_text(json.dumps(d), encoding="utf-8")
                    cat["items"][0]["export_sha256"] = hashlib.sha256(bad_export.read_bytes()).hexdigest()
                    (tmp_items / "catalog.json").write_text(json.dumps(cat), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, err_substr):
                        preview_server.load_items()
            finally:
                preview_server.REPO_ROOT = orig_root
                preview_server.CATALOG_JSON = orig_cat

    def test_1x_hard_alpha_zero_pockets_and_diagonal_sheen_bounds(self) -> None:
        item_dir = REPO_ROOT / "assets" / "items" / "dragon_balls" / "source" / "frames_1x"
        common_mask = np.ones((32, 32), dtype=bool)
        for n in range(1, 8):
            fp = item_dir / f"dragon_ball_{n:02d}.png"
            self.assertTrue(fp.is_file(), f"Missing {fp}")
            im = Image.open(fp).convert("RGBA")
            self.assertEqual(im.size, (32, 32))
            arr = np.asarray(im)
            alpha = arr[:, :, 3]
            self.assertTrue(np.isin(alpha, [0, 255]).all(), f"ball_{n:02d} must use hard 0/255 alpha")
            lbl, count = ndimage.label(alpha > 0)
            self.assertEqual(count, 1, f"ball_{n:02d} must have single connected shape (no speckles)")
            filled = ndimage.binary_fill_holes(alpha > 0)
            self.assertEqual(int(np.sum(filled ^ (alpha > 0))), 0, f"ball_{n:02d} must have 0 enclosed pockets")
            common_mask &= alpha > 0

        # Diagonal sheen frames 0..6 sweep top-left -> bottom-right strictly inside sphere; frame 7 is empty rest
        centers_u = []
        for j in range(7):
            sp_path = item_dir / f"sparkle_{j:02d}.png"
            sp_arr = np.asarray(Image.open(sp_path).convert("RGBA"))
            vis = sp_arr[:, :, 3] > 0
            self.assertTrue(vis.any(), f"sparkle_{j:02d} must contain diagonal sheen pixels")
            self.assertFalse((vis & ~common_mask).any(), f"sparkle_{j:02d} leaked outside common sphere mask")
            yy, xx = np.where(vis)
            centers_u.append(float(np.mean(xx + yy)))
        self.assertTrue(all(centers_u[k] < centers_u[k + 1] for k in range(6)), f"Sheen must sweep diagonally: {centers_u}")
        rest_arr = np.asarray(Image.open(item_dir / "sparkle_07.png").convert("RGBA"))
        self.assertEqual(int(np.sum(rest_arr[:, :, 3] > 0)), 0, "sparkle_07 rest frame must be empty")

    def test_shenron_summon_untouched_and_godot_zip_includes_items(self) -> None:
        seq_path = REPO_ROOT / "assets" / "rituals" / "shenron_summon" / "sequence.json"
        seq = json.loads(seq_path.read_text(encoding="utf-8"))
        atlas_path = REPO_ROOT / seq["atlas"]
        self.assertEqual(
            hashlib.sha256(atlas_path.read_bytes()).hexdigest(),
            "c82ec5e8460a2bf01ef515793e87cfdf2be96f448eeab1b914d9e9fec7215aba",
        )
        zbytes = preview_server.build_godot_zip_bytes()
        with zipfile.ZipFile(io.BytesIO(zbytes)) as zf:
            names = set(zf.namelist())
            self.assertIn("assets/items/catalog.json", names)
            self.assertIn("assets/items/dragon_balls/item-export.json", names)
            self.assertIn("assets/items/dragon_balls/godot/dragon_balls.tres", names)
            self.assertIn("assets/items/dragon_balls/godot/dragon_balls-atlas-00.png", names)
            self.assertIn("scenes/items/DragonBallItem2D.tscn", names)
            self.assertIn("scenes/items/DragonBallItem2D.gd", names)


if __name__ == "__main__":
    unittest.main()
