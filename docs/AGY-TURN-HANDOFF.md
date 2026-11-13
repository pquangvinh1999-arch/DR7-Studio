# Bàn giao cho agy CLI — hoàn thành TODO turn của DR7-Studio

> Owner giao: bổ sung/sửa turn lần lượt **Bat → T-rex → Pteranodon → Sarcosuchus**. Mỗi nhân vật phải giữ đúng tạo hình của các hoạt ảnh đã duyệt, chạy đúng cả trái→phải và phải→trái ở giới hạn di chuyển. Hoàn tất kiểm tra và Owner nghiệm thu từng nhân vật trước khi sang nhân vật tiếp theo.
>
> Đây là hướng dẫn thực thi, **không phải hiến pháp thứ hai**. Phải đọc và tuân thủ [AGENTS.md — Hiến pháp duy nhất](../AGENTS.md), cùng yêu cầu Owner hiện hành. Không sao chép AGENTS.md thành một bản hiến pháp riêng.

## 1. Trạng thái tiếp nhận và phạm vi

Snapshot bàn giao: **2026-11-13, v0.11.1**, workspace `/workspaces/DR7-Studio`.

- Chilopoda identity-v2 đã được Owner yêu cầu chốt; PIPE-008, biên nhận `assets/chilopoda/owner_approval.json`. Atlas SHA-256 `6fae71276ce9e24eff3ae5d5bcd22b7d4573e5e3190730095c438bbe4d83d42d`.
- Có **8 nhân vật Owner-approved**. Kiểm tra chốt gần nhất: 51 Python/E2E tests, 8 Godot bundles, 5 action tests, 2 Rust tests, WASM release, HTTP/ZIP đều exit0/khớp. Đây là kết quả lịch sử có log, không thay cho kiểm tra sau sửa.
- [TODO chính thức](turn-retrofit-todo.md) hiện **0/4 hoàn tất**. Gate chờ chốt Chilopoda đã mở. Bắt đầu bằng Bat.
- **King Crab không cần turn** vì di chuyển ngang. Giữ Spinosaurus, Dilophosaurus và Chilopoda đã duyệt; không tự sửa artwork/timing của chúng.
- Owner báo còn 7% quota ở phiên trước. Không có telemetry quy đổi thành số lượt ảnh/token; không cam kết đủ cả bốn. [Đánh giá khối lượng](turn-quota-assessment.json): ít nhất 3 clip turn mới, 1 clip cá sấu cần audit/sửa, 16 ca hướng/runtime cốt lõi; chưa tính vòng sửa. Làm tuần tự, ưu tiên hoàn tất Bat.
- Trước pickup, workspace có thay đổi chưa commit và asset chưa được tracking. Bản pickup v0.11.1 đưa nguồn cần thiết vào Git; khi tiếp nhận phải fetch/kiểm tra đúng commit và VERSION, không dùng checkout v0.9.1 cũ. **Không reset/clean/ghi đè công việc đang có.** Kiểm tra working tree trước khi sửa. ZIP project test và thư mục giải nén local không phải nguồn pickup; master/frozen frames/runtime/tài liệu được giữ trong repo.

| Thứ tự | Nhân vật / ID | Tình trạng thực tế lúc bàn giao | Đích cần đạt |
|---|---|---|---|
| 1 | Bat / `bat_chiroptera` | Chưa có clip `turn` | Turn trên không, giữ camera/cánh/độ cao; nối bay→turn→bay hai chiều |
| 2 | T-rex / `t_rex` | Chưa có clip `turn` | Turn có trọng lượng và tiếp đất, đầu/thân/đuôi liên tục; giữ heavy cũ |
| 3 | Dực long / `pteranodon` | Chưa có clip `turn` | Turn trên không đúng near/far wing, camera và anchor bay |
| 4 | Cá sấu / `sarcosuchus` | Có `turn` 4 frame/20 tick, chưa audit theo yêu cầu mới | Reproduce lỗi hai chiều/endpoint rồi sửa đúng nguyên nhân; không coi có tên clip là đã hoàn tất |

Không tự đổi turn của bốn nhân vật này thành độn thổ. Độn thổ đổi hướng là ngoại lệ Owner chỉ chốt cho Chilopoda.

## 2. Đọc và kiểm tra trước khi làm

Chạy từ gốc repo:

```bash
cd /workspaces/DR7-Studio
./loop.sh status
git status --short
```

Đọc đầy đủ:

1. [AGENTS.md](../AGENTS.md), [state.json](../state.json).
2. [skills.md](../skills.md): quy trình Owner đã nghiệm thu, hiện PIPE-001..008. Chỉ ghi quy trình mới **sau** Owner nghiệm thu Human Test.
3. [lerning.md](../lerning.md): đặc biệt LRN-040, 043, 045, 046, 047 về envelope FX, cadence, bằng chứng timing, turn hai chiều và lệch nhận diện.
4. [TODO](turn-retrofit-todo.md), [contract turn và score](art-standards/turn-contract.md).
5. Skill [.agents/skills/dr7-governance/SKILL.md](../.agents/skills/dr7-governance/SKILL.md), [create_atlas](../.agents/skills/create_atlas/SKILL.md), [generate2dsprite](../.agents/skills/generate2dsprite/SKILL.md); đọc `video2dsprite` nếu dùng nhánh video. `.agent` là alias của `.agents`, không tạo bản skill khác.

Không nhầm `skills.md` gốc với skill công cụ trong `.agents/skills/`. Nếu state cũ mâu thuẫn quyết định engine đã chốt trong AGENTS.md, không tự mở lại lựa chọn engine: dự án dùng Godot4 + Rust Core + Supabase.

Kiểm tra khả năng sinh ảnh thật của host agy và CLI bằng tài liệu/`--help`/skill hiện có. Không giả định agy có tool `image_gen` của Codex hoặc bịa flag cho agy. Lưu route, prompt, reference và ảnh đầu ra thực tế. Không có route hợp lệ thì báo thiếu công cụ; **không dùng cắt/warp/ghép chi làm fallback**. Không cần mở tài khoản/dịch vụ mới để đọc tài liệu này.

## 3. Nguồn nhận diện và dữ liệu phải giữ

Dùng `assets/roster.json` cùng `assets/<id>/owner_approval.json` để đối chiếu nguồn và SHA thực tế. Các đường dẫn dưới đây đã tồn tại ở snapshot này:

| ID | Mẫu nhận diện đã duyệt | Nguồn động tác / prefab |
|---|---|---|
| `bat_chiroptera` | `work/characters/bat_chiroptera/approved-master/master.png` | `work/characters/bat_chiroptera/approved-final-frames/animation-clips.json`; `scenes/BatChiroptera.tscn` |
| `t_rex` | `work/characters/t_rex/walk-style-v4/walk-00-reference.png` | `assets/t_rex/clips/animation-clips.json`; `scenes/TRex.tscn`; tự snapshot trước sửa vì receipt không khai báo frozen_source |
| `pteranodon` | `work/characters/pteranodon/master-match-v9/reference.png` | `assets/pteranodon/clips/animation-clips.json`; `scenes/Pteranodon.tscn`; tự snapshot trước sửa vì receipt không khai báo frozen_source |
| `sarcosuchus` | `work/characters/sarcosuchus/master-review/master-gameplay-v1.png` | `work/characters/sarcosuchus/approved-final-frames/animation-clips.json`; `scenes/Sarcosuchus.tscn` |

**Spinosaurus chỉ làm tham khảo motion**, không làm identity reference cho bốn nhân vật khác. Xem thật `assets/spinosaurus/clips/animation-clips.json`, `assets/spinosaurus/godot_bundle/engine-export.json`, `scenes/Spinosaurus.tscn`, receipt và [QA Spino](characters/spinosaurus-final-qa.json). Turn Spino hiện 4 pose, ticks `[6,4,4,6]`; không ép số pose/timing đó lên mọi loài và không thay/sửa `attack_heavy` đã duyệt.

**Chilopoda phải giữ nguyên**:

- Mẫu chuẩn là power_up1 cũ, tại `work/characters/chilopoda/identity-v2/canonical/master.png`, không phải master đầu tiên.
- Bản cuối: `work/characters/chilopoda/approved-final-frames/animation-clips.json` và `assets/chilopoda/owner_approval.json`.
- Turn độn thổ 36 tick: ẩn `[16,22)`, đổi hướng tick16, trồi22, tự bò ngược; attack ẩn `[24,54)` đúng0,5s rồi cắn/ở lại mục tiêu; hai laser đỏ riêng từ râu.
- Không chạy lại các `prepare.py`, `build_frames.py`, `install*.py` hay `finalize_approval.py` cũ để ghi đè bản đã chốt. Một số PNG staging trùng đã được dọn; staging manifest là lịch sử, dùng frozen final frames để tái xuất.

Có issue T-rex `ISS-TREX-TICK-LEGACY` trong state: duration xuất cũ có số thập phân khác authored ticks. Audit và báo bằng chứng. **Không âm thầm đổi timing của các clip cũ hoặc thay test để che issue**; nếu giải pháp turn đòi thay timing ngoài scope đã chốt thì trình bày cụ thể để Owner quyết định.

## 4. Thực hiện trọn vẹn từng nhân vật

Lặp các bước A→H cho **một nhân vật**, chưa qua nhân vật tiếp theo khi Owner chưa chốt revision đó.

### A. Snapshot trước sửa

- Tạo thư mục làm việc riêng, ví dụ `work/characters/bat_chiroptera/turn-v1/`; nháp, prompt, log và lỗi để ở `work/`, không thêm nhân vật thử vào roster.
- Snapshot receipt, master, clips, atlas, `.tres`, metadata, prefab, FX, script runtime liên quan và roster hiện tại; lưu manifest SHA-256 đầy đủ.
- Snapshot các nhân vật ngoài scope, gồm Chilopoda vừa chốt. Nếu sửa runtime dùng chung, vẫn phải regression test cả tám nhân vật.
- Lưu so sánh **RGBA từng pose, thứ tự, ticks, events, loop policy, anchor và FX contract** ngoài turn. Repack có thể đổi atlasSHA/Rect2; không được đổi pixel/nội dung/timing các clip cũ.
- Ghi issue, revision, phạm vi được đổi, các gate pending vào state và report của nhân vật.

### B. Audit trước khi sinh pose

- Xem canonical, frame di chuyển và các clip đã duyệt ở 1×/zoom nguyên lần, trên sáng/tối/ô cờ. Đừng coi một frame đầu đúng mẫu là cả clip cùng nhận diện.
- Ghi camera, hướng đầu/thân, near/far limb/wing, chi tiết bất đối xứng, root/ground hoặc anchor bay. Hướng ở đây là **trái/phải trên màn hình**.
- Reproduce endpoint hiện tại; với Sarcosuchus lưu clip/frame/Canvas/Atlas/log trước khi quy lỗi artwork hay state machine.
- Lập timeline turn: giảm tốc/chuẩn bị → chuyển phối cảnh có trọng lượng → hồi thế và hướng mới. Chọn số pose/ticks theo loài; công bố60Hz, không rải đều tick để biến thành lật tấm bìa.

### C. Sinh turn giữ đúng tạo hình

- Mọi keyframe là **toàn bộ cơ thể nối liền**, dùng canonical riêng làm ảnh reference thật trong tool. Giữ màu, cách tô, tỷ lệ đầu/thân/chi/cánh/đuôi/giáp và camera tương thích clip cũ.
- Không cắt ảnh tĩnh thành mảnh đầu/chi/thân để xoay, warp, kéo, vá hoặc ghép; không lấy mask/rig của Spino sang nhân vật khác.
- Không dùng `flip_h`, xoay quad hay thu ngang một ảnh làm các frame trung gian. Có thể mirror/reverse một chuỗi chuyển tiếp hợp lệ **chỉ sau** khi đã kiểm độc lập cả hai chiều, bất đối xứng, phối cảnh và nối đầu/cuối. Nếu không hợp lệ, vẽ hai chuỗi riêng và khai báo mapping runtime rõ ràng.
- Bat/dực long giữ chuyển động bay, vị trí gốc và near/far wing đúng; T-rex/cá sấu giữ tiếp đất và trọng tâm đúng. Không redesign các clip cũ để làm chúng giống turn sai.
- Bóc nguyên pose bằng ownership2D khi sheet có phần lấn ô/hàng. Loại chữ/viền/ảnh lấn hàng; xử lý hốc nền và spill theo AGENTS.md. Không xóa chi tiết cơ thể để đạt chỉ số alpha.
- Mốc nét: [ảnh T-rex chuẩn](art-standards/t-rex-sharpness-reference.png), [phương pháp đo](art-standards/character-pixel-sharpness.json). Native1px/Nearest, thân alpha100%, FX cho phép alpha mềm; không sharpen/LUT/dither hoặc ép Sobel để chạy theo số. Giữ size riêng đã duyệt.

### D. Nối runtime và tránh double flip

Kiểm tra mã thật trước sửa:

- `scenes/CharacterFighter2D.gd`: `set_facing_left`, `_turn_pending`, `_turn_target_left`, `_on_skill_finished`.
- `tests/SkillAnimator2D.gd`: đồng hồ, event và kết thúc clip.
- `tools/preview/index.html`: mapping turn, `arena.turnTargetFlip`, xử lý A/D, endpoint, tiến timeline và render hướng.
- `tests/test_character_bundles.gd`, `tests/test_frontend_wasm_e2e.mjs`, `tests/test_spinosaurus_contract.py`.

Phải có luồng thật **walk/fly → hãm tại giới hạn → turn → đi/bay ngược lại**; khoá lệnh không phù hợp khi đang turn. Kiểm trái→phải và phải→trái riêng, gồm đổi hướng bởi input và endpoint; không vượt giới hạn hoặc đứng idle mãi sau turn.

Xác định rõ mỗi pose nguồn nhìn về đâu, parent scale/facing hiện tại và thời điểm commit. Nếu frame cuối đã quay sang hướng ngược rồi parent lại flip, kết quả có thể quay ngược lần hai hoặc giật ở nối sang walk. **Phải render và xem frame cuối→frame đầu di chuyển**, không chỉ gọi callback giả lập rồi nhận PASS. Nếu mirror wholecanvas, tâm phản chiếu là `anchor_x`, không mặc định canvas_center; dùng tọa độ pixel-center đúng và kiểm root thực tế.

Giữ Godot/localhost cùng contract. Độn thổ đổi hướng giữa hidden interval trong `ChilopodaFighter2D.gd` là cơ chế riêng; không áp thời điểm commit của Chilopoda lên các turn phối cảnh mới.

### E. Atlas, receipt lịch sử và test đóng băng

- Thân `combined_1layer`: nguyên một sprite, không tách cánh/chi theo chiều sâu. Thân tắt FX là1quad; bật FX có chi phí riêng. Không `layered_3d_depth`.
- Một trang PNG/nhân vật, tối đa4096×4096; canvas bội16, giữ anchor và scale. `.tres`/metadata60Hz, `texture_filter=1`, `centered=false`, offset bằng `-anchor_px`; `.gdignore` ở `source/` và `clips/`.
- Đo và công bố canvas, anchor, body-only bbox, full-FX bbox, quy đổi64PPU và tile32px. Full-FX envelope phải đo trên composite sau đặt FX/đổi hướng theo contract, không union các PNG FX còn ở pivot nguồn. Không thu nhỏ nhân vật để ép vừa trang atlas.
- Với chroma-key, giữ `opaque_key_px=0`, `enclosed_key_pockets=0`, `outer_ring_spill_fraction<=0.005`; xử lý pocket trước unmix mép theo AGENTS.md. Không tự gán số sạch nền khi chưa đo. Thân pixel-art mới alpha100%; quy tắc biên pixel-art trong hiến pháp yêu cầu `alpha_hardness_pct>=95%`. Giữ FX alpha mềm nếu nguồn/contract cần.
- Dùng đúng PNG/Rect2/tick/anchor từ bundle cho engine và localhost; không làm một bộ preview khác để che lỗi engine.
- **Atlas đã repack không còn được receipt cũ tự phê duyệt.** Archive nguyên receipt/atlas/metadata/frames cũ trước thay live. Với workflow lịch sử, repo có cơ chế `approved_atlas_path` trong `state.approved_workflows`; xem test governance và `tools/preview/server.py` trước dùng. Trỏ receipt lịch sử tới archive phù hợp, không sửa SHA cũ thành SHA mới để giả đã duyệt.
- Revision live mới để `motion_quality=reviewed_pending_owner` chỉ khi đã có review thật, `owner_approved=false` cho đến Owner chốt; ghi `previous_revision_atlas_sha256` khi dùng nhánh archive đã được repo hỗ trợ. Trong lúc chưa review phải để pending/FAIL đúng sự thật.
- Test hiện có khóa snapshot cũ: Bat còn assert PIPE-007,61frame và tập clip bằng Pteranodon; Sarcosuchus khóa turn4frame/20tick; test Chilopoda còn đối chiếu manifest protected-peers của các revision cũ. **Phải di trú có chứng cứ**, không xoá/skip kiểm tra hoặc cập nhật baseline mù.
- Giữ test chứng minh revision lịch sử khớp archive; test revision mới phải so RGBA/ticks/events của toàn bộ clip ngoài turn với snapshot trước sửa, đồng thời thêm turn và kiểm hai chiều. Chỉ thay assertion không còn đúng do yêu cầu thêm turn được Owner cho phép. Những peer ngoài scope và Chilopoda vẫn phải giữ nguyên; allowlist thay đổi đúng nhân vật/revision hiện hành, không nới cho cả roster.
- `VERSION` là nguồn SemVer, đồng bộ state/project.godot/Cargo.toml và lock nếu có. Không tự công bố commit/push/deploy nếu chưa có yêu cầu phù hợp.

### F. Kiểm tra, lưu log và giới hạn5vòng

Mỗi vấn đề có ledger riêng: ID, số vòng, thay đổi đã thử, lệnh, exit code, log, lỗi còn lại. Giữ bộ đếm qua reconnect, không đổi tên issue để đếm lại.

**Tối đa5vòng phân tích→sửa→`./loop.sh test` cho mỗi vấn đề.** Vòng5 vẫn chưa sửa được: dừng phần đó, báo Owner nguyên nhân/bằng chứng/cách đã thử; không chạy vòng6, không bàn giao FAIL như hoàn thiện. Không sang nhân vật kế để tránh giải quyết lỗi của nhân vật hiện tại.

Lệnh sau đã có trong repo; điều chỉnh đường dẫn thư mục mới do mình tạo, đọc `--help` nếu cần tham số khác. Ví dụ cho Bat, **không chạy export khi build clip chưa exit0**:

```bash
TURN_CHAR=bat_chiroptera
TURN_WORK="work/characters/$TURN_CHAR/turn-v1"

# Chỉ chạy sau khi đã tạo manifest đúng schema và nguyên frame hoàn chỉnh.
python3 .agents/skills/generate2dsprite/scripts/build_animation_clips.py \
  --manifest "$TURN_WORK/clips_manifest.json" \
  --output-dir "$TURN_WORK/clips" --preview-background all --strict

# Output-dir phải mới; chờ lệnh build ở trên hoàn tất.
python3 .agents/skills/generate2dsprite/scripts/export_engine.py \
  --clips "$TURN_WORK/clips/animation-clips.json" \
  --target all --output-dir "$TURN_WORK/godot_bundle" \
  --name "$TURN_CHAR" --sampling nearest --godot-fps auto

# Sau khi bundle/contract/prefab/revision đã được cài đúng và motion gate có evidence.
./tools/godot/godot --headless --path . --editor --import --quit
# Chờ import exit0 rồi mới test.
./loop.sh check
./loop.sh test
cargo build --manifest-path engines/rust_combat_sim/Cargo.toml \
  --target wasm32-unknown-unknown --release
```

Đọc log thực tế. `loop.sh test` hiện chạy Python/E2E, Godot bundles +actiontests và `cargo test`; **WASM release build vẫn chạy riêng**. Khi Rust/WASM hoặc version thay đổi, đồng bộ artifact thực tế sang `tools/preview/rust_combat_sim.wasm` và đối chiếu hash; không dùng WASM cũ để nhận mới đã kiểm.

Nên ghi stdout/stderr ra file, ghi `$?` ngay sau lệnh; nếu pipe qua `tee` phải xử lý exitcode đúng, không lấy exit0 của `tee` thay lệnh test. Không nhận51tests của snapshot là đủ cho phần turn mới; thêm test có ý nghĩa và tích hợp vào `loop.sh`/CI khi cần.

Các cổng bắt buộc, ít nhất4nhân vật×2hướng×2runtime=16ca lõi:

| Cổng | Phải có bằng chứng |
|---|---|
| Bảo toàn | Non-turn RGBA/order/tick/event/FX/anchor khớp snapshot; peer ngoài scope không đổi |
| Tạo hình | Canonical cùng cỡ gameplay so từng pose, đặc biệt nối đi→turn và turn→đi |
| Hai chiều | Trace độc lập phải→trái, trái→phải; frame đầu/giữa/cuối và hướng sau commit |
| Hai endpoint | Đến cả giới hạn, dừng đủturn, tự đi lại; input giữa turn không phá state |
| Trực quan | Mở từng filmstrip và phát tốc độ thật trên sáng/tối/ô cờ; lưu clip/screenshot/frame/Canvas/Atlas |
| Kỹ thuật | Godot texture/frame/tick/offset/Nearest, Rust tests, WASMbuild, loopcheck/test thật |
| Đồng bộ | HTTP atlas/WASM/metadata hash,Rect2,tick,anchor và gói GodotZIP khớp runtime |
| Nghiệm thu | Owner chốt đúng revision; chỉ sau đó receipt mới/PIPE và chuyển nhân vật tiếp |

Technical exit0 không thay motion PASS. Xé cơ thể/hở khớp/đổi tỷ lệ/lộ patch/lật ảnh giả xoay = motion FAIL. Thiếu evidence = pending. Headless bỏ quan sát pose ngắn phải báo số frame bị bỏ; không nhận đó là benchmark mobile60FPS. WARN clip tham chiếu Owner đã loại phải giữ và giải thích, không tạo clip giả hoặc gỡ checker.

### G. Localhost và Human Test

- Kiểm tra server hiện tại trước khi khởi động. Lệnh server có sẵn: `python3 tools/preview/server.py` từ repo root, mặc định8080. Không bịa flag `--port`/`--help`; mã hiện đọc biến `PORT` nếu cần.
- Nếu sửa Python server/motion gate, process cũ phải được reload có kiểm soát; không kill nhầm process của Owner. Chỉ có thay PNG/JSON không có nghĩa phải restart toàn bộ môi trường.
- URL cho Bat: `http://localhost:8080/?character=bat_chiroptera&clip=turn&frame=0&paused=1`; Tab3 thử A/D và cả endpoint. Đổi ID cho nhân vật tương ứng.
- API đã có: `/api/bundles`, `/api/download-godot-pack.zip`. Xác minh status/revision/parity và byte HTTP so local; ZIP CRC/hashes/prefab/metadata; import GodotZIP độc lập rồi kiểm bundle/turn. Chờ import hoàn tất trước khi chạy test.
- Tham khảo cách lưu evidence trong `work/characters/chilopoda/identity-v2/verification/`, nhưng không chạy nguyên script Chilopoda cho Bat: chúng chứa contract/target/tick riêng của Chilopoda. Tạo report/test phù hợp nhân vật đang sửa.
- Báo Owner phần thay đổi, phần được bảo toàn, kết quả technical riêng với motion, WARN/giới hạn và link xem. Chờ Owner nghiệm thu revision trước khi đánh hoàn tất và đi tiếp.

### H. Chốt từng revision

Sau Owner chốt, lưu nguyên văn yêu cầu nghiệm thu và timestamp; receipt mới ràng buộc atlas/TRES/prefab/manifest/runtime SHA. Giữ receipt cũ như lịch sử, không ghi đè bằng cách dùng lại script finalize cũ.

Freeze final frames/contract, chạy kiểm tra chốt và HTTP/ZIP parity. Chỉ dọn PNG staging trùng byte khi đã chứng minh SHA có bản canonical giữ lại; không xoá master, nguồn, approval, review, log hoặc frame duy nhất. Cập nhật TODO, score, state, lesson lỗi đã sửa có kiểm chứng; lúc này mới ghi quy trình nghiệm thu mới vào `skills.md`. Giữ số thứ tự PIPE theo dữ liệu thực tế, không mặc định mọi lượt đều là PIPE-009 nếu người khác đã làm trước.

## 5. Score và mẫu bàn giao mỗi nhân vật

Dùng đầy đủ10tiêu chí×10điểm trong [turn-contract.md](art-standards/turn-contract.md), không gọi score là tỷ lệ nhận diện do AI đoán. Mỗi tiêu chí chỉ cộng10khi có evidence đạt; chưa kiểm là pending, lỗi là FAIL. Không dùng điểm mục khác bù lỗi cấu trúc/hướng. **100/100 chỉ sau đủ10gate và Owner chốt revision.**

Report cần có:

```text
Nhân vật / revision / canonical SHA / atlas SHA:
Baseline và receipt lịch sử:
Các file đã đổi, lý do và clip cũ được bảo toàn:
technical_checks: pass | fail | pending ; command/exit/log
motion_quality: pass | fail | pending ; evidence từng frame/chuỗi/3nền
Right→left / Left→right: report riêng
Endpoint trái / phải, input giữa turn, nối turn→walk:
10 tiêu chí score: pending/pass/fail + điểm có bằng chứng + đường dẫn
Owner acceptance: pending | approved ; message/timestamp/receipt
Repair ledger: issue/count1..5/attempt/log/lỗi còn lại
WARN/giới hạn/khác biệt đã đo:
TODO tiếp theo và điều kiện được chuyển:
```

## 6. Câu lệnh giao việc để Owner dán cho agy

```text
Đọc docs/AGY-TURN-HANDOFF.md và AGENTS.md tại workspace DR7-Studio hiện tại.
Chilopoda identity-v2/v0.11.1 đã chốt; giữ nguyên bản đó và các nhân vật ngoài scope.
Tiếp tục TODO turn đúng thứ tự Bat → T-rex → Pteranodon → Sarcosuchus, hiện0/4.
Bắt đầu Bat: snapshot bản đã duyệt, tham khảo turn Spino, sinh nguyên pose giữ đúng
canonical, nối runtime hai chiều và hai endpoint, không lật ảnh giả xoay.
Bảo toàn pixel/timing/event/FX mọi clip ngoài turn; xử lý receipt/test lịch sử đúng revision.
Chạy đủ Godot/Rust/WASM/loop.sh, review3nền và HTTP/ZIP parity; tối đa5vòng/issue,
vòng5 chưa sửa được phải dừng phần đó và báo tôi. Không cam kết theo quota chưa đo.
Bàn giao Bat để tôi Human Test/chốt trước khi chuyển T-rex. Cập nhật state và TODO
sau mỗi bước, không tự ghi Owner-approved hoặc score100 khi tôi chưa nghiệm thu.
```
