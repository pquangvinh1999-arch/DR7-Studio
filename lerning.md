# NHẬT KÝ BÀI HỌC SỬA LỖI KỸ THUẬT (`lerning.md`)

> Lưu ý lịch sử: Owner đã yêu cầu xóa toàn bộ nhân vật, nguồn, bundle và gói xuất. Các đường dẫn/tên nhân vật và số đo trong bài học dưới đây chỉ ghi bằng chứng các phiên trước, không phải asset hiện còn hoặc chỉ dẫn phục hồi.


> **QUY ĐỊNH BẮT BUỘC (Theo Điều 8 — `AGENTS.md`)**:
> 1. **Khi nào ĐỌC**: Agent bắt buộc đọc file này trước khi xử lý sprite/atlas, viết script tách nền, đóng gói resource cho Engine (Godot / Rust) hoặc khi gặp lỗi runtime/build để tránh lặp lại vết xe đổ.
> 2. **Khi nào GHI**: Mỗi khi Agent gặp lỗi trong quá trình làm việc, **sau khi đã tìm ra nguyên nhân gốc (root cause) và sửa thành công có kiểm chứng**, Agent phải ghi ngay 1 mục mới (`### [LRN-XXX] ...`) vào giữa hai thẻ đánh dấu bên dưới.

<!-- LERNING_ENTRIES_START -->

### [LRN-001] Nhiễu viền Magenta (`outer_ring_spill`) phát sinh trở lại sau khi thu nhỏ bằng Lanczos & thứ tự gọi `despill`
- **Bối cảnh**: Thu nhỏ các frame RGBA đã tách nền `#FF00FF` bằng nội suy `Image.Resampling.LANCZOS` và chạy `forge_matte.despill`.
- **Triệu chứng lỗi**:
  1. Gọi trực tiếp `.save()` lên kết quả trả về của `forge_matte.despill()` gây `AttributeError` vì hàm trả về tuple `(rgba_array_or_image, report_dict)`.
  2. Nếu chạy `despill` **trước** khi loại bỏ triệt để các hốc màu hồng khép kín (`enclosed_key_pockets`) nằm kẹt giữa cánh tay/chân và hào quang, `despill` hạ kênh `R` và `B` xuống bằng `G`, biến hốc nền hồng thành mảng màu xanh rêu tối (`RGB ~ [64, 80, 37]`) khiến `matte_qa` báo giả `enclosed_key_pockets = 0`.
- **Nguyên nhân gốc**: Chưa đục thủng toàn bộ vùng màu nền kẹt trong hốc kín trước khi khử ám màu (`despill`).
- **Cách sửa đã kiểm chứng**:
  1. Luôn kiểm tra và loại bỏ sạch 100% hốc nền kín (`enclosed_key_pockets == 0` trên ảnh chưa `despill`) **trước** khi gọi `despill`.
  2. Giải nén tuple kết quả của `forge_matte.despill(im, radius=2, key="magenta")` an toàn.

### [LRN-002] Lỗi broadcast mảng mặt nạ 1D sang 2D trong NumPy khi căn khớp bóng (silhouette registration)
- **Bối cảnh**: So khớp độ lệch `(dx, dy)` trên vùng rìa ngoài (`outer_m`) của frame hiệu ứng 2D kích thước `(H, W)`.
- **Triệu chứng lỗi**: `IndexError: boolean index did not match indexed array along axis 0`.
- **Nguyên nhân gốc**: Tạo `xx_c = np.arange(W)[None, :]` cho ra mảng `(1, W)` thay vì `(H, W)` rồi dùng trực tiếp làm boolean mask cho mảng 2D.
- **Cách sửa đã kiểm chứng**: Dùng mảng 1D rõ ràng theo trục cột `outer_1d = np.abs(np.arange(W) - cx) > margin` và cắt lát tường minh `rolled[:, outer_1d]`.

### [LRN-003] Godot quét nhầm các thư mục trung gian (`source/`, `clips/`, `engines/`) gây phình `.import`
- **Bối cảnh**: Xuất gói sprite vào `assets/<character>/godot_bundle/` và biên dịch Rust crate trong `engines/rust_combat_sim/target/`.
- **Triệu chứng lỗi**: Godot `--headless --import` quét toàn bộ PNG trung gian và thư mục build bên ngoài gói `godot_bundle`.
- **Cách sửa đã kiểm chứng**: Luôn tạo file rỗng `.gdignore` bên trong `source/`, `clips/`, `.agents/` và `engines/` để Godot chỉ nạp đúng thư mục tài nguyên chính thức.

### [LRN-004] Bảo vệ tông da đổ bóng ấm & chân ngọn lửa vàng khi khử ám hồng và xoá vệt watermark trắng + giữ chiều sâu 3 lớp `z = -1 / 0 / +1`
- **Bối cảnh**: Bóc tách nguyên bản mẫu Son Goku Super Saiyan từ `raw_input_atlas.png` (`1311x231`, nền hồng có sọc trắng watermark cắt ngang).
- **Triệu chứng lỗi**:
  1. Nếu lọc viền hồng cam của hào quang bằng ngưỡng rộng `G - B < 30` trên cả 8 frame, các pixel da cánh tay đổ bóng ấm ở Frame 1–2 bị kéo sang màu vàng chanh.
  2. Nếu xoá vệt trắng watermark dưới đế chân Frame 4 bằng hộp chữ nhật cứng không kèm điều kiện kênh `Blue`, góc chân ngọn lửa vàng (`Blue < 60`) sát giày phải bị lẹm mất vài pixel.
  3. Nếu dồn toàn bộ hiệu ứng vào 1 lớp `z = -1` sau lưng, các tia lửa/sét vàng đè trước ống chân và sóng xung kích mặt đất ở `z = +1` bị mất chiều sâu không gian 3D.
- **Nguyên nhân gốc**: Da người đổ bóng ấm luôn có `Green >= Blue + 18` trong khi pixel pha hồng-vàng thật sự có `Blue >= Green - 6`; vệt trắng watermark có `Blue > 135` còn lửa vàng có `Blue < 80`.
- **Cách sửa đã kiểm chứng**:
  1. Chỉ khử ám hồng-cam trên các frame có hào quang (`owner >= 3`) tại pixel thỏa `Blue >= Green - 6`, và chỉ xoá vệt xước watermark trắng ở khe sóng xung kích khi `Blue > 135`.
  2. Kiến trúc tách lớp bắt buộc tách đủ 3 tầng chiều sâu: `BackAura (z = -1)` + `Body (z = 0)` + `FrontFX (z = +1)`.

### [LRN-005] Lệch chữ ký hàm C-ABI giữa JS và Rust WASM (`wasm_count_aoi`), treo vòng lặp `requestAnimationFrame` & kẹt nút Phát cuối clip `oneshot`
- **Bối cảnh**: Giao diện 3 Tab tại `tools/preview/index.html` gọi module WebAssembly `rust_combat_sim.wasm` (`engines/rust_combat_sim/src/lib.rs`).
- **Triệu chứng lỗi**:
  1. Bấm sang Tab 2 (`Stress Test >2,000 User`) và Tab 3 (`Sân Tập`) không hiển thị hình ảnh; quay lại Tab 1 hoạt ảnh đứng im và bấm nút `▶ Phát` không chạy.
  2. Kể cả khi chưa sang Tab 2, các clip `oneshot` (`loop = false` như `power_up`, `focus_ki`) sau khi chạy hết frame cuối vẫn giữ `playing = true` và khi bấm `▶ Phát` không tự tua `stepIdx` về `0`.
  3. Ngoài ra, thứ tự 8 float trong `gpu_instances` của `lib.rs` (`facing` ở vị trí `2`) bị lệch với thuộc tính WebGL2 `iUv` (đọc từ vị trí `2..5`), và JS trong `index.html` bị gán cứng chuỗi `'songoku_ssj_*'` gây cản trở mở rộng nhiều nhân vật.
- **Nguyên nhân gốc**:
  1. Hàm `CombatWorld::count_aoi_entities` có trong Rust nhưng chưa xuất `#[no_mangle] pub extern "C" fn wasm_count_aoi`, gây lỗi `TypeError: stress.wasm.wasm_count_aoi is not a function` ngay khi mở Tab 2.
  2. Lệnh `requestAnimationFrame(mainLoop)` đặt ở cuối hàm `mainLoop` không bọc `try/catch`, nên 1 ngoại lệ ở Tab 2 làm chết vĩnh viễn vòng lặp vẽ của cả 3 Tab.
  3. Bộ test Python trước đó chỉ kiểm tra kích thước file `.wasm` mà chưa chạy kiểm thử đối chiếu danh sách export JS ⇄ WASM bằng Node.js.
- **Cách sửa đã kiểm chứng**:
  1. Xuất đầy đủ `wasm_count_aoi` & `wasm_clip_step` trong `src/lib.rs`, đồng bộ chính xác mảng GPU `[0:x, 1:y, 2:u, 3:v, 4:uw, 5:vh, 6:facing, 7:flash]`.
  2. Đặt `requestAnimationFrame(mainLoop)` lên dòng đầu tiên của `mainLoop` kèm `try/catch` hiển thị cảnh báo trực quan; tự tua `stepIdx = 0` khi bấm `▶ Phát` ở cuối clip và thêm tuỳ chọn `🔁 Tự lặp clip ngắn`.
  3. Xoá sạch mọi tên bundle gán cứng trong `index.html` (đọc động hoàn toàn từ `roster.json`) và bổ sung bài kiểm thử tự động `tests/test_frontend_wasm_e2e.mjs` chạy trực tiếp trong `./loop.sh test` và CI.

### [LRN-006] Cắt cụm 2D chống dính kiếm chéo / chữ thừa lấn hàng, khử viền vàng-pha-xanh (`#2B3772`) & khởi tạo trễ Node con trong Godot Headless `SceneTree._init()`
- **Bối cảnh**: Bóc tách nhân vật chính thức đầu tiên của Studio — `Future Trunks (Super Saiyan Rage)` (`trunks_rage`, `154` frame, `20` clip trên khung `320×256`, `anchor_px = [96, 220]`) từ sheet `TRUNKS RAGE SWL+` (`1185×2000`, nền xanh tím than `#2B3772`) và kiểm thử tự động trên Godot 4.7.2 Headless.
- **Triệu chứng lỗi**:
  1. Ở các hàng chém kiếm chéo (`R05`, `R13`, `R14`, `R15`), mũi kiếm vươn sang vùng cột X của pose kế bên; nếu cắt hộp chữ nhật thông thường sẽ dính mũi kiếm hàng xóm. Đồng thời ở ranh giới dọc giữa hai hàng sát nhau (`R10` giáp tia nổ `R11`, `R15` giáp nhãn chữ `"WIN"` và `R16` thắng trận), đỉnh chữ `"WIN"` (`y=1778..1784`) hoặc tia nổ hàng dưới chạm nhẹ vào cửa sổ quét hàng trên, còn đỉnh tóc nhọn `R16` (`y=1794..1802`) dễ bị cắt phẳng nếu đặt `y0` quá thấp.
  2. Trên nền xanh tím than `#2B3772` (`RGB 43, 55, 114`), biên hào quang vàng chanh `#F8FF0B` pha 50/50 tạo ra viền `1px` màu xanh rêu xám (`R~145, G~155, B~62`) không còn mang sắc xanh dương trội (`B > R`), nên bộ lọc viền indigo thông thường bỏ sót.
  3. Khi chạy kiểm thử prefab `Trunks_Rage.tscn` bên trong `SceneTree._init()` (`test_character_bundles.gd`), các biến `@onready var sprite = $Sprite` của `CharacterFighter2D.gd` vẫn bằng `null` vì `root` chưa bước vào chu kỳ `_ready()`, khiến `play_clip(&"idle")` trả về `false`.
- **Nguyên nhân gốc**:
  1. Sprite sheet tổng hợp bố trí các pose sát nhau theo hình dáng 2D tự do chứ không theo lưới ô vuông đều, kèm nhãn chữ chú thích nằm sát chân nhân vật.
  2. Pha tuyến tính giữa màu vàng (`B thấp`) và nền xanh tím (`B cao, R/G thấp`) triệt tiêu độ chênh kênh `B - G`, tạo màu trung tính rêu xám ở đúng vòng `1px` sát nền.
  3. Trong Godot 4, script kế thừa `SceneTree` chạy hàm `_init()` trước khi cây scene kích hoạt callback `_ready()` của các node con mới `add_child`.
- **Cách sửa đã kiểm chứng**:
  1. Dùng mặt nạ sở hữu liên thông 2D (`2D Component Ownership Masking`) kết hợp `extra_exclusions` khoanh chính xác vùng nhãn chữ `"WIN"` / tia nổ lấn hàng và kiểm tra trực quan toàn bộ `20/20` file `filmstrip-*.png` trên 3 nền sáng/tối/ô cờ.
  2. Bổ sung pha khử viền `olive_fringe` cho các pixel biên `1px` kề sát vùng vàng sáng (`w_yel = (114 - B) / 99`), đạt `opaque_key_px = 0`, `enclosed_key_pockets = 0`, `outer_ring_spill_fraction = 0.0001`, `alpha_hardness_pct = 98.7%`.
  3. Cài đặt hàm `_ensure_nodes()` dùng `get_node_or_null("Sprite")` và `get_node_or_null("SkillAnimator")` ngay đầu `play_clip()` / `has_clip()` trong `CharacterFighter2D.gd`, giúp prefab hoạt động tức thì cả trong `SceneTree._init()` lẫn trong game thực tế; đồng thời chuyển toàn bộ UI `index.html` sang đọc kích thước Canvas động `[cw, ch]` từ `roster.json`.

### [LRN-007] Khác biệt độ nét giữa ảnh gốc không nén trong Workspace (`1340×2261`) so với bản đính kèm bị thu nhỏ qua Chat (`1185×2000`), ghép hiệu ứng rời trên Sheet & lỗi so sánh mảng khác Realm trong Node `vm`
- **Bối cảnh**: Khôi phục phiên làm việc `TASK-006` của nhân vật `trunks_rage` và chạy kiểm định toàn diện `./loop.sh test` + đối chiếu trực quan 20 dải `filmstrip-*.png`.
- **Triệu chứng lỗi**:
  1. File đính kèm qua giao diện chat (`uploaded_media_*.png`) tự động bị thu nhỏ chiều cao tối đa về `2000px` (`1340×2261` → `1185×2000`, tỷ lệ lẻ `0.8845x`), làm nhòe bảng màu Pixel Art gốc từ `30` màu/pose lên `1,897` màu nội suy, trong khi bản gốc không nén `image.png` (`1340×2261`, `100%` nền thuần `#2B3772`) lại nằm ở thư mục gốc workspace (gây sinh thêm `image.png.import`).
  2. Trên sheet gốc `TRUNKS RAGE SWL+`, một số hiệu ứng đòn đánh (`R07` tia chưởng/nổ `ki_blast`, `R13[16]` chém chữ X vàng cuối `burning_sword`, `R15[11]` cột năng lượng xanh cuối `ultimate_spirit_sword`) được họa sĩ vẽ tách rời bên phải tư thế nhân vật, và cánh sét bên phải của `R07[3]` (`aura_loop`) tách thành cụm riêng `R07[4]`. Nếu đưa thẳng cụm hiệu ứng rời thành frame độc lập, thân nhân vật sẽ biến mất ở frame nổ chiêu.
  3. Trong `tests/test_frontend_wasm_e2e.mjs`, gọi `assert.deepEqual(T.getCanvasSize(), [320, 256])` (với `strict` assertion) báo `AssertionError` dù giá trị `[320, 256]` giống hệt nhau, do mảng trả về từ `vm.runInContext` mang `Array.prototype` của Realm bên trong sandbox khác với `Array.prototype` của Node ESM bên ngoài.
- **Nguyên nhân gốc**:
  1. Cơ chế nén/resize media của kênh chat thu nhỏ ảnh lớn hơn `2000px` bằng nội suy tuyến tính.
  2. Sprite sheet kiểu JUS/SWL+ tách riêng thân nhân vật và projectile/pillar FX để tiết kiệm diện tích vẽ.
  3. `node:assert/strict` kiểm tra chặt `Object.getPrototypeOf(actual) === Object.getPrototypeOf(expected)` giữa hai V8 Context khác nhau.
- **Cách sửa đã kiểm chứng**:
  1. Chuyển bản gốc không nén `1340×2261` vào `assets/trunks_rage/source/raw_trunks_rage_atlas.png` (xoá sạch `image.png` & `image.png.import` ở thư mục gốc), tách nền bit-exact `#2B3772` đạt `alpha_hardness_pct = 100.0%`, `outer_ring_spill_fraction = 0.0`, `opaque_key_px = 0`, `enclosed_key_pockets = 0`, `edge_acutance_sobel = 392.07`.
  2. Hợp nhất cánh sét đôi `R07[3] + R07[4]` cho `aura_loop`, đồng thời dùng `composite_fx_ahead()` ghép liền mạch tia nổ `ki_blast`, chém chữ X `burning_sword` và cột kiếm khí `ultimate_spirit_sword` ngay trước mũi kiếm/bàn tay Trunks trên khung `320×256` (`Combined 1-Layer`), kiểm chứng trực quan 20/20 `filmstrip-*.png`.
  3. Chuẩn hoá mảng qua `Array.from(T.getCanvasSize())` trước khi `assert.deepEqual` khi kiểm thử code chạy trong `vm.runInContext`, đồng thời thêm khóa tự đồng bộ `_lastWasmClipKey` ngay đầu `stepInspectorAnimation()` trong `tools/preview/index.html` để `wasm_clip_set_len` luôn khớp số frame của clip đang phát.

### [LRN-008] Hỗ trợ Roster rỗng (`0` nhân vật), lỗi suy luận kiểu `Variant` trong Godot 4.7.2 GDScript & DOM `appendChild` trong Node VM E2E Test
- **Bối cảnh**: Xoá sạch nhân vật `trunks_rage` (`assets/trunks_rage/`, `scenes/Trunks_Rage.tscn`, `tools/pipeline/build_trunks_rage.py`, placeholder trong `index.html`/`server.py`/`main.rs`) để đưa dự án về trạng thái sạch `0` nhân vật sẵn sàng nhận Atlas mới, và chạy lại toàn bộ kiểm định engine.
- **Triệu chứng lỗi**:
  1. Khi chạy độc lập `./tools/godot/godot --headless --path . --script res://tests/bench_godot_2000.gd`, Godot 4.7.2 báo lỗi biên dịch: `Parse Error: The variable type is being inferred from a Variant value, so it will be typed as Variant. (Warning treated as error.)` tại biểu thức ternary `var anim := &"aura_loop" if ... else sf.get_animation_names()[0]`.
  2. Ở Tab 3 (`Sân Tập`) khi thay thế các nút chiêu thức tĩnh của Trunks bằng `renderArenaControls()` sinh nút động từ `roster.json`, nếu dùng chuỗi `.innerHTML` + `querySelectorAll` sẽ không tạo nút bấm được trong sandbox `MockElement` của `tests/test_frontend_wasm_e2e.mjs` (vì `MockElement` lưu node qua `appendChild` / `children` và không parse HTML string); ngoài ra kiểm thử đánh cận chiến `attack_light` (`range = 170`) ở khoảng cách mặc định `360px` sẽ đánh trượt bù nhìn nếu không di chuyển nhân vật vào tầm đánh.
- **Nguyên nhân gốc**:
  1. Godot 4 coi kết quả ternary giữa `StringName` (`&"aura_loop"`) và phần tử lấy từ `PackedStringArray` (`String`) là kiểu hỗn hợp `Variant`, kích hoạt warning-as-error khi dùng toán tử `:=`.
  2. Môi trường kiểm thử headless Node `vm` giả lập DOM tối giản qua `document.createElement` + `appendChild`.
- **Cách sửa đã kiểm chứng**:
  1. Khai báo kiểu tường minh trong `tests/bench_godot_2000.gd`: `var anim: StringName = &"aura_loop" if sf.has_animation(&"aura_loop") else StringName(sf.get_animation_names()[0])`, đồng thời chuẩn bị sẵn `SpriteFrames` rỗng trong bộ nhớ khi `roster.json` có `0` nhân vật.
  2. Tạo các nút chiêu thức động ở `#arenaSkillButtons` trong `tools/preview/index.html` hoàn toàn bằng `document.createElement('button')` + `appendChild()`, và đặt lại vị trí nhân vật vào tầm cận chiến (`dist = 120 <= 170`) khi test `attack_light` trong `tests/test_frontend_wasm_e2e.mjs`.

### [LRN-009] Sheet sinh theo frame phải kiểm tra ownership và alpha thực trước khi đóng gói
- **Bằng chứng**: super take đầu tại `work/characters/hammer-human/atlas-v1/source/super_hammer_return/sheet-v1-rejected.png` (1983×793), ô thứ ba `Rect(793,0,397,396)` chỉ có cụm bạc lớn nhất 38 px; các ô có đầu búa đo được 2240–3664 px. Take gồng Ki đầu có 1360 pixel alpha ≥128 trên ranh giới ô. Không coi một grid đều hoặc prompt “đủ búa” là bằng chứng pose đúng.
- **Sửa đã kiểm chứng**: dựng lại super 9 pha, sửa halo, đổi chân dẫn ở nửa sau walk/run, giữ toàn bộ island theo nhãn sở hữu 2D trước crop; giữ một scale mỗi action và truy vết affine trong `registration-report.json`. Kết quả 63 frame/10 clip: builder `--strict` exit 0, warnings=0; exporter một trang exit 0; Godot kiểm tra đủ 63 texture exit 0; mở đủ 10 filmstrip trên sáng/tối/ô cờ.
- **Alpha / schema**: mẫu background tại (400,250) của take attack_light là RGBA (73,61,35,0): RGB khác đen dưới alpha 0 không phải nền đặc. Chỉ phân tích pixel có alpha và ghi rõ native-alpha không phải chroma QA. Builder từ chối `art_source="built-in image_gen"` với `error: art_source must be one of host_image, api, code, existing, video, mixed.`; dùng enum `host_image`, ghi tên tool thật riêng trong provenance.

### [LRN-010] Xuất Godot bằng tick nguyên, không ép FPS qua milliseconds đã làm tròn
- **Bằng chứng**: bản `godot-final/godot/hammer_human.tres` được xuất với `--godot-fps 60` có duration walk `7.02`, `6.96` thay vì `7.0`; Godot báo `Assertion failed: Tick duration differs`. Nguyên nhân: nhánh fixed-FPS chuyển preview milliseconds nguyên thành duration, trong khi nguồn đã có ticks 60Hz.
- **Sửa đã kiểm chứng**: để exporter chọn timing tự động từ ticks; bản bàn giao có `godot.basis="ticks at 60 Hz"`, speed 60, duration walk toàn `7.0`. Godot 4.7.2 nạp/đối chiếu 63 frame, duration, loop, anchor và demo đều exit 0.
- **Parity localhost**: bỏ phép làm tròn 0.01ms trong `parse_tres`; gửi trực tiếp `duration_ticks / speed_hz * 1000` cho browser/Rust WASM. Test mới kiểm tra timing phân số và tổng timeline; HTTP kiểm tra cùng PNG SHA-256, canvas/anchor và timing, exit 0. Milliseconds nguyên trong preview/JSON không thay thế timeline tick của `.tres`.

### [LRN-011] E2E roster phải tính cả nhân vật thật và fixture tổng hợp
- **Bằng chứng**: sau khi thêm human dùng búa, `test_frontend_wasm_e2e.mjs:362` thất bại `Roster list must render all N finalized characters`, actual `3`, expected `2`. Dữ liệu kiểm thử đọc roster thật rồi thêm hai fixture, nhưng assertion vẫn cố định 2.
- **Sửa đã kiểm chứng**: chụp `expectedRosterCount = current roster length + 2` trước khi thêm fixture; không xoá hoặc sửa roster để khớp test. `./loop.sh test` exit 0: 12 Python/E2E, Godot 10 clip và 2 Rust. WASM release build exit 0, SHA-256 trùng artifact đang phục vụ. WARN `jump, guard, win` được giữ, ghi rõ Owner loại ba clip này riêng cho nhân vật.

### [LRN-012] Kiểm định atlas không thay thế kiểm tra chuyển động và contract FX
- **Bằng chứng**: Owner chỉ ra walk #6/#7 vấp và heavy #1 cán cong trong bản v1 dù kiểm thử file/timing đã qua; screenshot vị trí Atlas(1257,813) thuộc vùng Rect(1167,783,384,256). Xác nhận mới yêu cầu loop đủ #0–#7, bỏ run riêng nhân vật và tách aura/búa.
- **Sửa đã kiểm chứng**: v2 sửa đúng #6/#7 walk, heavy #1, giữ byte 38 frame không đổi; tách island búa ở #2–#5 (3099/2347/2108/2228 px); body luôn hiện, một búa bay, ẩn khi bắt #6. Godot và browser dùng cùng render_contract: aura clock độc lập, incoming spin 3→2→1→0, hồi #5–#8. Standalone Godot 69 frame/12 clip, ./loop.sh test (13 Python/E2E, 2 Rust) đều exit0; metadata/ticks/PNG HTTP trùng. Chưa coi Owner đã nghiệm thu chuyển động v2.
- **Phạm vi QA alpha**: raw PNG so với texture Godot có RGB khác dưới alpha0 vì importer lấp màu vô hình; assertion byte-RGBA thô báo `atlas/PNG import differs: idle:0`. So khớp mọi alpha và RGB có alpha>0; checksum PNG vẫn kiểm tra byte nguồn. Không bỏ kiểm tra pixel nhìn thấy. Key nền xám chỉ áp dụng 17 frame FX lấy từ sheet: kết quả 0 residue/0 partial alpha. Búa vật lý có 266 pixel viền tối hợp lệ cùng dải màu xám; không xóa viền búa theo phép dò nền FX.
- **Chi phí**: thân nguyên một sprite; aura/búa/trail thêm quad theo ngoại lệ Owner đã ghi. Dùng một trang atlas không chứng minh cả tổ hợp chỉ 1 draw call. Không sửa skill chung để biến ngoại lệ của một nhân vật thành mặc định.

### [LRN-013] Gate sổ tay phải dựa vào bằng chứng nghiệm thu
- Test cũ yêu cầu số mục skills.md luôn bằng0; điều này chỉ đúng trước khi Owner nghiệm thu. Sau Owner xác nhận “ok nhân vật này đã xong”, gate được đổi để mỗi mục PIPE cần receipt owner_approved, đúng character_id và hash atlas đã duyệt. Không bỏ gate hoặc tạo xác nhận thay Owner. ./loop.sh test sau cập nhật exit0 (13 Python/E2E, Godot12clip,2Rust); gói mang tên Crep_Xayda_01 kiểm tra Godot69frame/FX exit0. Nghiệm thu hoạt ảnh không xác nhận Android export/device test.

### [LRN-014] Alpha yêu cầu, nền FX nhiễu và role clip cần kiểm tra trên dữ liệu thật
- **Alpha nguồn**: dải fly đầu có Canvas(0,0) RGBA(253,253,253,150), alpha136..252 dù yêu cầu transparency; attack_wing alpha230..250. Không threshold128 rồi nhận đã tách nền, cũng không key trắng mọi pixel vì mắt/giày/cánh có trắng thật. Đã tạo take khôi phục alpha cho3dải, giữ nguồn cũ trongwork; ownership mask, palette24màu và lưới2× hoàn thiện61PNG đều binary alpha.
- **FX super**: source backgroundRGBA(101,101,129,255), tolerance20 còn nhiễu màu quanh đạn. Review20/35/50/65 trên sáng/tối; chọn50, key pocket-first+edgeunmix,32-color shared palette. Phase0 loại1328pixel so bản trước; ví dụ Canvas(72,164) từRGBA(226,86,209,255) thành(0,0,0,0). Hash55frame thân giữ nguyên. Không áp ngưỡng này cho palette thân hoặc sheet khác.
- **Role khi chạy lại**: lấy `body=list(plan.clips)` sau khi plan đã cóFX khiến admission tìm `source/aura_loop/sheet.png` và FileNotFoundError, tạo bundle dang dở ngoài roster. Sửa lọc `role != fx`; assert tập body/effect rời nhau trong test; stage ngoàiassets, chỉ chuyển vào khi đã đủ nguồn/QA. Bản dở lưu ngoàiassets, roster sạch.
- **Kiểm chứng**: builder strict warnings0; exporter1page; standaloneGodot61frame/11clip+runtime bay/Ki/đạn exit0; ./loop.sh test13Python/E2E+Godot2bundle+2Rust exit0. HTTP PNG/tick/anchor/contract khớp. Ghi chú lịch sử: master từng được duyệt, nhưng Owner sau đó loại toàn bộ Tambourine vì không đạt; các số PASS kỹ thuật trên không phải nghiệm thu chất lượng. Asset và bundle đã xóa theo yêu cầu Owner.

### [LRN-015] Ki độc lập không bắt buộc nhân vật có đạn
- **Bằng chứng code**: khi rà checkpoint, renderer đọc `p.kind` ngay sau `const p=contract.projectile`; contract có body/aura nhưng không có projectile chưa được xử lý. Ki độc lập là mặc định Owner, không đồng nghĩa mọi nhân vật phải có chưởng.
- **Sửa đã kiểm chứng**: trả về các lớp body/aura khi projectile không được khai báo; gợi ý điều khiển không áp bộ đòn/chạy/nhảy của nhân vật cũ cho mọi contract. E2E dùng fixture có walk và aura nhưng không có projectile: aura đổi pha trong khi frame thân giữ nguyên, tắt aura còn thân và renderInspector không báo lỗi. ./loop.sh test exit0:13Python/E2E,Godot roster0,2Rust. Đây là kiểm chứng contract tổng hợp, không phải nghiệm thu một nhân vật mới.

### [LRN-016] Lọc liên thông từng bộ phận giải phẫu, xử lý render_contract không có aura_loop và đồng bộ sheet FX đảo chiều
- **Bằng chứng**:
  1. Ở bản `stage_v1` của `t_rex`, mặt nạ `far_leg_all` (`xx >= 53`) không chặn biên phải `xx <= 69` nên lấy nhầm 2 pixel móng tay `far_arm` tại toạ độ nguồn `(77, 57)` và `(79, 57)` (`components=3`), tạo 2 chấm đen trôi dưới tay ở `idle` p7 và `hit` p0.
  2. `tools/preview/index.html` và `tests/test_frontend_wasm_e2e.mjs` mặc định nhân vật có `render_contract` luôn có `contract.aura.loop_clip`, gây lỗi khi nhân vật đặc biệt (`t_rex`) chỉ có `projectile` (`fireball_fx`) và Owner loại `aura_loop`.
  3. Sheet lửa đính kèm (`400×250`, nền `RGB(14,14,14)`) của Owner có thứ tự bắt đầu->kết thúc từ phải sang trái (`Cụm 4 -> Cụm 3 -> Cụm 2 -> Cụm 1`) và hướng đạn gốc bay sang trái (`-X`).
- **Sửa đã kiểm chứng**:
  1. Thêm kiểm lọc thành phần liên thông chính (`ndimage.label`) trong `extract_part_with_cap` và khoá biên `xx <= 69` cho `far_leg_all`, đảm bảo cả 12 bộ phận của `t_rex` đều đạt `components == 1` và 0 hạt nhiễu rời trên toàn bộ 71 frame.
  2. Cập nhật `tools/preview/index.html` và `tests/test_frontend_wasm_e2e.mjs` kiểm tra `Boolean(contract.aura?.loop_clip && animations[contract.aura.loop_clip])` trước khi bật lớp `Aura`, đồng thời cho phép `power_up` gây sát thương trong Sân Tập khi `power_up` là đòn bắn `projectile`.
  3. Tách 4 cụm lửa từ phải sang trái (`x=295..400`, `195..295`, `98..195`, `0..98`), khử nền `RGB(14,14,14)` 2 giai đoạn (`diff > 32` + edge unmixing + viền `1px`), lật ngang hướng `+X` và đồng bộ khớp 1:1 với miệng `t_rex` ở `power_up` (`p0..p1` lấy đà nén lửa trong họng -> `p2..p5` khạc 4 cụm lửa tiến dần từ `x=266` tới `x=382` -> `p6..p8` hồi chiêu). Kiểm thử `./loop.sh test` (13 Python/E2E, Godot 4.7.2 Headless 9 clip / 71 frame, 2 Rust) đạt `exit code 0`.

### [LRN-017] Chuẩn giải phẫu dực long bay (`Pteranodon`), loại bỏ khối phồng biến dạng vai-cổ `Rect(154,103,84,43)`, chuẩn độ nét `T-rex` (`Sobel=201.3`) và tách riêng asset sóng âm `sonic_screech_fx` tốc độ độc lập
- **Bằng chứng lỗi**:
  1. Ở bản sửa `TASK-028` trước đó, khi vá khe hở vai ở `idle` step=1 (`Canvas Rect(156, 131, 49, 16)`), Agent đã đoán mò: (a) cắt `m_far_wing` tại `yy <= 43` làm phần dưới cánh xa (`xx=49..62, yy=44..50`) bị sót lại trong `m_torso`; (b) ép `| ((xx >= 42) & (yy >= 44) & (yy <= 58))` vào `m_torso` làm `60` pixel logic (`240` pixel canvas) màng cánh đỏ và khuỷu cánh nâng cao bị dính cứng vào lưng `m_torso`; và (c) vẽ 4 khối cầu/capsule lớn (`radius = 4.4..6.0`) đè lên lưng, vai và gáy. Hậu quả: tại `clip="walk", step=4` (`Body:AtlasTexture_p0c12@Atlas(1555,263,384,256)`), vùng `Canvas Rect(154, 103, 84, 43)` bị phồng to biến dạng cơ thể với **`2858/3612` pixel có hình (`RGB trung bình = [96, 67, 72]`)**.
  2. Ở `power_up`, việc vẽ trực tiếp 7 cụm sóng âm (`self.sonic_crops`) đè lên các frame thân `power_up` và hạ ticks của `power_up` xuống `[4, 4, 2, 2, 2, 2, 2, 2, 2, 4]` đã làm tăng tốc độ co giật của toàn bộ cơ thể dực long thay vì chỉ tăng tốc độ của sóng âm; đồng thời trên `tools/preview/index.html`, biểu thức `baseTick = (p.velocity_px_per_tick[0]===0 && p.velocity_px_per_tick[1]===0) ? animationFrameTick(anim,index) : tick` khiến `Projectile` không tự chạy theo đồng hồ `tick` riêng khi `velocity_px_per_tick = [0,0]`.
- **Sửa đã kiểm chứng**:
  1. Phân tách lại 6 bộ phận giải phẫu của `pteranodon` đúng ranh giới thực trên lưới `100×100`: `m_torso` chỉ lấy phần thân dưới đường lưng (`yy >= 51`, tô lại các điểm giao dưới nách cánh bằng `CHARCOAL_DARK`), `m_far_wing` lấy trọn cánh xa (`yy <= 50` ở `xx=49..62`) và dùng `far_wing_blade` (`yy < 40`) khi đập cánh xuống/ngang để rèm cánh xa không lồi vào hõm cổ, `m_near_wing` xoay quanh đáy khớp vai `(46, 55)` để gốc cánh luôn bám sát sườn mà không cần đắp khối cầu giả, và chỉ giữ duy nhất 1 cầu nối cổ mảnh `draw_neck_capsule(..., radius=2.8)` dọc đúng trục cổ. Kết quả đo tại `clip="walk", step=4`, `Canvas Rect(154, 103, 84, 43)` giảm từ **`2858/3612` px xuống `1870/3612` px (`RGB trung bình = [80, 56, 59]`, loại bỏ sạch `988` pixel khối phồng biến dạng)**, đồng thời giữ khớp vai ở `idle` step=1 `Rect(156, 131, 49, 16)` liền mạch 100% (`514/784` px, `0` khe hở) và `edge_acutance_sobel = 201.3`.
  2. Tách hoàn toàn sóng âm ra khỏi các frame thân của `power_up`: `power_up` (`8` frame thân `#0..#7`) chỉ chứa 100% cơ thể dực long ở tốc độ chuẩn `ticks = [5, 5, 5, 5, 4, 5, 5, 6]` (`667ms`), còn `sonic_screech_fx` (`7` frame `#0..#6`) là asset/clip FX độc lập chạy ở tốc độ cao `ticks = [2, 2, 2, 2, 2, 2, 2]` (`233ms`, kèm prefab độc lập `scenes/PteranodonSonicWaveFX.tscn` và node `ProjectileFX` trong `scenes/Pteranodon.tscn`). Cập nhật `tools/preview/index.html` dùng `const baseTick = tick;` và hiển thị `effect_clips` trên thanh chọn clip Tab 1 để sóng âm vừa tự chạy nhanh độc lập khi phát `power_up`, vừa chọn xem/chỉnh riêng được. Kiểm thử `./loop.sh check` và `./loop.sh test` đạt `exit code 0`.

### [LRN-019] 2026-11-11 — Chuẩn giải phẫu 2 mặt cánh (Dorsal Da Than Chì / Ventral Đỏ Đô), chống lem màu cánh tay, nối liền gốc cánh đối diện & khử răng cưa khi xoay frame (`pteranodon`)
- **Bối cảnh**: Trong quá trình Human Test nhân vật `pteranodon`, Owner gửi 4 thông số `[DR7-EDIT-SPEC]`:
  1. `walk` `step=0` tại `Canvas Rect(175, 108, 35, 42)` bị mất liên kết giữa gốc cánh trái (`far_wing`) vào thân (`630/1470` px).
  2. `idle` `step=0` tại `Canvas Rect(143, 75, 41, 80)` phần cánh tay bị lem màu đỏ của màng cánh gây nhầm lẫn giữa cánh và tay.
  3. `idle` `step=4` tại `Canvas Rect(103, 127, 95, 93)` khi đập cánh xuống mặt trên của cánh gần bị trùng màu đỏ với mặt trong, còn mặt dưới của cánh đối diện lại trùng màu da; đồng thời khi chạy frame còn cảm giác răng cưa và cần thêm 2 nút `"Lỗi màu sắc"`, `"Mất chi tiết"` vào UI Giao Tiếp Toạ Độ.
  4. `run` `step=4` tại `Canvas Rect(223, 131, 14, 22)` bị khuyết chi tiết ở cổ dưới ngay sau khớp hàm dưới (`156/308` px).
- **Nguyên nhân gốc**:
  1. Gốc của `far_wing` (`x = 48..64, y = 38..51`) bị mào đầu (`m_upper_head`) cắt ngang làm tách thành 2 cụm rời nhau khiến `clean_part_with_caps` xóa mất phần gốc dưới mào.
  2. Ngưỡng phân loại màu đỏ `r > g + 15` quá lỏng và chưa tách mặt nạ giải phẫu cánh tay (`arm_structure`), làm bắp tay/cẳng tay có sắc ấm bị tô nhầm sang `WING_RED_*`.
  3. Phép biến dạng `warp_wing_flap` khi `flap_elev < 0` lật dọc `near_wing` làm mặt dưới màu đỏ lộn lên mặt trên; đồng thời `far_wing` chưa phân tách mặt trên (màu da than chì) và mặt dưới (màu đỏ đô).
  4. Khi `head_dx = 3.5` ở `run`, chỉ có 1 capsule cổ trên nối tới `(67, 48)` mà thiếu capsule cổ họng dưới nối tới khớp hàm dưới `jaw_dst`, để lộ khe hở tại `Canvas Rect(223, 131, 14, 22)`.
  5. Các điểm tối nội vùng bị gán `OUTLINE_RGBA` và biến đổi xoay Nearest ở góc nghiêng tạo khấc răng cưa `1px`.
- **Cách khắc phục & Phòng tránh**:
  1. Khôi phục dải chord gốc cánh `far_wing` dưới mào (`far_wing_chord_fill` + cầu nối `caps`), nâng vùng `walk` `step=0` `Canvas Rect(175, 108, 35, 42)` từ `630/1470` px lên `1390/1470` px (`94.6%`, nối liền 100% vào lưng).
  2. Khóa mặt nạ giải phẫu `arm_structure` + đường gân viền `arm_crease_outline` để cánh tay/cổ tay/4 móng vuốt giữ nguyên 100% màu da than chì & móng xám (`0 px` lem màu đỏ lên tay tại `idle` `step=0` `Canvas Rect(143, 75, 41, 80)`, `2318/3280` px).
  3. Thiết lập `build_wing_surface_variants`: mặt trên của cả 2 cánh luôn mang màu da than chì (`CHARCOAL_*`), mặt dưới/mặt trong luôn mang màu đỏ đô (`WING_RED_*`); khi đập cánh xuống (`idle` `step=4` `Canvas Rect(103, 127, 95, 93)`), mặt trên `near_wing` dùng `near_wing_dorsal` (100% màu da than chì) và cánh đối diện dùng `far_wing_ventral` (mặt dưới màu đỏ đô).
  4. Bổ sung `cheek_throat_root` và cầu nối đôi `draw_neck_capsule` tới cả `head_dst` lẫn `jaw_dst`, nâng `run` `step=4` `Canvas Rect(223, 131, 14, 22)` từ `156/308` px lên `220/308` px (`71.4%`, kín khít hoàn toàn).
  5. Thêm bộ lọc khử răng cưa `smooth_warped_layer` sau mỗi bước xoay/biến dạng và bổ sung 2 nút `"🎨 Lỗi màu sắc"` (`LOI_MAU_SAC`), `"🧩 Mất chi tiết"` (`MAT_CHI_TIET`) vào `tools/preview/index.html`.

### [LRN-020] 2026-11-11 — Đồng bộ nhịp đập đối xứng 2 cánh ở pha đập xuống (`walk` `step=2`) & khôi phục màu đỏ mặt trong cánh ở khoang trên (`run` `step=0`) cho `pteranodon`
- **Bối cảnh**: Trong quá trình Human Test bản `pteranodon v5`, Owner gửi 2 thông số `[DR7-EDIT-SPEC]`:
  1. `walk` `step=2` tại `Canvas Rect(176, 129, 69, 79)` (`2187/5451` px, `RGB trung bình = [84, 62, 65]`): lỗi đồng bộ frame khi hoạt ảnh đập cánh xuống của dực long bị sai logic, 2 cánh không đối xứng (`near_wing` còn đang lướt ngang `y = 136..178` trong khi `far_wing` đã cắm thẳng đứng xuống `y = 208` thành một dải đỏ hẹp dưới ngực).
  2. `run` `step=0` tại `Canvas Rect(97, 76, 54, 36)` (`1260/1944` px, `RGB trung bình = [83, 63, 70]`): phần trong cánh còn 1 khoang bị dính màu da than chì nhưng logic đúng là màu đỏ của mặt trong cánh.
- **Nguyên nhân gốc**:
  1. Ở nhánh đập cánh xuống (`p.flap_elev < 0`), `far_wing_ventral` bị cắt cụt tại `y <= 43` từ mẫu cánh xa bị mào che khuất (`542` px thay vì `984` px của cánh nguyên vẹn) và cộng cứng góc xoay `+42.0°` kèm kẹp `flap_elev = min(-0.58, ...)`, làm `far_wing` ở `step=2` bị xoay chúc thẳng đứng xuống `y = 208` trước nhịp của `near_wing` (`y = 178`) tới `30 px` và mất đối xứng hình học giữa 2 cánh.
  2. Biểu thức `leading_wing_bone` trong `extract_logical_100` dùng hệ số dốc dương `yy <= 28 + (39 - xx) * 0.48` đi xuống tới `yy = 38` khi `xx` tiến về đầu cánh, làm khoang màng cánh phía trên (`Canvas Rect(97, 76, 54, 36)`) bị gộp nhầm vào `arm_structure` và tô màu da than chì (`CHARCOAL_*`) thay vì màu đỏ mặt trong cánh (`WING_RED_*`).
- **Cách khắc phục & Phòng tránh**:
  1. Dựng `far_wing_ventral` bằng phép đối xứng ngang chuẩn xác (`near_wing_ventral[:, ::-1, :]`) của toàn bộ bản cánh mặt trong nguyên vẹn và đồng bộ 1:1 tham số biến dạng ở pha đập xuống (`flap_elev = p.flap_elev * 0.96`, `camber_px = p.camber_px`, `shear_x_by_y = -p.shear_x_by_y * 0.60`, `rot_deg = -(p.body_angle + p.wing_rot)`), giúp 2 cánh ở `walk` `step=2` `Canvas Rect(176, 129, 69, 79)` (`2587/5451` px, `RGB = [91, 57, 61]`) và toàn bộ `step=2..5` đập xuống cùng nhịp độ cao (`NEAR y=[136..178]` ⇄ `FAR y=[134..176]` tại `step=2`; `NEAR y=[132..208]` ⇄ `FAR y=[132..208]` tại `step=4`) và đối xứng qua thân.
  2. Khóa `leading_wing_bone` đúng viền xương sống cánh `2px` sát mép trên (`yy <= top_y[xx] + 1` với `xx <= 37`) và gán toàn bộ `inner_wing_membrane` bên dưới xương cánh / bên trái cánh tay sang dải màu đỏ `WING_RED_*` (đồng thời bảo toàn 3 móng vuốt cánh xa `x >= 74, y <= 34` màu xương xám), đưa vùng `run` `step=0` `Canvas Rect(97, 76, 54, 36)` từ `RGB = [83, 63, 70]` sang `RGB = [147, 40, 47]` (`1084/1260` px màng đỏ + `176` px xương viền cánh trên, `0` khoang da thừa).

### [LRN-021] Pteranodon — bảo vệ cẳng tay cánh xa và tránh đảo giải phẫu khi đập xuống
- **Bằng chứng**: idle step=0 Canvas Rect(180,101,49,43) có1739pixel đục, RGB[102.61,63.55,67.89]; pixel cẳng tay Canvas(210,108) làRGBA(236,78,84,255). `build_wing_surface_variants` tô đỏ mọi pixel dưới đường chéo ridge, không chừa cẳng tay. idle step=3 Rect(166,145,85,71) có3171pixel đục; nhánh far-wing dùng `flap_elev < 0` làm đảo trụcY cả cẳng tay lẫn màng.
- **Sửa**: bảo vệ dải khuỷu(59,46)→cổ tay(68,31) trên lưới nguồn100², khôi phục da từ far_skin_source; pixelCanvas(210,108) thànhRGBA(163,141,151,255), vùngstep0 giữ1739pixel đục, chỉ160pixel đổi màu. Pha xuống của cánh xa dùng abs(elevation) và góc xoay tăng theo biên độ về+X, cẳng tay ở trên/dẫn về mỏ thay vì hướng dưới chân; vùngstep3 còn2961pixel đục do cánh đổi hướng. Không khẳng định toàn vùng khoanh phải hết đỏ:246pixel màng đỏ hợp lệ vẫn còn ởstep0.
- **Chống hồi quy**: tạo far_blade cho KO trước khi áp sửa màu bay; so cả8frameKO vớibuilderv6 đều0pixel đổi. FX giữ nguyên. Bỏ vòng xóa `image*` trongbuilder để không xóa ảnh tham chiếu Owner khi xuất.
- **Kiểm chứng**: work/characters/pteranodon/revision-v7/verify_revision.py exit0, qa.json lưu số liệu; ./loop.sh test exit0 (13Python/E2E,Godot2bundle,2Rust), WASMrelease exit0, HTTPparityok. Xem8filmstrip3nền; cảnh báo clip bị Owner loại giữ nguyên trongtests.log. Đây là bản chờ Human Test, chưa phải nghiệm thu.

### [LRN-022] Pteranodon v8 — gốc khuỷu cánh và chọn vùng lõm chính xác
- **Màu**: v7 vẫn còn140pixel đỏ trong idle step0 Rect(176,112,22,30),660/660pixel đục. Mặt nạ bảo vệ cẳng tay chưa gồm gốc vai/khuỷu phía trái. Bổ sung shoulder_root trên source100² tại x<=60,y>=39 sau khi chụp far_blade choKO; khôi phục màu nguồn, không vẽ silhouette. Kết quả đỏ0/660; pixelCanvas(192,118) từRGBA(236,78,84,255) thành(163,141,151,255); bbox màu đổiCanvas(180,118,18,20) trong vùngOwner. Audit tất cả54frame thân: alpha không đổi, toàn bộ pha xuống vàKO pixel-identical vớiv7.
- **Chọn vùng UI**: Rect chứa cả phần che khuất/vùng lõm dễ gây thống kê và hướng dẫn sửa dư. Thêm Lasso bên cạnh Rect; scanline even-odd tại tâm pixel, sao chép PolygonCanvas và PixelRunsCanvas[y,x,length] làm mask chính xác; bbox chỉ định vị. Stats vàmask dùng chung rasterizer, không tính toànbbox. Pointer capture hỗ trợ chuột/touch vàra ngoàicanvas; pause trước lấy mẫu, ghi cả điểm pointerup, hủy vùng0diện tích/cancel.
- **Kiểm chứng**: tests/test_frontend_wasm_e2e.mjs mô phỏng pointer quaCSSscale, vùngL lõm64pixel loại36pixel, vùngngoài đỏ không làm lệchRGB[20,40,60], copymask/pin khớp, rectkéo ngược121pixel, clear/cancel/degenerate và renderoverlay. ./loop.sh test exit0; WASMbuildexit0; HTTPHTML/PNG khớpfile thật,paritytrue. Sốliệu vàlog tạiwork/characters/pteranodon/revision-v8/. Xem8filmstrip3nền; chờ OwnerHumanTestv8.

<!-- LERNING_ENTRIES_END -->
