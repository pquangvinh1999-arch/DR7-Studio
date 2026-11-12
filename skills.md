# SỔ TAY QUY TRÌNH DỰNG HOẠT ẢNH TỪ ATLAS CỦA OWNER (`skills.md`)

> **PHÂN BIỆT BẮT BUỘC (Theo Điều 6 — `AGENTS.md`)**:
> - **File `skills.md` này KHÔNG PHẢI là bộ skill công cụ asset sprite (`.agents/skills/generate2dsprite`...)**.
> - `.agents/skills/*` là **thư viện công cụ kỹ thuật cấp thấp** (cắt ảnh, tách nền `forge_matte`, đóng gói `export_engine.py`).
> - Còn `skills.md` là **Quy trình Nghiệp vụ End-to-End của riêng dự án DR7-Studio**: từ lúc nhận một file Atlas / Ảnh gốc từ Owner → phân tích thông số → bóc tách bảo toàn chi tiết theo combined_1layer (Ki/aura độc lập theo mặc định Owner; FX khác theo contract từng nhân vật) → chạy vòng lặp kiểm thử trên Engine → xuất đồng bộ 1:1 ra `localhost:8080` cho tới khi đạt yêu cầu của Owner.
>
> **QUY TẮC ĐỌC / GHI**:
> 1. File này **khởi tạo ở trạng thái TRỐNG (`0` quy trình)**.
> 2. **Khi nào ĐỌC**: Đọc ngay khi Owner gửi một mẫu Atlas nhân vật/hiệu ứng mới để biết quy trình chuẩn đã từng được Owner duyệt (dùng ngay mà không cần hỏi lại những bước đã thống nhất).
> 3. **Khi nào GHI**: Chỉ sau khi hoàn tất chỉnh sửa một task cùng Owner và **được Owner xác nhận nghiệm thu Human Test thành công**, Agent mới ghi đúc kết quy trình đó vào giữa hai thẻ bên dưới.

> **Chỉ dẫn Owner hiện hành**: nhân vật/FX dùng pixel art đồng bộ, không nâng HD; Ki/aura độc lập cho nhân vật có Ki; không guard/win cho bất kỳ nhân vật nào và không hỏi lại. Giữ các chỉ dẫn chung này sau khi dọn toàn bộ nhân vật. Không ghi workflow chưa được Owner nghiệm thu.

<!-- SKILLS_ENTRIES_START -->
### [PIPE-001] T-rex — quy trình đã nghiệm thu v0.6.0
- **Nghiệm thu**: Owner chốt cả 3 nhân vật ngày `2026-11-12T07:38:36.605057+00:00`. Receipt `assets/t_rex/owner_approval.json`; atlas SHA-256 `d78b3b750c51793de4eafe3532c2350fff52bce9d54ecd40b879fc6e44c1d1b7`. Receipt này thay nghiệm thu revision cũ; lịch sử JSON tại docs/releases/.
- Nguồn tạo hình: `work/characters/t_rex/walk-style-v4/walk-00-reference.png`. Sinh lại nguyên pose theo walk0 để đồng bộ nét/màu/ánh sáng. attack_heavy 12 pose, 35 tick: lấy đà, xoay trụ và đổi phối cảnh, đuôi trễ, bước bắt trọng tâm và hồi thế; không xoay một quad. Giữ walk0 đã chọn. 73 frame refs / 9 clip; fireball_fx 4 pha độc lập.
- **Dựng và kiểm tra**: sinh pose TOÀN THÂN, không cắt chi/thân rồi xoay/warp/vá. Chỉ cắt nguyên frame khỏi sheet để key nền, căn anchor và đóng atlas. Giữ thân combined_1layer; FX độc lập theo render_contract. Nearest, native1px, alpha thân cứng; xem filmstrip sáng/tối/ô cờ, phát tốc độ thực và kiểm tra nối vòng. Technical exit0 và nghiệm thu motion là hai gate riêng.
- **Đóng gói**: cùng nguồn PNG/rect/tick60Hz/anchor cho Godot và localhost; canvas384×256, anchor [176,224]. Kiểm thử loop.sh test, Rust WASM build và HTTP parity. Không guard/win; các clip bị Owner loại được giữ WARN tham chiếu, không tạo giả.
- **Nguồn và bàn giao**: QA `docs/characters/t-rex-walk-style-v4-qa.json`; review `work/characters/t_rex/walk-style-v4/review/keyframe-review.json`. Giữ master, source pose cuối, frame runtime và filmstrip nghiệm thu; PNG nháp/baseline dư xóa theo docs/releases/v0.6.0-png-cleanup.json. Không dùng script lịch sử cần baseline đã xóa để ghi đè bản duyệt. Revision hình ảnh/timing sau này cần nghiệm thu mới.

### [PIPE-002] Pteranodon — quy trình đã nghiệm thu v0.6.0
- **Nghiệm thu**: Owner chốt cả 3 nhân vật ngày `2026-11-12T07:38:36.605057+00:00`. Receipt `assets/pteranodon/owner_approval.json`; atlas SHA-256 `8789d914abf677ac043ac16f6cf8713c0f2a28bb8f7acb223e874b9aa39cb005`. Receipt này thay nghiệm thu revision cũ; lịch sử JSON tại docs/releases/.
- Nguồn tạo hình: `work/characters/pteranodon/master-match-v9/reference.png`, đúng mẫu Owner test_scaled_canvas. Tái tạo 54 pose toàn thân theo mẫu, giữ thứ tự/tick/loop/events/state của các hoạt ảnh đã duyệt. Không thiết kế lại chuyển động. 61 refs / 8 clip; sonic_screech_fx 7 pha giữ nguyên byte, phát tại power_up frame2 từ [278,128], 14 tick; không tăng tốc thân để đổi tốc độ FX.
- **Dựng và kiểm tra**: sinh pose TOÀN THÂN, không cắt chi/thân rồi xoay/warp/vá. Chỉ cắt nguyên frame khỏi sheet để key nền, căn anchor và đóng atlas. Giữ thân combined_1layer; FX độc lập theo render_contract. Nearest, native1px, alpha thân cứng; xem filmstrip sáng/tối/ô cờ, phát tốc độ thực và kiểm tra nối vòng. Technical exit0 và nghiệm thu motion là hai gate riêng.
- **Đóng gói**: cùng nguồn PNG/rect/tick60Hz/anchor cho Godot và localhost; canvas384×256, anchor [176,200]. Kiểm thử loop.sh test, Rust WASM build và HTTP parity. Không guard/win; các clip bị Owner loại được giữ WARN tham chiếu, không tạo giả.
- **Nguồn và bàn giao**: QA `docs/characters/pteranodon-master-match-v9-qa.json`; review `work/characters/pteranodon/master-match-v9/review/keyframe-review.json`. Giữ master, source pose cuối, frame runtime và filmstrip nghiệm thu; PNG nháp/baseline dư xóa theo docs/releases/v0.6.0-png-cleanup.json. Không dùng script lịch sử cần baseline đã xóa để ghi đè bản duyệt. Revision hình ảnh/timing sau này cần nghiệm thu mới.

### [PIPE-003] Spinosaurus — quy trình đã nghiệm thu v0.6.0
- **Nghiệm thu**: Owner chốt cả 3 nhân vật ngày `2026-11-12T07:38:36.605057+00:00`. Receipt `assets/spinosaurus/owner_approval.json`; atlas SHA-256 `89d9696e447d346693b516472cdc4dceeca826dff5b2bd463332d911f883c4a4`. Receipt này thay nghiệm thu revision cũ; lịch sử JSON tại docs/releases/.
- Giữ bộ cuối chỉ có walk; không tạo run hay alias run. 71 refs / 9 clip, 68 vùng atlas. Walk8 pose vòng0..7→0, tick[7,8]×4; heavy12 pose35tick; turn4pose20tick nối đổi hướng trong state machine. Nguồn frame đóng băng `work/characters/spinosaurus/approved-final-frames/`; builder build_generated_spinosaurus.py copy/repack nguyên frame. Nguồn pose và SHA tại docs/characters/spinosaurus-final-qa.json.
- **Dựng và kiểm tra**: sinh pose TOÀN THÂN, không cắt chi/thân rồi xoay/warp/vá. Chỉ cắt nguyên frame khỏi sheet để key nền, căn anchor và đóng atlas. Giữ thân combined_1layer; FX độc lập theo render_contract. Nearest, native1px, alpha thân cứng; xem filmstrip sáng/tối/ô cờ, phát tốc độ thực và kiểm tra nối vòng. Technical exit0 và nghiệm thu motion là hai gate riêng.
- **Đóng gói**: cùng nguồn PNG/rect/tick60Hz/anchor cho Godot và localhost; canvas384×256, anchor [176,224]. Kiểm thử loop.sh test, Rust WASM build và HTTP parity. Không guard/win; các clip bị Owner loại được giữ WARN tham chiếu, không tạo giả.
- **Nguồn và bàn giao**: QA `docs/characters/spinosaurus-final-qa.json`; review `work/characters/spinosaurus/review-final/keyframe-review.json`. Giữ master, source pose cuối, frame runtime và filmstrip nghiệm thu; PNG nháp/baseline dư xóa theo docs/releases/v0.6.0-png-cleanup.json. Không dùng script lịch sử cần baseline đã xóa để ghi đè bản duyệt. Revision hình ảnh/timing sau này cần nghiệm thu mới.

<!-- SKILLS_ENTRIES_END -->
