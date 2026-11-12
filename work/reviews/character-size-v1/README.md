# Mẫu kích thước — chờ Owner duyệt trước atlas

Owner chọn chiều ngang đầy đủ của pose idle0, không tính FX. Giữ nguyên tỷ lệ riêng của từng loài, không ép chiều cao bằng nhau.

| Nhân vật | Bbox mẫu | Canvas | Anchor |
|---|---|---|---|
| Spinosaurus, giữ nguyên | 157×74 | 384×256 | [176,224] |
| Pteranodon, thu đồng đều | 157×107 | 384×256 | [176,200] |
| Tasmanian King Crab | 133×64 | 384×256 | [176,224] |

133/157=84.7134%, tức giảm15.2866%; mục tiêu chính xác133.45px được làm tròn133px. Kích thước tính trên toàn silhouette, gồm cánh/chân/càng. Pteranodon là pose bay, anchor được giữ nguyên; chân không bị kéo xuống đất để so chiều cao.

Ảnh so sánh comparison-light.png, comparison-dark.png, comparison-checker.png được xem trực tiếp. Mẫu PNG trong thư mục này dùng toàn pose, Nearest, alpha0/255; không chỉnh màu, LUT, sharpen hay chia/cắt chi.

Lệnh build_review.py đo lại bbox/alpha và assert đúng chiều ngang đã chốt; measurements.json ghi nguồn/SHA và hệ số. Nearest làm mất cực biên1px của Pteranodon khi thử raster157×107 (bboxthực156×107). Bản cuối resample đồng đều ra158×107, silhouette thực157×107; không vẽ bù hoặc kéo riêng cánh. Thông số scale thực nằm trong measurements.json.

Tasmanian dùng nguyên concept-v2, loại alpha nguồn dưới128 để bỏ quầng thấp alpha, alpha còn lại255, thu toàn pose vào133px. Đây là xử lý nền/đóng khung kỹ thuật, không phải sinh lại pose. Không ép palette/Sobel về mốc mẫu. Sobel đo thực: Spino271.574, Ptera190.305, cua349.243; các giá trị không tự chứng nhận đồng bộ thẩm mỹ. Hình dáng và nét nhỏ sau thu phải được Owner duyệt. Tạo hình/chi tiết chân bị che trong concept chưa được chứng nhận bằng hoạt ảnh.

Chỉ là mẫu kích thước tĩnh để duyệt. Bộ Pteranodon đã nghiệm thu trong assets/scenes chưa bị thay đổi; chưa tạo atlas mới hoặc đưa cua vào roster. Không có motion/engine PASS cho revision kích thước mới. Sau Owner duyệt mẫu mới áp dụng cùng scale vào toàn bộ hoạt ảnh Pteranodon và thiết kế atlas cua; kiểm thử Godot/Rust/WASM/parity khi đóng gói.
