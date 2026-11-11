# SỔ TAY QUY TRÌNH DỰNG HOẠT ẢNH TỪ ATLAS CỦA OWNER (`skills.md`)

> **PHÂN BIỆT BẮT BUỘC (Theo Điều 6 — `AGENTS.md`)**:
> - **File `skills.md` này KHÔNG PHẢI là bộ skill công cụ asset sprite (`.agents/skills/generate2dsprite`...)**.
> - `.agents/skills/*` là **thư viện công cụ kỹ thuật cấp thấp** (cắt ảnh, tách nền `forge_matte`, đóng gói `export_engine.py`).
> - Còn `skills.md` là **Quy trình Nghiệp vụ End-to-End của riêng dự án DR7-Studio**: từ lúc nhận một file Atlas / Ảnh gốc từ Owner → phân tích thông số → bóc tách bảo toàn chi tiết theo combined_1layer (Ki/aura độc lập theo mặc định Owner; FX khác theo contract từng nhân vật) → chạy vòng lặp kiểm thử trên Engine → xuất đồng bộ 1:1 ra `localhost:8080` cho tới khi đạt yêu cầu của Owner.
>
> **QUY TẮC ĐỌC / GHI**:
> 1. File này **khởi tạo ở trạng thái TRỐNG (`0` quy trình)**.
> 2. **Khi nào ĐỌC**: Đọc ngay khi Owner gửi một mẫu Atlas nhân vật/hiệu ứng mới để biết quy trình chuẩn đã từng được Owner duyệt (dùng ngay mà không cần hỏi lại những bước đã thống nhất).
> 3. **Khi nào GHI**: Chỉ sau khi hoàn tất chỉnh sửa một task cùng Owner và **được Owner xác nhận nghiệm thu Human Test thành công**, Agent mới ghi đúc kết quy trình đó vào giữa hai thẻ bên dưới.

> **Chỉ dẫn Owner hiện hành**: nhân vật/FX dùng pixel art đồng bộ, không nâng HD; Ki/aura độc lập cho nhân vật có Ki; không guard/win cho bất kỳ nhân vật nào và không hỏi lại. Giữ các chỉ dẫn chung này sau khi dọn toàn bộ nhân vật. Không ghi workflow chưa được Owner nghiệm thu.

<!-- SKILLS_ENTRIES_START -->
### [PIPE-001] Quy Trình Dựng Atlas & Godot 4 Bundle Từ Master Pixel Art + Sheet FX Của Owner (`T-rex` / `t_rex`)
- **Trạng thái nghiệm thu**: `owner_approved` (`2026-11-10T08:03:00Z` — Owner chốt đạt chuẩn toàn bộ bundle sau khi tinh chỉnh nét vòm đùi) — Biên nhận: `assets/t_rex/owner_approval.json` (`atlas_sha256: 90bb74abb48009fcb0ef624874e12fdefb0942b3ffacae7804bec09856f3236f`).
- **Thông số gốc & Khung chuẩn**:
  - Master tĩnh đã duyệt: `work/characters/t_rex/approved-master/approved-original.png` (`1024×1024`, lưới pixel logic gốc `100×100` texel, phóng `2:1 Nearest` lên khung gameplay `384 × 256 px`, tâm chân `foot_anchor_px = [176, 224]`).
  - Sheet FX lửa của Owner: `work/characters/t_rex/approved-master/fire_fx_source.png` (`400×250`, nền `RGB(14, 14, 14)`, gồm 4 cụm lửa đọc theo thứ tự từ phải sang trái `Cụm 4 -> Cụm 3 -> Cụm 2 -> Cụm 1` và lật ngang sang phải `+X`).
- **Quy tắc nghiệp vụ đã được Owner nghiệm thu**:
  1. **Khóa danh sách clip theo giải phẫu & đặc tả riêng nhân vật**:
     - Gồm 8 clip thân (`idle`, `walk`, `run`, `attack_light`, `attack_heavy`, `power_up`, `hit`, `ko`) + 1 clip FX độc lập (`fireball_fx`) = 9 clip / 71 frame trên 1 trang PNG Atlas duy nhất (`3494 × 2082 px <= 4096 × 4096`).
     - Không tạo và không setup các clip bị loại: `jump`, `aura_loop` (loại riêng cho `T-rex`), `guard`, `win` (loại toàn dự án).
  2. **Kiến trúc bộ phận giải phẫu liên thông & Đường viền hợp nhất (`Combined 1-Layer`)**:
     - Mỗi bộ phận giải phẫu tách từ master bắt buộc lọc giữ duy nhất thành phần liên thông chính (`components == 1`) để triệt tiêu hạt nhiễu rìa.
     - Hợp nhất `[đuôi + thân + cầu nối cổ + đầu trên]` vào một buffer chung trước khi viền `1px` (`OUTLINE_RGBA`) để không hở cổ khi vươn cắn/khạc lửa và không hở gốc đuôi khi xoay người quất đuôi `360°` ở `attack_heavy`.
     - Kẹp mặt đất (`clamp_ground_ko`) cho các frame ngã gục của `ko` để thân khủng long nằm đúng trên đường mặt đất `y = 224`.
  3. **Đồng bộ 1:1 giữa thân nhân vật và Sheet FX đính kèm ở `power_up`**:
     - Frame `0–1` (`p0..p1`): `T-rex` ngửa cổ lấy đà, mở hàm nén luồng khói nâu-vàng và lõi lửa sáng ngay trong vòm họng.
     - Frame `2–5` (`p2..p5`): `T-rex` lao đầu về trước và khạc 4 cụm lửa từ mẫu của Owner (đọc từ phải sang trái `Cụm 4 -> Cụm 3 -> Cụm 2 -> Cụm 1`, tách nền `diff > 32` + khử lem biên + lật ngang `+X`) tiến dần từ `x = 266` tới `x = 382` trên trục miệng `y = 138`, đồng thời xuất `fireball_fx` (`4 frame`, `[5, 5, 5, 5]` ticks) đồng bộ toạ độ qua `render_contract.projectile`.
     - Frame `6–8` (`p6..p8`): Khói tàn ở chóp mũi và khép hàm hồi về `idle`.
  4. **Khối đùi hòa nhập tự nhiên theo Master Pixel Art (`Seamless Natural Master`)**:
     - Triệt tiêu hoàn toàn vạch đen nhân tạo cắt ngang ở đỉnh đùi `y = 77` (`y = 154..155` gameplay); giữ nguyên 100% màu sắc và mảng sáng khối cơ đùi từ master kết hợp viền đen 2 mép trước/sau để khối đùi nổi rõ trên thân tự nhiên mà không bị thô cứng.
### [PIPE-002] Bộ hoạt ảnh dực long bay, 2 mặt cánh và sóng âm độc lập (`Pteranodon` / `pteranodon`)
- **Nghiệm thu**: Owner chốt bản v8 ngày `2026-11-11T08:33:19.680871+00:00`; receipt `assets/pteranodon/owner_approval.json`, atlas SHA-256 `1dfc61d34a41a02cfcc7a048c5310618950d71972953904cad19cf241d1d041a`.
- **Nguồn tái dựng**: `work/characters/pteranodon/approved-master/approved-original.png` (1024², SHA-256 `267c73d7ae35f9498d347cf96e78fe104202fbfdca469050c702b0ab03078353`), sheet Owner `sonic_fx_source.png` (308×89, SHA-256 `f9950880f4a6f06cb1dd012d76787be4a0346e45603d8089dae772fdebc38e03`), script `work/characters/pteranodon/build_pteranodon_pipeline.py`. Các pose mới do pipeline biến dạng từ master, không nhận là frame sẵn có trong sheet.
- **Contract đã duyệt**: nhìn ngang trái/phải, atlas gốc nhìn phải +X; canvas384×256, anchor[176,200], nearest2× từ lưới logic100². Thân combined_1layer; 7clip thân `idle/walk/run/attack_light/power_up/hit/ko` (54frame) và `sonic_screech_fx` (7frame), tổng61frame trên1page3106×2082. Không jump/guard/win/attack_heavy/aura_loop theo Owner; giữ WARN tham chiếu.
- **Giải phẫu và màu**: phân bộ phận liên thông nội bộ để dựng, xuất thân hợp nhất; không đắp khối cầu phồng vai/cổ. Da than chì cho cẳng tay/gốc khuỷu/móng, đỏ đô chỉ ở màng cánh; mặt nạ bảo vệ cả thân cẳng tay và gốc vai. Với cánh xa pha xuống, xoay nguyên cánh về+X và dùng elevation dương để cẳng tay dẫn phía trên về mỏ, màng theo phía dưới; không lậtY toàn cánh làm đảo giải phẫu. Giữ đối chiếu KO đã duyệt khi sửa cánh bay. Các thông số mask/pivot riêng Pteranodon không áp cứng sang sinh vật mới.
- **Sóng âm**: tách7cụm nguồn, khử nềnRGB(32,32,32), đổi đỏđô và hướng+X. Thân `power_up` 8frame40ticks; FX7frame14ticks tại60Hz, phát ởframe2 từ miệng[278,128], đồng hồ riêng vàprefab `scenes/PteranodonSonicWaveFX.tscn`; cùngatlas khi bậtFX thêmquad. Không tăng tốc thân để tăng tốcFX.
- **Vòng sửa**: Owner gửi `[DR7-EDIT-SPEC]` với clip/step/Canvas/Atlas; đo pixel thực rồi sửa mask/biến dạng tại nguồn. UI hỗ trợ Rect vàLasso đồng thời; Lasso xuấtPolygon+PixelRuns[y,x,length], chỉ đo/sửa mask, không coi bbox là toàn vùng chọn. Pause trước chọn, kiểmtra tọađộ quaCSSscale, vùnglõm,copy/pin vàhủy thao tác.
- **Đóng gói và nghiệm thu**: xem từngfilmstrip3nền; chạyGodot/Rust/WASM và `./loop.sh test`, kiểmtraHTTPatlasSHA/rect/tick/anchor khớpengine; đợiHumanTest trước ghiworkflow/receipt. QA bảnchốt tại `docs/characters/pteranodon-v8-qa.json`. Nghiệm thu này dành cho bộhoạtảnh, không chứng minh hiệu năng hay bảnbuild mobile.

<!-- SKILLS_ENTRIES_END -->
