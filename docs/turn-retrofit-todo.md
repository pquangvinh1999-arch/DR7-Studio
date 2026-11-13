# TODO turn cho nhân vật đã duyệt

Yêu cầu Owner2026-11-13. **Chưa bắt đầu: 0/4 hoàn tất.** Owner đã yêu cầu chốt Chilopoda identity-v2/v0.11.1; kiểm tra chốt cuối đã exit0, gate Chilopoda đã mở. Task hiện tại gồm chốt Chilopoda và trả lời mức khả thi quota; chưa chạy job turn mới. King Crab không cần turn; các nhân vật không nằm dưới đây giữ nguyên theo chỉ dẫn Owner.

Owner nêu Bat,T-rex,dực long,cá sấu cần bổ sung/sửa turn. File có tên `turn` không đủ chứng minh đã đáp ứng mục tiêu; riêng Sarcosuchus đã có clip/contract nhưng vẫn cần audit hành vi/nhận diện hai chiều theo phản hồi Owner, không tự kết luận nguyên nhân khi chưa có bằng chứng.

Tham chiếu: [contract và score100điểm](art-standards/turn-contract.md). Mọi hàng ban đầu `pending`, score **chưa chấm**, không tự nhận0%hay100%giống. Thực hiện tuần tự và hoàn tất sửa/test/HumanTest từng nhân vật trước khi chuyển hàng kế tiếp.

| Thứ tự | Nhân vật | Trạng thái | Gate mở đầu | Score |
|---|---|---|---|---|
|1|Bat - Chiroptera|Chưa bắt đầu; gate đã mở|Chilopoda Owner-approved|Chưa chấm/100|
|2|T-rex|Chưa bắt đầu|Bat turn hoàn tất và Owner-approved|Chưa chấm/100|
|3|Pteranodon / dực long|Chưa bắt đầu|T-rex turn hoàn tất và Owner-approved|Chưa chấm/100|
|4|Sarcosuchus / cá sấu|Chưa bắt đầu|Pteranodon turn hoàn tất và Owner-approved|Chưa chấm/100|

## Checklist thực hiện riêng cho từng nhân vật

- [ ]1.Bat:khóa revision/receipt/master và tất cả frame/tick cũ; xem Spino turn; audit camera/cánh/near-far. Sinh wholebody turn; reviewidentity từngpose. Test phải→trái/trái→phải và hai endpoint riêng, sửa qua loop.sh tối đa 5 vòng cho mỗi vấn đề, vòng 5 còn lỗi phải báo Owner, ghi đủ10gate, Owner HumanTest trước khi sangT-rex.
- [ ]2.T-rex:khóa revision/receipt/master và frame/tick cũ; audit đầu/hàm/đuôi, không sửa heavy đã duyệt. Wholebody turn có trọng lượng,không rigidturntable. Kiểm hai chiều/hai endpoint/clipseams; sửa/test/score và Ownerchốt trướcPteranodon.
- [ ]3.Pteranodon:khóa revision/receipt/master và frame/tick cũ; audit wingbeat/hoverphase/near-farwing và anchor bay. Wholebody aerial turn thật với phối cảnh/che khuất, không xoay/flipcard. Kiểm hai chiều/hai endpoint và nối bay; sửa/test/score và Ownerchốt trướcSarcosuchus.
- [ ]4.Sarcosuchus:khóa revision/receipt/master và frame/tick cũ; reproduce turnhiện tại/endpoint theo Owner, lưu log/frame/tọa độ lỗi. Audit bốnchân/thânthấp/hàm/đuôi; sửa artwork hoặc runtime đúng nguyênnhân. Kiểm hai chiều/hai endpoint/clipseams; sửa/test/score và Ownerchốt.

Mỗi nhân vật lưu một report10gate, nguồn pose/identitySHA, frozen-before, kết quả từng lần loop.sh, browser/Godottrace, ảnh/clip3nền, lỗi và số đo cụ thể. Các thay đổi nhận diện/timing mới cần biên nhận revision mới; không dùng biên nhận atlas cũ để nhận bản mới đã được duyệt.

Đối soát sau chốt Chilopoda: vẫn **0/4 turn retrofit hoàn tất**, ba nhân vật đầu chưa có turn; Sarcosuchus có4frame nhưng chưa audit/sửa. [Ước lượng với7%quota Owner báo](turn-quota-assessment.json): tối thiểu3clipmới+1audit/sửa và16ca hướng/runtime; không có telemetry để quy đổi quota, không cam kết đủ cả4. Ưu tiên trọn Bat rồi đánh giá lại; không tự tính phần trăm nhận diện.

Hướng dẫn bàn giao cho agent khác: [AGY-TURN-HANDOFF.md](AGY-TURN-HANDOFF.md), gồm hiến pháp, nguồn mẫu, migration receipt/test, QA hai chiều và giới hạn5vòng.
