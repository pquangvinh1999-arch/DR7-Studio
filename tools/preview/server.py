#!/usr/bin/env python3
"""DR7-Studio — Unified Engine Parity & Human-Test Sandbox Server (localhost:8080).

Đọc trực tiếp CÙNG MỘT nguồn tài nguyên chuẩn với Godot 4 & Rust Core:
- assets/roster.json (chỉ hiển thị nhân vật đã hoàn thiện — finalized roster)
- assets/**/godot_bundle/godot/*.tres, *.tscn, *-atlas-*.png (kèm đối soát SHA-256 1:1)
- engines/benchmark_report.json & rust_combat_sim.wasm (Stress Test >2,000 CCU @ 60 FPS)
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import socket
import sys
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = REPO_ROOT / "assets"
PREVIEW_DIR = Path(__file__).resolve().parent
BENCHMARK_JSON = REPO_ROOT / "engines" / "benchmark_report.json"
ROSTER_JSON = ASSETS_DIR / "roster.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_tres(tres_path: Path) -> dict:
    """Parse Godot 4 SpriteFrames .tres file for exact AtlasTexture regions and animations."""
    text = tres_path.read_text(encoding="utf-8")

    ext_textures: dict[str, str] = {}
    for m in re.finditer(
        r'\[ext_resource\s+type="Texture2D"\s+path="([^"]+)"\s+id="([^"]+)"\]',
        text,
    ):
        ext_textures[m.group(2)] = m.group(1)

    sub_regions: dict[str, dict] = {}
    sub_blocks = re.split(r"(?=\[sub_resource\s+)", text)
    for blk in sub_blocks:
        m_id = re.match(r'\[sub_resource\s+type="AtlasTexture"\s+id="([^"]+)"\]', blk)
        if not m_id:
            continue
        sub_id = m_id.group(1)
        m_atlas = re.search(r'atlas\s*=\s*ExtResource\("([^"]+)"\)', blk)
        m_reg = re.search(
            r"region\s*=\s*Rect2\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)",
            blk,
        )
        if m_reg:
            atlas_id = m_atlas.group(1) if m_atlas else ""
            sub_regions[sub_id] = {
                "atlas_file": ext_textures.get(atlas_id, ""),
                "x": float(m_reg.group(1)),
                "y": float(m_reg.group(2)),
                "w": float(m_reg.group(3)),
                "h": float(m_reg.group(4)),
            }

    animations: dict[str, dict] = {}
    res_idx = text.find("[resource]")
    if res_idx != -1:
        res_text = text[res_idx:]
        anim_chunks = res_text.split('"frames": [')
        for chunk in anim_chunks[1:]:
            frames_part, _, rest = chunk.partition("],")
            frames_list = []
            for fm in re.finditer(
                r'"duration":\s*([-\d.]+)\s*,\s*"texture":\s*SubResource\("([^"]+)"\)',
                frames_part,
            ):
                dur_ticks = float(fm.group(1))
                sub_id = fm.group(2)
                reg = sub_regions.get(sub_id)
                if reg:
                    frames_list.append({
                        "sub_id": sub_id,
                        "duration_ticks": dur_ticks,
                        **reg,
                    })
            m_loop = re.search(r'"loop":\s*(true|false)', rest)
            m_name = re.search(r'"name":\s*&"([^"]+)"', rest)
            m_speed = re.search(r'"speed":\s*([-\d.]+)', rest)
            if m_name:
                anim_name = m_name.group(1)
                speed_hz = float(m_speed.group(1)) if m_speed else 60.0
                for idx, f_item in enumerate(frames_list):
                    f_item["duration_ms"] = (f_item["duration_ticks"] / speed_hz) * 1000.0
                    f_item["index"] = idx
                animations[anim_name] = {
                    "name": anim_name,
                    "loop": (m_loop.group(1) == "true") if m_loop else False,
                    "speed_hz": speed_hz,
                    "frames": frames_list,
                }

    return {
        "ext_textures": ext_textures,
        "sub_regions": sub_regions,
        "animations": animations,
    }


def parse_tscn(tscn_path: Path) -> dict:
    """Parse Godot 4 AnimatedSprite2D .tscn for offset, centered, autoplay."""
    if not tscn_path.exists():
        return {}
    text = tscn_path.read_text(encoding="utf-8")
    m_off = re.search(r"offset\s*=\s*Vector2\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)", text)
    m_cent = re.search(r"centered\s*=\s*(true|false)", text)
    m_auto = re.search(r'autoplay\s*=\s*"([^"]+)"', text)
    m_filt = re.search(r"texture_filter\s*=\s*(\d+)", text)
    return {
        "offset": [float(m_off.group(1)), float(m_off.group(2))] if m_off else [0.0, 0.0],
        "centered": (m_cent.group(1) == "true") if m_cent else False,
        "autoplay": m_auto.group(1) if m_auto else "",
        "texture_filter": int(m_filt.group(1)) if m_filt else 0,
    }


def discover_bundles() -> list[dict]:
    """Scan assets/**/engine-export.json and assemble full Engine-verified bundle descriptors."""
    bundles: list[dict] = []
    if not ASSETS_DIR.exists():
        return bundles

    for export_json_path in sorted(ASSETS_DIR.rglob("engine-export.json")):
        bundle_dir = export_json_path.parent
        godot_2d_dir = bundle_dir / "godot"
        if not godot_2d_dir.exists():
            continue

        tres_files = sorted(godot_2d_dir.glob("*.tres"))
        tscn_files = sorted(godot_2d_dir.glob("*.tscn"))
        if not tres_files:
            continue

        tres_path = tres_files[0]
        tscn_path = tscn_files[0] if tscn_files else godot_2d_dir / (tres_path.stem + ".tscn")

        try:
            export_meta = json.loads(export_json_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        tres_data = parse_tres(tres_path)
        tscn_data = parse_tscn(tscn_path)

        atlas_hashes: dict[str, str] = {}
        clips_meta = export_meta.get("clips", {})
        for anim_name, anim_obj in tres_data["animations"].items():
            cmeta = clips_meta.get(anim_name, {})
            anim_obj["events_ms"] = cmeta.get("events_ms", [])
            anim_obj["hitstop_ms"] = cmeta.get("hitstop_ms", 0)
            anim_obj["role"] = cmeta.get("role", "")
            for f_item in anim_obj["frames"]:
                atlas_disk = godot_2d_dir / f_item["atlas_file"]
                atlas_rel = atlas_disk.relative_to(REPO_ROOT).as_posix()
                f_item["atlas_url"] = "/" + atlas_rel
                if f_item["atlas_file"] not in atlas_hashes and atlas_disk.is_file():
                    atlas_hashes[f_item["atlas_file"]] = sha256_file(atlas_disk)

        # Unique ordered source regions (Frame 0..N-1) for interactive frame reference slider
        unique_regions = []
        seen_sub = set()
        for sub_id in sorted(tres_data["sub_regions"].keys()):
            if sub_id not in seen_sub:
                seen_sub.add(sub_id)
                reg = dict(tres_data["sub_regions"][sub_id])
                atlas_disk = godot_2d_dir / reg["atlas_file"]
                reg["sub_id"] = sub_id
                reg["atlas_url"] = "/" + atlas_disk.relative_to(REPO_ROOT).as_posix()
                unique_regions.append(reg)

        rel_bundle = bundle_dir.relative_to(REPO_ROOT).as_posix()
        rel_tscn = tscn_path.relative_to(REPO_ROOT).as_posix() if tscn_path.exists() else ""
        rel_tres = tres_path.relative_to(REPO_ROOT).as_posix()
        rel_export = export_json_path.relative_to(REPO_ROOT).as_posix()

        bundle_parent = bundle_dir.parent.name
        display_title = f"{export_meta.get('name', bundle_parent)} — Gộp Chung 1 Lớp Nguyên Bản"
        priority = 1

        bundles.append({
            "id": bundle_parent,
            "priority": priority,
            "title": display_title,
            "name": export_meta.get("name", bundle_parent),
            "bundle_dir": "res://" + rel_bundle,
            "scene_2d": "res://" + rel_tscn if rel_tscn else "",
            "frames_2d": "res://" + rel_tres,
            "export_json": "res://" + rel_export,
            "sha256_tres": sha256_file(tres_path),
            "sha256_atlases": atlas_hashes,
            "frame_size": export_meta.get("frame_size", [0, 0]),
            "anchor_px": export_meta.get("anchor_px", [0.0, 0.0]),
            "shadow": export_meta.get("shadow", None),
            "default_clip": export_meta.get("default_clip", ""),
            "render_contract": export_meta.get("render_contract"),
            "tscn": tscn_data,
            "unique_frames": unique_regions,
            "animations": tres_data["animations"],
        })

    bundles.sort(key=lambda b: (b["priority"], b["id"]))
    return bundles


def load_finalized_roster(bundles: list[dict] | None = None) -> dict:
    """Load assets/roster.json and filter strictly to finalized 1-Layer Combined characters."""
    if bundles is None:
        bundles = discover_bundles()
    by_id = {b["id"]: b for b in bundles}
    if not ROSTER_JSON.is_file():
        return {"schema": "dr7-studio.character_roster.v1", "characters": []}

    raw = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
    finalized = []
    for ch in raw.get("characters", []):
        if not str(ch.get("status", "")).startswith("finalized"):
            continue
        modes = ch.get("modes", {})
        c1 = modes.get("combined_1layer", {}).get("bundle_id")
        if c1 and c1 in by_id and "layered_3d_depth" not in modes:
            finalized.append(ch)
    raw["characters"] = finalized
    return raw


def build_setups(bundles: list[dict], roster: dict | None = None) -> list[dict]:
    """Return official 1-Layer Combined setups dynamically from finalized roster.json."""
    by_id = {b["id"]: b for b in bundles}
    if roster is None:
        roster = load_finalized_roster(bundles)
    out = []
    for ch in roster.get("characters", []):
        cid = ch.get("character_id", "")
        c1 = ch.get("modes", {}).get("combined_1layer", {})
        if c1.get("bundle_id") in by_id:
            out.append({
                "character_id": cid,
                "key": "combined_1layer",
                "arch": "combined",
                "title": c1.get("label", "Gộp Chung 1 Lớp Nguyên Bản (1 Quad / 1 Draw Call)"),
                "prefab_scene": c1.get("godot_prefab", ""),
                "combined_id": c1["bundle_id"],
            })
    return out


def verify_engine_localhost_parity() -> dict:
    """Verify 100% Zero-Drift Parity between Engine files (.tres/.tscn/PNG) and Localhost API."""
    bundles = discover_bundles()
    raw_roster = json.loads(ROSTER_JSON.read_text(encoding="utf-8")) if ROSTER_JSON.is_file() else {"characters": []}
    roster = load_finalized_roster(bundles)
    by_id = {b["id"]: b for b in bundles}
    errors: list[str] = []
    warnings: list[str] = []

    raw_chars = raw_roster.get("characters", [])
    finalized_chars = roster.get("characters", [])

    if not raw_chars and not bundles:
        warnings.append(
            "Danh sách nhân vật (roster.json) hiện đang rỗng (0 nhân vật) — Hệ thống sẵn sàng nhận Atlas mới từ Owner."
        )
    else:
        if len(raw_chars) != len(finalized_chars):
            finalized_ids = {c.get("character_id") for c in finalized_chars}
            for rc in raw_chars:
                rcid = rc.get("character_id", "unknown")
                if rcid not in finalized_ids and "layered_3d_depth" not in rc.get("modes", {}):
                    errors.append(
                        f"Nhân vật '{rcid}' chưa ở trạng thái finalized hoặc thiếu bundle combined_1layer hợp lệ."
                    )

    for raw_ch in raw_chars:
        if "layered_3d_depth" in raw_ch.get("modes", {}):
            errors.append(
                f"Nhân vật '{raw_ch.get('character_id')}' chứa cấu hình 'layered_3d_depth' (Hướng 2) đã bị bãi bỏ theo Hiến pháp AGENTS.md!"
            )

    # Ensure NO unreferenced draft bundles pollute assets/ outside finalized roster
    referenced_ids: set[str] = set()
    for ch in roster.get("characters", []):
        modes = ch.get("modes", {})
        if "combined_1layer" in modes:
            referenced_ids.add(modes["combined_1layer"]["bundle_id"])
            prefab = REPO_ROOT / modes["combined_1layer"]["godot_prefab"].replace("res://", "")
            if not prefab.is_file():
                errors.append(f"Thiếu prefab Godot: {prefab}")
        else:
            errors.append(f"Nhân vật '{ch.get('character_id')}' thiếu cấu hình chuẩn 'combined_1layer'.")

        missing_clips = ch.get("missing_provisional_clips", [])
        if missing_clips:
            warnings.append(
                f"Nhân vật '{ch['character_id']}' hiện có {len(ch.get('present_clips', []))} hoạt ảnh "
                f"({', '.join(ch.get('present_clips', []))}); thiếu các clip tham chiếu tạm thời: "
                f"{', '.join(missing_clips)}. "
                f"Owner đã loại riêng nhân vật: {', '.join(k for k in missing_clips if k in ch.get('not_applicable_clips', {})) or 'chưa có'}."
            )

    stray = sorted(set(by_id.keys()) - referenced_ids)
    if stray:
        errors.append(f"Phát hiện bundle nháp/ngoài danh sách hoàn thiện trong assets/: {stray}")

    for bid, b in by_id.items():
        ax, ay = b["anchor_px"]
        ox, oy = b["tscn"].get("offset", [0.0, 0.0])
        if abs(ox + ax) > 0.01 or abs(oy + ay) > 0.01:
            errors.append(f"Lệch tâm chân anchor_px vs tscn offset ở {bid}: anchor={b['anchor_px']} offset={[ox, oy]}")
        if not b["sha256_atlases"]:
            errors.append(f"Thiếu mã băm SHA-256 atlas PNG ở {bid}")

    return {
        "ok": len(errors) == 0,
        "checked_bundles": len(bundles),
        "finalized_characters": len(roster.get("characters", [])),
        "errors": errors,
        "warnings": warnings,
    }


def build_godot_zip_bytes() -> bytes:
    """Build a lightweight, ready-to-open Godot 4 project ZIP on the fly."""
    buf = io.BytesIO()
    include_paths = [
        REPO_ROOT / "project.godot",
        REPO_ROOT / "scenes",
        REPO_ROOT / "tests",
        ROSTER_JSON,
    ]
    if ASSETS_DIR.exists():
        for export_json in sorted(ASSETS_DIR.rglob("engine-export.json")):
            include_paths.append(export_json.parent)
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in include_paths:
            if not item.exists():
                continue
            if item.is_file():
                zf.write(item, item.relative_to(REPO_ROOT).as_posix())
            else:
                for sub in sorted(item.rglob("*")):
                    if sub.is_file() and not sub.name.endswith((".pyc", ".uid")):
                        zf.write(sub, sub.relative_to(REPO_ROOT).as_posix())
    return buf.getvalue()


class PreviewHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[preview] " + (fmt % args) + "\n")

    def _send_bytes(self, status: int, content_type: str, data: bytes, extra_headers: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        if getattr(self, "command", "GET") != "HEAD":
            self.wfile.write(data)

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        req_path = unquote(parsed.path)

        if req_path in ("/", "/index.html"):
            html_file = PREVIEW_DIR / "index.html"
            self._send_bytes(200, "text/html; charset=utf-8", html_file.read_bytes())
            return

        if req_path == "/rust_combat_sim.wasm":
            wasm_file = PREVIEW_DIR / "rust_combat_sim.wasm"
            if wasm_file.is_file():
                self._send_bytes(200, "application/wasm", wasm_file.read_bytes())
            else:
                self._send_bytes(404, "text/plain; charset=utf-8", b"WASM not built")
            return

        if req_path == "/api/bundles":
            bundles = discover_bundles()
            roster = load_finalized_roster(bundles)
            parity = verify_engine_localhost_parity()
            payload = {
                "project_name": "DR7-Studio — Engine Parity & Human Test Workbench",
                "bundles": bundles,
                "roster": roster,
                "setups": build_setups(bundles, roster),
                "parity": parity,
            }
            data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self._send_bytes(200, "application/json; charset=utf-8", data)
            return

        if req_path == "/api/benchmarks":
            if BENCHMARK_JSON.is_file():
                self._send_bytes(200, "application/json; charset=utf-8", BENCHMARK_JSON.read_bytes())
            else:
                self._send_bytes(404, "application/json; charset=utf-8", b'{"error":"not_found"}')
            return

        if req_path == "/api/download-godot-pack.zip":
            zbytes = build_godot_zip_bytes()
            self._send_bytes(
                200,
                "application/zip",
                zbytes,
                {"Content-Disposition": 'attachment; filename="DR7-Studio-Godot4-Pack.zip"'},
            )
            return

        if req_path.startswith("/assets/"):
            target = (REPO_ROOT / req_path.lstrip("/")).resolve()
            if not str(target).startswith(str(ASSETS_DIR.resolve())) or not target.is_file():
                self._send_bytes(404, "text/plain; charset=utf-8", b"Not found")
                return
            ext = target.suffix.lower()
            ctype = {
                ".png": "image/png",
                ".json": "application/json; charset=utf-8",
                ".tres": "text/plain; charset=utf-8",
                ".tscn": "text/plain; charset=utf-8",
            }.get(ext, "application/octet-stream")
            self._send_bytes(200, ctype, target.read_bytes())
            return

        self._send_bytes(404, "text/plain; charset=utf-8", b"Not found")


class IPv4Server(ThreadingHTTPServer):
    address_family = socket.AF_INET
    allow_reuse_address = True
    daemon_threads = True


class IPv6OnlyServer(ThreadingHTTPServer):
    address_family = socket.AF_INET6
    allow_reuse_address = True
    daemon_threads = True

    def server_bind(self) -> None:
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        except OSError:
            pass
        super().server_bind()


def create_server(port: int) -> ThreadingHTTPServer:
    ipv4_server = IPv4Server(("0.0.0.0", port), PreviewHandler)
    try:
        ipv6_server = IPv6OnlyServer(("::", port), PreviewHandler)
        t6 = threading.Thread(target=ipv6_server.serve_forever, name="preview-ipv6", daemon=True)
        t6.start()
    except OSError:
        pass
    return ipv4_server


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = create_server(port)
    print(f"DR7-Studio Engine Parity & Human-Test Server listening on http://localhost:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
