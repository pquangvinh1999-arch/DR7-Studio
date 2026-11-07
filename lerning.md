# NHẬT KÝ BÀI HỌC SỬA LỖI KỸ THUẬT (`lerning.md`)

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

<!-- LERNING_ENTRIES_END -->
