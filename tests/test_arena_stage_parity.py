import gzip
import hashlib
import http.server
import io
import json
import pathlib
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile

import numpy as np
from PIL import Image

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "preview"))
import server as preview_server  # noqa: E402


class ArenaStageParityTests(unittest.TestCase):
    def test_stage_spec_map_bezel_and_godot_settings_match_1_to_1(self) -> None:
        stage_path = REPO_ROOT / "assets" / "maps" / "rocky_plateau" / "arena-stage.json"
        self.assertTrue(stage_path.is_file(), f"Missing {stage_path}")
        stage = json.loads(stage_path.read_text(encoding="utf-8"))

        vp = stage["viewport"]
        self.assertEqual((vp["width"], vp["height"]), (1920, 1080))
        self.assertEqual(vp["aspect_ratio"], "16:9")
        self.assertEqual(vp["orientation"], "landscape")
        self.assertEqual(vp["stretch_mode"], "canvas_items")
        self.assertEqual(vp["stretch_aspect"], "expand")
        self.assertEqual(vp["stretch_scale_mode"], "fractional")
        self.assertEqual(vp["renderer"], "gl_compatibility")
        self.assertEqual(vp["handheld_orientation_code"], 0)

        profiles_path = REPO_ROOT / vp["device_profiles_path"]
        self.assertTrue(profiles_path.is_file(), f"Missing device profiles: {profiles_path}")
        profiles_doc = json.loads(profiles_path.read_text(encoding="utf-8"))
        profile_ids = {p["id"] for p in profiles_doc["profiles"]}
        for req_id in ("redmi_k70e", "android_20_9_1080", "fhd_16_9", "iphone_15_pro", "android_720p_20_9"):
            self.assertIn(req_id, profile_ids)

        gp = stage["gameplay"]
        self.assertEqual(gp["ground_y"], 840)
        self.assertEqual(gp["walkable_bounds_x"], [140, 1780])
        self.assertEqual(gp["player_spawn_x"], 560)
        self.assertEqual(gp["dummy_spawn_x"], 1360)
        self.assertEqual(gp["character_scale_default"], 2)
        self.assertEqual(gp["character_scale_options"], [1, 2, 3])
        self.assertEqual(gp["character_scale_min"], 0.5)
        self.assertEqual(gp["character_scale_max"], 3.0)
        self.assertFalse(gp["screen_shake_enabled"])
        self.assertFalse(gp["ground_shadow_ellipse_enabled"])
        self.assertEqual(gp["burrow_dust_scale_default"], 2.65)
        self.assertEqual(gp["burrow_dust_scale_options"], [1, 1.5, 2.25, 2.65])
        self.assertEqual(gp["flight"]["min_y"], 60)
        self.assertEqual(gp["flight"]["max_y"], 840)
        self.assertEqual(gp["flight"]["default_y"], 250)
        self.assertEqual(gp["flight"]["middle_offset_px"], -290)
        self.assertEqual(gp["texture_filter"], "nearest")

        # Verify sample background image dimensions & hash
        map_path = REPO_ROOT / stage["map"]["background_path"]
        self.assertTrue(map_path.is_file())
        with Image.open(map_path) as map_img:
            self.assertEqual(list(map_img.size), stage["map"]["source_size_px"])
            self.assertEqual(map_img.mode, "RGB")

        # Verify phone frame transparent opening is exact 1920 x 1080
        bezel_path = REPO_ROOT / stage["phone_bezel"]["repo_path"]
        self.assertTrue(bezel_path.is_file())
        with Image.open(bezel_path) as bz:
            self.assertEqual(list(bz.size), stage["phone_bezel"]["image_size_px"])
            self.assertEqual(bz.mode, "RGBA")
            arr = np.array(bz)[:, :, 3]
        hx, hy, hw, hh = stage["phone_bezel"]["screen_hole_px"]
        self.assertEqual((hw, hh), (1920, 1080))
        mid_row = arr[hy + hh // 2, :]
        mid_col = arr[:, hx + hw // 2]
        self.assertEqual(int(np.where(mid_row[: arr.shape[1] // 2] > 0)[0].max()) + 1, hx)
        self.assertEqual(int(np.where(mid_row[arr.shape[1] // 2 :] > 0)[0].min()) + arr.shape[1] // 2 - 1, hx + hw - 1)
        self.assertEqual(int(np.where(mid_col[: arr.shape[0] // 2] > 0)[0].max()) + 1, hy)
        self.assertEqual(int(np.where(mid_col[arr.shape[0] // 2 :] > 0)[0].min()) + arr.shape[0] // 2 - 1, hy + hh - 1)
        self.assertTrue(np.all(arr[hy : hy + hh, hx + 120 : hx + hw - 120] == 0))
        self.assertTrue(np.all(arr[hy + 120 : hy + hh - 120, hx : hx + hw] == 0))

        # Server parity + Godot ZIP
        parity = preview_server.verify_engine_localhost_parity()
        self.assertTrue(parity["ok"], parity)
        self.assertEqual(parity["checked_bundles"], len(json.loads((REPO_ROOT / "assets/roster.json").read_text())["characters"]))
        self.assertEqual(parity["finalized_characters"], len(json.loads((REPO_ROOT / "assets/roster.json").read_text())["characters"]))

        zf = zipfile.ZipFile(io.BytesIO(preview_server.build_godot_zip_bytes()))
        names = set(zf.namelist())
        for req in (
            "project.godot",
            "scenes/ArenaSandbox.tscn",
            "scenes/ArenaSandbox.gd",
            "scenes/UtilityAIController.gd",
            "assets/maps/rocky_plateau/arena-stage.json",
            "assets/maps/rocky_plateau/terrain.json",
            "assets/maps/rocky_plateau/tiles/ground_tileset.png",
            "assets/maps/rocky_plateau/parallax/wing_left.jpg",
            "assets/maps/rocky_plateau/parallax/wing_right.jpg",
            "assets/maps/rocky_plateau/fx/ground_dust.png",
            "assets/maps/rocky_plateau/rocky-plateau-bg.jpg",
        ):
            self.assertIn(req, names)

        terrain_path = REPO_ROOT / "assets" / "maps" / "rocky_plateau" / "terrain.json"
        terrain = json.loads(terrain_path.read_text(encoding="utf-8"))
        self.assertEqual(terrain["viewport"]["tile_px"], 32)
        self.assertEqual(len(terrain["platforms"]), 0)
        self.assertEqual(terrain["backdrop"]["mode"], "original_jpg")
        for img_rel in (
            terrain["tileset"]["path"],
            terrain["dust_fx"]["path"],
        ):
            with Image.open(REPO_ROOT / img_rel) as timg:
                self.assertEqual(timg.mode, "RGBA")
                a = np.array(timg)[:, :, 3]
                self.assertTrue(np.all(np.isin(a, [0, 255])), f"Soft/non-binary alpha in {img_rel}")

        stage_uai = payload_stage["gameplay"].get("utility_ai", {}) if "payload_stage" in locals() else json.loads(
            zf.read("assets/maps/rocky_plateau/arena-stage.json").decode("utf-8")
        )["gameplay"].get("utility_ai", {})
        self.assertEqual(stage_uai.get("close_edge_px"), 50)
        self.assertEqual(stage_uai.get("mid_max_edge_px"), 200)
        self.assertEqual(stage_uai.get("heavy_max_edge_px"), 200)
        self.assertEqual(stage_uai.get("attack_cooldown_s"), 1.0)
        self.assertEqual(stage_uai.get("light_hits_before_heavy"), 2)
        self.assertEqual(stage_uai.get("zone_width_max_px"), 500)
        self.assertEqual(stage_uai.get("special_roles", {}).get("chilopoda"), "burrow_far_laser_close")
        self.assertEqual(stage_uai.get("special_roles", {}).get("flight"), "hover_no_chase_ranged_far_melee_close")

    def test_http_server_serves_map_jpg_bezel_png_and_arena_stage_json(self) -> None:
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), preview_server.PreviewHandler)
        port = httpd.server_address[1]
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/bundles", timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                payload = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(payload["parity"]["ok"])
            self.assertEqual(payload["arena_stage"]["viewport"]["width"], 1920)
            self.assertEqual(payload["arena_stage"]["viewport"]["height"], 1080)

            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/assets/maps/rocky_plateau/rocky-plateau-bg.jpg", timeout=5
            ) as resp:
                self.assertEqual(resp.status, 200)
                self.assertEqual(resp.headers.get("Content-Type"), "image/jpeg")
                self.assertEqual(len(resp.read()), 174816)

            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/preview-assets/phone-frame-landscape-16x9.png", timeout=5
            ) as resp:
                self.assertEqual(resp.status, 200)
                self.assertEqual(resp.headers.get("Content-Type"), "image/png")
                self.assertEqual(len(resp.read()), 44372)

            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/preview-assets/../../AGENTS.md", timeout=5)
            self.assertEqual(ctx.exception.code, 404)
            ctx.exception.close()
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_preview_server_anti_hang_gzip_etag_tls_and_queue(self) -> None:
        self.assertGreaterEqual(preview_server.IPv4Server.request_queue_size, 64)
        self.assertGreaterEqual(preview_server.IPv6OnlyServer.request_queue_size, 64)
        httpd = preview_server.IPv4Server(("127.0.0.1", 0), preview_server.PreviewHandler)
        port = httpd.server_address[1]
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/bundles", timeout=5) as plain_resp:
                raw_len = len(plain_resp.read())

            gz_req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/bundles",
                headers={"Accept-Encoding": "gzip"},
            )
            with urllib.request.urlopen(gz_req, timeout=5) as gz_resp:
                self.assertEqual(gz_resp.status, 200)
                self.assertEqual(gz_resp.headers.get("Content-Encoding"), "gzip")
                gz_bytes = gz_resp.read()
            self.assertLess(len(gz_bytes), raw_len * 0.35)
            decoded = json.loads(gzip.decompress(gz_bytes).decode("utf-8"))
            self.assertTrue(decoded["parity"]["ok"])

            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/preview-assets/phone-frame-landscape-16x9.png", timeout=5
            ) as asset_resp:
                etag = asset_resp.headers.get("ETag")
                self.assertTrue(etag)
                asset_resp.read()

            etag_req = urllib.request.Request(
                f"http://127.0.0.1:{port}/preview-assets/phone-frame-landscape-16x9.png",
                headers={"If-None-Match": etag},
            )
            with self.assertRaises(urllib.error.HTTPError) as not_mod:
                urllib.request.urlopen(etag_req, timeout=5)
            self.assertEqual(not_mod.exception.code, 304)
            not_mod.exception.close()

            with urllib.request.urlopen(f"http://127.0.0.1:{port}/favicon.ico", timeout=5) as fav_resp:
                self.assertEqual(fav_resp.status, 204)
                self.assertIsNone(fav_resp.headers.get("Content-Length"))

            import http.client
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            try:
                conn.request("GET", "/assets/maps/rocky_plateau/tiles/ground_tileset.png")
                r1 = conn.getresponse()
                b1 = r1.read()
                self.assertEqual(r1.status, 200)
                self.assertGreater(len(b1), 1000)
                conn.request("GET", "/assets/maps/rocky_plateau/rocky-plateau-bg.jpg")
                r2 = conn.getresponse()
                b2 = r2.read()
                self.assertEqual(r2.status, 200)
                self.assertEqual(len(b2), 174816)
            finally:
                conn.close()

            t0 = time.monotonic()
            with socket.create_connection(("127.0.0.1", port), timeout=2.0) as tls_sock:
                tls_sock.sendall(b"\x16\x03\x01\x00\x20" + b"A" * 32)
                tail = tls_sock.recv(1024)
            elapsed = time.monotonic() - t0
            self.assertEqual(tail, b"")
            self.assertLess(elapsed, 0.5)
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_android_apk_download_endpoint_and_bundles_metadata(self) -> None:
        import http.client

        orig_apk_path = preview_server.ANDROID_APK_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_dir = pathlib.Path(tmpdir)
            missing_apk = tmp_dir / "missing.apk"
            sample_apk = tmp_dir / "dr7-studio-debug.apk"
            sample_bytes = (b"PK\x03\x04DR7_TEST_APK" * 300000)  # ~4.8 MB exercises chunked streaming path
            sample_apk.write_bytes(sample_bytes)
            expected_sha = hashlib.sha256(sample_bytes).hexdigest()

            httpd = preview_server.IPv4Server(("127.0.0.1", 0), preview_server.PreviewHandler)
            port = httpd.server_address[1]
            t = threading.Thread(target=httpd.serve_forever, daemon=True)
            t.start()
            try:
                preview_server.ANDROID_APK_PATH = missing_apk
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/bundles", timeout=5) as resp:
                    missing_bundles = json.loads(resp.read().decode("utf-8"))
                self.assertFalse(missing_bundles["android_apk"]["available"])
                with self.assertRaises(urllib.error.HTTPError) as not_found_ctx:
                    urllib.request.urlopen(f"http://127.0.0.1:{port}/api/download-android-debug.apk", timeout=5)
                self.assertEqual(not_found_ctx.exception.code, 404)
                not_found_ctx.exception.close()

                preview_server.ANDROID_APK_PATH = sample_apk
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/bundles", timeout=5) as resp:
                    ready_bundles = json.loads(resp.read().decode("utf-8"))
                apk_meta = ready_bundles["android_apk"]
                self.assertTrue(apk_meta["available"])
                self.assertEqual(apk_meta["filename"], "dr7-studio-debug.apk")
                self.assertEqual(apk_meta["download_url"], "/api/download-android-debug.apk")
                self.assertEqual(apk_meta["size_bytes"], len(sample_bytes))
                self.assertEqual(apk_meta["sha256"], expected_sha)

                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/download-android-debug.apk", timeout=10) as dl_resp:
                    self.assertEqual(dl_resp.status, 200)
                    self.assertEqual(dl_resp.headers.get("Content-Type"), "application/vnd.android.package-archive")
                    self.assertIn("dr7-studio-debug.apk", dl_resp.headers.get("Content-Disposition", ""))
                    self.assertEqual(int(dl_resp.headers.get("Content-Length", "0")), len(sample_bytes))
                    self.assertIsNone(dl_resp.headers.get("Content-Encoding"))
                    etag = dl_resp.headers.get("ETag")
                    self.assertTrue(etag)
                    dl_bytes = dl_resp.read()
                self.assertEqual(dl_bytes, sample_bytes)

                etag_req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/download-android-debug.apk",
                    headers={"If-None-Match": etag},
                )
                with self.assertRaises(urllib.error.HTTPError) as not_mod:
                    urllib.request.urlopen(etag_req, timeout=5)
                self.assertEqual(not_mod.exception.code, 304)
                not_mod.exception.close()

                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                try:
                    conn.request("HEAD", "/api/download-android-debug.apk")
                    head_resp = conn.getresponse()
                    head_body = head_resp.read()
                    self.assertEqual(head_resp.status, 200)
                    self.assertEqual(int(head_resp.getheader("Content-Length", "0")), len(sample_bytes))
                    self.assertEqual(head_body, b"")
                finally:
                    conn.close()
            finally:
                preview_server.ANDROID_APK_PATH = orig_apk_path
                httpd.shutdown()
                httpd.server_close()


if __name__ == "__main__":
    unittest.main()
