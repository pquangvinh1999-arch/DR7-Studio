#!/usr/bin/env python3
"""DR7-Studio — Unified Engine Parity & Human-Test Sandbox Server (localhost:8080).

Đọc trực tiếp CÙNG MỘT nguồn tài nguyên chuẩn với Godot 4 & Rust Core:
- assets/roster.json (chỉ hiển thị nhân vật đã hoàn thiện — finalized roster)
- assets/**/godot_bundle/godot/*.tres, *.tscn, *-atlas-*.png (kèm đối soát SHA-256 1:1)
- engines/benchmark_report.json & rust_combat_sim.wasm (Stress Test >2,000 CCU @ 60 FPS)
"""

from __future__ import annotations

import datetime
import gzip
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
ITEMS_DIR = ASSETS_DIR / "items"
CATALOG_JSON = ITEMS_DIR / "catalog.json"
PREVIEW_DIR = Path(__file__).resolve().parent
BENCHMARK_JSON = REPO_ROOT / "engines" / "benchmark_report.json"
ROSTER_JSON = ASSETS_DIR / "roster.json"
WEB_EXPORT_DIR = REPO_ROOT / "build" / "web"
ANDROID_APK_PATH = REPO_ROOT / "build" / "android" / "dr7-studio-debug.apk"
REVIEW_ROOT = REPO_ROOT / "review"
_APK_SHA256_CACHE: dict[tuple[int, int], str] = {}


def load_review_content() -> dict:
    """Load provisional Human Test assets separately from the release roster."""
    roster_path = REVIEW_ROOT / "review-roster.json"
    if not roster_path.is_file():
        return {"roster": {"schema": "dr7-studio.review_roster.v1", "characters": []}, "bundles": []}
    bundle_dir = REVIEW_ROOT / "floating_camera/godot_bundle"
    export_path = bundle_dir / "engine-export.json"
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    export = json.loads(export_path.read_text(encoding="utf-8"))
    source = REVIEW_ROOT / "floating_camera/source/FloatingCamera.gif"
    ch = roster["characters"][0]
    if sha256_file(source) != ch["canonical_identity"]["sha256"]:
        raise ValueError("Review source SHA-256 mismatch")
    for item in export["files"]:
        if sha256_file(bundle_dir / item["path"]) != item["sha256"]:
            raise ValueError(f"Review bundle SHA-256 mismatch: {item['path']}")
    godot_dir = bundle_dir / "godot"
    tres_path = godot_dir / "floating_camera.tres"
    atlas_path = godot_dir / "floating_camera-atlas-00.png"
    if sha256_file(atlas_path) != ch["review_atlas_sha256"]:
        raise ValueError("Review roster atlas SHA-256 mismatch")
    parsed = parse_tres(tres_path)
    atlas_url = "/review/floating_camera/godot_bundle/godot/floating_camera-atlas-00.png"
    for anim in parsed["animations"].values():
        for frame in anim["frames"]:
            frame["atlas_url"] = atlas_url
    bundle = {
        "id": "floating_camera_review", "priority": 2,
        "title": "Floating Camera · Quái Human Test",
        "name": "floating_camera", "bundle_dir": "res://review/floating_camera/godot_bundle",
        "scene_2d": "res://review/floating_camera/FloatingCamera.tscn",
        "frames_2d": "res://review/floating_camera/godot_bundle/godot/floating_camera.tres",
        "export_json": "res://review/floating_camera/godot_bundle/engine-export.json",
        "sha256_tres": sha256_file(tres_path),
        "sha256_atlases": {atlas_path.name: sha256_file(atlas_path)},
        "frame_size": export["frame_size"], "anchor_px": export["anchor_px"],
        "default_clip": export["default_clip"],
        "render_contract": export["render_contract"],
        "tscn": parse_tscn(godot_dir / "floating_camera.tscn"),
        "unique_frames": [], "animations": parsed["animations"],
        "review_status": "human_test_pending",
    }
    return {"roster": roster, "bundles": [bundle]}


def get_android_apk_info(apk_path: Path | None = None) -> dict:
    target = apk_path if apk_path is not None else ANDROID_APK_PATH
    if not target.is_file():
        return {
            "available": False,
            "filename": target.name,
            "download_url": "/api/download-android-debug.apk",
        }
    st = target.stat()
    cache_key = (int(st.st_size), int(st.st_mtime_ns))
    sha = _APK_SHA256_CACHE.get(cache_key)
    if sha is None:
        h = hashlib.sha256()
        with target.open("rb") as fh:
            while True:
                chunk = fh.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
        sha = h.hexdigest()
        _APK_SHA256_CACHE.clear()
        _APK_SHA256_CACHE[cache_key] = sha
    built_at = datetime.datetime.fromtimestamp(st.st_mtime, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "available": True,
        "filename": target.name,
        "download_url": "/api/download-android-debug.apk",
        "size_bytes": int(st.st_size),
        "size_mb": round(st.st_size / (1024.0 * 1024.0), 1),
        "sha256": sha,
        "built_at_utc": built_at,
    }


def load_rituals() -> dict:
    path = ASSETS_DIR / "rituals/shenron_summon/sequence.json"
    if not path.is_file():
        return {}
    sequence = json.loads(path.read_text())
    atlas = REPO_ROOT / sequence["atlas"]
    if sha256_file(atlas) != sequence["atlas_sha256"]:
        raise ValueError("Summon atlas hash mismatch")
    if sequence.get("reveal"):
        reveal = sequence["reveal"]
        if sha256_file(REPO_ROOT / reveal["mask"]) != reveal["mask_sha256"]:
            raise ValueError("Summon dissolve mask hash mismatch")
    return {"shenron_summon": sequence}


def load_items() -> dict:
    """Load game-item catalog + .tres animation specs with strict SHA-256 Engine parity."""
    if not CATALOG_JSON.is_file():
        return {"schema": "dr7-studio.item_catalog.v1", "items": [], "by_id": {}}
    catalog = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    by_id: dict[str, dict] = {}
    enriched_entries: list[dict] = []
    for entry in catalog.get("items", []):
        item_id = entry.get("item_set_id", "")
        export_rel = str(entry["export_json"]).replace("res://", "")
        export_file = REPO_ROOT / export_rel
        if not export_file.is_file():
            raise ValueError(f"Missing item export JSON: {entry['export_json']}")
        if sha256_file(export_file) != entry.get("export_sha256"):
            raise ValueError(f"Item export SHA-256 mismatch for {item_id}")
        export_meta = json.loads(export_file.read_text(encoding="utf-8"))

        atlas_rel = str(entry["atlas_path"]).replace("res://", "")
        atlas_file = REPO_ROOT / atlas_rel
        if not atlas_file.is_file():
            raise ValueError(f"Missing item atlas PNG: {entry['atlas_path']}")
        atlas_sha = sha256_file(atlas_file)
        if atlas_sha != entry.get("atlas_sha256") or atlas_sha != export_meta.get("atlas", {}).get("sha256"):
            raise ValueError(f"Item atlas SHA-256 mismatch for {item_id}")

        tres_rel = str(entry["godot_tres"]).replace("res://", "")
        tres_file = REPO_ROOT / tres_rel
        if not tres_file.is_file():
            raise ValueError(f"Missing item SpriteFrames .tres: {entry['godot_tres']}")
        tres_sha = sha256_file(tres_file)
        if tres_sha != export_meta.get("godot", {}).get("frames_tres_sha256"):
            raise ValueError(f"Item .tres SHA-256 mismatch for {item_id}")

        prefab_rel = str(entry.get("godot_prefab", "")).replace("res://", "")
        if prefab_rel and not (REPO_ROOT / prefab_rel).is_file():
            raise ValueError(f"Missing item Godot prefab: {prefab_rel}")

        tres_data = parse_tres(tres_file)
        tres_dir = tres_file.parent
        for anim_obj in tres_data["animations"].values():
            for f_item in anim_obj["frames"]:
                disk = (tres_dir / f_item["atlas_file"]).resolve()
                f_item["atlas_url"] = "/" + disk.relative_to(REPO_ROOT).as_posix()

        # Constitutional Item Completeness Gate (AGENTS.md Diep/Dieu 7.5):
        # Every build under assets/items/ must expose: static bag icon (FX hidden),
        # diagonal full-body sheen FX, drop jump+roll physics, and shrink-to-collector pickup.
        if export_meta.get("atlas", {}).get("pages") != 1:
            raise ValueError(f"Item {item_id} must pack onto 1 PNG atlas page")
        if not export_meta.get("bag_anchor_px") or not export_meta.get("map_anchor_px"):
            raise ValueError(f"Item {item_id} missing bag_anchor_px or map_anchor_px")
        sp_meta = export_meta.get("sparkle_fx", {})
        if sp_meta.get("style") != "diagonal_body_sheen":
            raise ValueError(f"Item {item_id} must use diagonal_body_sheen FX (got {sp_meta.get('style')!r})")
        if sp_meta.get("show_in_bag") is not False or sp_meta.get("show_on_map_after_roll") is not True:
            raise ValueError(f"Item {item_id} must hide FX in bag and start sheen after drop roll")
        sp_anim = tres_data["animations"].get(sp_meta.get("clip", "sparkle_fx"))
        if not sp_anim or not sp_anim.get("frames") or sp_anim.get("speed_hz") != 60.0:
            raise ValueError(f"Item {item_id} missing 60Hz diagonal sheen animation in .tres")
        dp = export_meta.get("drop_physics", {})
        if (
            float(dp.get("jump_height_px", 0)) <= 0
            or float(dp.get("roll_distance_px", 0)) <= 0
            or int(dp.get("rise_ticks", 0)) <= 0
            or int(dp.get("roll_ticks", 0)) <= 0
            or dp.get("start_sheen_after_roll") is not True
        ):
            raise ValueError(f"Item {item_id} missing mandatory drop jump/roll physics")
        pp = export_meta.get("pickup_physics", {})
        if int(pp.get("duration_ticks", 0)) <= 0 or float(pp.get("end_scale", 1.0)) >= float(pp.get("start_scale", 1.0)):
            raise ValueError(f"Item {item_id} missing mandatory shrink-to-collector pickup physics")
        item_root = export_file.parent
        for req_dir in ("source", "clips"):
            if not (item_root / req_dir / ".gdignore").is_file():
                raise ValueError(f"Item {item_id} missing {req_dir}/.gdignore")

        merged = {
            **entry,
            **export_meta,
            "sha256_tres": tres_sha,
            "sha256_atlas": atlas_sha,
            "atlas_url": "/" + atlas_file.relative_to(REPO_ROOT).as_posix(),
            "animations": tres_data["animations"],
        }
        by_id[item_id] = merged
        enriched_entries.append(entry)
    return {
        "schema": catalog.get("schema", "dr7-studio.item_catalog.v1"),
        "items": enriched_entries,
        "by_id": by_id,
    }


def verify_motion_quality() -> dict:
    """Keep anatomical acceptance separate from technical parity."""
    try:
        from .motion_quality import assess_motion_quality
    except ImportError:
        from motion_quality import assess_motion_quality
    roster = json.loads(ROSTER_JSON.read_text())
    records = {}
    errors = []
    for ch in roster.get("characters", []):
        cid = ch["character_id"]
        bid = ch["modes"]["combined_1layer"]["bundle_id"]
        atlas = ASSETS_DIR / bid / "godot_bundle" / "godot" / (bid + "-atlas-00.png")
        digest = sha256_file(atlas) if atlas.is_file() else "missing"
        receipt = ASSETS_DIR / bid / "owner_approval.json"
        approval = json.loads(receipt.read_text()) if receipt.is_file() else {}
        if (not ch.get("motion_quality") and approval.get("status") == "owner_approved"
                and approval.get("atlas_sha256") == digest):
            result = {"ok_for_human_test": True, "release_approved": True,
                      "status": "owner_approved", "errors": []}
        else:
            result = assess_motion_quality(ch.get("motion_quality"), digest, ch.get("render_contract"))
        records[cid] = result
        errors.extend(cid + ": " + e for e in result["errors"])
    return {"ok_for_human_test": not errors, "release_approved": all(
        r["release_approved"] for r in records.values()), "characters": records, "errors": errors}


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

    try:
        load_rituals()
    except (ValueError, OSError, KeyError) as exc:
        errors.append("Summon contract/atlas: " + str(exc))
    try:
        load_items()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        errors.append("Item catalog/atlas: " + str(exc))
    errors.extend(verify_arena_stage_parity())
    return {
        "ok": len(errors) == 0,
        "checked_bundles": len(bundles),
        "finalized_characters": len(roster.get("characters", [])),
        "errors": errors,
        "warnings": warnings,
    }


def load_arena_stage() -> dict:
    """Load the Single-Source-of-Truth Landscape 16:9 (1920x1080) stage spec."""
    stage_path = ASSETS_DIR / "maps" / "rocky_plateau" / "arena-stage.json"
    if not stage_path.is_file():
        return {}
    try:
        return json.loads(stage_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def verify_arena_stage_parity() -> list[str]:
    """Verify 1:1 viewport, map asset, phone bezel, and Godot 4 scene parity."""
    errs: list[str] = []
    stage = load_arena_stage()
    if not stage:
        return ["Missing or invalid assets/maps/rocky_plateau/arena-stage.json"]

    vp = stage.get("viewport", {})
    if vp.get("width") != 1920 or vp.get("height") != 1080:
        errs.append(f"arena-stage viewport must be 1920x1080, got {vp.get('width')}x{vp.get('height')}")

    map_cfg = stage.get("map", {})
    bg_rel = map_cfg.get("background_path", "")
    bg_file = REPO_ROOT / bg_rel if bg_rel else None
    if not bg_file or not bg_file.is_file():
        errs.append(f"Missing sample map background: {bg_rel}")
    else:
        actual_sha = hashlib.sha256(bg_file.read_bytes()).hexdigest()
        if actual_sha != map_cfg.get("sha256"):
            errs.append(f"Sample map sha256 mismatch: {actual_sha} != {map_cfg.get('sha256')}")

    bezel_cfg = stage.get("phone_bezel", {})
    bezel_rel = bezel_cfg.get("repo_path", "")
    bezel_file = REPO_ROOT / bezel_rel if bezel_rel else None
    if not bezel_file or not bezel_file.is_file():
        errs.append(f"Missing phone bezel overlay: {bezel_rel}")
    else:
        bezel_sha = hashlib.sha256(bezel_file.read_bytes()).hexdigest()
        if bezel_sha != bezel_cfg.get("sha256"):
            errs.append(f"Phone bezel sha256 mismatch: {bezel_sha} != {bezel_cfg.get('sha256')}")

    pg_path = REPO_ROOT / "project.godot"
    if not pg_path.is_file():
        errs.append("Missing project.godot")
    else:
        pg = pg_path.read_text(encoding="utf-8")
        expected_lines = [
            f"window/size/viewport_width={vp.get('width', 1920)}",
            f"window/size/viewport_height={vp.get('height', 1080)}",
            f'window/stretch/mode="{vp.get("stretch_mode", "canvas_items")}"',
            f'window/stretch/aspect="{vp.get("stretch_aspect", "expand")}"',
            f'window/stretch/scale_mode="{vp.get("stretch_scale_mode", "fractional")}"',
            f"window/handheld/orientation={vp.get('handheld_orientation_code', 0)}",
            f'renderer/rendering_method="{vp.get("renderer", "gl_compatibility")}"',
            'run/main_scene="res://scenes/ArenaSandbox.tscn"',
        ]
        for needle in expected_lines:
            if needle not in pg:
                errs.append(f"project.godot missing 1:1 stage setting: {needle}")

    profiles_rel = vp.get("device_profiles_path", "")
    profiles_file = REPO_ROOT / profiles_rel if profiles_rel else None
    if not profiles_file or not profiles_file.is_file():
        errs.append(f"Missing device profiles spec: {profiles_rel}")

    terrain = load_map_terrain()
    if not terrain:
        errs.append("Missing or invalid assets/maps/rocky_plateau/terrain.json")
    else:
        bd = terrain.get("backdrop") or {}
        if bd.get("bg_path"):
            bg_orig = REPO_ROOT / str(bd.get("bg_path", ""))
            if not bg_orig.is_file():
                errs.append(f"Missing terrain backdrop image: {bd.get('bg_path')}")
            elif sha256_file(bg_orig) != bd.get("sha256"):
                errs.append("Terrain backdrop SHA-256 mismatch")
        for wkey in ("wing_left", "wing_right"):
            winfo = bd.get(wkey) or {}
            if winfo:
                wfile = REPO_ROOT / str(winfo.get("path", ""))
                if not wfile.is_file():
                    errs.append(f"Missing terrain {wkey}: {winfo.get('path')}")
                elif sha256_file(wfile) != winfo.get("sha256"):
                    errs.append(f"Terrain {wkey} SHA-256 mismatch")
        for pid, pinfo in (terrain.get("parallax") or {}).items():
            pfile = REPO_ROOT / str(pinfo.get("path", ""))
            if not pfile.is_file():
                errs.append(f"Missing terrain parallax layer {pid}: {pinfo.get('path')}")
            elif sha256_file(pfile) != pinfo.get("sha256"):
                errs.append(f"Terrain parallax SHA-256 mismatch for {pid}")
        for section_key in ("tileset", "platforms_sheet", "dust_fx"):
            sinfo = terrain.get(section_key) or {}
            if not sinfo:
                if section_key != "platforms_sheet":
                    errs.append(f"Missing terrain {section_key} entry")
                continue
            sfile = REPO_ROOT / str(sinfo.get("path", ""))
            if not sfile.is_file():
                errs.append(f"Missing terrain {section_key}: {sinfo.get('path')}")
            elif sha256_file(sfile) != sinfo.get("sha256"):
                errs.append(f"Terrain {section_key} SHA-256 mismatch")

    for sc_rel in (
        "scenes/ArenaSandbox.tscn",
        "scenes/ArenaSandbox.gd",
        "scenes/SkillAnimator2D.gd",
        "scenes/runtime/DisplayPolicy.gd",
        "scenes/runtime/TouchHudOverlay.gd",
        "scenes/net/NetworkTransport.gd",
        "scenes/net/WebSocketTransport.gd",
        "scenes/net/ZoneClientSync.gd",
    ):
        if not (REPO_ROOT / sc_rel).is_file():
            errs.append(f"Missing Godot arena scene/runtime file: {sc_rel}")
    return errs


def load_device_profiles() -> dict:
    p = ASSETS_DIR / "maps" / "rocky_plateau" / "device-profiles.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_map_terrain() -> dict:
    p = ASSETS_DIR / "maps" / "rocky_plateau" / "terrain.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_godot_zip_bytes() -> bytes:
    """Build a lightweight, ready-to-open Godot 4 project ZIP on the fly."""
    buf = io.BytesIO()
    include_paths = [
        REPO_ROOT / "project.godot",
        REPO_ROOT / "scenes",
        REPO_ROOT / "tests",
        ASSETS_DIR / "maps",
        ASSETS_DIR / "items",
        ASSETS_DIR / "rituals",
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
                        rel_str = sub.relative_to(REPO_ROOT).as_posix()
                        if any(skip in rel_str for skip in ("/godot-sprite3d/", "/aseprite/", "/source/")):
                            continue
                        zf.write(sub, rel_str)
    return buf.getvalue()


class PreviewHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def setup(self) -> None:
        super().setup()
        try:
            self.connection.settimeout(45.0)
            self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass

    def handle_one_request(self) -> None:
        try:
            if hasattr(self.rfile, "peek"):
                head = self.rfile.peek(2)
                if not head or head.startswith(b"\x16"):
                    self.close_connection = True
                    return
            self.raw_requestline = self.rfile.readline(65537)
            if not self.raw_requestline:
                self.close_connection = True
                return
            # Silently close TLS ClientHello probes (\x16...) without waiting for headers/errors
            if self.raw_requestline.startswith(b"\x16"):
                self.close_connection = True
                return
            if len(self.raw_requestline) > 65536:
                self.requestline = ""
                self.request_version = ""
                self.command = ""
                self.send_error(414)
                return
            if not self.parse_request():
                return
            mname = "do_" + self.command
            if not hasattr(self, mname):
                self.send_error(501, f"Unsupported method ({self.command})")
                return
            method = getattr(self, mname)
            method()
            self.wfile.flush()
        except (TimeoutError, socket.timeout, ConnectionResetError, BrokenPipeError):
            self.close_connection = True

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[preview] " + (fmt % args) + "\n")

    def _file_etag(self, file_path: Path) -> str:
        st = file_path.stat()
        return f'"{st.st_size}-{st.st_mtime_ns}"'

    def _send_file(
        self,
        content_type: str,
        file_path: Path,
        extra_headers: dict | None = None,
        *,
        cache_control: str = "no-cache",
        compress: bool = False,
    ) -> None:
        etag = self._file_etag(file_path)
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", cache_control)
            self.send_header("Connection", "close" if self.close_connection else "keep-alive")
            self.end_headers()
            return
        headers = {"ETag": etag}
        if extra_headers:
            headers.update(extra_headers)
        size_bytes = file_path.stat().st_size
        if compress or size_bytes < 4 * 1024 * 1024:
            self._send_bytes(
                200,
                content_type,
                file_path.read_bytes(),
                extra_headers=headers,
                cache_control=cache_control,
                compress=compress,
            )
            return
        self.send_response(200)
        self.send_header("Cache-Control", cache_control)
        if self.close_connection:
            self.send_header("Connection", "close")
        else:
            self.send_header("Connection", "keep-alive")
            self.send_header("Keep-Alive", "timeout=30")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(size_bytes))
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        if getattr(self, "command", "GET") != "HEAD" and size_bytes > 0:
            try:
                with file_path.open("rb") as fh:
                    while True:
                        chunk = fh.read(262144)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                self.close_connection = True

    def _send_bytes(
        self,
        status: int,
        content_type: str,
        data: bytes,
        extra_headers: dict | None = None,
        *,
        cache_control: str = "no-store, no-cache, must-revalidate",
        compress: bool = False,
    ) -> None:
        payload = data
        is_gzip = False
        if status not in (204, 304) and compress and len(data) >= 1024 and "gzip" in self.headers.get("Accept-Encoding", "").lower():
            payload = gzip.compress(data, compresslevel=5)
            is_gzip = True
        self.send_response(status)
        self.send_header("Cache-Control", cache_control)
        if self.close_connection:
            self.send_header("Connection", "close")
        else:
            self.send_header("Connection", "keep-alive")
            self.send_header("Keep-Alive", "timeout=30")
        if status not in (204, 304):
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
        if is_gzip:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        if status not in (204, 304) and getattr(self, "command", "GET") != "HEAD" and payload:
            try:
                self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                self.close_connection = True

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        req_path = unquote(parsed.path)

        if req_path == "/favicon.ico":
            self._send_bytes(204, "image/x-icon", b"", cache_control="public, max-age=86400")
            return

        if req_path in ("/", "/index.html"):
            html_file = PREVIEW_DIR / "index.html"
            self._send_bytes(200, "text/html; charset=utf-8", html_file.read_bytes(), compress=True)
            return

        if req_path == "/rust_combat_sim.wasm":
            wasm_file = PREVIEW_DIR / "rust_combat_sim.wasm"
            if wasm_file.is_file():
                self._send_file("application/wasm", wasm_file, compress=True)
            else:
                self._send_bytes(404, "text/plain; charset=utf-8", b"WASM not built")
            return

        if req_path == "/api/bundles":
            bundles = discover_bundles()
            roster = load_finalized_roster(bundles)
            parity = verify_engine_localhost_parity()
            godot_web_index = REPO_ROOT / "build" / "web" / "index.html"
            payload = {
                "project_name": "DR7-Studio — Engine Parity & Human Test Workbench",
                "bundles": bundles,
                "roster": roster,
                "setups": build_setups(bundles, roster),
                "arena_stage": load_arena_stage(),
                "terrain": load_map_terrain(),
                "device_profiles": load_device_profiles(),
                "godot_web_ready": godot_web_index.is_file(),
                "android_apk": get_android_apk_info(),
                "rituals": load_rituals(),
                "items": load_items(),
                "parity": parity,
                "motion_quality": verify_motion_quality(),
                "review": load_review_content(),
            }
            data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self._send_bytes(200, "application/json; charset=utf-8", data, compress=True)
            return

        if req_path.startswith("/godot-web/"):
            web_root = (REPO_ROOT / "build" / "web").resolve()
            rel_name = req_path[len("/godot-web/"):].lstrip("/") or "index.html"
            target = (web_root / rel_name).resolve()
            if not str(target).startswith(str(web_root)) or not target.is_file():
                self._send_bytes(404, "text/plain; charset=utf-8", b"Godot Web export not built. Run ./loop.sh web-export")
                return
            ext = target.suffix.lower()
            ctype = {
                ".html": "text/html; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".wasm": "application/wasm",
                ".pck": "application/octet-stream",
                ".png": "image/png",
                ".svg": "image/svg+xml",
                ".json": "application/json; charset=utf-8",
            }.get(ext, "application/octet-stream")
            self._send_file(ctype, target, compress=ext in (".html", ".js", ".wasm", ".svg", ".json"))
            return

        if req_path == "/api/benchmarks":
            if BENCHMARK_JSON.is_file():
                self._send_bytes(200, "application/json; charset=utf-8", BENCHMARK_JSON.read_bytes(), compress=True)
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

        if req_path == "/api/download-android-debug.apk":
            if not ANDROID_APK_PATH.is_file():
                self._send_bytes(404, "text/plain; charset=utf-8", b"Android APK not built. Run ./loop.sh apk-debug")
                return
            self._send_file(
                "application/vnd.android.package-archive",
                ANDROID_APK_PATH,
                extra_headers={
                    "Content-Disposition": f'attachment; filename="{ANDROID_APK_PATH.name}"',
                    "X-Content-Type-Options": "nosniff",
                },
                cache_control="no-cache",
                compress=False,
            )
            return

        if req_path.startswith("/preview-assets/"):
            preview_assets_dir = (REPO_ROOT / "tools" / "preview" / "assets").resolve()
            rel_name = req_path[len("/preview-assets/"):].lstrip("/")
            target = (preview_assets_dir / rel_name).resolve()
            if not str(target).startswith(str(preview_assets_dir)) or not target.is_file():
                self._send_bytes(404, "text/plain; charset=utf-8", b"Not found")
                return
            ext = target.suffix.lower()
            ctype = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".json": "application/json; charset=utf-8",
            }.get(ext, "application/octet-stream")
            self._send_file(ctype, target, compress=ext == ".json")
            return

        if req_path.startswith("/assets/"):
            target = (REPO_ROOT / req_path.lstrip("/")).resolve()
            if not str(target).startswith(str(ASSETS_DIR.resolve())) or not target.is_file():
                self._send_bytes(404, "text/plain; charset=utf-8", b"Not found")
                return
            ext = target.suffix.lower()
            ctype = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".json": "application/json; charset=utf-8",
                ".tres": "text/plain; charset=utf-8",
                ".tscn": "text/plain; charset=utf-8",
            }.get(ext, "application/octet-stream")
            self._send_file(ctype, target, compress=ext in (".json", ".tres", ".tscn"))
            return

        if req_path.startswith("/review/"):
            target = (REPO_ROOT / req_path.lstrip("/")).resolve()
            if not str(target).startswith(str(REVIEW_ROOT.resolve())) or target.suffix.lower() != ".png" or not target.is_file():
                self._send_bytes(404, "text/plain; charset=utf-8", b"Not found")
                return
            self._send_file("image/png", target)
            return

        self._send_bytes(404, "text/plain; charset=utf-8", b"Not found")


class IPv4Server(ThreadingHTTPServer):
    address_family = socket.AF_INET
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 128


class IPv6OnlyServer(ThreadingHTTPServer):
    address_family = socket.AF_INET6
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 128

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
