# Shenron — ĐÃ CHỐT v0.13.1 / PIPE-018 (`pixel_dissolve` reveal)

> **Trạng thái hiện hành:** Owner đã nghiệm thu bản `v3-pixel-dissolve` (`PIPE-018`, supersedes ritual reveal `PIPE-017`). Giữ nguyên thân `idle-v5-hover`, quỹ đạo 7 viên ngọc, 2 chớp trắng, cụm đất `144x136` và aura; chốt reveal `pixel_dissolve` `96x68` cell `4x4`. Receipt [assets/shenron/owner_approval.json](../assets/shenron/owner_approval.json) & [assets/rituals/shenron_summon/owner_approval.json](../assets/rituals/shenron_summon/owner_approval.json).

> Ghi nhận ban đầu tại `2026-11-15T06:46:30Z` (`VERSION v0.12.0`). Mọi thay đổi bắt buộc tuân thủ [AGENTS.md](../AGENTS.md) (`combined_1layer`, `Nearest 1px`, `alpha_hardness_pct = 100%`, không cắt/kéo/warp ảnh tĩnh giả chuyển động).

## 1. Trạng thái hiện tại & lý do tạm dừng
- **Blocker**: Model `gemini-3.1-flash-image` trả lỗi `429 Too Many Requests: RESOURCE_EXHAUSTED` sau khi sinh xong `idle_01`.
- **Thời điểm reset quota**: **`2026-11-15T11:18:57Z`** (khoảng **18:18 giờ Việt Nam**, `~4h43m9s` tính từ `06:36Z`).
- **`forge_doctor.py`**: Đã xác minh chưa cấu hình API key hoặc CLI dự phòng (`openai`, `gemini`, `xai`, `byteplus`, `fal`, `codex`, `grok` đều thiếu).
- **Workspace chính thức**: `assets/`, `scenes/`, `VERSION` (`0.12.0`), `skills.md` giữ nguyên trạng thái sạch đã chốt (`8` nhân vật, `./loop.sh check` đang `exit 0`).

## 2. Yêu cầu Owner đã chốt (KHÔNG hỏi lại)
1. **Master Pixel đã duyệt**: [master.png](../work/characters/shenron/master-v1/master.png) (`384×256`, body bbox `[45, 27, 294, 201]`, `96` màu, `edge_acutance_sobel = 419.261`, `alpha_hardness_pct = 100.0`).
2. **Kích thước hiển thị (+20% so với comparison `2.0x`)**: `default_scale = 2.4` (`294×201 @ 2.4x = 706×482 px`, `44.63%` 1080p). Giữ nguyên pixel `master.png` làm `idle_00`; chỉ scale hiển thị qua `default_scale = 2.4`.
3. **Phạm vi hoạt ảnh**: **`idle`-only** (`present_clips: ["idle"]`), chính diện gốc (`front_only`), không tạo `walk/run/jump/guard/win/attack_light/attack_heavy/power_up/aura_loop/hit/ko/turn`.
4. **Nội dung 4 frame `idle` (`0 → 1 → 2 → 3 → 0` tiến pha liên tục, KHÔNG ping-pong)**:
   - Kết hợp: **nhịp thở**, **đuôi vẫy**, **râu vẫy hai bên**, **lơ lửng nhấp nhô nhẹ**.
   - **Cấm nháy mắt**: mắt đỏ mở to nhìn thẳng đồng nhất cả 4 frame.
5. **Kiến trúc & đồng bộ**: `combined_1layer`, 1 trang PNG Atlas `<= 4096`, lọc `Nearest (1)`, `60Hz` ticks (`--godot-fps auto`), đồng bộ 1:1 Godot ⇄ Rust/WASM ⇄ `localhost:8080`, giữ trạng thái **chờ Owner Human Test** (không tự ghi `skills.md` hay tạo `owner_approval.json` trước khi Owner duyệt).

## 3. Tài nguyên đã hoàn thành & tái sử dụng ngay
- Ảnh nguồn gốc Owner (bất biến): `work/characters/shenron/source/shenron-original.jpg` (`sha256: 0440297a160f4f3c39e95eb166d6b44d8186a7b1f434879d0edcffc18a1f95bb`)
- Raw imagegen gốc (`1024×1024`, nền `#0245C8`): `work/characters/shenron/master-v1/source-imggen-raw.jpg`
- **Frame 0 (`idle_00`, exact Master)**: `work/characters/shenron/master-v1/master.png` (`sha256: 7d32a92302b9af7a4286d8c11f07222d2874c555e3fa51c5f1738e0af87e0526`)
- **Frame 1 (`idle_01`, đã sinh + tách sạch)**:
  - Raw: `work/characters/shenron/idle-v1/raw/idle_01-raw.jpg`
  - Extracted (`384×256`, bbox `[45, 27, 294, 204]`, `96` màu khớp Master, `0` blue spill, `100%` alpha, mắt mở `(180.6, 75.0)`): `work/characters/shenron/idle-v1/idle_01-candidate.png` (`sha256: 4d264b4d3f191c1638a1dc188167a86ebbe68f71e592485da25bd436cda1e0b4`)
  - Đối chiếu 3 cột: `work/characters/shenron/idle-v1/compare-idle00-idle01.png`
- **Script tách nền + khóa 96 màu sẵn dùng**: `work/characters/shenron/idle-v1/extract_shenron_frame.py`

## 4. Checklist thực hiện ngay khi quota reset (`>= 2026-11-15T11:18:57Z`)

- [x] **Bước 1**: Bóc tách nguồn gốc + tạo Master Pixel + chốt scale `+20%` (`2.4x`) + chốt phạm vi `idle`-only.
- [x] **Bước 2a**: Sinh & tách sạch `idle_01` (râu cong lên, đuôi sang trái, mắt mở nguyên, `0` spill).
- [x] **Bước 2b**: Sinh nốt **`idle_02`** (đỉnh lơ lửng, vòm râu đối pha, đuôi lắc phải, mắt mở) và **`idle_03`** (hạ nhẹ + hồi râu/đuôi về `idle_00`) bằng built-in `image_gen` (route thực tế thay thế quota Gemini), tham chiếu **cả** `source-imggen-raw.jpg` lẫn `master.png` trên nền phẳng `#0245C8`.
- [x] **Bước 3**: Tách & khóa 96 màu bằng `work/characters/shenron/idle-v1/extract_shenron_frame.py` (`--dy` nhịp lơ lửng mượt, không cắt đầu/râu/đuôi); đo `tools/art/measure_pixel_sharpness.py`; mở xem đủ 4 frame + diff heatmap để bảo đảm mắt không chớp, không xé hình, không lỗi màu.
- [x] **Bước 4**: Đóng gói 60Hz (`build_animation_clips.py --strict`, gợi ý `[12, 12, 12, 12]` hoặc `[10, 10, 10, 10]` ticks/cycle) và xuất `export_engine.py --target all --sampling nearest --godot-fps auto`. Mở xem trực quan `review/*.png` trên 3 nền (`light`, `dark`, `checker`) và chạy thực tế kiểm tra độ mượt vòng lặp.
- [x] **Bước 5**: Tích hợp tối thiểu nhưng đồng bộ 1:1 theo Hiến pháp:
  - Tạo `assets/shenron/clips/` + `assets/shenron/godot_bundle/` (`anchor_px` gợi ý `[192.0, 240.0]` khớp `map_sync_metrics.foot_anchor_px`).
  - Tạo `scenes/Shenron.tscn` (theo mẫu `scenes/Spinosaurus.tscn` + `CharacterFighter2D.gd`).
  - Cập nhật `assets/roster.json`: thêm `shenron` (`status: "finalized_combined_1layer"` để server/parity nạp hợp lệ, `atlas_stage: "demo_pending_owner"`, `owner_animation_approval: "pending"`, `motion_quality.status: "reviewed_pending_owner"`, `owner_approved: false`, `render_contract.locomotion.kind: "stationary"`, `clip: "idle"`, `speed_px_per_second: 0.0`, `default_scale: 2.4`, `allow_turn_or_flip: false`, `lock_spawn_facing: true`, `body_clips: ["idle"]`, `effect_clips: []`).
  - Bổ sung guard cho `locomotion.kind == "stationary"` (đã xác định vị trí chính xác):
    1. `scenes/ArenaSandbox.gd`: `_get_walk_speed_px_per_s` (~L526) trả `0.0` khi `kind == "stationary"`; `_physics_process` (~L574) không nhảy `W/Space` khi stationary.
    2. `scenes/UtilityAIController.gd`: trả `idle` / `move_dir: 0` khi stationary.
    3. `tools/preview/index.html`: `getContractWalkSpeedPxPerS` (~L1865) trả `0` khi `kind === 'stationary'`; `evaluateUtilityAI` (~L2045) trả `idle`; ẩn/tắt tuần tra khi stationary (~L2535); cập nhật hint (~L870).
    4. `tests/test_arena_sandbox.gd:70`: cập nhật số nhân vật kỳ vọng từ `8` → `9` (giữ nguyên assert scale spawn player `+expected_scale` / dummy `-expected_scale` và `ground_y = 840.0` nên không đổi `y` spawn).
  - **Không sửa** `VERSION`, `skills.md`, hay tạo `owner_approval.json` cho Shenron trước khi Owner Human Test chốt.
- [x] **Bước 6**: Chạy đầy đủ `./loop.sh check`, `./loop.sh test` (Python/Node WASM E2E, Godot `4.7.2` headless, Rust tests), kiểm tra trực tiếp `http://localhost:8080` (`?character=shenron&clip=idle`), cập nhật `state.json` và bàn giao Owner Human Test.

## 5. Lệnh vào phiên chiều nay
```bash
cd /workspaces/DR7-Studio
./loop.sh status
python3 .agent/skills/generate2dmedia/scripts/forge_doctor.py --host-tools none
```

## Tiếp tục phiên 2026-11-15 — host imagegen
- Không còn phụ thuộc quota Gemini cho bản nháp: đã sinh `idle_02-host-candidate.png` và `idle_03-host-candidate.png` bằng built-in image_gen, tham chiếu cả raw/master. Giữ nguyên master và idle_01.
- Đã build `work/characters/shenron/idle-v1/host-clips-v1` (strict:0warnings), export `host-engine-v1` (1page), timing `[12,12,12,12]` tại60Hz (800ms).
- Đã mở trực tiếp filmstrip light/dark/checker; **motion_quality=pending** vì chưa có review phát tốc độ thực. Chưa đưa bản nháp vào roster.
- Đã triển khai stationary Godot/web: speed0, chặn di chuyển/nhảy, AI idle giữ facing, ẩn tuần tra. `./loop.sh test` attempt2 exit0; attempt1 parse error do guard đặt nhầm hàm đã sửa.
- Bằng chứng: `work/characters/shenron/idle-v1/evidence/review.json`, `evidence/stationary-test-pass.log`.
- Việc kế tiếp: review playback và seam3→0, rồi mới tích hợp assets/scene/roster + engine/localhost Human Test theo bước5/6.

## Hoàn tất tích hợp — 2026-11-15T09:02:35.887934+00:00
- Đã đưa4frame vào `assets/shenron`, `scenes/Shenron.tscn`, roster thứ9; source master giữ SHA ban đầu. Atlas778×522/1page,offset[-192,-240],Nearest.
- Bốn pose đều còn2mắt đỏ mở; key/pocket/spill đều0 theo `key-eye-measurements.json`. Đã xem filmstrip/ảnh trình duyệt3nền và diff3→0; runtime tiến pha đã lưu trong `browser-playback-unrecorded.json`.
- Full `./loop.sh test` lần4 exit0; WASM release build exit0, copy binary mới sang preview, Node/WASM E2E exit0; hash khớp ở `final-parity.json`. Giữ nguyên WARN các clip Owner loại và Owner chưa nghiệm thu; log còn Pillow DeprecationWarning được ghi trong QA.
- Human Test: http://localhost:8080/?character=shenron&clip=idle . Kiểm tra nhịp thở/râu/đuôi/lơlửng và seam3→0; chưa ghi skills.md/receipt/version cho đến khi Owner chốt.

## Owner yêu cầu8frame — 2026-11-15T09:15:18.255114+00:00
- [x] Snapshot4frame cũ tại `work/characters/shenron/idle-v2/snapshot-before`.
- [x] Sinh4pose toàn thân mới bằng built-in image_gen, key/palette cùng master, bố trí xen kẽ4pose gốc giữ byte-identical tại0/2/4/6.
- [x] Chu kỳ0→7→0,6tick/frame tại60Hz (100ms/frame), giữ800ms/vòng;1atlas1166×782. Giữcanvas384×256,anchor[192,240],scale2.4,stationary/front-only.
- [x] Review filmstrip3nền,8pose/diff và7→0; browser phát đủ8pose,không JSerror;8mắt-cặp đều đỏ mở,key/pocket/spill0,hardalpha100%.
- [x] Godotimport/WASMbuild/full `./loop.sh test` exit0 ngaylần1; servedatlas8regions khớpRGBAnguồn/hash. QA vàlogs ở `work/characters/shenron/idle-v2/evidence/`.
- [ ] Owner Human Test: http://localhost:8080/?character=shenron&clip=idle . Chưa ghi skills.md/receipt/version trước nghiệm thu.

## Owner undo8→4frame — 2026-11-15T09:19:02.430289+00:00
- Owner phản hồi: “cảm giác shenron tĩnh nhưng hoạt ảnh trôi quá nhanh”; loại bản8frame, không coi là nghiệm thu.
- Khôi phục nguyên snapshot trước nâng cấp cho assets + roster + timing:4frame,12tick/frame,800ms/cycle,scale2.4. AtlasSHA `86fafe02e99a86ef7c3cc58e9d26ac42e4bd44d5fc6c986c8cb56cdd2e25cfc3`.
- Bằng chứng rollback/hash/localhost và logs: `work/characters/shenron/idle-v2/rollback-evidence/`. Bản8frame chỉ giữ ở work để audit, không phục vụ live.

## Owner làm rõ chuyển động sóng +scale15%
- Đuôi phải uốn lượn qua hai phía theo sóng chạy dọc thânđuôi; hai râu cũng có pha uốn sóng, không chỉgiữhướng/di chuyểncảảnh.
- Dự kiến8pose toànthân mới theo0..7→0,đối chiếutừngpha/đoạncuốiđầu;khôngtáiápdụng8frameđãbịloại. Giữmaster/nhậndiện/mắtđỏmởvàstationary.
- Scalehiểnthị+15%:2.4→2.76;canvas/PNGkhôngresize. ĐãcậpnhậtcontractGodot/web.
- ChờOwnerchốtnhịpvòng:đềxuất1.6s;phươngán2.4s hoặcgiữ0.8s.

## Owner chốt bắt đầu wave8pose —1.6s/vòng
- Dựng8phase0..315°; giữmasterpixelởframe0,7wholebodyposesmới;khôngdùnglạibản8framebịloại.
- Timing12tick/frameở60Hz=200ms/frame,1600ms/vòng;scale2.76.
- Đuôi/râu cóuốnSqua2phía;đặcbiệtphase4đuôivềtrái,phase2/6qua giữa vớiđộcongngượcnhau.
- Canvasthêm16hàngtrongsuốtphíadướithành384×272đểgiữchópđuôiphahạthấp;giữnguyênanchor[192,240],pixelmastervàtỷlệthân.

## Wave8pose hoàn tất kỹ thuật — 2026-11-15T09:44:31.056582+00:00
- [x] Giữ master pixels ở frame0;7pose toàn thân mới theo phase45..315°, không tái sử dụng8frame cũ.
- [x] Đuôi uốnS sang hai phía: tail ROI trái[65,212,35,30] có288opaque px ởframe4/0px ởframe0; ROI phải[210,210,40,25] có274px ởframe0/0px ởframe4. Hai râu đổi độ cong theo pha, mắt luôn đỏ mở.
- [x] 1page1166×830,8frames,[12]×8tick ở60Hz=1600ms. Canvas384×272,anchor[192,240],scale2.76.
- [x] Đã mở filmstrip3nền,wholepose/diff và8nối frame gồm7→0; browser phát đúng0→7→0 và đo vòng1601.5/1597.6/1601.6ms.
- [x] Godotimport,WASMbuild,full `./loop.sh test` exit0; HTTP/hash/8RGBAatlasregions khớp,9bundleparity.
- [ ] Owner nghiệm thu tại http://localhost:8080/?character=shenron&clip=idle ; chưa ghi skills.md/receipt/version.

## Nhịp thở + triệu hồi — bản hiện tại
- [x] Thêm chu kỳ ngực/họng phồng–xẹp cho idle 8 pose, giữ pha sóng đuôi/râu; 1.6 giây/vòng, scale 2.76.
- [x] Tách 7 viên nguyên bản thành PNG riêng; thứ tự sao 1→7, bay từ người chơi đến tâm map, giữ đội hình ảnh 1 rồi chuyển cụm ảnh 2.
- [x] Nút Gọi Shenron, chuỗi 360 tick/60Hz (~6 giây); cụm rộng 240px, đáy Y840, Shenron tại X960 phía trên cụm, VFX sáng nhấp nháy.
- [x] Giữ đến khi Thu hồi; đã kiểm tra thu hồi và gọi lại.
- [x] Full ./loop.sh test exit 0; Godot/Rust/WASM/browser đối chiếu 15 mẫu, sai khác số học tối đa 0.000057706px do float32/float64. Dữ liệu atlas/tick dùng chung.
- [x] Review filmstrip 3 nền, vòng cuối→đầu và ảnh triệu hồi cuối.
- [ ] Owner Human Test bản breathing + summon tại http://localhost:8080/ (Tab Sân Tập → Gọi Shenron).
- QA: docs/characters/shenron-idle-v4-breath-qa.json và docs/characters/shenron-summon-v1-qa.json. Chưa ghi nghiệm thu vào skills.md.

## Bản hiện tại: idle-v5-hover + summon-v2
- Owner duyệt riêng đoạn ngọc bay; giữ PNG, quỹ đạo, timing và đội hình của đoạn này.
- Owner loại nhịp ngực v4: sửa thành dao động toàn thân.
- [x] Giữ nguyên whole poses sóng v3, dịch toàn pose dy [0,-1,-2,-1,0,1,2,1] px; 8×12tick/60Hz, scale2.76.
- [x] Hai chớp trắng, tắt hoàn toàn giữa hai nhịp: tick228..238 và246..256; cụm đất từ276, rồng từ300→360.
- [x] Cụm đất240→144px (-40%), native144×136, alpha cứng100%, Nearest. Một lần premultiplied-area từ nguồn; không AI redraw/ép Sobel/palette.
- [x] Hào quang vàng trắng luôn sáng; rồng hiện dần từ dưới lên trên nguồn sáng.
- [x] Review3nền/0→7→0, browser Thu hồi/gọi lại; full Godot/Rust/WASM test lần2exit0. Lần1 lỗi metadata path đã sửa, giữ log.
- [ ] Owner Human Test tại localhost:8080 → Sân Tập → Gọi Shenron. Chưa ghi skills.md/receipt/version.
- QA: docs/characters/shenron-idle-v5-hover-qa.json; docs/characters/shenron-summon-v2-qa.json.

## Đã nghiệm thu — 2026-11-15T12:36:59.698744+00:00
- [x] Owner Human Test combo Shenron thành công: “ok anh chốt combo gọi rồng thần này tiến hành chốt theo qui trình giúp anh nhé”.
- [x] Khóa byte/hash thân và ritual; receipt PIPE-017; frozen frames/ritual.
- [x] Ghi quy trình vào skills.md và đồng bộ phiên bản 0.13.0.
- Kiểm thử chốt cuối tại docs/releases/v0.13.0-shenron-tests.log.

## Đã nghiệm thu v0.13.1 / PIPE-018 (`pixel_dissolve`) — 2026-11-15T13:11:10+00:00
- [x] Owner duyệt bản `v3-pixel-dissolve`: “ok tiếp tục chốt kết quả này giúp anh theo quy trình rồi push lên main”.
- [x] Thay riêng reveal sau chớp trắng sang `pixel_dissolve` (`96x68` mask seed `17013`, cell `4x4 px`, `edge_width 0.07`, viền sáng `[255,236,156]`); giữ nguyên 7 viên ngọc bay, 2 chớp trắng, cụm đất `144x136` + aura và `idle-v5-hover`.
- [x] Godot OpenGL3 shader (`scenes/ShenronPixelDissolve.gdshader` + `canvas_anchor = -offset` trên `AnimatedSprite2D`) khớp `0` sai khác pixel (`alpha_diff=0`, `max_rgb_diff=0`) với Browser Canvas2D `applyShenronPixelDissolve` và đối soát 22 tick Godot⇄WASM.
- [x] Khóa 52 runtime files tại `assets/shenron/owner_approval.json` & `assets/rituals/shenron_summon/owner_approval.json`, đóng băng `work/rituals/shenron_summon/approved-final/`, ghi `PIPE-018` vào `skills.md` và đồng bộ `VERSION v0.13.1`.
- Báo cáo QA: [shenron-summon-v3-qa.json](characters/shenron-summon-v3-qa.json); release manifest: [v0.13.1-shenron-pixel-dissolve-finalization.json](releases/v0.13.1-shenron-pixel-dissolve-finalization.json).
