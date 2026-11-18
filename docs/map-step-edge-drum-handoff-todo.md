# TODO bàn giao: Mép bậc địa hình cho toàn bộ nhân vật & Camera đa thiết bị

**Trạng thái:** Đã sửa đồng bộ trong `ArenaSandbox.gd`, `DisplayPolicy.gd` và `tools/preview/index.html` (chờ Owner Human Test trên Godot Web `localhost:8080`; APK cần xuất ở máy có Android SDK `build-tools`).

## Đo đạc thực tế trên `combined.png` (`4800×1350`, gốc `(-240, -210)`)

- **Nguyên nhân treo ở mép bậc (toàn bộ nhân vật, không riêng Drum):**
  - `STEP_ONE_X = 2935` và `STEP_TWO_X = 3768` lệch `~75–85 px` về bên phải so với mép đá vẽ tại cao độ đi bộ (`2850` tại `y=840`, `3695` tại `y=890`), khiến mọi nhân vật đi qua mép vẽ đều đứng trên không trước khi đổi bục.
  - Cao độ đi bộ **bục số 2** (`930`) và **bục cuối** (`975`) nằm sát mép cỏ/đá trước vách (`925..955` và `965..995`) thay vì mặt đá đi được; đã hiệu chỉnh về **`890`** (`+50`) và **`945`** (`+105`) để giữ `~30–40 px` mặt đá trước chân ở cả 3 bục (giữ nguyên artwork `combined.png` ở bục cuối và chỗ nối map cũ).
  - Gộp thứ tự xử lý ngang → dọc và dùng chung `_resolve_terrain_horizontal_move` / `_move_node_horizontal` cho mọi nhân vật hiện tại & tương lai (đi/chạy, `turn`, teleport, độn thổ Chilopoda, AI, nhân vật bay, ngọc rơi, bóng tiếp xúc).
- **Tương thích toàn bộ hệ máy (kể cả iPad & màn cao/dài/to):**
  - Sửa `DisplayPolicy.gd` & `tools/preview/index.html` tính đúng `vis_h` khi bật Pixel Perfect trên màn cao (`2360×1640` iPad, `2560×1440` QHD).
  - `_update_follow_camera()` tính `cam_zoom = max(1.0, vis_w/map_w, vis_h/map_h)` đồng nhất (không méo hình) và lia/kẹp camera `(cam_x, cam_y)` bám nhân vật trong biên thế giới chung `[-240..4560, -210..1140]`, không còn dải hở đáy trên iPad hay khóa cứng cấu hình K70E.

## Tiến độ kiểm thử

- [x] Tái hiện và đo tọa độ pixel/world trên [`combined.png`](../review/rocky_plateau_extension/combined.png), [`ArenaSandbox.gd`](../scenes/ArenaSandbox.gd) và [`DisplayPolicy.gd`](../scenes/runtime/DisplayPolicy.gd).
- [x] Sửa `STEP_ONE_X = 2850`, `STEP_TWO_X = 3695`, cao độ sàn `(840, 890, 945)`, thứ tự physics ngang→dọc, bóng tiếp xúc theo biên bục, ngọc rơi/bay theo `_ground_y_at(x)` và xử lý AI/teleport/burrow cho toàn bộ nhân vật.
- [x] Sửa camera & layout đa thiết bị (`DisplayPolicy.gd`, `ArenaSandbox.gd`, `tools/preview/index.html`) tương thích cả 9 device profile (kể cả `ipad_10th` Fractional & Pixel Perfect) và màn lớn (`2732×2048`, `3840×2160`, `3440×1440`).
- [x] Bổ sung kiểm thử đa nhân vật & đa thiết bị trong [`test_arena_sandbox.gd`](../tests/test_arena_sandbox.gd) và [`test_frontend_wasm_e2e.mjs`](../tests/test_frontend_wasm_e2e.mjs).
- [x] Chạy `./loop.sh test` (exit 0) và `./loop.sh web-export` (exit 0).
- [ ] Xuất Android APK (môi trường hiện tại thiếu Android SDK `build-tools`) và Owner Human Test trực quan trên `localhost:8080` + thiết bị thực tế.
