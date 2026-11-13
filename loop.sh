#!/usr/bin/env bash
# ==============================================================================
# DR7-Studio — Unified Agent Governance, Parity Check & CI/CD Test Loop (loop.sh)
# Compatible with Antigravity CLI (agy) & OpenAI Codex CLI (codex)
# ==============================================================================
set -euo pipefail

export PATH="$HOME/.cargo/bin:$PATH"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

CMD="${1:-status}"

case "$CMD" in
  --agy-session-start)
    # Consume stdin safely per AGY hooks.json SessionStart contract and emit valid JSON
    cat >/dev/null || true
    python3 - "$ROOT_DIR" << 'PY'
import json, pathlib, re, sys

root = pathlib.Path(sys.argv[1])
state_file = root / "state.json"
skills_file = root / "skills.md"
lerning_file = root / "lerning.md"

focus_summary = "Unknown"
active_task = "N/A"
open_cnt = 0
ver = "0.0.0"
if state_file.exists():
    st = json.loads(state_file.read_text(encoding="utf-8"))
    ver = st.get("project", {}).get("version", ver)
    cf = st.get("current_focus", {})
    active_task = cf.get("active_task_id", "N/A")
    focus_summary = cf.get("summary", "")
    open_cnt = len(st.get("open_issues", []))

def count_entries(md_path: pathlib.Path, start_tag: str, end_tag: str) -> int:
    if not md_path.exists():
        return 0
    txt = md_path.read_text(encoding="utf-8")
    m = re.search(re.escape(start_tag) + r"(.*?)" + re.escape(end_tag), txt, re.S)
    if not m:
        return 0
    return len(re.findall(r"^###\s+\[", m.group(1), re.M))

sk_cnt = count_entries(skills_file, "<!-- SKILLS_ENTRIES_START -->", "<!-- SKILLS_ENTRIES_END -->")
lr_cnt = count_entries(lerning_file, "<!-- LERNING_ENTRIES_START -->", "<!-- LERNING_ENTRIES_END -->")

msg = (
    f"[DR7-Studio v{ver} Bootstrap] "
    f"BẮT BUỘC tuân thủ 'AGENTS.md' & 'state.json' (Task hiện tại: {active_task} | Open issues: {open_cnt}). "
    f"Trạng thái: {focus_summary} "
    f"| Quy tắc phân biệt & đọc file: "
    f"(1) 'skills.md' ({sk_cnt} quy trình end-to-end từ Atlas -> Hoạt ảnh đã được Owner duyệt) KHÁC với '.agents/skills/*' (công cụ xử lý sprite cấp thấp); "
    f"(2) Đọc 'lerning.md' ({lr_cnt} bài học lỗi đã fix) trước khi xử lý sprite/code; "
    f"(3) Mọi hoạt ảnh phải pass test Engine rồi đồng bộ 1:1 SHA-256 ra localhost:8080 cho Human Test; "
    f"(4) Cập nhật 'state.json' sau mỗi task và chạy './loop.sh test'."
)
print(json.dumps({"injectSteps": [{"systemMessage": {"systemMessage": msg}}]}, ensure_ascii=False))
PY
    ;;

  status)
    python3 - "$ROOT_DIR" << 'PY'
import json, pathlib, re, sys

root = pathlib.Path(sys.argv[1])
st = json.loads((root / "state.json").read_text(encoding="utf-8"))

def count_entries(md_path: pathlib.Path, start_tag: str, end_tag: str) -> int:
    txt = md_path.read_text(encoding="utf-8")
    m = re.search(re.escape(start_tag) + r"(.*?)" + re.escape(end_tag), txt, re.S)
    return len(re.findall(r"^###\s+\[", m.group(1), re.M)) if m else 0

sk_cnt = count_entries(root / "skills.md", "<!-- SKILLS_ENTRIES_START -->", "<!-- SKILLS_ENTRIES_END -->")
lr_cnt = count_entries(root / "lerning.md", "<!-- LERNING_ENTRIES_START -->", "<!-- LERNING_ENTRIES_END -->")

proj = st["project"]
cf = st["current_focus"]
print("======================================================================")
print(f" DR7-STUDIO STATUS — v{proj['version']} ({st['updated_at']})")
print("======================================================================")
print(f"• Mục tiêu dự án : {proj['name']} | Mobile: {', '.join(proj['target_platforms'])}")
print(f"• Hiệu năng      : {proj.get('performance_target', '60 FPS @ >2,000 real-time combat users')}")
print(f"• Backend        : {proj['backend']}")
print(f"• Engine         : [{proj['engine_evaluation']['status']}] {', '.join(proj['engine_evaluation']['candidates'])}")
print(f"• Task hiện tại  : {cf['active_task_id']} [{cf['status']}]")
print(f"  -> {cf['summary']}")
print(f"• Open Issues    : {len(st.get('open_issues', []))} vấn đề đang mở trong state.json")
print("----------------------------------------------------------------------")
print(" QUY TẮC BẮT BUỘC KHI NÀO ĐỌC / GHI CÁC FILE BỘ NHỚ:")
print("  1. [BẮT BUỘC MỌI PHIÊN] AGENTS.md (duy nhất, không giữ agent.md dư thừa) & state.json")
print(f"  2. [QUY TRÌNH ATLAS -> HOẠT ẢNH] skills.md (Hiện có: {sk_cnt} quy trình Owner đã duyệt):")
print("     -> KHÔNG nhầm với '.agents/skills/*' (skill công cụ tách nền/đóng gói sprite cấp thấp).")
print("     -> Chỉ GHI vào skills.md sau khi Owner nghiệm thu Human Test thành công.")
print(f"  3. [BÀI HỌC SỬA LỖI KỸ THUẬT] lerning.md (Hiện có: {lr_cnt} bài học lỗi):")
print("     -> Đọc trước khi code / sửa sprite; GHI ngay sau khi fix xong lỗi mới có kiểm chứng.")
print("======================================================================")
PY
    ;;

  check)
    echo "[loop.sh] Đang kiểm tra Hiến pháp AGENTS.md, đồng bộ Engine ⇄ Localhost 1:1 và bộ nhớ dự án..."
    python3 - "$ROOT_DIR" << 'PY'
import json, pathlib, re, subprocess, sys

root = pathlib.Path(sys.argv[1])
errors = []

# 1. Single canonical AGENTS.md (ensure redundant agent.md is removed!)
if (root / "agent.md").exists() or (root / "agent.md").is_symlink():
    errors.append("Phát hiện file dư thừa 'agent.md' — chỉ giữ duy nhất 'AGENTS.md' cho cả AGY CLI và OpenAI Codex.")

required_files = [
    "VERSION",
    "AGENTS.md",
    "state.json",
    "skills.md",
    "lerning.md",
    "loop.sh",
    "assets/roster.json",
    ".agents/.gdignore",
    ".agents/hooks.json",
    ".agents/skills/dr7-governance/SKILL.md",
    ".agents/skills/dr7-governance/agents/openai.yaml",
]
for rel in required_files:
    if not (root / rel).exists():
        errors.append(f"Thiếu file bắt buộc: {rel}")

dot_agent = root / ".agent"
if not dot_agent.exists() or dot_agent.resolve() != (root / ".agents").resolve():
    errors.append("Thư mục tương thích .agent chưa liên kết (symlink) chuẩn sang .agents")

# 2. Rule size limits (AGY <= 24,000 bytes, Codex <= 32,768 bytes)
if (root / "AGENTS.md").is_file():
    sz = (root / "AGENTS.md").stat().st_size
    if sz > 24000:
        errors.append(f"AGENTS.md vượt giới hạn 24,000 bytes của AGY CLI ({sz} bytes)")
    if sz < 500:
        errors.append("AGENTS.md quá ngắn, thiếu các điều khoản Hiến pháp bắt buộc")

# 3. VERSION sync across VERSION, state.json, project.godot & Rust Cargo.toml
ver_txt = (root / "VERSION").read_text(encoding="utf-8").strip() if (root / "VERSION").exists() else ""
if not re.match(r"^\d+\.\d+\.\d+$", ver_txt):
    errors.append(f"VERSION '{ver_txt}' không đúng chuẩn SemVer MAJOR.MINOR.PATCH")

if (root / "state.json").exists():
    try:
        st = json.loads((root / "state.json").read_text(encoding="utf-8"))
        for k in ("schema", "updated_at", "project", "mandatory_files", "current_focus", "open_issues", "task_history"):
            if k not in st:
                errors.append(f"state.json thiếu trường bắt buộc: {k}")
        if st.get("project", {}).get("version") != ver_txt:
            errors.append(f"Lệch version giữa VERSION ({ver_txt}) và state.json ({st.get('project', {}).get('version')})")
    except Exception as exc:
        errors.append(f"state.json lỗi cú pháp JSON: {exc}")

if (root / "project.godot").exists():
    pg = (root / "project.godot").read_text(encoding="utf-8")
    if f'config/version="{ver_txt}"' not in pg:
        errors.append(f"project.godot chưa đồng bộ config/version=\"{ver_txt}\"")

rust_cargo = root / "engines" / "rust_combat_sim" / "Cargo.toml"
if rust_cargo.exists():
    ct = rust_cargo.read_text(encoding="utf-8")
    if f'version = "{ver_txt}"' not in ct:
        errors.append(f"engines/rust_combat_sim/Cargo.toml chưa đồng bộ version = \"{ver_txt}\"")

# 4. skills.md & lerning.md structural markers
for fname, s_tag, e_tag in [
    ("skills.md", "<!-- SKILLS_ENTRIES_START -->", "<!-- SKILLS_ENTRIES_END -->"),
    ("lerning.md", "<!-- LERNING_ENTRIES_START -->", "<!-- LERNING_ENTRIES_END -->"),
]:
    if (root / fname).exists():
        txt = (root / fname).read_text(encoding="utf-8")
        if s_tag not in txt or e_tag not in txt:
            errors.append(f"{fname} thiếu cặp thẻ đánh dấu {s_tag} ... {e_tag}")

# 5. Validate Engine ⇄ Localhost Zero-Drift Parity & Animation Completeness Gate
sys.path.insert(0, str(root / "tools" / "preview"))
import server as preview_server
parity = preview_server.verify_engine_localhost_parity()
if not parity["ok"]:
    for pe in parity["errors"]:
        errors.append(f"Lỗi đồng bộ Engine ⇄ Localhost: {pe}")
for w in parity.get("warnings", []):
    print(f"[WARN] {w}")
motion = preview_server.verify_motion_quality()
errors.extend(motion["errors"])
for cid, record in motion["characters"].items():
    if not record["release_approved"]:
        print(f"[WARN] {cid}: motion={record['status']}; Owner Human Test chưa nghiệm thu.")

# 6. Validate AGY SessionStart hook execution & JSON output contract
res = subprocess.run(
    [str(root / "loop.sh"), "--agy-session-start"],
    input="{}",
    text=True,
    capture_output=True,
    check=False,
)
if res.returncode != 0:
    errors.append(f"Hook --agy-session-start trả về mã lỗi {res.returncode}: {res.stderr}")
else:
    try:
        hk = json.loads(res.stdout)
        msg = hk["injectSteps"][0]["systemMessage"]["systemMessage"]
        if not isinstance(msg, str) or len(msg) < 20:
            errors.append("Output của --agy-session-start không đúng chuẩn injectSteps.systemMessage")
    except Exception as exc:
        errors.append(f"Output JSON của --agy-session-start không hợp lệ: {exc}")

if errors:
    for e in errors:
        print(f"[FAIL] {e}", file=sys.stderr)
    sys.exit(1)

print(f"[OK] Kiểm tra kỹ thuật / Hiến pháp / Engine ⇄ Localhost ({parity['checked_bundles']} gói SHA-256), VERSION v{ver_txt}. Nghiệm thu Owner theo motion_quality riêng.")
PY
    ;;

  log-task)
    if [ "$#" -lt 4 ]; then
      echo "Cách dùng: ./loop.sh log-task <TASK_ID> <status> <summary>" >&2
      exit 1
    fi
    TASK_ID="$2"
    TASK_STATUS="$3"
    shift 3
    TASK_SUMMARY="$*"
    python3 - "$ROOT_DIR" "$TASK_ID" "$TASK_STATUS" "$TASK_SUMMARY" << 'PY'
import datetime, json, pathlib, sys

root = pathlib.Path(sys.argv[1])
tid, tstatus, tsum = sys.argv[2], sys.argv[3], sys.argv[4]
st_path = root / "state.json"
st = json.loads(st_path.read_text(encoding="utf-8"))
now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

st["updated_at"] = now_iso
st["current_focus"]["active_task_id"] = tid
st["current_focus"]["status"] = tstatus
st["current_focus"]["summary"] = tsum

updated = False
for item in st.get("task_history", []):
    if item.get("id") == tid:
        item["timestamp"] = now_iso
        item["status"] = tstatus
        item["summary"] = tsum
        updated = True
        break
if not updated:
    st.setdefault("task_history", []).append({
        "id": tid,
        "timestamp": now_iso,
        "status": tstatus,
        "summary": tsum,
    })

st_path.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[OK] Đã ghi nhận {tid} [{tstatus}] vào state.json lúc {now_iso}")
PY
    ;;

  test)
    "$ROOT_DIR/loop.sh" check
    echo "[loop.sh] Đang chạy Python Unit Tests..."
    python3 -m unittest discover -s "$ROOT_DIR/tests" -p "test_*.py" -v
    if [ -x "$ROOT_DIR/tools/godot/godot" ] && [ -f "$ROOT_DIR/project.godot" ]; then
      echo "[loop.sh] Đang chạy Godot 4.7.2 Headless Engine Verification..."
      "$ROOT_DIR/tools/godot/godot" --headless --path "$ROOT_DIR" --script res://tests/test_character_bundles.gd
      "$ROOT_DIR/tools/godot/godot" --headless --path "$ROOT_DIR" --script res://tests/test_tasmanian_charge.gd
      "$ROOT_DIR/tools/godot/godot" --headless --path "$ROOT_DIR" --script res://tests/test_sarcosuchus_charge.gd
      "$ROOT_DIR/tools/godot/godot" --headless --path "$ROOT_DIR" --script res://tests/test_dilophosaurus_power.gd
    fi
    if [ -f "$ROOT_DIR/engines/rust_combat_sim/Cargo.toml" ] && command -v cargo >/dev/null 2>&1; then
      echo "[loop.sh] Đang chạy Rust 1.99.1 Real-Time >2,000 Combat Engine Unit Tests..."
      cargo test --manifest-path "$ROOT_DIR/engines/rust_combat_sim/Cargo.toml"
    fi
    echo "[OK] Kiểm thử kỹ thuật './loop.sh test' (Governance + Python + Godot 4 + Rust) exit 0. Nghiệm thu chuyển động theo motion_quality và Owner Human Test riêng."
    ;;

  *)
    echo "Cách dùng: ./loop.sh {status|check|test|log-task <ID> <status> <summary>|--agy-session-start}" >&2
    exit 1
    ;;
esac
