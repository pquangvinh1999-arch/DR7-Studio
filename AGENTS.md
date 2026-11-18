# HIẾN PHÁP DỰ ÁN DR7-STUDIO (`AGENTS.md`)

Hiến pháp tối cao ở root `DR7-Studio` (tự nạp bởi `agy` & `codex`). Mọi quyết định kỹ thuật, asset, test engine và preview phải tuân thủ tuyệt đối:

---

## Điều 1. Cấm Tuyệt Đối Bịa Đặt & Đoán Mò (Zero Hallucination / Evidence-Only)

1. **Cấm bịa code, API, tham số**: Chỉ dùng API, flag CLI, schema, hàm đã xác minh qua tài liệu nội bộ, `--help`, mã nguồn hoặc chạy kiểm thử.
2. **Cấm bịa kết quả test/QA**: Chỉ báo cáo `PASS`/`OK` khi lệnh trả về `exit code 0` và đã đọc log thực tế. Mọi `WARN`/`FAIL` phải trích nguyên số liệu, không che giấu.
3. **Cấm suy đoán thiếu bằng chứng**: Nhận định lỗi code hoặc ảnh (alpha, viền màu, lệch tâm, mất chi tiết, độ nét) phải kèm đo đạc cụ thể (`Canvas (x,y)` / `Atlas (x,y)`, `RGBA`, log, path).

---

## Điều 2. Cổng Rõ Ràng & Đồng Nhất Mẫu Chuẩn (Pre-Task Clarity Gate)

1. **Rà soát trước khi làm**: Xác nhận rõ 100% mục tiêu, logic, đầu vào/ra, hiệu năng, nền tảng trước khi code hoặc xử lý asset.
2. **Mơ hồ = Dừng & Hỏi Owner**: Còn điểm chưa rõ từ Owner, `state.json`, `skills.md` thì **BẮT BUỘC dừng, hỏi Owner** kèm phương án + ưu/nhược điểm; cấm đoán mò.
3. **Đồng nhất mẫu chuẩn**: Nhận 1 mẫu chuẩn thì mọi hoạt ảnh phải đồng nhất **kích thước, hình dạng, màu sắc**; không hiểu phải hỏi ngay.

---

## Điều 3. Kiến Trúc `Combined 1-Layer` & Quy Trình Chuẩn Asset/Item

1. **Quy trình phân loại đầu vào bắt buộc (Chốt D7)**:
   - **1a. Nhân vật mới từ ý tưởng (`imagegen` từ 0)**: Ra bản **demo trước** (luôn hỏi **kích thước** + **phân loại** `tướng chính` dùng nút skill hay `quái/boss` dùng AI) → Owner chốt demo → dựng đủ bộ hoạt ảnh atlas (hỏi thêm **tốc độ**, **độ cao bay** nếu là quái bay) và đóng gói bundle Godot ra APK/iOS; sau khi Human Test duyệt → chốt và **xóa toàn bộ file demo trung gian `/work` (D6)**.
   - **1b. Nhân vật có sẵn Sprite Sheet (`Exact Sheet Fidelity`)**: Giữ nguyên **100% cấu trúc và màu sắc bản gốc** (`Zero AI Redraw`). Nếu chưa đạt độ nét pixel chuẩn Hiến pháp (Điều 7.2) phải nâng độ nét lên bằng chuẩn mà **không phá vỡ cấu trúc**; hỏi **kích thước**, **tốc độ**, **phân loại** nếu thiếu; nếu sheet thiếu hoạt ảnh theo bộ chuẩn (Điều 7.1) phải **hỏi lại Owner có cần thêm cho đủ không**; mọi hoạt ảnh xuất ra phải đồng bộ 100% nhân vật gốc, không sai lệch giữa các clip.
   - **1c. Item & ảnh thường (không phải pixel)**: Nếu Owner đưa 1 ảnh không phải pixel vào (áp dụng cho cả **character** lẫn **item**), bắt buộc **convert về đúng pixel chuẩn Hiến pháp trước**, sau đó hỏi kích thước nếu thiếu. Item bắt buộc đủ 4 yếu tố ở Điều 7.5 (`drop_physics`, `diagonal_body_sheen`, `pickup_physics`, icon balo tĩnh).
2. **Kiến trúc Lớp Chính Thức Duy Nhất — `Combined 1-Layer` (`1 Quad / 1 Draw Call` cho phần thân khi tắt FX)**:
   - Giữ thân nhân vật 1 sprite/lớp; **bãi bỏ vĩnh viễn `layered_3d_depth` / `Hướng 2`** (`./loop.sh check` đánh `FAIL` nếu xuất hiện).
   - Ki/aura phải xuất và điều khiển độc lập dùng chung với nhiều hoạt ảnh thân (mặc định cho nhân vật có Ki; không hỏi lại); thân không tách chi/cánh theo chiều sâu.
   - Sheet đã gộp không tách an toàn thì báo giới hạn, không AI redraw để nhận bảo toàn pixel.
3. **Thông Số Kỹ Thuật Bóc Tách, Tách Nền & Đóng Gói Bắt Buộc (Chuẩn `trunks_rage`)**:
   - **Phân tách cụm 2D (`2D Component Ownership Masking`)**: Nhãn liên thông 2D `3×3`/`5×5`, loại bỏ header/footer/chữ thừa/vạch chia `1px`, ghép liền chiêu chia khúc vào đúng tọa độ tay.
   - **Tách nền 2 giai đoạn**: (1) Đục thủng 100% hốc nền kín (`enclosed_key_pockets == 0`, `opaque_key_px == 0`) trước khi khử viền; (2) Khử pha viền `1px` (`outer_ring_spill_fraction <= 0.005`), giữ `alpha_hardness_pct >= 95%` (với pixel art).
   - **Tâm gốc chống trượt chân**: `X` theo trung vị thân/viền tối (`detect_body_center_x`); `Y` theo mặt đất chung từng hàng (`row_ground_y` / `detect_boot_bottom_y`). Khung `[W, H]` bội số của `16`; `centered = false`, `offset = Vector2(-anchor_x, -anchor_y)`.
   - **Texture Atlas Engine**: **1 trang PNG duy nhất (`pages == 1`, `<= 4096 × 4096 px`)**, lọc **`Nearest` (`texture_filter = 1`)**, tốc độ **`60Hz` ticks** trên `.tres` + `engine-export.json`, đặt `.gdignore` trong `source/` & `clips/`.

---

## Điều 4. Kiến Trúc Engine, Mục Tiêu `0đ` & Lộ Trình Scale `35,000` Thực Thể (`ADR-0001`)

Chi tiết kỹ thuật chốt tại [docs/adr/0001-architecture-and-scale-roadmap.md](docs/adr/0001-architecture-and-scale-roadmap.md):

- **Mục tiêu ngân sách & quy mô (Chốt D8, D10)**:
  - **Chi phí giai đoạn dev/test hiện tại = `0đ`** (tối ưu sẵn đường test & scale).
  - **Nền tảng**: Mobile (**Android `.apk`/`.aab`** & **iOS `.ipa`**), khóa **60 FPS (`<= 16.67 ms/frame`)**.
  - **Quy mô gameplay mục tiêu (D10)**: **`7 map lớn × 5 map nhỏ (35 map) × 20 khu = 700 khu`**, trung bình **`50 thực thể/khu` (user + quái) = `35,000` thực thể** toàn server; mỗi Client Mobile chỉ xử lý `1` khu (`<= 50` thực thể), đồng thời vẫn giữ năng lực benchmark `> 2,000` thực thể cho server/core.
- **Kiến trúc Chính Thức Theo 2 Pha (Cấm đánh tráo Pha)**:
  1. **Client Mobile (Mọi Pha)**: **Godot Engine 4 (`GDScript`, renderer `Compatibility`, `canvas_items` + `expand` full ngang D1, `fractional` mặc định + công tắc `Pixel Perfect integer` D2, Safe Area + Touch)**. Do 1 khu chỉ `<= 50` thực thể, Client **không dùng `GDExtension`** (chỉ xét nếu 1 màn hình mở dồn `> 300–2,000` thực thể). Giữ `engines/rust_combat_sim` cho WASM preview (`60Hz` stepper) và Rust Server Pha 2.
  2. **Cloudflare (`0đ` Free)**: DNS + Orange-Cloud Proxy (`wss://` port `443`, không có raw UDP/ENet) + WAF chặn cứng IP **`VN` & `JP`**.
  3. **Supabase (`Free -> Pro`)**: Chỉ Auth JWT + PostgreSQL (hồ sơ, balo, giao dịch ghi theo lô `30–60s` + sự kiện quan trọng); **cấm** dùng Supabase Realtime cho combat 20Hz.
  4. **Game Server (`INetworkTransport` chuyển được `WebSocket` ⇄ `ENet`)**:
     - **Pha 1 (`0đ` Test/Alpha)**: **`Godot Headless Dedicated Server`** chạy **`WebSocket (wss://)`** xuyên Cloudflare Proxy (chung 100% logic GDScript).
     - **Pha 2 (Scale D10 `700` khu / VPS)**: Chuyển Game Server sang **`Rust` trên VPS** (nối crate `engines/rust_combat_sim`, khu trống ngủ) đặt sau Cloudflare WAF Allowlist hoặc mở UDP/ENet kèm firewall GeoIP khi tick server `p99 > 25 ms @20Hz` hay CPU/RAM chạm ngưỡng ADR-0001.
- **Luật Chống Lệch Hiến Pháp (D8)**: Mọi agent phải bám sát Pha đang hiệu lực; **cấm tuyệt đối** tự ý đổi kiến trúc hoặc ghi comment/tài liệu nhận vơ "đã dùng Rust/GDExtension" khi chưa tích hợp thật.

---

## Điều 5. Vòng Lặp Kiểm Thử Engine, Đồng Bộ Đa Nền Tảng & Quản Lý `/work`

1. **Vòng lặp Tự Kiểm Thử (`Engine Verification Loop`)**:
   - Mọi thay đổi asset/scene/core phải chạy `./loop.sh test` (Python unit + JS/WASM E2E + Godot 4 Headless + Compatibility/OpenGL3 shader check + Rust `cargo test`).
   - **FAIL/sai thông số**: Phân tích → sửa → chạy `./loop.sh test`, tối đa **5 vòng cho mỗi vấn đề**; quá 5 vòng phải dừng, báo Owner kèm lỗi, bằng chứng và cách đã thử.
   - **Cổng `motion_quality`**: Kiểm thử kỹ thuật `exit 0` không chứng nhận hoạt ảnh tự nhiên. Frame bị xé/hở khớp/mất kết nối/biến dạng/xuyên sai giải phẫu = **`FAIL`** dù test kỹ thuật pass. Cấm cắt xé ảnh tĩnh thành mảnh xoay/vá; luôn kiểm frame liên tiếp, vòng lặp, tốc độ thực trên 3 nền.
2. **Đồng bộ 1:1 `Localhost ⇄ Godot Web ⇄ APK ⇄ iOS` (Chốt D9)**:
   - Mọi demo, asset, UI/SafeArea, cấu hình map & bước tick `60Hz` phải dùng **cùng 1 nguồn** (`assets/`, `arena-stage.json`, `device-profiles.json`, `atlas.png`, `.tres`, `engine-export.json`, kiểm SHA-256 & `get_stage_metrics()`).
3. **Dọn `/work` & Chỉ lưu Asset Hoàn Thiện (Chốt D6)**:
   - Sau khi nhân vật/item chốt quy trình và duyệt chuyển char mới, **xóa toàn bộ file demo/trung gian trong `/work`**; không giữ rác, char nháp hay video thừa trong git, `assets/`, `scenes/`, `roster.json`.
4. **Hai nơi Human Test bắt buộc, không đổi trang khi chọn nhân vật (Owner 2026-11-16)**:
   - **Tab Human Test tại `localhost:8080`** là nơi xem từng clip và từng frame với scrubber, thước tọa độ, nền sáng/tối/ô cờ và tốc độ thật. Chọn nhân vật trong danh sách phải cập nhật ngay trong tab này; **cấm chuyển sang URL/trang demo khác**. Nhân vật đang chờ Owner duyệt được ghi rõ là `Human Test`, phân loại tướng/quái/boss đúng yêu cầu, tách khỏi roster phát hành.
   - **Tab Sân Tập** là nơi thử gameplay thực trên **Godot Web** và **APK trên màn Android thực tế**. Trước khi mời Owner test, phải đưa cùng atlas, `.tres`, prefab, thông số size/speed/flight và hành vi tấn công/trúng đòn/chết vào Godot, export Web/APK, kiểm SHA-256 và chạy thử. Canvas2D riêng hoặc trang HTML giả lập không được nhận là Godot Web/Sân Tập thực.
   - Asset chờ duyệt có thể nằm trong vùng `review/` được export có kiểm soát cho Godot Web/APK; không ghi là `finalized` trong `assets/roster.json`. Sau Owner Human Test OK mới chuyển vào bundle chính thức và dọn nguồn demo `/work`, `review/`.
   - Với quái bay, xác nhận **hướng nòng súng/đầu trên pose nguồn** bằng pixel cụ thể; chiều chuyển động, hướng nhìn, điểm phát skill và lật ngang phải đồng bộ theo hướng đó ở Human Test, Godot Web và APK. Cấm suy hướng từ thứ tự ô trong sheet hoặc giữ hướng bay ngược nòng súng.
5. **Chuẩn kiểm thử K70E & parity khi đóng gói/chốt version (Owner 2026-11-17)**: Redmi K70E thực tế là thiết bị chuẩn hiện tại. Mỗi lần đóng gói và chốt version phải đồng bộ 1:1 Godot chạy trực tiếp tại localhost với APK về cùng bản build, nguồn asset, map, camera, gameplay, cấu hình hiển thị và tick; kiểm bằng chứng build/hash và chạy thử, đối chiếu trên K70E thực tế trước khi kết luận đạt. So sánh tại cùng tỷ lệ viewport và trạng thái gameplay; không coi Canvas2D giả lập là Godot. Yêu cầu đồng bộ iOS và Godot Web tại Điều 5.2 vẫn áp dụng.

---

## Điều 6. Phân Biệt `skills.md` & `.agents/skills/`

- **`.agents/skills/*`**: Thư viện công cụ kỹ thuật (tách nền, `generate2dsprite`, `video2dsprite`, `generate2dmap`, `export_engine.py`).
- **`skills.md`**: Nhật ký quy trình nghiệp vụ đã qua **Owner Human Test OK** (đọc trước khi làm atlas; chỉ ghi sau khi Owner nghiệm thu). Luôn xem `filmstrip` trên 3 nền (sáng, tối, ô cờ) trước Human Test.

---

## Điều 7. Chuẩn Bộ Hoạt Ảnh, Độ Nét, Hướng Nhìn, Item (`assets/items/`) & Bản Đồ 2D (`assets/maps/`)

1. **Bộ clip chuẩn**: Tham chiếu `idle`, `walk`, `run`, `jump`, `attack_light`, `attack_heavy`, `power_up`, `aura_loop`, `hit`, `ko` (+ kỹ năng đặc trưng). **Owner chốt phạm vi chung: không tạo `guard` và `win`**; giữ WARN tham chiếu không tạo clip giả. Tướng/quái không có hiệu ứng vụ nổ va chạm riêng kèm sheet/atlas hoặc yêu cầu riêng mặc định dùng `assets/fx/powerup_explosion/` (`scale 0.68`).
2. **Mốc độ nét chuẩn — T-rex (`2026-11-12`) & Thẩm mỹ mặc định**:
   - Đối chiếu [t-rex-sharpness-reference.png](docs/art-standards/t-rex-sharpness-reference.png) và [character-pixel-sharpness.json](docs/art-standards/character-pixel-sharpness.json): **1px gameplay, Nearest**, alpha thân 100%; VFX được alpha mềm (`idle0` mẫu 384×256, anchor `[176,224]`, Sobel **245.516**). Đo bằng `python3 tools/art/measure_pixel_sharpness.py <frame.png>`, không blur/sharpen/dither ép số.
   - Quái thú/sinh vật mặc định phong cách **"Hung tợn"** (nanh nhọn, mắt dữ, vuốt bén, màu đậm) trừ khi Owner chỉ định riêng. Công bố đủ metrics chuẩn trong `roster.json`.
3. **Giao tiếp tọa độ UI**: Hỗ trợ `[W, H]`, scrubber, thước X/Y, `RGBA`, khoanh `Rect` → `[DR7-EDIT-SPEC]`.
4. **Hướng nhìn, Chu kỳ Walk/Run & Turn**:
   - Khóa kiểu camera/hướng nhìn/hướng đánh rõ ràng; không flip dọc hay suy hướng mặt từ vị trí atlas.
   - `walk`: vòng tiến pha liên tục `0→N-1→0`, đủ 2 nhịp chân đối, cấm ping-pong hay trùng pose đóng vòng. `run`: dáng chạy riêng (không tăng tốc walk). `turn`: bắt buộc trong atlas mới (ngoại lệ King Crab), xoay phối cảnh thật (cấm `flip_h`/thu ngang lật bìa), timing lấy đà → vung → hồi thế.
5. **Chuẩn Bắt Buộc Cho Mọi Item Game (`assets/items/`)**:
   - Phải convert về pixel chuẩn trước khi đóng gói `1 PNG atlas, 60Hz Nearest, alpha thân 100% 0/255, .gdignore source/&clips/`, và đạt đủ **4 yếu tố** đồng bộ 1:1 Godot ⇄ Localhost ⇄ Mobile:
     - **Icon Balo (`bag` mode)**: Icon tĩnh nguyên bản, **ẩn 100% hiệu ứng**.
     - **Quét sáng chéo (`diagonal_body_sheen`)**: Nằm gọn trong silhouette item, chỉ bật khi nằm chờ trên map.
     - **Rơi từ quái (`drop_physics`)**: Nhảy lên `10px` → rơi chạm `ground_y` → lăn `10px` rồi mới bật sáng chéo.
     - **Nhặt vào người & Sân Tập (`pickup_physics`)**: Tắt sáng chéo, bay vào thân người nhặt và **thu nhỏ dần** đến khi vào balo; Sân Tập có nút **Ẩn/Hiện** + test rơi & nhặt.
6. **Chuẩn Bắt Buộc Cho Bản Đồ 2D & Dựng Tile Khối Từ Ảnh Mẫu (`assets/maps/`)**:
   - Mọi ảnh map mẫu Owner gửi đều **không được** dùng làm tấm ảnh phẳng duy nhất thiếu mặt sàn tương tác; agent **BẮT BUỘC** giữ nguyên tài nguyên/bản gốc và đồng bộ 1:1 Godot ⇄ Localhost ⇄ APK/iOS qua `terrain.json` / `arena-stage.json`:
     - **Hậu Cảnh Trung Thực Bản Gốc & Phủ Kín Mọi Tỷ Lệ Màn Hình (`D1 expand`)**: Giữ nguyên ảnh gốc về màu và bố cục; trên K70E/iPad dùng `cover` với cùng một hệ số X/Y cho riêng nền, cắt phần vượt khung, không dùng cánh ghép hai bên hoặc dải đen trên/dưới. Nhân vật và va chạm giữ tỷ lệ đều, `Nearest`, không kéo giãn pixel; mặt đất tile phải phủ tới đáy viewport. Không AI vẽ lại hoặc lật gương nguồn.
     - **TileSet Khối Đất Ngang `32×32` (`TileMapLayer` + `StaticBody2D`, scale `2× = 64px` khớp `ppu_reference=64`)**: Bóc tách trực tiếp màu sắc và kết cấu vốn có từ ảnh mẫu gốc để dựng 1 bục sàn ngang góc nhìn `side-view` (`ground_y`) liền mạch không vết ghép; chỉ bổ sung bục phụ (`One-Way Platforms`) khi map được chỉ định rõ (Sân Tập giữ đúng 1 bục sàn ngang chuẩn).
     - **Tương Tác Chân–Đất (`Ground Interaction FX`)**: Bắt buộc có **Dynamic Pixel Contact Shadow** bám bề mặt đỡ gần nhất bên dưới chân (co nhỏ & giảm alpha theo độ cao nhảy/bay; ẩn khi độn thổ; cấm vẽ elip thô) và **Footstep / Landing Dust Pixel FX** khi tiếp đất/bứt chạy.
     - **Duyệt Demo Trước Khi Nhân Rộng**: Với map mẫu mới, xuất demo chạy thử trên cả Godot & Sân Tập `localhost:8080` để Owner nghiệm thu trực quan trước khi nhân bản `35 map` (`D10`).
7. **Kích thước map độc lập màn hình & camera ngang (Owner 2026-11-17)**:
   - Neo kích thước thế giới và biên gameplay của map theo góc nhìn K70E được Owner chọn làm chuẩn; lưu biên theo tọa độ thế giới dùng chung cho mọi thiết bị, có thể mở rộng chiều dài theo từng map. Không lấy mép viewport làm biên map, va chạm hay giới hạn di chuyển; tọa độ, khoảng cách và kết quả combat phải thống nhất giữa các client.
   - Thiết bị có vùng nhìn ngang hẹp hơn chuẩn phải cuộn camera theo player khi đi về phía cuối map, giới hạn camera tại biên map chuẩn; không thay đổi chiều dài map hay kéo giãn nhân vật. Vùng nhìn và camera là hiển thị cục bộ, không thay đổi trạng thái thế giới dùng chung.
   - Kích thước số cụ thể của map chuẩn và chính sách chiều cao cho màn hình cao hơn K70E cần đo/đối chiếu và Owner chốt; không tự coi kích thước viewport 1920×1080 là biên map đã duyệt. Quy định mới về biên thế giới thay thế cách giới hạn đi lại theo mép màn hình trước đây; việc triển khai và kiểm thử phải được xác minh riêng.
8. **Bậc địa hình rắn và tương tác skill (Owner 2026-11-17)**: Mọi bậc hạ cấp phải có mặt ngang đủ rộng, tương đương bậc cao trong cùng đoạn map; mặt cắt đứng và mặt sàn dùng chung tọa độ với ảnh, va chạm và bóng tiếp xúc. Nhân vật đi xuống mép bậc được rơi theo trọng lực; đi ngược lên bị mặt cắt chặn và chỉ vượt khi nhảy đủ cao, không tự nâng chân/trồi lên. Skill/đạn phải dừng hoặc va chạm với mặt cắt và khối đất, không xuyên địa hình. Kiểm đường đi hai chiều và đường bay skill trên các cao độ trước Human Test; áp dụng cho mọi map về sau.
   - Căn chân nhân vật theo **mặt đi được trong ảnh**, không theo mép trước của vách đá; đo ở từng bậc và ở cả frame vừa vượt mép, tránh đứng lơ lửng hoặc chìm sâu trong đất. Nhân vật AI dùng cùng cao độ địa hình.
   - **Nối map và cây tiền cảnh (Owner 2026-11-18)**: Ảnh map là lớp cuối cùng; cây đặt lớp ngay trên map nhưng dưới mọi nhân vật/FX (`Z_map < Z_cây < Z_nhân_vật`), gốc cây nằm dưới mặt đi trên phần vách đất như ảnh mẫu. Với từng bậc mới, đo mặt cắt **tại độ cao chân nhân vật trên ảnh** rồi dùng đúng X đó cho va chạm, bóng, AI và skill; cấm lấy mép lùi phía sau làm X va chạm khiến nhân vật đi quá mép 30–50 px vẫn đứng trên không. Căn chân lùi vào trong mặt sàn theo ảnh mẫu Owner (ảnh 2026-11-18: khoảng 23 px màn hình từ chân đến mép trước), không đặt chân sát mép trước; nếu cao độ mới làm mất độ rơi thì sinh lại **toàn bộ đoạn ảnh nối** với mặt sàn sâu hơn và mép nối liền mạch, không cắt xé ảnh cũ để vá. Kiểm frame đầu tiên tâm chân vượt mặt cắt phải bắt đầu rơi, và kiểm tiếp đất/đi ngược/đạn ở mọi bậc trước Human Test.
   - Nghi thức triệu hồi Shenron và hiệu ứng đặt theo **tâm camera hiện tại** cùng cao độ sàn tại khu vực người gọi; không quay về tâm map gốc khi người chơi đã đi sang khu khác.

---

## Điều 8. Tiêu Chuẩn Developer, SemVer & Bộ Nhớ (`./loop.sh`)

1. **Test, CI/CD & SemVer**: Mọi module (data, Godot prefab/layout, Rust/WASM, server transport, UI preview) phải pass `./loop.sh test` (`exit 0`) & `.github/workflows/ci.yml`. Đồng bộ SemVer tại `VERSION`, `state.json`, `project.godot`, `engines/rust_combat_sim/Cargo.toml`.
2. **Quy tắc Đọc/Ghi File & Bộ Nhớ**:
   - Chạy `./loop.sh status` ngay đầu phiên; đọc `state.json` và giữ `AGENTS.md <= 24,000 bytes`.
   - Đọc `skills.md` trước khi làm atlas; chỉ ghi sau khi Owner nghiệm thu Human Test OK.
   - Đọc `lerning.md` trước khi code/sửa asset; ghi ngay sau khi fix lỗi mới có kiểm chứng.
   - Cập nhật `state.json` sau mỗi task (`./loop.sh log-task`).
