# Mốc độ nét nhân vật — T-rex nâng cấp

Owner chọn độ nét T-rex đã nâng cấp làm chuẩn chung cho nhân vật tạo tiếp theo. Việc chọn mốc này không nghiệm thu bộ hoạt ảnh T-rex đang demo.

- Ảnh cố định: [t-rex-sharpness-reference.png](t-rex-sharpness-reference.png), copy nguyên byte từ idle0 sau TASK-048. SHA `8c46b31b6fd328fef3b5b4bd8a1d1ebbd30d51f4d5720c673b3f2437ad565311`.
- [Contract và số đo](character-pixel-sharpness.json): chi tiết1px gameplay, Nearest, alpha thân100%. Mẫu canvas384×256, thân186×134, anchor[176,224]; đây là kích thước mẫu, không bắt mọi loài cùng kích thước.
- Sobel biên trong245.516, đo BT.709 trên RGB đã đặt0 ngoài alpha, Sobel scipy chưa chuẩn hóa, biên alpha phía trong. Đây là số tham chiếu, không phải scalar cần gán hoặc số bằng tuyệt đối cho mọi hình dạng/palette.

Trước khi tạo nhân vật mới, mở mẫu ở kích thước1× và zoom nguyên lần Nearest, đối chiếu trên nền sáng/tối/ô cờ. Giữ độ rõ của viền/mảng màu và mật độ chi tiết tương đương, tránh nhòe, viền quá dày, dither mịn hoặc biến thành HD. VFX được dùng alpha mềm khi cần. Không ép16màu hoặc quay lại pipeline100texel→2×Nearest cũ.

Đo frame gameplay thực tế:

```bash
python3 tools/art/measure_pixel_sharpness.py path/to/frame.png
```

Công cụ báo hash, bbox, số pixel/màu, alpha và Sobel thực tế; không tự đánh giá giải phẫu hay cảm giác chuyển động. Sobel biên trong còn phụ thuộc độ dày viền: viền đen quá dày có thể làm chỉ số giảm dù ảnh nhìn tương phản hơn. Vì vậy phải xem ảnh, không dùng blur/sharpen/LUT để ép số hoặc tự đặt dung sai chưa được Owner chốt.

Đọc chuẩn này qua Điều7.2 `AGENTS.md` và các skill `create_atlas`, `generate2dsprite`, `video2dsprite`. Mốc mới chỉ áp dụng trong phạm vi Owner yêu cầu tạo/sửa; không tự tái dựng các nhân vật đã duyệt. Structural tear/hở khớp/lật ảnh giả xoay vẫn là motion FAIL dù độ nét đạt.
