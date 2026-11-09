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
<!-- Chưa có quy trình nghiệm thu đang lưu sau khi Owner yêu cầu dọn toàn bộ nhân vật. -->
<!-- SKILLS_ENTRIES_END -->
