# Turn mặc định cho atlas nhân vật

Owner chốt2026-11-13: mọi atlas nhân vật mới mặc định có turn. King Crab là ngoại lệ đã chốt vì loài này di chuyển ngang. Không tự thêm turn vào nhân vật đã nghiệm thu ngoài task được Owner cho phép. Bốn nhân vật cũ có hàng đợi riêng, chỉ thực hiện sau khi Owner nghiệm thu Chilopoda: [TODO](../turn-retrofit-todo.md).

Turn phục vụ đổi hướng khi đi tới hai đầu đường hoặc phạm vi giới hạn: di chuyển→hãm/bắt đầu turn→chuyển tiếp phối cảnh có trọng lượng→cam kết hướng mới→di chuyển ngược lại. Tách vector di chuyển khỏi hướng mặt trong khi turn. Công bố ticks60Hz; không dịch xuyên ranh giới hoặc lật hướng ngay ở frame đầu. Clip đang quay cần trạng thái khóa/chờ hoàn tất để tránh một lệnh phím làm đảo chiều lần nữa giữa chừng.

**Cơ chế riêng Owner chốt cho Chilopoda**: thay xoay vòng trên đất bằng chui xuống→thân ẩn hoàn toàn→đổi hướng trong giai đoạn ẩn→trồi lên theo hướng ngược. Kiểm hai chiều/endpoint và nối bò thấp; không lộ frame đang flip hay gọi đây là pose xoay phối cảnh. King Crab vẫn không cần turn. Cơ chế riêng này không tự áp sang bốn nhân vật cũ trong TODO.

Tham khảo bộ Spinosaurus đã duyệt (`assets/spinosaurus/owner_approval.json`, manifest/turn và prefab tương ứng), quan sát cả hai chiều và state machine. Không lấy artwork/mask/rig của Spino làm hình của nhân vật khác. Canonical master của từng nhân vật quyết định nhận diện. Mỗi frame turn phải là toàn thân liên tục, giữ đầu/thân/chi/cánh/đuôi/giáp/vũ khí, bảng màu, cách tô, tỷ lệ và thứ tự che khuất. Không cắt/warp/ghép cơ thể; không flip_h, xoay quad hay thu ngang một tấm ảnh làm hoạt ảnh quay.

Phải kiểm RIÊNG phải→trái và trái→phải, tại cả hai endpoint. Một bộ pose có thể dùng mirror/reverse khi giải phẫu, phối cảnh, chi tiết bất đối xứng và nối đầu/cuối của CẢ HAI chiều đều được chứng minh hợp lệ. Không suy rằng chiều còn lại đúng chỉ vì một chiều chạy đúng. Nếu cần hai chuỗi authored riêng thì khai báo mapping rõ trong contract; số tên clip là triển khai, không thay gate hai chiều.

Trước sửa một nhân vật đã duyệt, lưu SHA của toàn bộ ảnh/frame/atlas/manifest và timing ngoài turn. Repack atlas được đổi atlasSHA/rect nhưng PNG decoded của các pose cũ, thứ tự và ticks/events phải giữ nguyên; kiểm RGBA khi tên file/đóng gói thay đổi. Những bản nghiệm thu cũ chỉ chứng nhận revision cũ, không tự duyệt artwork mới. Giữ nguồn/biên nhận cũ và tạo revision/biên nhận mới sau Human Test.

## Score nghiệm thu:100 điểm và gate bắt buộc

Đây là score checklist có bằng chứng, **không phải phần trăm hình giống do mô hình tự suy đoán**. Mỗi tiêu chí10điểm khi có bằng chứng đạt; chưa kiểm là `pending`; sai là `FAIL`, không được cộng điểm bằng suy đoán. Chỉ chốt100/100 khi cả10tiêu chí đạt và Owner đã nghiệm thu revision. Không dùng tổng điểm bù cho lỗi anatomy/hướng/timing. Sửa→`./loop.sh test` tối đa5vòng cho mỗi vấn đề; vòng5 còn FAIL thì dừng phần đó, báo Owner lỗi/bằng chứng/cách đã thử, không vòng6. Hoàn tất từng nhân vật trước khi sửa nhân vật kế.

| # | Tiêu chí10điểm | Bằng chứng bắt buộc |
|---|---|---|
|1|Bảo toàn clip cũ|SHA/RGBA từng pose ngoài turn và ticks/order/events trước/sau;100% khớp|
|2|Nhận diện đúng master|Bảng đối chiếu cùng cỡ gameplay; đầu/thân/chi/palette/cách tô; mỗi pose có kết quả review|
|3|Cơ thể liên tục|Review từng frame, các cặp nối và vòng; không rách khớp/mất cơ quan/patch/đổi tỷ lệ|
|4|Phải→trái đúng|Cơ chế turn Owner chốt: phối cảnh có trọng lượng, hoặc Chilopoda đổi hướng khi hoàn toàn ẩn; đầu/cuối nối đúng di chuyển|
|5|Trái→phải đúng|Bằng chứng riêng, không lấy kết quả chiều4thay thế|
|6|Nối state machine đúng|Trace walk→turn→walk hai chiều; không nhảy/lặp pose, không flip ngay khi bắt đầu|
|7|Root/ground đúng|Canvas/anchor/darkbody root và tiếp đất có ghi tọa độ; không lấy bbox cánh/FX để căn thân|
|8|Hai endpoint hoạt động|Trace tới giới hạn trái/phải→turn đủticks→đi ngược; lệnh giữa turn không phá chuyển tiếp|
|9|Engine⇄localhost đồng bộ|./loop.sh test exit0,Godot/Rust/WASM,PNG/rect/tick/anchor/hash và HTTP đúng cùngrevision|
|10|Chất lượng thực và nghiệm thu|Phát tốc độ thật3nền,clip/ảnh lỗi lưu tọa độ/Atlas; Owner Human Test chốt đúngrevision|

Report từng hàng `pending/pass/fail`, đường dẫn bằng chứng, điểm đã có bằng chứng và tổng. Texture/timing exit0 không chứng nhận anatomy hoặc naturalness. Không tự đặt ngưỡng Sobel/độ giống ảnh để nhận turn đạt. Giữ `technical_checks` riêng với `motion_quality`.
