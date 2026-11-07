# SỔ TAY QUY TRÌNH DỰNG HOẠT ẢNH TỪ ATLAS CỦA OWNER (`skills.md`)

> **PHÂN BIỆT BẮT BUỘC (Theo Điều 6 — `AGENTS.md`)**:
> - **File `skills.md` này KHÔNG PHẢI là bộ skill công cụ asset sprite (`.agents/skills/generate2dsprite`...)**.
> - `.agents/skills/*` là **thư viện công cụ kỹ thuật cấp thấp** (cắt ảnh, tách nền `forge_matte`, đóng gói `export_engine.py`).
> - Còn `skills.md` là **Quy trình Nghiệp vụ End-to-End của riêng dự án DR7-Studio**: từ lúc nhận một file Atlas / Ảnh gốc từ Owner → phân tích thông số → bóc tách bảo toàn chi tiết (Gộp 1 lớp hoặc Tách đa lớp chiều sâu) → chạy vòng lặp kiểm thử trên Engine → xuất đồng bộ 1:1 ra `localhost:8080` cho tới khi đạt yêu cầu của Owner.
>
> **QUY TẮC ĐỌC / GHI**:
> 1. File này **khởi tạo ở trạng thái TRỐNG (`0` quy trình)**.
> 2. **Khi nào ĐỌC**: Đọc ngay khi Owner gửi một mẫu Atlas nhân vật/hiệu ứng mới để biết quy trình chuẩn đã từng được Owner duyệt (dùng ngay mà không cần hỏi lại những bước đã thống nhất).
> 3. **Khi nào GHI**: Chỉ sau khi hoàn tất chỉnh sửa một task cùng Owner và **được Owner xác nhận nghiệm thu Human Test thành công**, Agent mới ghi đúc kết quy trình đó vào giữa hai thẻ bên dưới.

<!-- SKILLS_ENTRIES_START -->
<!-- Hiện tại: TRỐNG (0 quy trình). Chờ ghi nhận sau khi Owner nghiệm thu Human Test thành công. -->
<!-- SKILLS_ENTRIES_END -->
