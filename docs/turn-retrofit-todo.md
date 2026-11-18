# TODO turn cho nhân vật đã duyệt

Yêu cầu Owner2026-11-13 (đã cập nhật 2026-11-14). **Owner chốt hủy TODO tạo `turn` cho `#3 Pteranodon` (`TURN-003`)**: không cần chờ reset quota để sinh thêm `turn` cho Pteranodon hay các nhân vật tương lai; xoay ngang tức thì (`instant_flip`, +20% phản hồi cho Pteranodon, +30% cho King Crab) đã đạt yêu cầu, kết hợp tăng tốc clip `turn` sẵn có (`Bat +40%`, `Spino +25%`, `Sarco +25%`, `Dilo +43%`) và tối ưu cảm giác chuyển tiếp `walk ⇄ turn` mượt mà.

Owner nêu Bat,T-rex,dực long,cá sấu cần bổ sung/sửa turn. File có tên `turn` không đủ chứng minh đã đáp ứng mục tiêu; riêng Sarcosuchus đã có clip/contract nhưng vẫn cần audit hành vi/nhận diện hai chiều theo phản hồi Owner, không tự kết luận nguyên nhân khi chưa có bằng chứng.

Tham chiếu: [contract và score100điểm](art-standards/turn-contract.md). Mọi hàng ban đầu `pending`, score **chưa chấm**, không tự nhận0%hay100%giống. Thực hiện tuần tự và hoàn tất sửa/test/HumanTest từng nhân vật trước khi chuyển hàng kế tiếp.

| Thứ tự | Nhân vật | Trạng thái | Gate mở đầu | Score |
|---|---|---|---|---|
|1|Bat - Chiroptera|`pending_reapproval` (`calibration-v1` — tăng tốc clip `turn` +40%: `[2,3,4,3,3]`, 15 ticks / 250ms từ `PIPE-009` `21 ticks` + fix khựng `walk ⇄ turn`)|Chilopoda Owner-approved|Chờ Human Test (tốc độ + calibration)|
|2|T-rex|`owner_approved` (`PIPE-010` / `turn-v1` / `v0.11.2` — 5 pose turn phối cảnh `turn_00..04` (`ticks [6,3,3,3,6]`) + `TRexFighter2D.gd` 2 chiều/2 endpoint (`walk` & `run`); `73/73` frame gốc bảo toàn; `--godot-fps auto` fix `ISS-TREX-TICK-LEGACY` theo chốt Owner)|Bat turn hoàn tất và Owner-approved (`v0.11.2`)|100/100 (`owner_approved: true`, `docs/characters/t-rex-turn-v1-qa.json`)|
|3|Pteranodon / dực long|`canceled_by_owner` (`TURN-003` — Owner chốt `2026-11-14` **không cần tạo `turn`**; giữ `61` frame gốc, mở phản hồi xoay ngang +20%, `default_scale = 1.5`, `screen_speed = 140 px/s`, `fly_default_y = 250`)|T-rex turn hoàn tất|N/A (Miễn `turn` theo chốt Owner)|
|4|Sarcosuchus / cá sấu|`pending_reapproval` (`calibration-v1` — tăng tốc clip `turn` +25%: `[2,5,6,3]`, 16 ticks / 267ms từ `PIPE-005` `20 ticks`, `default_scale = 2.0`, `screen_speed = 135 px/s`)|Owner chốt trực tiếp `2026-11-14`|Chờ Human Test (tốc độ + calibration)|

## Checklist thực hiện riêng cho từng nhân vật

- [x]1.Bat: hoàn tất `PIPE-009` (`2026-11-13`) và tăng tốc `turn` +40% (`[2,3,4,3,3]`, `250ms`) theo calibration `2026-11-14`.
- [x]2.T-rex: hoàn tất `PIPE-010` (`2026-11-14`) và tối ưu chuyển tiếp `walk ⇄ turn` mượt tại runtime.
- [x]3.Pteranodon: **Hủy tạo `turn` (`canceled_by_owner`)** theo chỉ dẫn Owner `2026-11-14` (không chờ reset quota, nhân vật tương lai không bắt buộc thêm `turn`); chỉ tối ưu tốc độ phản hồi xoay ngang +20% và calibration bay/tốc độ.
- [x]4.Sarcosuchus: giữ 4 pose `turn` gốc `PIPE-005` và tăng tốc `turn` +25% (`[2,5,6,3]`, `267ms`) theo calibration `2026-11-14`.

Mỗi nhân vật lưu một report10gate, nguồn pose/identitySHA, frozen-before, kết quả từng lần loop.sh, browser/Godottrace, ảnh/clip3nền, lỗi và số đo cụ thể. Các thay đổi nhận diện/timing mới cần biên nhận revision mới; không dùng biên nhận atlas cũ để nhận bản mới đã được duyệt.

Cập nhật trạng thái hàng đợi (`2026-11-14T13:44Z`): **Đã chốt 3/4 (`Bat` `PIPE-009`, `T-rex` `PIPE-010`, `Sarcosuchus` `TURN-004 / PIPE-005` giữ nguyên hiện trạng); chỉ còn duy nhất `#3 Pteranodon` (`TURN-003`) đang chờ quota `gemini-3.1-flash-image` reset sau `2026-11-14T18:36:31Z`** để sinh nốt 2 pose `3/4` trung gian `±35°` từ `turn_anchor_ref_3pose.png` (hoặc nguồn API key / sheet ngoài nếu Owner cung cấp sớm hơn).

Hướng dẫn bàn giao cho agent khác: [AGY-TURN-HANDOFF.md](AGY-TURN-HANDOFF.md), gồm hiến pháp, nguồn mẫu, migration receipt/test, QA hai chiều và giới hạn5vòng.
