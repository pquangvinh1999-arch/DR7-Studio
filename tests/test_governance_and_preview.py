import io
import json
import pathlib
import re
import subprocess
import sys
import unittest
import zipfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "preview"))
import server as preview_server  # noqa: E402


class GovernanceAndPreviewTests(unittest.TestCase):
    def test_single_agents_md_and_dual_cli_compatibility(self) -> None:
        agent_md = REPO_ROOT / "agent.md"
        agents_md = REPO_ROOT / "AGENTS.md"
        dot_agents = REPO_ROOT / ".agents"
        dot_agent = REPO_ROOT / ".agent"

        self.assertFalse(agent_md.exists() or agent_md.is_symlink(), "Redundant agent.md must be removed")
        self.assertTrue(agents_md.is_file(), "Single canonical AGENTS.md must exist for AGY CLI & OpenAI Codex")
        self.assertFalse(agents_md.is_symlink(), "AGENTS.md must be a standalone file, not a dangling symlink")
        self.assertLessEqual(agents_md.stat().st_size, 24000, "Must fit AGY CLI 24KB inline rule limit")

        text = agents_md.read_text(encoding="utf-8")
        for keyword in (
            "Supabase",
            "Godot",
            "Rust",
            "GDExtension",
            "Combined 1-Layer",
            "2,000",
            "60 FPS",
            "state.json",
            "skills.md",
            "lerning.md",
            "loop.sh",
            "Human Test",
        ):
            self.assertIn(keyword, text)

        self.assertTrue(dot_agents.is_dir())
        self.assertTrue(dot_agent.exists())
        self.assertEqual(dot_agent.resolve(), dot_agents.resolve(), ".agent must alias .agents")

        expected_skills = {
            "codeart2d",
            "generate2dmap",
            "generate2dmedia",
            "generate2dsprite",
            "video2dsprite",
            "dr7-governance",
        }
        for sk in expected_skills:
            self.assertTrue((dot_agents / "skills" / sk / "SKILL.md").is_file(), f"Missing SKILL.md for {sk}")
            self.assertTrue((dot_agents / "skills" / sk / "agents" / "openai.yaml").is_file(), f"Missing openai.yaml for {sk}")

    def test_old_test_characters_completely_purged(self) -> None:
        assets_dir = REPO_ROOT / "assets"
        scenes_dir = REPO_ROOT / "scenes"
        tools_dir = REPO_ROOT / "tools"
        for p in list(assets_dir.rglob("*")) + list(scenes_dir.rglob("*")):
            low = p.name.lower()
            self.assertNotIn("songoku", low, f"Old Son Goku test asset must be deleted: {p}")
            self.assertNotIn("sphere_of_destruction", low, f"Old purple test asset must be deleted: {p}")
            self.assertNotIn("modularauracharacter", low, f"Deprecated 3-layer rig script must be deleted: {p}")
            self.assertNotIn("trunks", low, f"Deleted Trunks asset/scene must not remain: {p}")
        self.assertFalse(
            (tools_dir / "pipeline" / "build_trunks_rage.py").exists(),
            "Deleted Trunks extraction script must not remain",
        )

    def test_skills_md_remains_empty_until_owner_approval_and_lerning_md_populated(self) -> None:
        skills_txt = (REPO_ROOT / "skills.md").read_text(encoding="utf-8")
        m_sk = re.search(r"<!-- SKILLS_ENTRIES_START -->(.*?)<!-- SKILLS_ENTRIES_END -->", skills_txt, re.S)
        self.assertIsNotNone(m_sk)
        sk_entries = re.findall(r"^###\s+\[", m_sk.group(1), re.M)
        self.assertEqual(len(sk_entries), 0, "skills.md must remain empty until Owner confirms Human Test")

        lerning_txt = (REPO_ROOT / "lerning.md").read_text(encoding="utf-8")
        m_lr = re.search(r"<!-- LERNING_ENTRIES_START -->(.*?)<!-- LERNING_ENTRIES_END -->", lerning_txt, re.S)
        self.assertIsNotNone(m_lr)
        lr_entries = re.findall(r"^###\s+\[LRN-\d+\]", m_lr.group(1), re.M)
        self.assertGreaterEqual(len(lr_entries), 6, "lerning.md should record verified bug fixes LRN-001..006")

    def test_version_sync_across_all_manifests(self) -> None:
        ver = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(ver, r"^\d+\.\d+\.\d+$")
        state = json.loads((REPO_ROOT / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["project"]["version"], ver)
        pg = (REPO_ROOT / "project.godot").read_text(encoding="utf-8")
        self.assertIn(f'config/version="{ver}"', pg)
        cargo_txt = (REPO_ROOT / "engines" / "rust_combat_sim" / "Cargo.toml").read_text(encoding="utf-8")
        self.assertIn(f'version = "{ver}"', cargo_txt)

    def test_engine_localhost_zero_drift_parity_and_dynamic_roster(self) -> None:
        parity = preview_server.verify_engine_localhost_parity()
        self.assertTrue(parity["ok"], msg=f"Parity errors: {parity['errors']}")
        roster = preview_server.load_finalized_roster()
        chars = roster.get("characters", [])
        self.assertEqual(parity["finalized_characters"], len(chars))
        self.assertEqual(parity["checked_bundles"], len(chars))

        if not chars:
            self.assertEqual(preview_server.discover_bundles(), [])
            self.assertEqual(preview_server.build_setups([]), [])
            self.assertGreaterEqual(len(parity["warnings"]), 1, "Empty roster should report readiness warning")
        else:
            for ch in chars:
                self.assertNotIn("layered_3d_depth", ch["modes"], "Multi-layer mode (Hướng 2) must be removed")
                self.assertIn("combined_1layer", ch["modes"])
                self.assertEqual(ch["pixel_sharpness_metrics"]["enclosed_key_pockets"], 0)
                self.assertEqual(ch["pixel_sharpness_metrics"]["opaque_key_px"], 0)

    def test_hybrid_engine_benchmark_report_and_wasm_artifact(self) -> None:
        bench_path = REPO_ROOT / "engines" / "benchmark_report.json"
        self.assertTrue(bench_path.is_file())
        bench = json.loads(bench_path.read_text(encoding="utf-8"))
        self.assertIn("shared_asset_under_test", bench)
        self.assertIsNone(bench["shared_asset_under_test"].get("bundle_id"))
        self.assertGreaterEqual(len(bench["rust_engine"]["benchmarks"]), 3)
        self.assertGreaterEqual(len(bench["godot_engine"]["benchmarks"]), 6)
        wasm_path = REPO_ROOT / "tools" / "preview" / "rust_combat_sim.wasm"
        self.assertTrue(wasm_path.is_file())
        self.assertGreater(wasm_path.stat().st_size, 1024)

    def test_loop_sh_check_and_agy_hook(self) -> None:
        res_chk = subprocess.run([str(REPO_ROOT / "loop.sh"), "check"], capture_output=True, text=True, check=False)
        self.assertEqual(res_chk.returncode, 0, msg=res_chk.stderr)

        res_hk = subprocess.run(
            [str(REPO_ROOT / "loop.sh"), "--agy-session-start"],
            input="{}",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res_hk.returncode, 0, msg=res_hk.stderr)
        payload = json.loads(res_hk.stdout)
        self.assertIn("injectSteps", payload)
        self.assertIn("AGENTS.md", payload["injectSteps"][0]["systemMessage"]["systemMessage"])

    def test_preview_server_zip(self) -> None:
        zbytes = preview_server.build_godot_zip_bytes()
        with zipfile.ZipFile(io.BytesIO(zbytes)) as zf:
            names = set(zf.namelist())
            self.assertIn("project.godot", names)
            self.assertIn("assets/roster.json", names)
            self.assertIn("scenes/CharacterFighter2D.gd", names)
            self.assertIn("tests/SkillAnimator2D.gd", names)
            self.assertNotIn("scenes/Trunks_Rage.tscn", names)

    def test_frontend_js_wasm_exports_3tabs_and_n_character_roster(self) -> None:
        res = subprocess.run(
            ["node", str(REPO_ROOT / "tests" / "test_frontend_wasm_e2e.mjs")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 0, msg=f"Frontend E2E failed:\n{res.stdout}\n{res.stderr}")


if __name__ == "__main__":
    unittest.main()
