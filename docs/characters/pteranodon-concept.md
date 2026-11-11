# Hồ Sơ Thiết Kế Nhân Vật & Hợp Đồng Atlas: `Pteranodon` (`pteranodon`)

## 1. Nguồn Nhận Diện & Thông Số Đo Đạc Thực Tế

| Thuộc tính | Giá trị xác minh |
|---|---|
| Tên hiển thị (`display_name`) | `Pteranodon` |
| Mã kỹ thuật (`character_id` / `bundle_id`) | `pteranodon` |
| Master tĩnh đã duyệt | `work/characters/pteranodon/approved-master/approved-original.png` |
| SHA-256 Master | `267c73d7ae35f9498d347cf96e78fe104202fbfdca469050c702b0ab03078353` |
| Sheet FX Sóng Âm của Owner | `work/characters/pteranodon/approved-master/sonic_fx_source.png` (`308 × 89 px`, nền `RGB(32, 32, 32)`, 7 cụm sóng âm `Cụm 1 -> Cụm 7`) |
| SHA-256 Sheet FX Sóng Âm | `f9950880f4a6f06cb1dd012d76787be4a0346e45603d8089dae772fdebc38e03` |
| Art Source / Route | `host_image` |
| Kích thước ảnh Master | `1024 × 1024 px` (nền Magenta `#FF00FF`) |
| Lưới Pixel Art nội tại | `100 × 100` ô logic texel, phóng `2:1 Nearest` lên khung gameplay `384 × 256 px` |
| Điểm neo trọng tâm | `foot_anchor_px = [176, 200]` (tâm bay lượn trên không) |

---

## 2. Đặc Tả Cơ Chế & Quyết Định Nghiệp Vụ Của Owner

- **Bản sắc nhận diện (Mẫu 2 — Dực Long Ác Ma)**:
  - Mỏ khoằm há rộng để lộ hai hàng răng cưa tam giác sắc nhọn cực kỳ hung tợn.
  - Ánh mắt vàng rực sắt máu, mào gai nhọn lởm chởm kéo dài về sau sọ.
  - Đôi cánh da dơi hai mặt theo chuẩn sinh học giống loài:
    - **Mặt trên cánh (`Dorsal Surface`)**: Cùng màu da than chì (`CHARCOAL_*`) với cơ thể dực long ở cả hai cánh (`near_wing` và `far_wing`). Khi đập cánh xuống (`flap_elev < 0`), phần mặt trên của cánh gần gập xuống hướng ra ngoài hoàn toàn mang màu da than chì đồng nhất với thân.
    - **Mặt trong / Mặt dưới cánh (`Ventral Membrane`)**: Màng cánh màu đỏ đô chiến trận (`WING_RED_*`) ở mặt dưới của cả cánh gần lẫn cánh đối diện (`far_wing`), tách biệt sắc nét với phần xương cẳng tay, bắp tay và 4 móng vuốt màu da than chì / đá xám (`0 px` lem màu đỏ lên cánh tay).
  - Cơ bắp thân, cánh tay, cổ và hàm dưới màu than chì / nâu máu gân guốc liền mạch (`dual neck & throat capsules` chống hở khấc cổ dưới hàm khi lao nhanh ở `run`).
- **Cơ học đập cánh bay (`Biomechanical 2D Wingbeat`)**:
  - Toàn bộ hoạt ảnh bay (`idle`, `walk`, `run`, `hit`) thực hiện **chu kỳ đập cánh toàn biên độ dọc** qua trục ngang cơ thể:
    1. **Đỉnh nâng cánh (`High Upstroke V`)**: Hai cánh giương cao hình chữ V trên lưng (`flap_elev = +1.04 .. +1.10`), thân hơi hạ thấp lấy đà.
    2. **Quét ngang uốn vòm (`Horizontal Forward Camber Sweep`)**: Cánh quét nhanh qua mặt phẳng ngang thân, đầu mút cánh uốn cong theo sức cản không khí (`camber_px`).
    3. **Đáy đập cánh lực đẩy (`Deep Power Downstroke Below Belly`)**: Toàn bộ sải cánh đỏ và 4 móng vuốt đập sâu xuống **bên dưới ngực và bụng** (`flap_elev = -0.98 .. -1.10`, kết hợp `shear_x_by_y` bảo toàn 100% bề rộng màng cánh), tạo lực nâng đẩy thân vọt lên cao (`body_dy = -4.0 .. -4.8` logic).
    4. **Thu khớp cánh hồi thế (`Folded Upstroke Recovery`)**: Cổ tay dẫn hướng nâng lên, màng cánh khép nhẹ giảm cản gió trước khi mở rộng về đỉnh nâng cánh.
- **Phương thức tấn công**:
  - `attack_light`: **Dùng mỏ tấn công thẳng về phía trước (`Forward Beak Strike`)** — thu cổ lấy đà, giương cánh rồi đập cánh đẩy thân lao vọt về trước (`+X`), vươn cổ liền mạch (`draw_neck_capsule` không hở cổ) đâm mỏ răng cưa khép chặt kèm VFX mũi thương mỏ phá gió.
  - **Không có `attack_heavy`** (Owner chốt bỏ đòn tấn công nặng riêng cho nhân vật `Pteranodon`).
  - `power_up` + `sonic_screech_fx` (**Supers Sóng Âm Tách Riêng Asset & Tốc Độ Độc Lập**):
    - `power_up` (`8` frame thân `#0–#7`, `ticks = [5, 5, 5, 5, 4, 5, 5, 6]`, tổng `40` ticks / `667ms`): **Chỉ chứa thuần thân dực long (`100% Body-Only`, không gắn cứng sóng âm vào frame thân)** ở tốc độ cơ thể chuẩn (`5` ticks/frame). Ngửa cổ lấy hơi (`#0–#1`), lao đầu há rộng mỏ phát sóng âm (`#2–#4`, trong `14` ticks từ tick `10` tới tick `24`), rồi khép mỏ nâng cánh hồi thế (`#5–#7`).
    - `sonic_screech_fx` (`7` frame FX độc lập `#0–#6`, `ticks = [2, 2, 2, 2, 2, 2, 2]`, tổng `14` ticks / `233ms`, kèm prefab độc lập `res://scenes/PteranodonSonicWaveFX.tscn` và node `ProjectileFX` trong `res://scenes/Pteranodon.tscn`): Tách riêng hoàn toàn thành 1 asset độc lập để tự điều chỉnh tốc độ bay siêu thanh (`2` ticks/frame = `33ms`, nhanh gấp `2.5×` tốc độ thân dực long) mà không làm tăng tốc độ toàn bộ cơ thể dực long.
- **Phạm vi clip loại trừ**:
  - Không có `guard` và `win` (mặc định toàn dự án theo Owner).
  - Không có `attack_heavy` (loại riêng cho `Pteranodon` theo yêu cầu Owner).
  - Không có `aura_loop` (loại riêng cho sinh vật tự nhiên).
  - Không có `jump` (loại riêng cho nhân vật bay trên không).

---

## 3. Khóa Hướng Nhìn Trên Map 2D (`Movement / Facing Contract` — Điều 7.4 `AGENTS.md`)

- **Kiểu nhìn Map / Camera**: Nhìn ngang 2D (`Side-view Left/Right`).
- **Tập hướng vẽ trong Atlas**: Vẽ gốc nhìn sang **Phải (`+X`)**: đầu và mỏ hướng sang phải (`+X`), đuôi và chân sau ở phía sau (`-X`), trọng tâm bay lượn tại `anchor_px = [176, 200]`.
- **Ánh xạ đổi hướng Trái / Phải**: Lật ngang (`flip_h` / `scale.x = -1`) qua trục dọc `anchor_x = 176` khi quay sang **Trái (`-X`)**.
- **Hướng di chuyển & tác động**:
  - `walk` / `run`: Đập cánh bay tiến và lao nhanh theo hướng nhìn (`+X`).
  - `attack_light`: Đâm và táp mỏ răng cưa thẳng tới mục tiêu phía trước (`+X`).
  - `power_up` + `sonic_screech_fx`: Sóng âm 7 pha tỏa từ mỏ (`[278, 128]`) lan truyền thẳng về phía trước (`+X`, `X = 278..360`).

---

## 4. Bảng Timeline & Hợp Đồng Từng Clip (`60Hz` Ticks)

| Clip ID | Vai trò (`role`) | Số Frame | Ticks từng frame (`@60Hz`) | Tổng Ticks | Loop | Cơ quan / VFX & Sự kiện (`events`) |
|---|---|---|---|---|---|---|
| `idle` | `player` (body) | `8` | `[7, 7, 7, 7, 7, 7, 7, 7]` | `56` | `cycle` (`true`) | Đập cánh toàn biên độ giữ thăng bằng trên không, nối vòng mượt `#7 → #0` |
| `walk` | `player` (body) | `8` | `[6, 6, 6, 6, 6, 6, 6, 6]` | `48` | `cycle` (`true`) | Chu kỳ đập cánh bay tiến mạnh mẽ (`step_r` `#3`, `step_l` `#7`) |
| `run` | `player` (body) | `8` | `[4, 4, 4, 4, 4, 4, 4, 4]` | `32` | `cycle` (`true`) | Đập cánh tốc độ cao lao vọt rẽ gió (`step_r` `#3`, `step_l` `#7`) |
| `attack_light` | `player` (body) | `8` | `[5, 5, 4, 4, 4, 5, 5, 6]` | `38` | `oneshot` (`false`) | Lao mỏ răng cưa đâm/táp mạnh về trước + VFX mũi thương mỏ (`tell` `#1`, `hit` `#3`, `end` `#7`) |
| `power_up` | `player` (body) | `8` | `[5, 5, 5, 5, 4, 5, 5, 6]` | `40` | `oneshot` (`false`) | Thân dực long độc lập tốc độ chuẩn: lấy hơi `#0–#1`, gào phát sóng âm `#2–#4`, hồi thế `#5–#7` (`tell` `#1`, `hit` `#2`, `end` `#7`) |
| `hit` | `player` (body) | `6` | `[4, 4, 5, 5, 5, 5]` | `28` | `oneshot` (`false`) | Giật ngửa thân trên không, cánh chao đảo rồi vỗ cánh hồi thế (`in` `#0`, `end` `#5`) |
| `ko` | `player` (body) | `8` | `[5, 5, 5, 5, 5, 6, 6, 15]` | `52` | `oneshot` (`false`) | Thu cánh rơi xuống mặt đất, nằm bất động (`in` `#0`, `impact` `#3`, `hold` `#7`) |
| `sonic_screech_fx` | `fx` (projectile) | `7` | `[2, 2, 2, 2, 2, 2, 2]` | `14` | `oneshot` (`false`) | Asset sóng âm đỏ đô 7 pha độc lập tốc độ cao (`2 ticks/frame = 33ms`) lan truyền về phía trước (`+X`) |


## 5. Nghiệm thu cuối — v8

Owner đã chốt Pteranodon ngày 2026-11-11T08:33:19.680871+00:00. Biên nhận: `assets/pteranodon/owner_approval.json`; atlas SHA-256 `1dfc61d34a41a02cfcc7a048c5310618950d71972953904cad19cf241d1d041a`. Xem `skills.md` PIPE-002 cho quy trình đã nghiệm thu và `pteranodon-v8-qa.json` cho số đo bản chốt. Cánh xa pha xuống dùng elevation dương và xoay về +X để giữ cẳng tay ở trên hướng mỏ; mô tả elevation âm trong bảng pha cũ là tham số pose, không phải phép lậtY cánh xa hiện tại.
