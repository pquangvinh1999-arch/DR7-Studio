# Chilopoda — đồng bộ tạo hình theo power_up frame 1

Owner chọn frame1 của power_up atlas-v1 làm chuẩn mới cho tất cả hoạt ảnh. Chuẩn trước đó được giữ làm lịch sử; bản atlas-v1 bị Owner báo sai nhận diện ở power_up và đã được đánh dấu superseded/FAIL về nhận diện.

Mẫu mới giữ nguyên PNG tại [canonical/master.png](../../work/characters/chilopoda/identity-v2/canonical/master.png), SHA-256 `e0ac076682825160ee3723d363269b2d3ead0da463743af8ae3da184c82a04a3`. Canvas384×256, anchor[176,224], bbox[98,154,160,70], alpha thân100%, Sobel234.28 đo thực, không ép số. [Biên nhận lựa chọn mẫu](../../work/characters/chilopoda/identity-v2/canonical/approval.json) chỉ xác nhận mẫu Owner chọn, không xác nhận atlas mới đã nghiệm thu.

Dùng **built-in image_gen** sinh lại các pose TOÀN THÂN idle/walk/attack_light/hit/ko theo đúng mẫu này. [Prompt set](../../work/characters/chilopoda/identity-v2/prompts/) và [ảnh nguồn](../../work/characters/chilopoda/identity-v2/generated/) được lưu trong workspace. Turn lấy nguyên pose walk/attack của bản mới; không ghép chi hoặc cắt/vá đầu. Bộ đầu có đầu/giáp quá lớn và ảnh dive thiếu hàm đã loại, lưu riêng làm bằng chứng. [Registration](../../work/characters/chilopoda/identity-v2/registration.json) ghi từng nguồn, scale đồng đều theo action, ownership và bbox.

Các pose ready idle0, attack0/15, power0/10, hit0/5, ko0 bằng đúng pixel mẫu mới. Giữ nguyên10pose power trước đây ở chỉ số1..10 và toàn bộ18pha FX. Gộp hai hold ready đầu power thành8tick; release chuyển từ index4 sang3 nhưng vẫn tại tick16, tổng42tick; anchor/event được remap. [Bằng chứng pixel](../../work/characters/chilopoda/identity-v2/verification/identity-frame-proof.json) không được dùng làm phần trăm giống nhau của những pose đã đổi tư thế.

Hành vi giữ nguyên: attack ẩn đúng30tick/0,5s rồi trồi ở mục tiêu/cắn/ở lại; turn36tick ẩn16..21, đổi hướng16, trồi22, không dịch vị trí, tự bò ngược lại ở cả hai đầu; hai laser đỏ riêng từ râu, ẩn khi trúng. Walk12pha liên tục, không run. Atlas mới94refs/10clips/76cells, một trang3494×2342, Nearest60Hz. SHA-256 `6fae71276ce9e24eff3ae5d5bcd22b7d4573e5e3190730095c438bbe4d83d42d`.

[QA](chilopoda-identity-v2-qa.json): loop.sh test vòng1 exit0,50Python/E2E+8Godotbundles+5actiontests+2Rust; WASMrelease exit0. HTTP/ZIP213file khớp byte; Godot mở độc lập/import/bundle/actiontests đều exit0. Chromium phát30chuỗi/0pageerrors,27lượt pose ngắn chưa được RAF quan sát có ghi rõ; actual raster440tick kiểm riêng hidden interval, FX và hai hướng. FullFX thực[84,146,254,78] theo defaulttarget[304,224], không nhận đây là giới hạn cho mọi mục tiêu động. Các WARN clip tham chiếu Owner loại được giữ trong QA/log.

Đã mở xem7filmstrip thân và2composite turn trên sáng/tối/ô cờ. Đây là self-review để Owner xem bản sửa; final naturalness/identity acceptance vẫn **pending Owner Human Test**, không có score100% hay PIPE008. Hàng đợi turn Bat→T-rex→Pteranodon→Sarcosuchus chỉ mở sau khi Owner chốt Chilopoda.

Preview: http://localhost:8080/?character=chilopoda&clip=power_up&frame=0&paused=1

Owner yêu cầu chốt bản hiện tại lúc 2026-11-13T08:22:39.853349+00:00; PIPE-008/receipt `assets/chilopoda/owner_approval.json`. Các câu pending phía trên là lịch sử trước chốt; ảnh/thứ tự/tick/event giữ nguyên.
