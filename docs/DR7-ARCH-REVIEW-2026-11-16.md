# DR7-Studio — Đánh giá kiến trúc & Yêu cầu sửa cho Agent

- **Ngày:** 2026-11-16 · **Phiên bản repo được xem:** v0.13.1 (commit `eb60064`, nhánh `main`)
- **Mục đích:** (1) đánh giá hiện trạng, (2) trả lời "có cần Rust không" cho tải 20 user + 20 quái/khu × 20 khu/map, (3) giao việc cho Agent, **ưu tiên số 1: kích thước 1:1 giữa localhost test và APK trên mobile mà không phải căn chỉnh lại**.
- **Cách đọc:** Phần 0 là kết luận. Phần 5 là phần giao việc (Agent đọc từ đó). Phần 6 là Owner cần chốt trước khi Agent làm (đúng Điều 2 `AGENTS.md`: mơ hồ → dừng & hỏi).

---

## 0. Kết luận nhanh

1. **1:1 hiện chỉ đúng ở mức "cùng thông số", chưa đúng ở mức "cùng kết quả hiển thị".** Preview `localhost:8080` là mô phỏng JS trên canvas, không phải Godot chạy. Các test parity so khớp cấu hình (JSON, hash, `project.godot`), không so khớp ảnh render. Chưa có `export_presets.cfg`, safe area, input cảm ứng, nên chưa có đường nào từ preview tới APK để kiểm chứng.
2. **Cách sửa gốc:** để **bản export Web của chính project Godot** làm nguồn chân lý cho preview (đặt trong khung thiết bị có profile W×H, DPR, safe area), JS canvas chỉ còn làm công cụ QA asset (scrubber, thước, Rect). Thêm bảng thiết bị mẫu, overlay thước dùng chung và test so số liệu `get_stage_metrics()` giữa Web và APK.
3. **Không phải máy nào cũng đạt pixel đều.** Với base 1920×1080 + `canvas_items` + `keep`, chỉ màn **cao đúng 1080 px** (Pixel 8, Galaxy S24, tablet FHD…) cho scale 1,000 → nhân vật 2× ra đúng 2 px/pixel art. iPhone Pro, QHD, máy 720p cho scale lẻ (1,09 / 1,19 / 1,33 / 0,67) → pixel không đều khi dùng Nearest. Đây là quyết định của Owner (Phần 6), không phải lỗi code.
4. **Rust không cần ở quy mô 20 user + 20 quái/khu × 20 khu/map**, cả client lẫn server. Đo thực trên Godot 4.7.2: 40 thực thể tốn ~0,03 ms/frame, 800 thực thể (cả map) ~0,83 ms. Điểm nghẽn thật là **mạng và hạ tầng**, không phải CPU: Supabase Realtime không dùng được cho combat 20 Hz (trần 100/500/2.500 msg/s tùy gói).
5. **Hiện có khoảng cách giữa tài liệu và thực tế:** `AGENTS.md` Điều 4, comment trong `CharacterFighter2D.gd` và `benchmark_report.json` ghi Rust tích hợp qua GDExtension là "đã chốt", nhưng repo **không có** `.gdextension` hay crate `godot`; Rust chỉ chạy native bench và WASM cho preview. Đang tồn tại hai bản mô phỏng song song, dễ lệch nhau.
6. **Repo nặng:** `work/` 594 MB (webm, ảnh `rejected/`, filmstrip), `.git` ~472 MB ở bản clone nông; 619/1.361 PNG trong `assets/` trùng nội dung. Cần dọn trước khi thêm APK/CI export.

---

## 1. Phạm vi & bằng chứng

| Việc đã làm | Việc **chưa** làm |
|---|---|
| Clone repo (read-only), đọc `AGENTS.md`, `project.godot`, `ci.yml`, `loop.sh`, `tools/preview/{index.html,server.py}`, `scenes/*.gd`, `tests/*`, `assets/maps/rocky_plateau/arena-stage.json`, `engines/*` | Chưa chạy CI, `./loop.sh check/test`, chưa chạy preview, chưa build/export APK |
| Chạy lại hàm benchmark của repo (`tests/bench_godot_2000.gd`) bằng Godot 4.7.2 headless ở 40/120/800/2000 thực thể | Chưa đo trên điện thoại thật, chưa đo có render, AI, kỹ năng, mạng |
| Tra tài liệu Godot (multiple resolutions) và Supabase Realtime limits | Chưa đọc hết `AGENTS.md`, `loop.sh check`; chưa xem lịch sử commit (clone nông 1 commit) |

Môi trường đo: Godot `4.7.2.stable`, headless, **1 vCPU Intel Xeon 2,1 GHz** (máy chủ sandbox, chậm hơn PC phát triển nhưng nhanh hơn nhiều điện thoại tầm thấp), 300 bước/mẫu.

---

## 2. Phần A — Kích thước 1:1 (localhost ↔ APK)

### 2.1. Định nghĩa "1:1" để kiểm thử được

Đề xuất tách làm 3 mức, mỗi mức có tiêu chí đo:

| Mức | Nghĩa | Tiêu chí (dung sai) |
|---|---|---|
| **L1 — Logic** | Cùng hệ toạ độ 1920×1080, cùng kích thước thân (px logic), `ground_y`, biên đi, spawn | Số liệu `get_stage_metrics()` giữa Web preview và APK **trùng tuyệt đối** (0 dung sai) |
| **L2 — Bố cục** | Cùng vị trí khung, dải đen, HUD, vùng an toàn trên cùng một thiết bị | Sai lệch vị trí ≤ 1 px thiết bị |
| **L3 — Pixel** | Mỗi pixel art ra số px thiết bị đều nhau | Đều tuyệt đối **chỉ khi** `char_scale × scale_viewport` là số nguyên; ngoài ra ghi nhận dung sai cho phép (Owner chốt) |

### 2.2. Hiện trạng (bằng chứng trong repo)

**Đã khớp (L1 ở mức cấu hình):**
- Preview và Godot cùng đọc `assets/maps/rocky_plateau/arena-stage.json`: viewport 1920×1080, `ground_y` 840, biên đi 140–1780, `character_scale_default` 2, texture filter `nearest`.
- `project.godot`: 1920×1080, `stretch/mode=canvas_items`, `stretch/aspect=keep`, `handheld/orientation=0`, `default_texture_filter=0`. CI khóa các giá trị này qua `verify_arena_stage_parity()` và `tests/test_arena_sandbox.gd`.
- Badge "Thân 2.5× ≈ 140×125px (11.6% 1080p)" tính đúng (125/1080).

**Chưa đạt:**

| # | Vấn đề | Bằng chứng | Hệ quả |
|---|---|---|---|
| A1 | Preview là mô phỏng JS, không phải Godot runtime | `tools/preview/index.html` tự vẽ bằng `ctx.drawImage`; test parity chỉ kiểm file/hash/số liệu | "1:1" = cùng thông số, chưa phải cùng pixel đầu ra |
| A2 | "Pixel thật 1:1" = 1920 **CSS pixel**, không xét `devicePixelRatio`; khi tắt, canvas co ~0,56–0,59× | `index.html` ~dòng 2383–2410 (khung tối đa 1140–1180 px) | Không dùng được để đánh giá độ nét trên máy thật |
| A3 | Không có profile thiết bị (tỉ lệ 19.5:9–20:9, notch, bo góc, thanh cử chỉ). Khung bezel là điện thoại 16:9 lý tưởng 2096×1166 | `arena-stage.json → phone_bezel` | L2 không kiểm được |
| A4 | Không có safe area, không có input cảm ứng, không có `[input]` trong `project.godot` | grep `safe_area`, `InputEventScreenTouch`: 0 kết quả | HUD/nút điều khiển mobile chưa test được ở đâu |
| A5 | Chưa có `export_presets.cfg`, `icon.svg`; chưa có lệnh build APK | thư mục gốc repo | Chưa có đường localhost → APK |
| A6 | Renderer `Forward Plus` trong khi nhắm Android/iOS 2D | `project.godot → config/features` | Web export của Godot cần renderer Compatibility (Agent xác minh trong tài liệu 4.7); khác renderer = khó đảm bảo parity pixel |
| A7 | Sprite scale lẻ + Nearest: 2.5×, 1.75× (T-rex), 1.5×… | `character_scale_presets=[1,1.25,1.5,1.75,2,2.5,3]`; `test_arena_sandbox.gd` chấp nhận scale lẻ | Pixel art không đều ngay cả trước khi nhân hệ số thiết bị |
| A8 | Map mẫu 1199×675 phóng ~1,6× lên 1920×1080 | `ArenaSandbox.gd` dòng 159–175 | Nền không đều khi Nearest (chấp nhận được với map mẫu) |

### 2.3. Bảng thiết bị mẫu (tính cho `canvas_items` + `keep`, base 1920×1080)

Độ phân giải theo thông số công bố thường gặp; Agent cần xác nhận lại khi chọn máy thật. `scale = min(W/1920, H/1080)`.

| Thiết bị | W×H | Tỉ lệ | Scale | Dải đen mỗi bên (px thiết bị) | px thiết bị / pixel art @2× | @3× | Pixel đều? |
|---|---|---|---|---|---|---|---|
| Tablet/TV box FHD | 1920×1080 | 1,78 | 1,000 | 0 | 2,00 | 3,00 | Có |
| Pixel 8 / nhiều Android 20:9 | 2400×1080 | 2,22 | 1,000 | 240 (trái/phải) | 2,00 | 3,00 | Có |
| Galaxy S24 | 2340×1080 | 2,17 | 1,000 | 210 | 2,00 | 3,00 | Có |
| iPhone 15 Pro | 2556×1179 | 2,17 | 1,092 | 230 | 2,18 | 3,27 | **Lệch** |
| iPhone 15 Pro Max / 16 Plus | 2796×1290 | 2,17 | 1,194 | 251 | 2,39 | 3,58 | **Lệch** |
| Android QHD 16:9 | 2560×1440 | 1,78 | 1,333 | 0 | 2,67 | 4,00 | **Lệch** |
| Android HD+ giá rẻ | 1600×720 | 2,22 | 0,667 | 160 | 1,33 | 2,00 | **Lệch** |
| iPad 10th gen | 2360×1640 | 1,44 | 1,229 | 156 (trên/dưới) | 2,46 | 3,69 | **Lệch** |

Kích thước vật lý: thân 11,6% chiều cao ≈ **7,5 mm** (6,1" 19.5:9) đến **8,1 mm** (6,7" 20:9). Tỉ lệ khớp, nhưng cảm giác to/nhỏ phải thử máy thật.

### 2.4. Phương án chính sách pixel (Owner chọn — Phần 6, D2)

Theo tài liệu Godot: `canvas_items` không còn tương ứng 1:1 giữa pixel sprite và pixel màn hình nên có thể sinh artifact; từ Godot 4.2 có `stretch/scale_mode` = `fractional` (mặc định) hoặc `integer` (làm tròn xuống số nguyên).

| Phương án | Mô tả | Ưu | Nhược |
|---|---|---|---|
| **A (hiện tại)** | `canvas_items` + `keep` + `fractional` | Lấp tối đa màn hình, chữ/UI nét ở độ phân giải thật | Pixel art không đều trên màn có scale lẻ (iPhone, QHD, 720p) |
| **B** | A + `integer` | Pixel đều tuyệt đối | iPhone 15 Pro chỉ dùng ~69% diện tích màn, Pro Max ~57%; màn < 1080 px cao cần kiểm hành vi riêng (không đoán) |
| **C** | `viewport` + `integer`, đổi base xuống ~960×540 | Lưới pixel chặt nhất | Đổi toàn bộ base/scale/hitbox/UI — thay đổi lớn, cần Owner duyệt riêng |
| **D** | Đổi `aspect` sang `keep_height`/`expand` | Lấp đầy màn 20:9 | Người chơi thấy sân rộng hơn (công bằng PvP?), phải sửa biên sân/camera/HUD |

**Khuyến nghị của reviewer:** giữ **A làm mặc định** (đã chốt và đã có test), thêm **công tắc "Pixel Perfect" = B** trong cài đặt người chơi, đặt "thiết bị chuẩn vàng" là màn cao 1080 px, và đo/ghi nhận dung sai cho nhóm còn lại. C/D chỉ làm khi Owner yêu cầu rõ.

### 2.5. Kiến trúc localhost test đề xuất

```
loop.sh web-export ──► build/web/ (export HTML5 của CHÍNH project.godot)
                              │
tools/preview/server.py ──────┤  phục vụ build/web trong "Khung thiết bị"
   ├─ device-profiles.json  ◄─┘  (W, H, DPR, safe-area insets, notch rects, bezel)
   ├─ Tab 1: Godot Web (nguồn chân lý L1/L2/L3)
   └─ Tab 2: JS canvas QA (scrubber, thước, Rect, [DR7-EDIT-SPEC]) — gắn nhãn "mô phỏng"
```

Điểm chính:
- Cùng `project.godot`, cùng scene, cùng stretch settings với APK ⇒ khớp theo cấu trúc, không theo "cố gắng giống".
- Khung thiết bị đặt kích thước cửa sổ Godot theo profile (W×H/DPR), kèm safe-area insets; đổi profile = đổi kích thước cửa sổ, không sửa code game.
- Overlay "Thước" **viết trong game** (debug build) và dùng chung với preview JS; mọi lần chạy ghi `get_stage_metrics()` ra JSON để so Web ↔ APK bằng số.
- Đổi nhãn "Pixel thật 1:1 (1920×1080)" thành "1 CSS px = 1 canvas px" để khỏi gây hiểu nhầm về pixel vật lý.
- Lưu ý kỹ thuật Agent phải xác minh trong tài liệu Godot 4.7 trước khi làm: renderer cho Web export, tùy chọn thread support và header COOP/COEP khi serve, export templates trong CI.

---

## 3. Phần B — Có cần Rust cho 20 user + 20 quái/khu × 20 khu/map?

### 3.1. Tải thực tế

| Phạm vi | Thực thể | Ghi chú |
|---|---|---|
| 1 khu | 20 user + 20 quái = **40** | Client chỉ mô phỏng/vẽ khu của mình |
| Khu + khu lân cận + đạn/FX | ~**120** (ước lượng) | Ví dụ khi đứng gần biên khu |
| Cả map | 20 × 40 = **800** | Chỉ **server** quan tâm; client không cần |
| CCU/map | 20 × 20 = 400 người chơi | |

### 3.2. Đo thực (hàm benchmark của repo, Godot 4.7.2 headless, 1 vCPU 2,1 GHz, 300 bước)

| Thực thể | Node2D/AnimatedSprite2D (ms/frame) | MultiMeshInstance2D (ms/frame) | % ngân sách 60 FPS (16,67 ms) |
|---|---|---|---|
| 40 | 0,029 | 0,031 | 0,2% |
| 120 | 0,073 | 0,105 | 0,4–0,6% |
| 800 | 0,830 | 0,835 | 5,0% |
| 2.000 | 1,888 | 2,069 | 11–12% |

So sánh số liệu trong repo (`engines/benchmark_report.json`): Rust 2.000 thực thể = 0,4246 ms (≈ 4–5× nhanh hơn GDScript), nhưng **khối lượng việc khác nhau** (Rust xử lý 11.260 hit, bản Godot trong report 69.353 hit, lần chạy lại này 240.944 hit) nên không so sánh công bằng. Cả `AGENTS.md` (~0,61 ms) và report (0,4246 ms) cũng đang lệch số.

**Giới hạn của benchmark (phải nói rõ):** vòng lặp "đồ chơi" (mỗi thực thể chỉ kiểm tối đa 4 ứng viên cùng một ô lưới, không xét ô lân cận), headless nên **không đo render** (draw call chỉ là ước lượng), không có AI, kỹ năng, hoạt ảnh, mạng, và chưa chạy trên điện thoại. Điện thoại tầm trung chậm hơn máy đo vài lần (ước lượng, chưa đo); ngay cả nhân hệ số 10, khu 40–120 thực thể vẫn dưới ~1 ms.

### 3.3. Phía server (tick 20 Hz = 50 ms)

- Toy benchmark: 800 thực thể ≈ 0,83 ms/tick ≈ **1,7%** ngân sách một lõi.
- Kịch bản thận trọng: logic thật nặng gấp 20 lần ⇒ ~16,6 ms ≈ 33% ngân sách một lõi cho **cả map 20 khu**. Vẫn khả thi với 1 tiến trình/map hoặc 1 tiến trình/vài khu.
- Băng thông (theo ước lượng AoI trong repo ≈ 1,6 kbps/thực thể ở 20 Hz): 40 thực thể ≈ **64 kbps/client**; 400 client/map ≈ **25,6 Mbps** tổng ra. Cần xác minh bằng prototype, nhưng không phải vấn đề CPU.

### 3.4. Điểm nghẽn thật: Supabase không phải game server real-time

Theo trang giới hạn chính thức của Supabase Realtime: messages/giây **Free 100 · Pro 500 · Pro không spend cap/Team 2.500**; kết nối đồng thời 200 / 500 / 10.000.

- 1 khu, 20 client × snapshot 20 Hz = **400 msg/s** giao đến client; cộng input 20 client × 20 Hz = 400 msg/s lên. Một khu đã vượt Free và sát trần Pro; cả map vài nghìn msg/s.
- (Chưa chắc cách Supabase đếm fan-out; kể cả đếm một chiều, kết luận về bậc độ lớn không đổi.)
- **Kết luận:** Supabase dành cho Auth, hồ sơ, trang bị, bang hội, lưu trữ (tần suất thấp). Combat real-time cần **game server riêng**.

### 3.5. Kết luận & ngưỡng quyết định

**Không cần Rust** cho quy mô này. Khuyến nghị: **server authoritative = Godot headless (dedicated server export), chạy cùng GDScript/scene với client** — một nguồn chân lý cho luật chiến đấu, không cần GDExtension, không phải giữ hai bản mô phỏng. Chỉ cân nhắc Rust khi một trong các điều kiện sau **đo được** (ngưỡng đề xuất, Owner/Agent có thể chỉnh):

| Điều kiện kích hoạt Rust | Cách đo |
|---|---|
| p99 thời gian tick server > 50% ngân sách (25 ms @20 Hz) ở tải mục tiêu, sau khi đã tối ưu GDScript (static typing, `Packed*Array`, spatial hash, không cấp phát trong tick) | Prototype 1 khu + 20 bot client, mở rộng đến 20 khu |
| Cần mô phỏng **deterministic** dùng chung client/server (rollback/lockstep) mà GDScript không đảm bảo được | Test lệch trạng thái sau N tick giữa hai nền tảng |
| Chi phí hạ tầng/CCU không chấp nhận được và profile chỉ ra CPU là nút cổ chai | Báo cáo chi phí theo CCU |

Nếu sau này cần Rust: ưu tiên dùng **rlib trực tiếp trong server Rust** (không cần GDExtension); GDExtension chỉ khi client phải chạy chung code mô phỏng (dự đoán phía client).

---

## 4. Phần C — Đánh giá tổng thể repo

Mức: **P0** chặn mục tiêu mobile/1:1; **P1** nên sửa sớm; **P2** dọn dẹp.

| ID | Mức | Hạng mục | Bằng chứng | Đề xuất |
|---|---|---|---|---|
| R1 | P0 | Preview không phải Godot runtime (A1) | `tools/preview/index.html` | Web export làm nguồn chân lý (Phần 2.5) |
| R2 | P0 | Không có đường APK: thiếu `export_presets.cfg`, icon, safe area, input cảm ứng (A4, A5) | gốc repo; grep 0 kết quả | Phase 1 (Phần 5) |
| R3 | P0 | Tài liệu nói GDExtension "đã chốt" nhưng không tồn tại | `Cargo.toml` không có crate `godot`; không có `*.gdextension`; `AGENTS.md` Điều 4; `CharacterFighter2D.gd` dòng 5 | Sửa tài liệu về hiện trạng; ADR cho Rust (Phase 2) |
| R4 | P0 | Hai bản mô phỏng song song (Rust cho preview/bench, GDScript cho game), số liệu lệch và khối lượng không tương đương | `benchmark_report.json` vs `bench_godot_2000.gd` vs `AGENTS.md` | Một nguồn chân lý (Godot headless server), regenerate benchmark cùng khối lượng |
| R5 | P0 | Không có code mạng (không `MultiplayerAPI`/ENet/WebSocket/`@rpc`/Supabase) dù mục tiêu 400 CCU/map | grep 0 kết quả ngoài tài liệu/log | Prototype netcode 1 khu (Phase 2) |
| R6 | P0 | Repo quá nặng | `work/` 594 MB; webm tới 12 MB tracked dù `.gitignore` có `/work/**/browser-video*/` (commit trước khi thêm rule); `offline-video` chưa có rule | `git rm -r --cached`, gom pattern; LFS hoặc `git filter-repo` để giảm lịch sử (Owner duyệt, D6) |
| R7 | P1 | 619/1.361 PNG trong `assets/` trùng nội dung (nhiều khả năng `clips/frames` ↔ `godot_bundle/godot-sprite3d/frames`) | md5 toàn `assets/` | Giữ một bản, bản còn lại sinh khi cần |
| R8 | P1 | `ArenaSandbox.gd` 791 dòng/37 hàm, gánh quá nhiều trách nhiệm; dữ liệu nhân vật đi qua `Dictionary` | `scenes/ArenaSandbox.gd` | Tách: loader roster/stage, controller AI, input, HUD, rendering debug; dùng `Resource` có kiểu |
| R9 | P1 | `CharacterFighter2D.set_facing_left()` đọc + parse JSON mỗi lần quay đầu | `scenes/CharacterFighter2D.gd` | Cache trong `_ready()` |
| R10 | P1 | Code runtime nằm trong `tests/` (`SkillAnimator2D.gd`, được `CharacterFighter2D` dùng) | `tests/`, `scenes/CharacterFighter2D.gd` | Chuyển sang thư mục script |
| R11 | P1 | 4 lớp con Fighter2D ghi đè cùng bộ hàm (`start_patrol`, `play_clip`, `_physics_process`…) | grep tên hàm | Data-driven / composition |
| R12 | P1 | `scenes/` phẳng 34 file lẫn scene/script/shader | `scenes/` | Chia `characters/<id>/`, `ui/`, `fx/` |
| R13 | P1 | Renderer Forward Plus cho game 2D mobile | `project.godot` | Chuyển Compatibility sau khi kiểm 2 shader (D3) |
| R14 | P2 | `state.json` 94 KB, `task_history` ~99 mục — dễ conflict | `state.json` | Tách history ra log append-only |
| R15 | P2 | Gốc repo: 4 ảnh `image*.png` + `.import`, `lerning.md` sai chính tả (108 KB), README 12 byte | thư mục gốc | Dọn/đổi tên/viết README |
| R16 | P2 | `.agent` là symlink tới `.agents` (hỏng trên Windows) | `ls -la` | Chọn một tên |
| R17 | P2 | CI chạy mọi push, cài Godot + import >1.300 resource, chưa cache | `ci.yml` | Cache cargo + `.godot`; job Android export tách riêng, chạy khi cần |

---

## 5. Phần D — Yêu cầu giao Agent

### 5.1. Quy tắc bắt buộc (kế thừa `AGENTS.md`)

- **Điều 1:** mọi nhận định phải kèm bằng chứng (lệnh + kết quả). Cấm đoán. Số liệu nào chưa đo thì ghi "chưa đo".
- **Điều 2:** các điểm D1–D6 (Phần 6) **chưa có quyết định thì dừng và hỏi Owner**, kèm phương án + ưu/nhược. Không tự chọn.
- **Điều 5:** tối đa **5 vòng sửa/vấn đề**; hết 5 vòng thì dừng và báo Owner (lỗi, bằng chứng, các cách đã thử).
- **Điều 8:** chạy `./loop.sh status` đầu phiên; cập nhật `state.json` sau mỗi task; bump `VERSION` (đồng bộ `project.godot`, `Cargo.toml`, `state.json`); `./loop.sh check` và `./loop.sh test` phải `exit 0`.
- **Không đụng** atlas/nhân vật đã duyệt (Owner approved), không đổi base 1920×1080 khi chưa có D2/D1 chốt, không viết GDExtension ở giai đoạn này, không tạo clip giả.

### 5.2. Phase 1 — Kích thước 1:1 (làm trước)

| ID | Việc | Tiêu chí nghiệm thu (DoD) |
|---|---|---|
| ARCH-101 | Tạo `assets/maps/rocky_plateau/device-profiles.json` (hoặc thư mục dùng chung): tên, W, H, DPR, safe-area insets, vùng notch/bo góc. Bao gồm tối thiểu 8 thiết bị ở Phần 2.3. Preview và Godot test cùng đọc file này | File được `verify_*` kiểm schema; không còn hằng số thiết bị rải rác trong JS/GD |
| ARCH-102 | `./loop.sh web-export`: export HTML5 của chính project vào `build/web/` (không commit); `server.py` phục vụ trong "Khung thiết bị" theo profile; tab JS hiện tại giữ lại, gắn nhãn "Mô phỏng"; đổi nhãn "Pixel thật 1:1" như Phần 2.5 | Chọn profile → cửa sổ Godot có đúng W×H/DPR; `get_stage_metrics()` in ra JSON; CI build được bản web (cần export templates) |
| ARCH-103 | Chuẩn bị Compatibility renderer (**chỉ sau D3**): kiểm `ChilopodaGroundClip.gdshader`, `ShenronPixelDissolve.gdshader`, MultiMesh | Test `test_shenron_dissolve_render.gd` và test 2 shader pass trên Compatibility; ghi khác biệt (nếu có) vào `lerning.md` |
| ARCH-104 | Lớp **SafeArea + Input cảm ứng**: autoload đọc `DisplayServer.get_display_safe_area()`; HUD/nút điều khiển neo trong vùng an toàn; khai báo `[input]` actions, hỗ trợ touch | Test với từng profile: không control nào nằm ngoài safe area; có test headless cho layout |
| ARCH-105 | **Overlay thước/lưới trong game** (debug build) dùng cùng định dạng với preview; ghi `stage_metrics.json` mỗi lần chạy | So sánh Web ↔ APK: L1 trùng tuyệt đối (script `tools/parity/compare_metrics.py`) |
| ARCH-106 | `export_presets.cfg` (Android; **không commit keystore/mật khẩu**, dùng biến môi trường), icon, `./loop.sh apk-debug`, hướng landscape + chế độ toàn màn hình/edge-to-edge | Build ra APK debug; ghi cấu hình tối thiểu theo tài liệu Godot 4.7 (Agent xác minh, không đoán) |
| ARCH-107 | Chính sách pixel theo D2: cài đặt runtime "Pixel Perfect" (tên thuộc tính `Window.content_scale_*` Agent xác minh trong docs 4.7); thử `snap_2d_transforms_to_pixel`/`snap_2d_vertices_to_pixel` và **đo**; kiểm hành vi khi màn < 1080 px cao | Báo cáo bảng 8 thiết bị × (fractional, integer): scale thực, dải đen, % diện tích dùng, ảnh chụp |
| ARCH-108 | Test render: Godot chạy frame ở từng profile (xvfb/software GL) → PNG → so với golden (đo L2/L3) | CI có job so sánh; dung sai ghi trong `docs/art-standards/` |
| ARCH-109 | **Smoke test thiết bị thật** (Owner cung cấp ≥3 máy: 1 Android 20:9 cao 1080, 1 iPhone, 1 máy khác tỉ lệ) bằng `adb shell screencap` + `stage_metrics.json` | Báo cáo trong `docs/releases/`; L1 = trùng tuyệt đối, L2 ≤ 1 px |

### 5.3. Phase 2 — Mạng & quyết định Rust (sau khi Phase 1 pass hoặc song song nếu Owner cho phép)

| ID | Việc | DoD |
|---|---|---|
| ARCH-201 | Viết ADR `docs/adr/0001-zone-server.md`: server authoritative = Godot headless; Supabase chỉ Auth/DB; ngưỡng kích hoạt Rust (Phần 3.5) | Owner ký duyệt |
| ARCH-202 | Sửa tài liệu: `AGENTS.md` Điều 4 (Rust = candidate/WASM preview, chưa tích hợp), comment trong `CharacterFighter2D.gd`, `benchmark_report.json`; thống nhất số liệu | `grep -r GDExtension` không còn khẳng định "đã tích hợp" |
| ARCH-203 | Regenerate benchmark **cùng khối lượng** cho Rust và GDScript, có render thật nếu được, có AI/kỹ năng mẫu; chạy ở 40/120/800 và trên ≥2 điện thoại | `engines/benchmark_report.json` v2 có mô tả khối lượng, môi trường, p50/p99 |
| ARCH-204 | Prototype 1 khu: 20 bot client + 20 quái, snapshot 20 Hz qua ENet/WebSocket, đo CPU server, băng thông/client, độ trễ | Báo cáo số thực; so với ước lượng 64 kbps/client |
| ARCH-205 | Mở rộng thử 20 khu/process và/hoặc 20 process | p99 tick, RAM, băng thông tổng; kết luận có cần Rust theo ngưỡng 3.5 |

### 5.4. Phase 3 — Dọn repo & code

| ID | Việc | DoD |
|---|---|---|
| ARCH-301 | `git rm -r --cached` các thư mục sinh ra/`rejected`/video; gom `.gitignore` thành pattern chung (`**/revision-*/`, `**/browser-video*/`, `**/offline-video*/`…) | `git ls-files` không còn webm/rejected; **chưa** viết lại lịch sử khi chưa có D6 |
| ARCH-302 | (Sau D6) LFS hoặc `git filter-repo` để giảm lịch sử | Kích thước clone mới ≤ mục tiêu Owner đặt; hash commit đổi — báo trước |
| ARCH-303 | Dedupe PNG trong `assets/` (R7), giữ SHA-256 đối soát | `./loop.sh check` pass |
| ARCH-304 | Cache JSON trong `set_facing_left()` (R9); chuyển `SkillAnimator2D.gd` khỏi `tests/` (R10) | Toàn bộ test Godot hiện có pass |
| ARCH-305 | Tách `ArenaSandbox.gd` (R8) theo trách nhiệm, giữ nguyên hành vi (test hiện có là lưới an toàn) | Không đổi hành vi; mỗi file < ~250 dòng |
| ARCH-306 | README đầy đủ (mục tiêu, phiên bản Godot, cách chạy preview/test, cấu trúc thư mục); đổi tên `lerning.md` → `learning.md` (cập nhật mọi tham chiếu trong `AGENTS.md`/`loop.sh`/test); dọn 4 ảnh ở gốc | `./loop.sh check` pass |
| ARCH-307 | Tách `task_history` khỏi `state.json`; CI cache (cargo, `.godot`); job Android export riêng | CI thời gian giảm có số liệu |

### 5.5. Mẫu lệnh giao việc (copy cho Agent)

```
Bạn là Agent của DR7-Studio. Đọc AGENTS.md, chạy ./loop.sh status, đọc docs/DR7-ARCH-REVIEW-2026-11-16.md.
Mục tiêu phiên này: Phase 1 (ARCH-101 → ARCH-109) — kích thước 1:1 giữa localhost test và APK mobile, không cần căn chỉnh lại.
Ràng buộc: tuân thủ Điều 1/2/5/8; không đoán; mọi số liệu kèm lệnh và kết quả; tối đa 5 vòng sửa/vấn đề.
TRƯỚC KHI CODE: kiểm tra D1–D6 trong Phần 6. Điểm nào chưa có quyết định của Owner thì DỪNG và hỏi Owner kèm phương án, ưu/nhược. Không tự chọn.
Không đụng nhân vật/atlas đã duyệt. Không viết GDExtension. Không commit keystore/mật khẩu.
Báo cáo cuối task: bảng tiêu chí DoD đạt/không đạt, bằng chứng, rủi ro còn lại, đề xuất bước tiếp.
```

---

## 6. Việc Owner cần chốt (Agent phải hỏi nếu thiếu)

| ID | Câu hỏi | Khuyến nghị của reviewer | Ảnh hưởng nếu chọn khác |
|---|---|---|---|
| **D1** | Khung hình trên máy 20:9: giữ `keep` (dải đen hai bên) hay mở rộng ngang? | Giữ `keep` (công bằng PvP, ít việc nhất); có thể vẽ nền trang trí vào dải đen | Mở rộng: phải sửa camera, biên sân, HUD, cân bằng tầm nhìn |
| **D2** | Chính sách pixel: A (fractional) mặc định + công tắc B (integer)? Hay C/D? | A mặc định + B tùy chọn | C: đổi base/scale/UI toàn bộ; D: xem D1 |
| **D3** | Cho phép đổi renderer sang Compatibility (để Web preview = renderer thật của mobile)? | Có, sau khi 2 shader pass | Giữ Forward Plus: Web export thật có thể không chạy, mất parity renderer |
| **D4** | Thiết bị "chuẩn vàng" và danh sách máy thật để test (≥3 máy)? | Màn cao 1080 px làm chuẩn L3 tuyệt đối; thêm 1 iPhone, 1 máy giá rẻ | Không có máy thật → L2/L3 chỉ là mô phỏng |
| **D5** | Server combat: Godot headless (khuyến nghị) hay server Rust? | Godot headless | Rust server: viết lại luật chiến đấu, phải đồng bộ hai bản, thêm công cụ test |
| **D6** | Dọn lịch sử git (`filter-repo`/LFS) hay chỉ ngừng track? Repo là fork của `pquangvinh1999-arch/DR7-Studio` | Ngừng track ngay; filter-repo khi đã backup và thống nhất với nhánh gốc | Viết lại lịch sử làm đổi hash, ảnh hưởng nhánh/fork khác |

---

## 7. Phụ lục — Tái lập số liệu

```bash
# Benchmark: Godot 4.7.2 headless, thay counts trong _init() của tests/bench_godot_2000.gd
curl -sSL -o godot.zip https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64.zip
unzip godot.zip && chmod +x Godot_v4.7.2-stable_linux.x86_64
# _init(): for n in [40, 120, 800, 2000]: chạy _run_node_tree_bench(n, 300) và _run_multimesh_bench(n, 300)
./Godot_v4.7.2-stable_linux.x86_64 --headless --path <project> --script res://tests/bench_zone.gd

# Scale thiết bị (canvas_items + keep): s = min(W/1920, H/1080); dải đen X = (W - 1920*s)/2
# px thiết bị trên mỗi pixel art = char_scale * s
```

Nguồn tham khảo: tài liệu Godot "Multiple resolutions" (stretch mode/aspect, `scale_mode` từ 4.2); Supabase Realtime Limits (`supabase.com/docs/guides/realtime/rate-limits`). Các giá trị độ phân giải thiết bị là thông số thường gặp, cần xác nhận khi test máy thật.
