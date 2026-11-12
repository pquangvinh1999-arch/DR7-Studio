# T-rex attack_heavy — xoay quật đuôi có phối cảnh

Owner báo đòn cũ trông như ảnh bị lật và yêu cầu tham khảo Spinosaurus. Chỉ `attack_heavy` được dựng lại; toàn bộ T-rex vẫn là demo chờ Human Test.

Dải cũ nhảy từ nhìn ngang phải ở frame1 sang nhìn ngang trái ở frame2. Bản mới có12 pose toàn thân:0 chuẩn bị,1 cuộn đuôi lấy đà,2/3 xoay chéo về camera,4 chính diện,5 quật đuôi sang phải màn hình,6 xoay chéo lưng,7 nhìn lưng,8 chéo lưng sang phải,9 giảm tốc,10/11 hồi thế. Các góc trong prompt/frame-evidence là mục tiêu thiết kế, không phải số đo góc suy ra chính xác từ ảnh.

Spinosaurus được dùng để tham khảo nhịp, phối cảnh và che khuất. T-rex giữ đầu rộng, tay nhỏ, thân/đuôi xanh ôliu và bụng kem; không lấy pixel/chi/buồm Spinosaurus để ghép. Imagegen tái tạo từng pose nguyên cơ thể. Đầu–cổ–vai–hông–chân–đuôi được xem lại trên nền sáng/tối/ô cờ.

12 pose được tạo ở kích thước gameplay, cắt nguyên ô384×320, chuẩn hóa alpha128, dịch nguyên frame để giữ trục hôngCanvas x176 và mặt đất y225 như pose heavy cũ. Không scale riêng tư thế chính diện/lưng thành chiều rộng của nhìn ngang; bản cuối không resize ảnh pose. Không flip/xoay quad/warp chi để tạo góc quay.

Timing60Hz: `[5,4,2,1,1,1,1,2,3,4,5,6]` =35tick≈583ms, thay46tick trước. Đây là duration clip, chưa cộng hitstop6tick được giữ nguyên. Hit tại frame5/tick13; active_end frame7/tick15; end frame11/tick29. Có vệt cam–vàng nhỏ ở đầu đuôi tại frame5, tan ở6, hết ở7. Không thay damage/hitbox hoặc timing các clip khác.

61PNG ngoài heavy giữ đúng SHA và cùng thứ tự pose/ticks/duration/loop/events theo từng clip. Tổng73frame/9clip,1atlas3494×2342,canvas384×256,anchor[176,224],Nearest. Atlas SHA `7cdc28601c3f8ac7867409d4bd6c036e78c5091ffd3d45751a7db1f12798d7e7`.

Mẫu nét chung Owner chọn được lưu độc lập ở [chuẩn độ nét](../art-standards/character-pixel-sharpness.md), ảnh idle0 giữ nguyên SHA. Sobel mẫu245.516; heavy0 mới236.143,alpha thân100%,chi tiết1px. Bản thử viền dày bị loại vì đổi cảm giác hình ảnh; không ép Sobel bằng sharpen/LUT. Ảnh chuẩn không có nghĩa đã duyệt hoạt ảnh mới.

Kiểm chứng: clip builder/exporter exit0,warnings0; Godot import exit0; `./loop.sh test` exit0(25Python/E2E,3bundle Godot,2Rust); WASMreleasebuild exit0. HTTP PNG/WASM SHA khớp, parity=true;500file Spinosaurus/Pteranodon không đổi. Lượt check đầu bị chặn vì AGENTS.md24791byte vượt24k; đã rút gọn phần quy chuẩn còn23834byte, giữ chi tiết trong contract tham chiếu, rồi test lại đạt. WARN clip Owner đã loại và chờ Human Test vẫn giữ.

Nguồn, prompt, lựa chọn ảnh và bằng chứng từng frame: `work/characters/t_rex/heavy-spin-v2/`. Review gồm filmstrip3nền, playback WebP đúng timing và dải35tick `review/timeline-60hz.png`. Báo cáo máy đọc: `docs/characters/t-rex-heavy-spin-v2-qa.json`; log/hash HTTP tại `verification/` trong thư mục nguồn. Chưa ghi workflow mới vào `skills.md` hoặc thay biên nhận Owner cũ.
