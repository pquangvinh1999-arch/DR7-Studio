# T-rex: phục hồi hình ảnh, giữ bộ chuyển động cũ

Owner xác nhận: “Đúng, phục hồi từng pose cũ; giữ nguyên nhịp chuyển động”. Bản sửa hiện là demo chờ Human Test; PIPE-001 chỉ nghiệm thu bản atlas cũ, không tự động nghiệm thu hình ảnh mới.

## Mật độ pixel đo từ ảnh gameplay

Cùng canvas 384×256, anchor [176,224]. Đo trực tiếp idle frame0, không lấy thông số khai báo làm kết quả đo.

| Đại lượng | Spinosaurus đã chốt | T-rex trước sửa | T-rex demo sửa |
|---|---:|---:|---:|
| Bbox thân (px) | 157×74 | 186×134 | 186×134 |
| Bước chi tiết nhỏ nhất | 1 px | 2 px | 1 px |
| Envelope lấy mẫu tương ứng | 157×74 | 93×67 | 186×134 |
| Texel/m tại 64 PPU | 64 | 32 | 64 |
| Sobel biên trong | 271.574 | 182.074 | 245.516 |
| Alpha cứng | 100% | 100% | 100% |

T-rex cũ có 100% khối RGBA 2×2 hữu hình đồng nhất; Spinosaurus không có khối đồng nhất trong phép đo này. Để đạt cùng bước lấy mẫu trên kích thước T-rex hiện tại cần gấp 2 mật độ tuyến tính, tức gấp 4 số vị trí lấy mẫu trên diện tích. Không tăng kích thước nhân vật hoặc canvas. Nearest phóng ảnh cũ không tạo chi tiết mới.

Sobel dùng BT.709, `scipy.ndimage.sobel` chưa chuẩn hóa, trung bình trên pixel alpha hữu hình sát biên ngoài. Con số T-rex khai báo cũ 201.3 không trùng phép đo hiện tại 182.074; không ép kết quả mới bằng một scalar. Mật độ pixel tương đương không có nghĩa độ tương phản biên và artwork giống hệt; Sobel T-rex demo vẫn thấp hơn Spinosaurus khoảng 9.6%.

RGB hữu hình idle0: Spinosaurus 2677 màu, T-rex cũ12, T-rex mới5795. Không lượng tử hóa cưỡng bức16 màu vì Owner yêu cầu đồng bộ theo Spinosaurus đã duyệt. Những con số này không phải số texel và không chứng minh tính liền mạch giải phẫu.

## Lỗi liên kết và phương pháp phục hồi

Ảnh Owner `image copy 3.png` khớp nhất với idle7: phóng2×, offset ảnh[-117,-92], 95.77% RGB khớp trên31857 mẫu ngoài overlay. Vùng Owner khoanh Canvas Rect(214,123,49,22) là cổ/hàm. Ảnh đối chiếu: `work/characters/t_rex/sharpness-repair/review/owner-throat-roi-comparison.png`.

Mã nguồn cũ `build_t_rex_pipeline.py` dựng các mảnh rig bằng warp và neck capsule trước khi phóng2×. Không chạy lại phương pháp đó. Bản sửa dùng imagegen phục hồi67 pose toàn thân dựa trên đúng các ảnh cũ; chỉ cắt nguyên ô hoàn chỉnh, chuẩn hóa alpha ngưỡng128 và đăng ký nguyên pose bằng Nearest vào envelope cũ. Không cắt/warp/vá chi hoặc ghép đầu/cổ. Thay đổi đường nét nhỏ giữa các pose vẫn cần Owner đánh giá.

67 frame thân/8 clip +4 frame lửa độc lập =71 frame/9 clip. So sánh dữ liệu cũ/mới giữ nguyên `frames`, `ticks`, `duration_ms`, `loop`, `loop_policy`, `events_ms` cho mọi clip. Không thiết kế lại walk/run/attack hoặc tốc độ xoay người. Bốn PNG `fireball_fx` khớp SHA bản cũ.

## Power up

Frame0/1 dùng lõi lửa tròn cam–vàng nằm trong miệng thay khối vuông. Phục hồi cổ/hàm ở mọi pose. Nguồn cũ còn vẽ trực tiếp bốn frame lửa vào thân ở pha2..5 tại x[266,278,292,306],y106, trong khi contract lại vẽ cùng FX độc lập tại origin[304,138], pivot[176,128].

Ảnh thân mới không chứa lửa bay ở2..5; giữ nguyên4 ảnh FX, vị trí, release_frame2 và lifetime20tick, vẽ đúng một lần. Vùng FX cũ chỉ dùng làm ownership mask khi đo bbox tham chiếu, không dùng để chắp vá cơ thể mới. Filmstrip `power_up-composite` thể hiện đúng tổ hợp Engine/localhost.

## Bằng chứng và trạng thái

- Phân tích ban đầu: `work/characters/t_rex/sharpness-repair/analysis.json`.
- Nguồn imagegen, prompt và đăng ký pose: `generated/`, `references/`, `registration.json` trong cùng thư mục.
- Đã mở9 filmstrip và tổ hợp power_up trên nền sáng/tối/ô cờ; playback WebP giữ timing cũ.
- Atlas một trang3494×2082, SHA `616ad71fb609acb7238a5e3bf502ec6a97f2575326234b1e91ac81d610c2d9c7`.
- `./loop.sh test`:25 tests Python/E2E, Godot3 bundle, Rust2 tests; lần sau import exit0. Lần đầu Godot thiếu import texture, log lỗi được giữ lại; đã import và sửa installer giữ sidecar.
- WASM release build exit0; HTTP PNG/WASM SHA khớp file thực; API parity=true, T-rex `release_approved=false`.
- 500 file Spinosaurus/Pteranodon giữ nguyên hash. Không cập nhật `skills.md` hoặc tự chốt revision.

Báo cáo máy đọc: `docs/characters/t-rex-visual-repair-qa.json`. Log và đối soát byte: `work/characters/t_rex/sharpness-repair/verification/`. WARN thiếu clip đã Owner loại và WARN chờ Human Test vẫn được giữ.
