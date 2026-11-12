# T-rex — walk frame0 làm mẫu hình ảnh và heavy có chuyển trọng lượng

> **Chốt v0.6.0**: Owner đã nghiệm thu cả 3 nhân vật. Receipt hiện hành ở `assets/` và `docs/releases/v0.6.0-owner-approval.json`. Các ghi chú pending/baseline bên dưới là lịch sử trước nghiệm thu; ảnh nháp đã dọn theo `docs/releases/v0.6.0-png-cleanup.json`. Nguồn cuối, runtime và filmstrip được giữ; không chạy lại script lịch sử cần baseline đã xóa.

Owner 2026-11-12 chọn `walk` frame0 hiện hành làm mốc nhận diện, độ nét, màu, cách tô sáng/bóng cho toàn bộ hoạt ảnh T-rex. Owner vẫn thấy heavy giống một khối quay, nên chỉ dẫn cũ “motion đã chốt, chỉ sửa identity” của TASK050 không còn áp dụng.

## Mẫu khóa và phạm vi

- Nguồn chính xác: `work/characters/t_rex/walk-style-v4/walk-00-reference.png`, copy byte từ `assets/t_rex/clips/frames/frame-08.png` trước sửa.
- SHA-256: `d4dc74e198774a0af2097962967492e3d2f909831b40b7c811ea7b5aa3208e69`.
- Canvas384×256, bbox `Rect(80,102,188,122)`,8355pixel visible,6763RGB,Sobel230.524,alpha thân100%. Công cụ đo `tools/art/measure_pixel_sharpness.py`.
- Mẫu này áp cho T-rex đang sửa; không tự đổi chuẩn toàn dự án hoặc sửa Spinosaurus/Pteranodon đã duyệt.
- Không có shader vật liệu bóng riêng trên sprite thân trong scene được kiểm tra. WebGL preview có shader lấy texture và hit-flash; độ bóng/cách chiếu sáng người xem cảm nhận chủ yếu được tô trong PNG. Bản sửa đồng bộ art, không thêm shader specular.

## Thay đổi

Built-in imagegen dùng cùng walk0 làm identity/style reference cho mọi action. Bảy sheet action cũ chỉ cung cấp pose/layout; heavy tạo12pose toàn thân mới theo pha tuyệt đối. Không cắt đầu/chi rồi warp/xoay/ghép, không mirror/rotate quad để giả chuyển động.

- Giữ nguyên PNG walk0 và4PNG `fireball_fx`. Tổng73refs/9clip,68PNG thân mới. Giữ count/order/ticks/events/loop/hitstop của toàn bộ clip so baseline đầu task.
- Các action không phải heavy không resize pose: alpha128→binary và dịch toàn frame vào bbox/đường chân cũ. Hình nguồn được chỉnh bằng imagegen nên không nhận silhouette/pose giữ pixel100%; các khác biệt contour cần Human Test.
- Heavy dùng cùng một phép thu toàn ô384→242 cho mọi góc, không ép bbox góc trước/lưng thành chiều rộng nhìn ngang. Trục hông tham chiếu176 và chân trụ thấp nhất225; giữ crouch/head-height trong pose. Không kéo riêng chi hay thay tỷ lệ theo từng góc.
- Heavy có pha hạ gối/tải trọng và cuộn đuôi ở1, bước chân xoay ở2–4, quật ở5, chân sau nhấc ở6–7, bước bắt thăng bằng ở8–9 rồi hồi ở10–11. Đây là thiết kế/quan sát candidate, không phải chứng minh lực hoặc giải phẫu bằng số đo.
- Heavy giữ `[5,4,2,1,1,1,1,2,3,4,5,6]`=35tick≈583.33ms, hitframe5/tick13 và hitstop giữ nguyên. Phần thay đổi là art articulation, không chỉ tăng playback.

Ảnh heavy đầu trả nền trắng bán đục: Atlas nguồn `(0,0)` làRGBA(252,253,253,194). Ảnh đó lưu dưới `generated/attack_heavy-raw-background-rejected.png`, không dùng để slice/runtime. Đã gọi imagegen background-extraction riêng, đo alpha min0 trước khi đóng frame. Không xóa trắng bằng ngưỡng màu vào răng/bụng.

## Kiểm chứng và giới hạn

Atlas một trang, SHA `d78b3b750c51793de4eafe3532c2350fff52bce9d54ecd40b879fc6e44c1d1b7`. PNG/WASM/HTML localhost khớp file đĩa; các thông số rect/tick/anchor dùng chung.500file peers giữSHA. Các số đo theo từng pose ở `work/characters/t_rex/walk-style-v4/measurements.json`; không ép cùng Sobel, không chạy LUT/sharpen để khớp scalar.

Builder/exporter exit0, warnings0. Godot import exit0. `./loop.sh test` exit0:26Python/E2E,3bundle Godot và2Rust. WASM release build exit0. Các cảnh báo clip Owner đã loại và `t_rex: motion=reviewed_pending_owner; Owner Human Test chưa nghiệm thu.` được giữ nguyên trong `verification/tests.log` và QA JSON.

Đã mở đủ9filmstrip và power_up-composite trên sáng/tối/ô cờ. Có playbackWebP đúng tick của từng action, reference-lineup, per-frame Canvas bbox và source-cell trong registration.json. **Độ tự nhiên khi phát, nối vòng và mức khớp cách tô với mẫu vẫn pending Owner; không có motion-naturalness PASS.** Technical exit0 không thay nghiệm thu hình ảnh. Không ghi quy trình mới vào `skills.md`, không thay biên nhận Owner cũ.

Preview có link chọn character/clip/frame và pause, kèm E2E kiểm tra chọn0 và clamp frame ngoài phạm vi:

- Mốc: `http://localhost:8080/?character=t_rex&clip=walk&frame=0&paused=1`.
- Heavy: `http://localhost:8080/?character=t_rex&clip=attack_heavy&frame=0`.

Nguồn/prompt/baseline/stage/review/log: `work/characters/t_rex/walk-style-v4/`. QA: `docs/characters/t-rex-walk-style-v4-qa.json`. Bản cũ được lưu để đối chiếu, không rollback các thay đổi khác sẵn có trong workspace.
