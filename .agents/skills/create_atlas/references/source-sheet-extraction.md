# Bóc tách sheet Owner — nhánh bảo toàn nguồn
> Chỉ dẫn Owner hiện hành: pixel art, không guard/win; Ki/aura độc lập theo create_atlas/SKILL.md. Với sheet nguồn đã gộp, chỉ tách Ki nếu bảo toàn được hình nguồn; nếu không, báo giới hạn trước phần phụ thuộc, không AI redraw rồi nhận là bóc tách nguyên bản.


Chỉ đọc khi đầu vào đã có nhiều pose/frame và Owner yêu cầu phân tích hoặc bóc tách. Không dùng nhánh này để thay thế thiết kế chuyển động từ ảnh tĩnh. Không AI redraw/inpaint/vẽ bù pose nguồn.

## Đọc nguồn và lập bằng chứng

1. Dùng file thực trên đĩa; ghi tên, SHA-256, bytes, kích thước, mode, alpha extrema, màu phổ biến và metadata ảnh. Không lấy kích thước ảnh hiển thị trong chat làm kích thước nguồn.
2. Mọi tọa độ dùng **Atlas gốc**, gốc trái trên, X sang phải, Y xuống dưới. `Rect(x,y,w,h)` dùng cận phải/dưới loại trừ. Phân biệt rõ tọa độ atlas, crop phóng và canvas xuất.
3. Mở toàn ảnh và mọi dải ở native size/phóng nearest, bao gồm header, mép trái/phải, footer, bảng màu và các khoảng trống. Vạch, đốm nhỏ, vòng năng lượng đứt nét đều cần ghi nhận; không tự xóa bằng ngưỡng diện tích.
4. Ghi màu và alpha đo thực. Nền phẳng màu không phải transparency; màu trắng trong chưởng không mặc nhiên là nền. Tổng số màu của cả sheet không chứng minh ảnh bị resize hay nén.

## Phân tích cấu trúc đầy đủ

- Tách **nhóm nhãn**, **hàng bố cục**, **pose có thân**, **FX độc lập**, **đồ trang trí/chữ**, **mẫu palette/trang phục**. Một hàng không tương đương một clip; một connected component không tương đương một frame.
- Gán ID ổn định cho hàng và slot theo vị trí, ví dụ `ATK-R1-P01`, `KI-FX02`. Ghi cửa sổ khảo sát và bbox/mask riêng khi đã xác minh. Cửa sổ khảo sát không phải lệnh crop.
- Với từng slot: mô tả tư thế, hướng mặt/thân, tay/chân, tiếp đất/không trung, FX gắn liền hay rời, chi tiết sát hàng bên cạnh và ứng viên nhóm động tác. Chỉ dùng tên chiêu chính thức khi có nhãn hoặc Owner xác nhận.
- Phân biệt **số pose quan sát** với **số frame timeline**. Timing, loop, recovery, event hit và thứ tự các mảnh FX không suy ra chắc chắn chỉ từ thứ tự trái→phải. Giữ chúng ở trạng thái chưa xác nhận.
- Bao quát intro/biến hình, đứng/guard, di chuyển/teleport, toàn bộ hàng đánh, damage/knockdown, ki, supers, ultimates và biến thể cuối sheet. Không tự coi footer variants là nhân vật đã có đủ hoạt ảnh.
- Các mảnh tia, vòng, đuôi đạn và smear có thể nhiều component rời nhưng cùng một FX; một beam có thể dính thân nhưng vượt xa bbox cơ thể. Tránh lọc largest-component hoặc chia cột đơn thuần.
- Credits và thống kê trang trí được giữ trong hồ sơ nguồn; không tự diễn giải chúng thành damage, tốc độ, reach hoặc chỉ số gameplay.

## Chốt phân tích trước khi xử lý

Phân loại kết luận: **đo được**, **quan sát trực tiếp**, **giả thuyết**, **chưa xác nhận**. Báo cáo những khoảng chưa đủ bằng chứng, không tuyên bố “đủ mọi frame” bằng cách đếm component.

Đưa ra: danh mục vùng/slot, vùng không thuộc runtime, rủi ro key/ownership/anchor, ứng viên nhóm clip, dữ liệu còn thiếu và kế hoạch kiểm chứng. Không bắt Owner chốt timing khi họ mới yêu cầu phân tích.

## Khi được yêu cầu thực thi sau này

Đọc skill [generate2dsprite](../../generate2dsprite/SKILL.md) và reference kỹ thuật phù hợp; dùng tooling xử lý ảnh có sẵn, bỏ qua nhánh sinh ảnh/master/video khi nguồn là sheet Owner. Xác minh API và flag từ code/`--help` trước khi gọi.

1. Giữ nguồn bất biến; dựng inventory/mask truy vết được pixel về nguồn, có thể nhiều island cho một pose/FX. Loại nhãn/underline/credits bằng vùng xác minh, không xóa hàng loạt chi tiết nhỏ.
2. Pocket-first key trước edge unmixing; kiểm tra hốc nền và foreground cùng màu key. Không áp phép đổi màu toàn sheet. Không đổi nét pixel để “làm mượt”.
3. Căn X theo thân/viền tối, Y theo baseline hàng; giữ quỹ đạo nhảy/bay. Không căn theo bbox gồm beam. Đo body bbox, full-FX bbox, PPU và envelope hai hướng trước khi chọn canvas bội 16; không sao chép canvas Trunks `[320,256]` một cách máy móc.
4. FX rời cần mapping với pose, điểm phát, hướng và pha theo contract; Ki/aura điều khiển độc lập theo mặc định Owner, thân vẫn luôn hiện. Các FX khác theo phạm vi đã chốt. Không bịa frame mất hoặc phát một projectile rời như thể là toàn thân nhân vật. Với nguồn đã gộp không tách được mà vẫn bảo toàn pixel, báo giới hạn trước phần phụ thuộc.
5. Khi backend xuất đã được chọn: một trang atlas tối đa 4096² mỗi nhân vật, nearest, timing tick 60Hz và anchor nhất quán theo quy định hiện hành. 60Hz là đơn vị timeline, không bắt mọi pose giữ đúng 1 tick; một atlas không bảo đảm cả scene chỉ có một draw call.
6. Đọc báo cáo QC và mở từng filmstrip trên sáng/tối/ô cờ. Các ngưỡng dự án: `opaque_key_px=0`, `enclosed_key_pockets=0`, `outer_ring_spill_fraction<=0.005`, `alpha_hardness_pct>=95%` cho pixel art. Chỉ công bố số thực đo, giữ WARN/FAIL nguyên văn.
7. Thực hiện kiểm tra Godot headless, Rust cargo test và WASM theo AGENTS.md hiện hành; không dùng ghi chép kiến trúc cũ để bỏ kiểm thử bắt buộc. Kiểm tra parity dữ liệu riêng với kiểm tra hình ảnh/hiệu năng. Roster rỗng pass không chứng minh bundle nhân vật đúng.
8. Đo render thật trên thiết bị sau khi đủ asset/scene/UI; báo CPU/GPU/frame-time và phạm vi phép đo. Chỉ thêm bundle hoàn thiện vào roster. `skills.md` gốc chỉ cập nhật sau nghiệm thu Human Test.
