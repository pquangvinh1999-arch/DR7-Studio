# HIẾN PHÁP DỰ ÁN DR7-STUDIO (`AGENTS.md`)

Tài liệu `AGENTS.md` này là **Hiến pháp tối cao và duy nhất** ở thư mục gốc của kho mã nguồn `DR7-Studio`, được tự động nạp trực tiếp bởi cả **Antigravity CLI (`agy`)** lẫn **OpenAI Codex (`codex`)**. Mọi quyết định kỹ thuật, xử lý asset, kiểm thử engine và hiển thị preview đều phải tuân thủ tuyệt đối các điều khoản dưới đây.

---

## Điều 1. Cấm Tuyệt Đối Bịa Đặt & Đoán Mò (Zero Hallucination / Evidence-Only)

1. **Không tự ý bịa code, bịa API, bịa tham số cấu hình**: Chỉ dùng API, flag CLI, schema và hàm đã được xác minh thực tế qua tài liệu nội bộ, `--help`, mã nguồn hoặc chạy kiểm thử.
2. **Không bịa kết quả kiểm thử hoặc QA**: Chỉ báo cáo `PASS` / `OK` khi lệnh kiểm thử thực sự trả về `exit code 0` và đã đọc log/output thực tế. Mọi cảnh báo (`WARN`) hoặc lỗi (`FAIL`) phải được trích dẫn nguyên văn số liệu, tuyệt đối không che giấu.
3. **Không suy đoán khi thiếu bằng chứng**: Mọi nhận định về lỗi code hoặc lỗi hình ảnh (alpha, viền màu, lệch tâm, mất chi tiết, sai độ nét) phải kèm bằng chứng đo đạc cụ thể (tọa độ pixel `Canvas (x,y)` / `Atlas (x,y)`, giá trị `RGBA`, dòng log, đường dẫn file).

---

## Điều 2. Cổng Đánh Giá Độ Rõ Ràng Trước Khi Code (Pre-Task Clarity Gate)

1. **Đánh giá bắt buộc trước khi thực thi**: Trước khi viết code, sửa kiến trúc hoặc chạy pipeline xử lý asset, Agent bắt buộc tự rà soát:
   - Mục tiêu cuối cùng của Owner trong task này đã rõ 100% chưa?
   - Logic nghiệp vụ, thông số đầu vào/đầu ra, ràng buộc hiệu năng hoặc nền tảng còn điểm nào mơ hồ không?
2. **Mơ hồ = Dừng lại & Hỏi rõ Owner**:
   - Nếu còn bất kỳ điểm nào chưa rõ từ yêu cầu của Owner hoặc từ `state.json` / `skills.md`: **BẮT BUỘC dừng việc triển khai và hỏi lại Owner**.
   - Khi hỏi, trình bày khách quan các phương án khả thi kèm ưu/nhược điểm kỹ thuật để Owner chốt nhanh, tuyệt đối không tự đoán ý làm trước.

---

## Điều 3. Kiến Trúc Lớp Duy Nhất (`Combined 1-Layer`) & Thông Số Kỹ Thuật Bóc Tách Atlas Bắt Buộc

1. **Cổng hỏi bắt buộc khi thiếu thông tin**: Khi Owner đính kèm hoặc trỏ tới một file ảnh / atlas bất kỳ mà chưa nêu rõ mục đích xử lý, Agent **chỉ được phép đo đạc thông số thực tế** (kích thước px, số hàng/frame, nền màu, nhiễu/watermark, bố cục chiêu thức), sau đó **BẮT BUỘC hỏi lại Owner** trước khi xử lý.
2. **Kiến trúc Lớp Chính Thức Duy Nhất — Gộp Chung 1 Lớp Nguyên Bản (`Combined 1-Layer`)**:
   - Toàn bộ nhân vật trong dự án **bắt buộc sử dụng duy nhất kiến trúc `combined_1layer` (`1 Quad / 1 Draw Call`)**: giữ nguyên thân nhân vật một sprite/lớp; các phần FX theo contract Owner dưới đây. `1 Quad / 1 Draw Call` chỉ nói phần thân khi tắt FX.
   - **Bãi bỏ vĩnh viễn hướng bóc tách đa lớp (`layered_3d_depth` / `Hướng 2`)** vì làm sai cấu trúc vẽ gốc của sprite 2D. Hệ thống kiểm thử (`./loop.sh check` và `test_character_bundles.gd`) tự động đánh `FAIL` nếu xuất hiện bất kỳ cấu hình `layered_3d_depth` nào.
   - **Cấm tuyệt đối dùng AI vẽ lại làm biến dạng chi tiết gốc (`Zero AI Redraw`)** khi bóc tách từ sheet của Owner.
   - **Quy tắc chung mới theo Owner**: Ki/aura phải xuất và điều khiển độc lập để dùng cùng nhiều hoạt ảnh thân, mặc định cho nhân vật có Ki; không hỏi lại. Thân không tách chi/cánh theo chiều sâu. Cùng atlas khi khả thi, contract/anchor/tick đồng bộ Godot và localhost; FX thêm sprite/quad và có chi phí riêng. Sheet đã gộp không tách an toàn thì báo giới hạn, không vẽ lại để nhận bảo toàn pixel.
3. **Thông Số Kỹ Thuật Bóc Tách, Tách Nền & Đăng Ký Tâm Chân Bắt Buộc (Chuẩn Khởi Đầu Studio từ `trunks_rage`)**:
   - **Phân tách cụm 2D theo mặt nạ sở hữu liên thông (`2D Component Ownership Masking`)**:
     - Cắt từng pose bằng nhãn liên thông 2D (`3×3` / `5×5` ownership mask) thay vì cắt hộp chữ nhật thô theo cột dọc, nhằm **ngăn chặn 100% mũi kiếm chéo hoặc tia lửa của pose kế bên lọt vào khung cắt**.
     - Loại bỏ sạch khung viền header/footer, chữ chú thích trên sheet (như nhãn `WIN`), dấu gạch ngang phân cách `-`, ảnh chân dung cắt ngang (`cut-in`), và vùng rìa giao thoa giữa hai hàng sát nhau (`extra_exclusions`).
     - Với các tia chưởng chia khúc trên sheet (như `Final Flash` gồm `Đầu | Thân | Ngọn` ngăn bởi vạch tối `1px`), bắt buộc khử vạch chia `1px` và ghép liền mạch vào đúng toạ độ bàn tay nhân vật; sắp xếp đúng thứ tự thời gian thực của chiêu thức.
   - **Tách nền 2 giai đoạn bảo toàn độ sắc Pixel Art (`Pocket-First Chroma Key + Edge Unmixing`)**:
     - **Giai đoạn 1**: Đục thủng 100% hốc nền kín kẹt giữa tay/chân/vỏ kiếm/hào quang (`enclosed_key_pockets == 0`, `opaque_key_px == 0`) bằng lan truyền hạt giống màu nền (`binary_propagation`) **trước** khi khử viền.
     - **Giai đoạn 2**: Khử pha màu trên viền biên `1px` (gồm cả viền pha màu nền trực tiếp lẫn viền vàng-pha-xanh `olive fringe` quanh hào quang sáng, chỉ số sạch viền `outer_ring_spill_fraction <= 0.005`), đồng thời giữ độ cứng biên pixel `alpha_hardness_pct >= 95%` (với pixel art) để không làm nhòe nét gốc.
   - **Chuẩn căn tâm gốc chống trượt chân (`Shared Row Ground Baseline + Dark-Outline/Torso Centroid`)**:
     - Trục ngang `X`: Căn theo trung vị viền tối của cơ thể / khăn choàng (`detect_body_center_x`) thay vì tâm hộp bao toàn ảnh, đảm bảo khi vung kiếm dài hoặc bắn chưởng xa cơ thể nhân vật đứng vững tuyệt đối tại `anchor_x`, không bị giật lùi.
     - Trục dọc `Y`: Căn theo đường mặt đất chung của từng hàng (`row_ground_y`) để giữ nguyên độ cao quỹ đạo nhảy/bay (`jump`, `ultimate`), riêng các frame gồng biến hình có tia lửa đâm xuống dưới đế giày phải căn theo đáy giày tối (`detect_boot_bottom_y`).
     - Kích thước khung Canvas nhân vật `[W, H]` bội số của `16` (chuẩn tham chiếu `trunks_rage`: `canvas_size_px = [320, 256]`, `foot_anchor_px = [96, 220]`, Godot `AnimatedSprite2D` đặt `centered = false`, `offset = Vector2(-anchor_x, -anchor_y)`).
   - **Chuẩn đóng gói Texture Atlas cho Engine**:
     - Đóng gói toàn bộ hoạt ảnh của 1 nhân vật lên **1 trang PNG Atlas duy nhất (`pages == 1`, kích thước tối đa `<= 4096 × 4096 px`)** để toàn bộ thực thể dùng chung nhân vật đó gộp gọn trong `1 Draw Call`.
     - Bắt buộc bật lọc mẫu **`Nearest` (`texture_filter = 1`)**, tốc độ chuẩn **`60Hz` ticks** trên `.tres` + `engine-export.json`, và đặt `.gdignore` trong `source/` & `clips/`.

---

## Điều 4. Kiến Trúc Engine & Hạ Tầng Chính Thức Đã Chốt

- **Dự án**: Game 2D **Dragon Ball** (`DR7-Studio`).
- **Nền tảng phát hành mục tiêu**: Mobile (**Android `.apk` / `.aab`** và **iOS `.ipa`**).
- **Mục tiêu hiệu năng cốt lõi**: **60 FPS mượt tuyệt đối (`<= 16.67 ms/frame`) khi có hơn `2,000` người chơi / thực thể giao tranh theo thời gian thực (Real-time Mass Combat)**.
- **Kiến trúc Engine Chính Thức (ĐÃ CHỐT — Hybrid Godot 4 + Rust Core + Supabase)**:
  1. **Godot Engine 4 (Client Chính Thức)**: Đảm nhận Scene, Map, Camera, UI cảm ứng Mobile, Âm thanh, xuất gói cài đặt Android/iOS và vẽ hàng nghìn nhân vật 1 lớp bằng `MultiMeshInstance2D` (`1 Draw Call`).
  2. **Rust Core (`engines/rust_combat_sim`)**: Đảm nhận tính toán vật lý, va chạm lưới không gian `O(N) Spatial Hash`, máy trạng thái 60Hz và đóng gói buffer GPU/mạng siêu tốc (`~0.61 ms/frame` cho `2,000` thực thể — dưới `4%` quỹ frame 60FPS), tích hợp vào Godot qua **`GDExtension`** (Native Mobile), chạy trực tiếp trên Server combat và biên dịch ra **`WebAssembly` (`rust_combat_sim.wasm`)** cho trạm kiểm thử `localhost:8080`.
  3. **Supabase**: Đảm nhận Auth, PostgreSQL (Hồ sơ nhân vật, Trang bị, Bang hội), Storage kết hợp đồng bộ nhị phân theo vùng nhìn **Spatial AoI** cho bài toán `> 2,000` CCU.

---

## Điều 5. Vòng Lặp Kiểm Thử Engine Bắt Buộc & Đồng Bộ Tuyệt Đối 1:1 Với Localhost

1. **Vòng lặp Tự Kiểm Thử & Tự Sửa Trên Engine (`Engine Verification Loop`)**:
   - Mọi kết quả dựng hoạt ảnh từ atlas **bắt buộc phải chạy kiểm thử tự động đầy đủ trên cả Godot 4 Headless (`test_character_bundles.gd`) và Rust Core (`cargo test` + WASM build)** (kiểm tra nạp texture/atlas, số frame, thời lượng tick `60Hz`, `offset == -anchor_px`, lọc `Nearest`, không hốc màu nền).
   - **FAIL/sai thông số**: Phân tích → sửa → chạy `./loop.sh test`, tối đa **5 vòng cho mỗi vấn đề**. Hết 5 vòng chưa sửa được phải dừng sửa vấn đề đó, báo Owner kèm lỗi, bằng chứng và các cách đã thử; không chạy vòng 6 hoặc bàn giao bản lỗi.
   - **Cổng chất lượng chuyển động và liên kết cơ thể (bắt buộc, áp dụng toàn dự án)**: kiểm thử texture/tick/hash không chứng nhận hoạt ảnh tự nhiên. Sau setup atlas, chỉ cần frame phát bị xé/cắt rời cơ thể, hở khớp, mất kết nối cơ quan, lộ mảng vá, biến dạng tỷ lệ hoặc xuyên/chồng bộ phận sai giải phẫu thì **kết quả hoạt ảnh = `FAIL`**, dù mọi unit test kỹ thuật exit0. Báo đúng `technical_checks` và `motion_quality` riêng; không dùng technical PASS để che motion FAIL. Kiểm tra cả từng frame, nối frame liên tiếp, nối vòng, phát ở tốc độ thực trên nền sáng/tối/ô cờ; lưu clip/frame/Canvas/Atlas/ảnh lỗi và kết quả kiểm tra. Thiếu bằng chứng trực quan là `pending`, không phải PASS; Owner báo lỗi cấu trúc thì hạ gate thành FAIL cho đến khi sửa được kiểm chứng.
   - **Tạo chuyển động từ master tĩnh**: phải tái tạo nhiều pose toàn thân liên tục theo skill, giữ các cơ quan liên kết, đúng giải phẫu, nhận diện và tỷ lệ. **Cấm cắt xé một ảnh tĩnh thành các mảnh thân/chi/đầu rồi xoay, kéo, vá hoặc ghép lại để giả chuỗi chuyển động.** Không dùng lấp khe/sửa alpha hoặc tăng FPS để hợp thức hóa cơ thể bị rách. Việc cắt nguyên frame hoàn chỉnh khỏi sheet và xử lý nền/anchor/atlas vẫn được phép; quy tắc này không cấm bóc tách bảo toàn các frame vốn đã có trong sheet Owner. Zero AI Redraw của sheet nguồn và kiến trúc thân `combined_1layer` vẫn giữ nguyên. Khi Owner chọn imagegen thay video, sinh toàn bộ nhân vật cho từng keyframe, review chuỗi trước đóng atlas; không lấy bộ khớp/mask của nhân vật khác để dựng chuyển động mới.
2. **Đồng bộ Tuyệt đối 100% Giữa Engine và Localhost (`Zero-Drift Engine ⇄ Localhost Parity`)**:
   - Sau khi pass kiểm thử trên Engine, kết quả phải được phục vụ lên `localhost:8080` **đồng bộ tuyệt đối 1:1** với Engine để Owner thực hiện **Human Test**.
   - Cả Godot 4, Rust Core và `localhost:8080` bắt buộc đọc **cùng một nguồn dữ liệu duy nhất** (`assets/roster.json`, cùng file PNG atlas, cùng toạ độ `Rect2(x, y, w, h)` trong `.tres`, cùng thời lượng tick `60Hz`, cùng `anchor_px`). Lệnh `./loop.sh check` tự động đối soát mã băm **SHA-256** và khung kích thước động `[W, H]`.
3. **Chỉ lưu Nhân vật Đã Hoàn Thiện trên Danh sách Nhân vật**:
   - Tuyệt đối không lưu trữ rác, nhân vật test cũ hoặc các bản nháp lỗi trong `assets/`, `scenes/` hay `roster.json`.

---

## Điều 6. Phân Biệt Rạch Ròi Giữa `skills.md` (Quy Trình Nghiệp Vụ) & `.agents/skills/` (Skill Công Cụ Asset)

Agent tuyệt đối **KHÔNG ĐƯỢC NHẦM LẪN** hai khái niệm sau:

| Thành phần | Bản chất | Khi nào SỬ DỤNG | Khi nào CẬP NHẬT |
|---|---|---|---|
| **`.agents/skills/*`** (`.agent/skills/*`: `generate2dsprite`, `video2dsprite`, `generate2dmap`, `generate2dmedia`, `codeart2d`) | **Bộ Skill Công Cụ Kỹ Thuật Cấp Thấp (Asset Tooling Skills)**: Cung cấp script xử lý ảnh, đóng gói `build_animation_clips.py`, xuất `export_engine.py`. | Dùng **bên trong bước thực thi kỹ thuật** khi cần đóng gói clip 60Hz, tạo filmstrip review và xuất `.tres` / PNG atlas. | Bộ thư viện công cụ cài đặt sẵn; không ghi nhật ký quy trình làm việc của Owner vào đây. |
| **`skills.md`** (ở thư mục gốc dự án) | **Sổ Tay Quy Trình Nghiệp Vụ End-to-End Của Dự Án (`Owner Atlas -> Final Animation Pipeline`)**: Quy định quy trình tổng thể từ lúc nhận atlas từ Owner -> bóc tách 1 lớp bảo toàn chi tiết -> pass Engine -> đồng bộ Localhost đúng ý Owner. | Đọc **ngay đầu task khi nhận ảnh/atlas từ Owner** để áp dụng quy trình chuẩn đã được Owner nghiệm thu. | Khởi tạo **TRỐNG**. Chỉ được ghi vào sau khi hoàn thành trọn vẹn quy trình cùng Owner và **được Owner nghiệm thu Human Test thành công**. |

**Kỷ luật kiểm tra trực quan bắt buộc**:
- Trước khi bàn giao Human Test, Agent bắt buộc mở xem trực tiếp từng dải ảnh `filmstrip-*.png` bằng mắt trên cả 3 nền (**sáng, tối, ô cờ**) để phát hiện và xử lý triệt để mọi chữ thừa, vạch cắt hoặc chi tiết lấn hàng mà chỉ số tự động có thể bỏ sót.

---

## Điều 7. Chuẩn Bộ Hoạt Ảnh Nhân Vật, Thước Đo Map & Giao Tiếp Toạ Độ Trên UI Test

1. **Điều kiện Kiểm thử Bộ Hoạt Ảnh Nhân Vật (`Character Animation Completeness Gate`)**:
   - Bộ clip tham chiếu chiến đấu cốt lõi gồm: `idle`, `walk`, `run`, `jump`, `guard`, `attack_light`, `attack_heavy`, `power_up`, `aura_loop`, `hit`, `ko`, `win` (cùng các kỹ năng đặc trưng từng tướng như kiếm khí, chưởng lực, tốc biến, chiêu cuối).
   - Hệ thống kiểm thử (`./loop.sh check` và UI `localhost:8080`) kiểm tra danh sách clip của mỗi nhân vật và phát cảnh báo nhắc nhở (`WARN`) rõ ràng nếu nhân vật mới chỉ có một phần hoạt ảnh.
   - **Owner chốt phạm vi chung**: không tạo `guard` và `win` cho bất kỳ nhân vật nào; không hỏi lại. Giữ WARN tham chiếu nếu có và ghi lý do Owner loại, không tạo clip giả.
2. **Thông số Kích thước Nhân vật, Mốc Chuẩn Pixel Art & Phong Cách Chung Mặc Định**:
   - **Mốc độ nét chung — T-rex đã nâng cấp (Owner chốt mốc 2026-11-12)**:
     - Nhân vật tạo tiếp theo phải đối chiếu [ảnh T-rex cố định](docs/art-standards/t-rex-sharpness-reference.png) và [thông số/phương pháp](docs/art-standards/character-pixel-sharpness.json): **1px gameplay, Nearest**, alpha thân100%; VFX được alpha mềm. Thay chuẩn100texel/2×/16màu/201.3 cũ; kích thước riêng từng nhân vật vẫn giữ.
     - Mẫu idle0: canvas384×256,bbox186×134,anchor[176,224],Sobel **245.516**. Đo bằng `python3 tools/art/measure_pixel_sharpness.py <frame.png>`; xem1×/zoom nguyên lần trên3nền. Không ép scalar/dung sai tự đặt, blur/sharpen/LUT/dither để chạy theo số; đo key/pocket/spill theo nền nguồn.
     - Mốc này chốt độ nét, không chốt atlas/hoạt ảnh T-rex đang demo. Xé cấu trúc/hở khớp/lật ảnh giả xoay vẫn FAIL; không tự sửa nhân vật đã duyệt ngoài phạm vi Owner.
   - **Phong cách thẩm mỹ chung mặc định**:
     - Toàn bộ quái thú / sinh vật mặc định mang phong cách **"Hung tợn"** (hàm răng nanh/răng cưa nhọn hoắt tạo cảm giác đáng sợ, ánh mắt sắt lẹm hung dữ, móng vuốt sắc bén uy lực, tông màu đậm chắc sẫm) — trừ khi Owner có yêu cầu đặc thù riêng cho từng nhân vật.
   - Mọi nhân vật trong `roster.json` bắt buộc đo đạc và công bố đầy đủ:
     - `canvas_size_px` (`[W, H]`), `foot_anchor_px` (`[ax, ay]`).
     - `body_only_bbox_px` (rộng × cao phần thân thuần ở tư thế đứng) và `full_fx_bbox_px` (rộng × cao bao trọn kiếm khí / hào quang / chưởng lực cực đại).
     - `reference_ppu_64` (quy đổi kích thước mét thế giới tại `64 PPU` và số ô Tile Map `32×32 px`) để đồng bộ tỷ lệ nhân vật với Scene Map tương lai.
     - `pixel_sharpness_metrics` (`texel_scale_ratio`, `edge_acutance_sobel`, `alpha_hardness_pct`, `opaque_key_px == 0`, `enclosed_key_pockets == 0`, `outer_ring_spill_fraction`).
3. **Chuẩn Giao Tiếp Toạ Độ & Thước Đo Sửa Lỗi Giữa Owner và Agent (`Owner ⇄ Agent Coordinate Protocol`)**:
   - UI Test tại `localhost:8080` bắt buộc hỗ trợ khung kích thước động `[W, H]` theo từng nhân vật, thanh kéo frame (`frame scrubber`), thước đo pixel X/Y, toạ độ con trỏ + mã màu `RGBA`, và khoanh vùng `Rect(x, y, w, h)` xuất chuỗi `[DR7-EDIT-SPEC]` chuẩn xác 100%.


4. **Khóa hướng nhìn nhân vật trên Map 2D (`Movement / Facing Contract`)**:
   - Trước khi sinh bộ atlas theo hướng, ghi rõ trong hồ sơ nhân vật: kiểu nhìn map/camera, tập hướng cần vẽ, hướng di chuyển trên map, hướng thân/mặt, và hướng tác động vũ khí. Không dùng từ “trước/sau” khi chưa xác định nó là trái/phải trên màn hình hay mặt trước/lưng nhân vật.
   - Không mặc định map 2D đồng nghĩa với nhìn ngang, top-down hoặc 4/8 hướng. Khi Owner chưa nêu rõ ánh xạ, hỏi trước phần sinh frame phụ thuộc hướng.
   - Lật ngang chỉ đổi trái/phải; không tạo được mặt lưng từ mặt trước. Không dùng flip dọc để giả lập đổi hướng lên/xuống. Các hướng phải giữ cùng nhận diện, tỷ lệ, anchor và thiết kế vũ khí; kiểm tra chi tiết bất đối xứng khi dùng mirror.
   - Tách vector di chuyển khỏi hướng nhìn khi có lùi/strafe hoặc đánh theo mục tiêu. Với mỗi clip, ghi rõ nhân vật quay về đâu, chân di chuyển thế nào và búa/vũ khí đánh về đâu; không tự suy hướng mặt chỉ từ vị trí trong atlas.
   - **Xoay người, quật đuôi và đổi hướng phải có trọng lượng thật**: tạo các pose chuyển tiếp phù hợp trục xoay/góc camera, có thay đổi phối cảnh và che khuất đúng thứ tự, đầu/ngực/hông/chân/đuôi chuyển động liên tục, tiếp đất và trọng tâm hợp lý. Cấm dùng flip_h, xoay quad hoặc thu ngang một tấm ảnh như các frame của hành động xoay; mirror chỉ chọn bộ hướng trái/phải sau khi có chuyển tiếp hợp lệ, không thay thế hoạt ảnh quay đầu/quay thân. Timing60Hz phải tách lấy đà → tăng tốc vung/tác động → giảm tốc/hồi thế, ghi tick và kiểm tra tốc độ thực; không rải đều tick khiến xoay như lật bìa ảnh. Với Spinosaurus, pha vung đuôi `attack_heavy` phải nhanh hơn bản bị Owner loại; tăng tốc đơn thuần mà vẫn lật ảnh hoặc xé cơ thể vẫn FAIL. Không áp cứng tốc độ đó cho mọi sinh vật; thiết kế theo cơ thể và lực tác động.

---

**Chu kỳ di chuyển và tái sử dụng walk/run — Owner 2026-11-12**:
- Walk phải là một vòng tiến pha liên tục `0→1→…→N−1→0` (bộ8frame: `0→7→0`), đủ hai nhịp chân đối nhau. Không dùng ping-pong, phát ngược `7→1`, bỏ frame ở biên hoặc nhánh loop riêng để chữa dáng đi sai.
- Không đưa hai frame trùng hoặc gần trùng pha chuyển động vào chu kỳ; đặc biệt frame cuối phải là pha trước frame đầu, không sao lại tư thế đầu để “đóng vòng”. Lấy mẫu `[0,360°)` không lấy cả0°và360°. Kiểm tra mọi cặp trùng pixel, so thêm tư thế/chân và cadence ở biên cuối→đầu; khác màu vài pixel không đủ chứng minh pose khác. Hai chân phải đổi vai trò chân trụ/chân vung, tránh lò cò. Sai nhịp tiếp đất = motion FAIL dù hash frame khác nhau.
- **Run phải có dáng chạy riêng** (Owner làm rõ 2026-11-12, thay thế hướng dẫn run=walk tăng tốc trước đó): walk chỉ là tiền đề tham khảo nhận diện, giải phẫu và nhịp chân. Không dùng lại toàn bộ frame/rect walk rồi tăng playback để nhận là run. Tạo pose chạy toàn thân riêng: sải dài, trọng tâm/chúi thân, pha đẩy chân/thu chân/tiếp đất phù hợp; vòng0..N−1→0 liên tục (8pose:0..7→0; thêm pose thì cập nhậtN), không ping-pong. Không áp cứng tỷ lệ duration0.5 giữa hai clip. Review cadence và biên cuối→đầu của run độc lập; tốc độ map tách khỏi tốc độ frame.
- Turn bắt buộc trong atlas mới; ngoại lệ Owner: King Crab. Xoay phối cảnh thật hoặc cơ chế Owner chốt, giữ nhận diện master, kiểm riêng trái→phải và phải→trái; nối walk→turn→walk ở hai đầu đường/giới hạn trên Godot/localhost, không lật ảnh giả xoay. Sửa/test theo giới hạn 5 vòng; giữ nguyên heavy đã duyệt.

## Điều 8. Tiêu Chuẩn Developer (Unit Test, CI/CD, Versioning) & Bộ Nhớ Bắt Buộc (`./loop.sh`)

1. **Unit Test, CI/CD & SemVer**:
   - Mọi module xử lý dữ liệu, Godot prefab/bundle, Rust WASM/combat core và giao diện 3 Tab phải có kiểm thử tự động chạy qua `./loop.sh test` (`exit 0`) và tích hợp CI (`.github/workflows/ci.yml`).
   - Phiên bản nguồn duy nhất tại `VERSION` theo chuẩn `MAJOR.MINOR.PATCH`, đồng bộ chặt với `state.json`, `project.godot` và `engines/rust_combat_sim/Cargo.toml`.
2. **Quy tắc Đọc / Ghi Hệ Thống Bộ Nhớ (`./loop.sh`)**:
   - **`AGENTS.md` & `state.json` (BẮT BUỘC MỌI PHIÊN)**: Chạy `./loop.sh status` ngay khi vào phiên; cập nhật `state.json` ngay sau mỗi task để chống mất ngữ cảnh khi đứt kết nối.
   - **`skills.md` (ĐỌC TRƯỚC KHI NHẬN XỬ LÝ ATLAS)**: Chỉ ghi vào sau khi Owner nghiệm thu Human Test thành công.
   - **`lerning.md` (ĐỌC TRƯỚC KHI CODE / SỬA ASSET)**: Đọc để tránh lặp lại lỗi kỹ thuật cũ; ghi bổ sung ngay sau khi gặp lỗi mới và đã sửa xong có kiểm chứng.
