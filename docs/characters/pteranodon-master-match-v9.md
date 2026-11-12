# Pteranodon — tạo hình theo Image1, giữ bộ chuyển động cũ

> **Chốt v0.6.0**: Owner đã nghiệm thu cả 3 nhân vật. Receipt hiện hành ở `assets/` và `docs/releases/v0.6.0-owner-approval.json`. Các ghi chú pending/baseline bên dưới là lịch sử trước nghiệm thu; ảnh nháp đã dọn theo `docs/releases/v0.6.0-png-cleanup.json`. Nguồn cuối, runtime và filmstrip được giữ; không chạy lại script lịch sử cần baseline đã xóa.

Owner 2026-11-12 yêu cầu đổi toàn bộ tạo hình Pteranodon theo `work/characters/pteranodon/master-review/test_scaled_canvas.png`, không sửa hoạt ảnh. Phạm vi task này là7clip thân đang có; không thêm động tác hoặc tái thiết kế nhịp cánh/chiêu.

## Mẫu và bản lưu

- Mẫu PNG384×256, bbox `Rect(60,45,220,150)`,alpha thân100%,12908pixel visible,8543RGB,Sobel151.428 đo bằng `tools/art/measure_pixel_sharpness.py`.
- SHA256 mẫu: `7c9d71fe2033b0be2644bb8df1bb8d3cd5e5d38a7a0a71e3b7833c84a0e9e702`. Bản sao bất biến: `work/characters/pteranodon/master-match-v9/reference.png`.
- Tạo hình: da than chì/nâu sẫm, màng trong cánh đỏ đô, mặt trên cánh xám tối, đầu/mào dài và hàm răng kim, mắt hổ phách, đường gân da và ngón cánh tinh hơn bản2× cũ. Không áp bảng màu/độ bóng T-rex vào Pteranodon.
- Bản đã duyệt v8, kể cả receipt và atlas SHA `1dfc61d34a41a02cfcc7a048c5310618950d71972953904cad19cf241d1d041a`, lưu nguyên tại `work/characters/pteranodon/master-match-v9/baseline`. `state.json` trỏ PIPE002 vào bản lưu để không dùng receipt cũ tự duyệt hình mới. Không sửa `skills.md`.

## Cách làm và phần giữ nguyên

Built-in imagegen chỉnh tạo hình nguyên pose của từng action, dùng Image1 làm identity/style duy nhất, sheet cũ làm mẫu vị trí/pha.54pose thân mới,7PNG `sonic_screech_fx` giữ nguyên SHA. Không dùng các part/mask của pipeline rig cũ, không cắt/xoay/warp đầu hoặc cánh để tạo motion mới.

Sau sinh ảnh chỉ lấy nguyên ô384×256 theo layout cố định4cột, strideY320, inset32; alpha128→binary. Không scale, không đổi vị trí theo bbox từng frame, không căn lại cánh/chân. Giữ canvas384×256,anchor[176,200],camera/hướng phải và contract độc lập sóng âm.

| Clip | Frame | Tick giữ nguyên |
|---|---:|---|
| idle | 8 | 7,7,7,7,7,7,7,7 |
| walk | 8 | 6,6,6,6,6,6,6,6 |
| run | 8 | 4,4,4,4,4,4,4,4 |
| attack_light | 8 | 5,5,4,4,4,5,5,6 |
| power_up | 8 | 5,5,5,5,4,5,5,6 |
| hit | 6 | 4,4,5,5,5,5 |
| ko | 8 | 5,5,5,5,5,6,6,15 |
| sonic_screech_fx | 7 | 2,2,2,2,2,2,2 |

Tổng61refs/8clip. So sánh máy xác nhận mọi `frames/ticks/duration_ms/events_ms/keys/loop/loop_policy/hitstop_ticks` bằng baseline, `states/anchor/shadow` cũng bằng. Sonic releaseframe2,origin[278,128],lifetime14ticks không đổi; composite review lấy FX theo tổng tick thực của thân, không theo số thứ tự frame thân.

Giữ các pha cánh lên/ngang/xuống, lunge mỏ, đổi pitch khi hit/KO theo frame gốc. Cẳng tay/gốc khuỷu/ngón là màu da; đỏ đô chỉ màng trong, mặt trên cánh gần ở pha xuống vẫn tối. Mẫu mới có contour/răng/ngón chi tiết hơn, vì vậy **không nhận silhouette pixel-identical hoặc pose hình học100% bất biến** chỉ từ metadata. `pose-preservation.json` ghi bbox delta và IoU từng frame để truy vết; chúng không tự chứng minh motion đạt. Biến thiên mép bbox body lớn nhất25px và IoU body0.625–0.871 phản ánh hình tái tạo cần đối chiếu trực quan, không được che bằng technicalPASS. FX giữ IoU1.0.

## Kiểm chứng

- Builder exit0,warnings0; exporter exit0,một atlas3106×2082,Nearest60Hz,không thêm trang. Atlas SHA `8789d914abf677ac043ac16f6cf8713c0f2a28bb8f7acb223e874b9aa39cb005`.
- Godot import exit0; `./loop.sh test` exit0:26Python/E2E,3bundle Godot,2Rust; WASM release build exit0.
- HTTPatlas/WASM/HTML khớpbytefile đĩa vàparitytrue.540file T-rex/Spinosaurus giữ nguyên SHA.
- Mở đủ8filmstrip trên sáng/tối/ô cờ và power_up-composite. Có dải cũ/mới cùng frame index để đối chiếu, playbackWebP giữ đúng timing. Chưa có Owner nghiệm thu hình mới; không tuyên bố độ tự nhiên/nhận diện PASS từ unit test.
- WARN thiếu clip Owner đã loại và hai revision T-rex/Pteranodon pendingOwner giữ nguyên trong `verification/tests.log` và QA JSON.

Nguồn/prompt/baseline/stage/filmstrip/playback/số đo: `work/characters/pteranodon/master-match-v9/`. QA máy đọc: `docs/characters/pteranodon-master-match-v9-qa.json`.

Mở xem: `http://localhost:8080/?character=pteranodon&clip=idle&frame=0&paused=1`; chọn các clip còn lại trong cùng inspector. Bản mới là `reviewed_pending_owner`, giữ riêng lịch sử v8 đã duyệt.
