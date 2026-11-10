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
### [PIPE-001] Quy Trình Dựng Atlas & Godot 4 Bundle Từ Master Pixel Art + Sheet FX Của Owner (`T-rex` / `t_rex`)
- **Trạng thái nghiệm thu**: `owner_approved` (`2026-11-10T04:32:34Z`) — Biên nhận: `assets/t_rex/owner_approval.json` (`atlas_sha256: 67df45fe8d8c517725c90648d461f9f3501db89f1edbf2ad20ef6069ff7c4ea8`).
- **Thông số gốc & Khung chuẩn**:
  - Master tĩnh đã duyệt: `work/characters/t_rex/approved-master/approved-original.png` (`1024×1024`, lưới pixel logic gốc `100×100` texel, phóng `2:1 Nearest` lên khung gameplay `384 × 256 px`, tâm chân `foot_anchor_px = [176, 224]`).
  - Sheet FX lửa của Owner: `work/characters/t_rex/approved-master/fire_fx_source.png` (`400×250`, nền `RGB(14, 14, 14)`, gồm 4 cụm lửa đọc theo thứ tự từ phải sang trái `Cụm 4 -> Cụm 3 -> Cụm 2 -> Cụm 1` và lật ngang sang phải `+X`).
- **Quy tắc nghiệp vụ đã được Owner nghiệm thu**:
  1. **Khóa danh sách clip theo giải phẫu & đặc tả riêng nhân vật**:
     - Gồm 8 clip thân (`idle`, `walk`, `run`, `attack_light`, `attack_heavy`, `power_up`, `hit`, `ko`) + 1 clip FX độc lập (`fireball_fx`) = 9 clip / 71 frame trên 1 trang PNG Atlas duy nhất (`3494 × 2082 px <= 4096 × 4096`).
     - Không tạo và không setup các clip bị loại: `jump`, `aura_loop` (loại riêng cho `T-rex`), `guard`, `win` (loại toàn dự án).
  2. **Kiến trúc bộ phận giải phẫu liên thông & Đường viền hợp nhất (`Combined 1-Layer`)**:
     - Mỗi bộ phận giải phẫu tách từ master bắt buộc lọc giữ duy nhất thành phần liên thông chính (`components == 1`) để triệt tiêu hạt nhiễu rìa.
     - Hợp nhất `[đuôi + thân + cầu nối cổ + đầu trên]` vào một buffer chung trước khi viền `1px` (`OUTLINE_RGBA`) để không hở cổ khi vươn cắn/khạc lửa và không hở gốc đuôi khi xoay người quất đuôi `360°` ở `attack_heavy`.
     - Kẹp mặt đất (`clamp_ground_ko`) cho các frame ngã gục của `ko` để thân khủng long nằm đúng trên đường mặt đất `y = 224`.
  3. **Đồng bộ 1:1 giữa thân nhân vật và Sheet FX đính kèm ở `power_up`**:
     - Frame `0–1` (`p0..p1`): `T-rex` ngửa cổ lấy đà, mở hàm nén luồng khói nâu-vàng và lõi lửa sáng ngay trong vòm họng.
     - Frame `2–5` (`p2..p5`): `T-rex` lao đầu về trước và khạc 4 cụm lửa từ mẫu của Owner (đọc từ phải sang trái `Cụm 4 -> Cụm 3 -> Cụm 2 -> Cụm 1`, tách nền `diff > 32` + khử lem biên + lật ngang `+X`) tiến dần từ `x = 266` tới `x = 382` trên trục miệng `y = 138`, đồng thời xuất `fireball_fx` (`4 frame`, `[5, 5, 5, 5]` ticks) đồng bộ toạ độ qua `render_contract.projectile`.
     - Frame `6–8` (`p6..p8`): Khói tàn ở chóp mũi và khép hàm hồi về `idle`.
<!-- SKILLS_ENTRIES_END -->
