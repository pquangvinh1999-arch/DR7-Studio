# Dilophosaurus motion revision v0.9.1

Giữ nguyên turn để đổi hướng; không có clip thân stun. Quy trình choáng: giữ pose hit và chạy VFX đầu độc lập. Chưa triển khai gameplay/VFX choáng trong bản này.

Chỉ sửa idle và power_up. Idle12pose×10tick, chu kỳ120tick; idle0 giữ nguyên canonical. Power_up:8wholepose mang uốn nhẹ lặp trong60tickactive, đầu không phồng/xẹp lớn; vẫn còn dao động outline khoảng1px. Toàn clip88tick;3nét chém độc lập tại12/31/50tick, chung mục tiêu và giữ nguyên PNG/timing. Walk, cắn, hit, ko, turn vàFX giữ hash/tick/event;909file của5nhân vật khác không đổi.

Kỹ thuật:40Python/E2E,6Godotbundle,3customticktests,2Rust exit0; WASMbuild0; gói tải xuống import/testGodot độc lập0; HTTPPNG/TRES/metadata/WASM khớp byte. Atlas1page3494×2342,76cell,80PNG,102cliprefs,10clips. Canvas384×256,anchor[176,224],Nearest60Hz.

Kiểm trực quan filmstrip trên3nền và lưu playback/ảnh runtime. Chromiumheadless phát21chuỗi, đi đúng cuối/vòng nhưng bỏ hiển thị một số pose33ms của power; trace88tick đủ38indexthân và18tickFX. Không nhận đây là chứng nhận60FPS hoặc motionOwnerapproved. Xem JSON liên quan để có warnings nguyên văn và skipped indices. Bản sửa chờ OwnerHumanTest, không PIPE006.

Preview: http://localhost:8080/?character=dilophosaurus&clip=power_up&frame=0&paused=1

Owner đã nghiệm thu toàn bộ nhân vật lúc 2026-11-13T04:57:15.924909+00:00; chốt PIPE-006, receipt assets/dilophosaurus/owner_approval.json. Ghi chú chờ Human Test phía trên là lịch sử trước nghiệm thu. Giữ nguyên toàn bộ ảnh/timing.
