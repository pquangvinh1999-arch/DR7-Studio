# Hồ Sơ Thiết Kế Nhân Vật & Hợp Đồng Atlas: `T-rex` (`t_rex`)

## 1. Nguồn Nhận Diện & Thông Số Đo Đạc Thực Tế

| Thuộc tính | Giá trị xác minh |
|---|---|
| Tên hiển thị (`display_name`) | `T-rex` |
| Mã kỹ thuật (`character_id` / `bundle_id`) | `t_rex` |
| Ảnh Master gốc đã duyệt | `work/trex_pixel_sample.png` (bản gốc từ `image-generator` / `host_image`) |
| SHA-256 (`trex_pixel_sample.png`) | `a2059008470a9c4e63f85b67963e72d2268021d7e1049da7e1632b7a73c09775` |
| SHA-256 (bản đính kèm xác nhận của Owner) | `86805f21563fa268a9bba021daefa535852606e33c496ae064f31dbc9cf4bf65` |
| Kích thước ảnh Master | `1024 × 1024 px` (`RGB`, nền hồng `#FF00FF`) |
| Lưới Pixel Art nội tại | `100 × 100` ô logic (`10.24 px / texel`), BBox thân trên lưới logic: `Rect(3, 18, 93, 66)` |
| Kích thước hiển thị Gameplay (`2× Nearest`) | Thân đứng `186 × 132 px` trên khung Canvas `384 × 256 px`, tâm chân `anchor_px = [176, 224]` |

---

## 2. Phân Tách Hồ Sơ Nhân Vật (Theo `create_atlas/SKILL.md` Mục 1)

- **Quan sát từ ảnh gốc**:
  - Loài khủng long bạo chúa (`Tyrannosaurus Rex` — `bipedal theropod`) đứng bằng 2 chân sau to khỏe có 3 móng vuốt mỗi bàn chân; 2 chi trước nhỏ có 2 ngón móng; đầu lớn với hàm răng nhọn sắc lộ rõ; đuôi dài vươn ngang phía sau làm đối trọng.
  - Bảng màu Pixel Art 16 màu: viền đen sắc nét (`#010215` / `#191c1f`), vảy lưng xanh rêu nhiều sắc độ (`#525730`, `#626639`, `#7f8148`, `#8c8d4f`, `#a5ae68`), vùng bụng/cổ/hàm dưới màu kem cát (`#a7a072`, `#ac977e`, `#d0caa1`).
- **Owner quy định & đã chốt**:
  - Di chuyển bằng **2 chân** (`walk`, `run`), **không có `jump`**, **không có `aura_loop`**, **không có `guard` và `win`**.
  - `attack_light`: Dùng **hàm cắn về phía trước có VFX** (gộp trực tiếp VFX nhát cắn vào frame thân).
  - `attack_heavy`: Dùng **đuôi tấn công bằng cách xoay người** (xoay thân quét đuôi mạnh về phía mục tiêu trước mặt rồi hồi thế).
  - `power_up`: **Phun 1 hạt lửa xoay nhiều frame về phía trước** (tách hạt lửa xoay làm clip FX độc lập `fireball_fx` điều khiển qua `render_contract.projectile`).
  - Các hoạt ảnh cơ bản còn lại giữ đầy đủ: `idle`, `walk`, `run`, `hit`, `ko`.
  - Mỗi hoạt ảnh phải được nối liền mạch nhiều frame tạo chuyển động xuyên suốt, không bị gấp khúc.
  - Không chỉnh sửa bất kỳ file skill nào của hệ thống.

---

## 3. Khóa Hướng Nhìn & Di Chuyển Trên Map 2D (`Movement / Facing Contract` — Điều 7.4 `AGENTS.md`)

- **Kiểu nhìn Map / Camera**: Nhìn ngang 2D (`Side-view Left/Right`).
- **Tập hướng vẽ trong Atlas**: Vẽ gốc 1 hướng nhìn sang **Phải (`+X`)**: đầu và mõm hướng sang phải (`+X`), đuôi ở tư thế nghỉ hướng sang trái (`-X`), hai bàn chân đặt trên đường mặt đất `y = 224` quanh tâm ngang `x = 176`.
- **Ánh xạ đổi hướng Trái / Phải**: Khi nhân vật quay sang **Trái (`-X`)**, lật ngang (`flip_h` / `scale.x = -1`) qua trục dọc `anchor_x = 176`.
- **Hướng di chuyển & hướng tác động vũ khí/cơ quan**:
  - `walk` / `run`: Hai chân sau bước luân phiên đẩy cơ thể theo hướng nhìn (`+X` hoặc `-X` khi lật).
  - `attack_light`: Cổ vươn tới, hàm trên và hàm dưới táp thẳng về phía trước mặt (`+X`) kèm VFX cung răng cắn xé.
  - `attack_heavy`: Cơ thể xoay quanh trục trọng tâm `anchor_x = 176`, đưa chiếc đuôi từ phía sau (`-X`) quét vòng cung qua phía trước mặt (`+X`) để đập trúng mục tiêu đối diện rồi xoay trả về tư thế nhìn sang phải (`+X`).
  - `power_up` + `fireball_fx`: Cổ gập nhẹ về trước, hàm mở rộng phun hạt lửa từ vị trí miệng `[264, 134]` bay thẳng về phía trước (`+X`) vừa bay vừa tự xoay tròn liên tục.

---

## 4. Bảng Chức Năng → Hành Vi Riêng & Trạng Thái Phạm Vi

| Chức năng | Clip ID | Hành vi áp dụng cho `T-rex` | Trạng thái |
|---|---|---|---|
| Đứng yên | `idle` | Đứng 2 chân thở nhịp nhàng, lồng ngực/hàm/đuôi dao động điều hòa nối vòng mượt | **Đã yêu cầu & chốt** |
| Đi bộ | `walk` | Bước đi 2 chân luân phiên 10 pha, đầu và đuôi nhịp đối trọng giữ thăng bằng | **Đã yêu cầu & chốt** |
| Chạy nhanh | `run` | Chạy nhanh 2 chân 8 pha, thân chúi thấp về trước, sải chân rộng | **Đã yêu cầu & chốt** |
| Rời mặt đất | `jump` | *Không áp dụng* (Khủng long đi mặt đất, Owner chỉ định không có `jump`) | **Loại bỏ theo Owner** |
| Phòng thủ | `guard` | *Không áp dụng* (Mặc định toàn dự án của Owner) | **Loại bỏ theo Owner** |
| Đòn nhẹ | `attack_light` | Lao cổ dùng hàm cắn mạnh về phía trước kèm VFX nhát cắn / hàm răng sắc (gộp 1 lớp) | **Đã yêu cầu & chốt** |
| Đòn mạnh | `attack_heavy` | Xoay người 360° quét đuôi mạnh về phía trước mặt kèm vệt lực quét rồi hồi thế | **Đã yêu cầu & chốt** |
| Kỹ năng / Phun lửa | `power_up` | Hít lửa trong họng rồi khạc hạt lửa về phía trước từ miệng (`release_frame = 2`) | **Đã yêu cầu & chốt** |
| Hạt lửa xoay (FX) | `fireball_fx` | Hạt lửa 8 pha xoay tròn liên tục và bay thẳng về phía trước (`render_contract.projectile`) | **Đã yêu cầu & chốt** |
| Duy trì hào quang | `aura_loop` | *Không áp dụng* (Owner chỉ định khủng long không có `aura_loop`) | **Loại bỏ theo Owner** |
| Trúng đòn | `hit` | Đầu và thân trên giật ngửa về sau theo lực đánh rồi gượng lại thăng bằng | **Đã yêu cầu & chốt** |
| Hạ gục | `ko` | Khuỵu hai chân, thân đổ sập dần xuống mặt đất, nảy nhẹ rồi nằm bất động | **Đã yêu cầu & chốt** |
| Thắng trận | `win` | *Không áp dụng* (Mặc định toàn dự án của Owner) | **Loại bỏ theo Owner** |

---

## 5. Bảng Timeline & Hợp Đồng Từng Clip (`60Hz` Ticks)

| Clip ID | Vai trò (`role`) | Số Frame | Ticks từng frame (`@60Hz`) | Tổng Ticks | Loop | Cơ quan / VFX & Sự kiện (`events`) |
|---|---|---|---|---|---|---|
| `idle` | `player` (body) | `8` | `[7, 7, 7, 7, 7, 7, 7, 7]` | `56` | `cycle` (`true`) | Thân/ngực thở, hàm & đuôi nhịp điều hòa nối vòng `#7 → #0` |
| `walk` | `player` (body) | `10` | `[6, 6, 6, 6, 6, 6, 6, 6, 6, 6]` | `60` | `cycle` (`true`) | Hai chân bước luân phiên (`step_r` tại `#2`, `step_l` tại `#7`) |
| `run` | `player` (body) | `8` | `[5, 5, 5, 5, 5, 5, 5, 5]` | `40` | `cycle` (`true`) | Chạy sải rộng thân chúi ngang (`step_r` tại `#1`, `step_l` tại `#5`) |
| `attack_light` | `player` (body) | `8` | `[5, 5, 4, 4, 4, 5, 5, 6]` | `38` | `oneshot` (`false`) | Hàm cắn + VFX cung răng gộp vào thân (`tell` `#1`, `hit` `#3`, `end` `#7`) |
| `attack_heavy` | `player` (body) | `10` | `[5, 5, 4, 4, 4, 4, 4, 5, 5, 6]` | `46` | `oneshot` (`false`) | Xoay người quét đuôi về trước (`tell` `#1`, `hit` `#4`, `end` `#9`) |
| `power_up` | `player` (body) | `9` | `[5, 5, 5, 4, 5, 5, 5, 5, 6]` | `45` | `oneshot` (`false`) | Nạp lửa họng `#0–#1`, phun hạt lửa tại miệng `#2` (`tell` `#1`, `hit` `#2`, `end` `#8`) |
| `hit` | `player` (body) | `6` | `[4, 4, 5, 5, 5, 5]` | `28` | `oneshot` (`false`) | Giật ngửa đầu/thân khi trúng đòn rồi hồi thế (`in` `#0`, `end` `#5`) |
| `ko` | `player` (body) | `8` | `[5, 5, 5, 5, 5, 6, 6, 15]` | `52` | `oneshot` (`false`) | Khuỵu chân đổ sập xuống đất nằm bất động (`in` `#0`, `impact` `#5`, `hold` `#7`) |
| `fireball_fx` | `fx` (projectile) | `8` | `[3, 3, 3, 3, 3, 3, 3, 3]` | `24` | `cycle` (`true`) | Hạt lửa 8 pha xoay tròn bay về phía trước từ miệng `[264, 134]` |
