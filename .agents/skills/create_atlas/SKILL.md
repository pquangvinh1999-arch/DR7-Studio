---
name: create-atlas
description: Thiết kế bộ hoạt ảnh và atlas nhân vật 2D từ ảnh tĩnh theo giải phẫu, cách di chuyển, phương thức tấn công và yêu cầu Owner. Ưu tiên khi Owner yêu cầu tạo atlas đồng bộ concept; cũng hỗ trợ phân tích/bóc tách sheet có sẵn theo nhánh bảo toàn nguồn. Không áp bộ chiêu Vegeta cho nhân vật khác.
---

# Create Atlas — từ bản sắc nhân vật đến bộ hoạt ảnh

## Mục tiêu và ranh giới

Học **các chức năng cần có của một bộ atlas dùng trong game**, rồi thiết kế cách thể hiện phù hợp từng nhân vật. Sheet Vegeta SSJB là ví dụ về độ bao phủ chức năng và nhiều pha chuyển động; tư thế võ thuật, ki, supers, ultimates, biến hình và màu FX trong sheet gắn với Vegeta, không phải khuôn bắt buộc cho nhân vật khác.

Đọc `AGENTS.md`, `state.json`, `skills.md`, `lerning.md`; chạy `./loop.sh status` đầu phiên. Chỉ dẫn Owner hiện hành ưu tiên ghi chép cũ. Không thay đổi quyết định engine trong task atlas. Đây là skill thiết kế/điều phối atlas, không phải `skills.md` gốc dành riêng cho quy trình đã nghiệm thu Human Test.

- **Ảnh tĩnh → thiết kế atlas:** phân tích nhân vật, lập bộ hành động, pha chuyển động và tiêu chí đồng bộ. Khi Owner yêu cầu tạo, dùng công cụ sinh ảnh/chuyển động phù hợp để thực hiện bản thiết kế.
- **Sheet có sẵn → phân tích/bóc tách:** bảo toàn pixel nguồn; đọc [source-sheet-extraction.md](references/source-sheet-extraction.md). Zero AI Redraw áp dụng nhánh này. Việc tạo chuyển động mới từ ảnh tĩnh phải được phân biệt rõ với bóc tách nguồn, không nhận đó là frame vốn có trong ảnh.
- Yêu cầu “học/review/sửa skill” chỉ cho phép cập nhật tài liệu. Không tự sinh ảnh, xử lý asset, export hoặc thêm roster.

Giữ `create_atlas` làm điểm vào ưu tiên khi Owner yêu cầu xây dựng bộ atlas theo concept. `generate2dsprite` và `video2dsprite` là công cụ thực hiện phía sau; không chuyển giao việc quyết định bộ động tác cho một preset tạo asset chung.

## Mặc định dự án do Owner chốt

- **Mốc nét chung mới (Owner 2026-11-12)**: trước khi sinh nhân vật/pose mới, mở [ảnh T-rex chuẩn](../../../docs/art-standards/t-rex-sharpness-reference.png) và đọc [thông số chuẩn](../../../docs/art-standards/character-pixel-sharpness.json). Dùng chi tiết1px gameplay/Nearest, alpha thân100%, Sobel mẫu245.516 đo theo `tools/art/measure_pixel_sharpness.py`; đối chiếu trực quan ở1× và phóng nguyên lần. Không ép100texel/2×/16màu/201.3 cũ, không gán scalar hoặc tự đặt dung sai. Giữ kích thước/giải phẫu riêng từng nhân vật; độ nét đạt không thay thế motion QA. Mốc này chỉ chốt nét, không chốt hoạt ảnh T-rex đang demo.
- **Khóa phương pháp chuyển động mới theo Owner (2026-11-12)**: master tĩnh phải sinh nhiều pose **toàn thân** liên tục; cấm cắt các mảnh chi/thân/đầu rồi warp/xoay/ghép/vá để giả chuyển động. Cắt nguyên frame hoàn chỉnh để đóng atlas vẫn hợp lệ; nhánh sheet có sẵn vẫn bảo toàn nguồn. Quy trình PIPE-001/002 cũ là lịch sử đã nghiệm thu, không phải giấy phép áp bộ mask/rig đó sang nhân vật mới.
- **Nhánh imagegen do Owner chọn rõ**: dùng master đã duyệt làm identity reference cho mọi action; tái tạo toàn bộ nhân vật ở từng keyframe với pha tuyệt đối, không nối chỉnh sửa chắp vá từ frame trước. Có thể trình bày các keyframe toàn thân trong sheet review của **một action** để kiểm tra liên tục; chỉ slice nguyên ô frame, không slice chi để dựng pose. Giữ góc camera, thiết kế, tỷ lệ, hướng và baseline nhất quán. Không gọi đó là video-generated. Video2dsprite vẫn là nhánh image-to-video khi có route, nhưng không được lấy `no-route` làm lý do quay lại cắt ghép cơ thể. Thiếu công cụ sinh pose hợp lệ thì lưu job/prompt, báo thiếu và để gate pending/FAIL.
- **Khóa một nhận diện cho mọi clip**: lưu master chuẩn riêng nhân vật và SHA; ảnh action bị Owner báo sai chỉ là motion guide, không làm identity reference. So trực tiếp đầu/hàm/cổ/thân/chi/palette và cách tô ở cùng cỡ gameplay với master, đặc biệt lúc vào/ra clip. Chuyển động đúng và Sobel gần nhau không chứng minh cùng nhân vật. Lệch mẫu = `checks.character_identity=false`, chặn bàn giao dù technical exit0; chỉ đổi gate sau khi xem lại ảnh sửa. Có thể dùng nguyên pose master hoàn chỉnh ở pha ready, không ghép chi/đầu để giả pose.
- **Motion QA là gate độc lập**: technical exit0 không đủ. Xé hình/hở khớp/lộ mảng vá/mất kết nối cơ quan/đảo giải phẫu/ảnh lật thay xoay = FAIL. Review từng frame và chuỗi ở tốc độ thực trên3nền, kể cả nối vòng/đổi hướng; lưu bằng chứng clip/index/Canvas/Atlas. Không tự ghi PASS từ số connected-components: các cơ quan có thể chạm trong ảnh2D nhưng vẫn sai cấu trúc/che khuất. Owner đã báo lỗi thì giữ FAIL tới khi bản sửa được kiểm tra lại.

- **Pixel art** cho hệ thống nhân vật/FX: giữ độ thô của pixel, silhouette, bảng màu và mật độ chi tiết đồng bộ với ảnh nguồn và các nhân vật đã duyệt. Không tự nâng thành HD, thêm vân cơ/ánh sáng/viền siêu mịn hoặc làm nét quá mức. Đánh giá ở kích thước gameplay và phóng nguyên lần bằng nearest; không coi ảnh nhiều pixel hơn là chất lượng phù hợp hơn. Master mới đổi góc nhìn/thiết kế cần review trước chuỗi hoạt ảnh.
- **Ki/aura độc lập**: với nhân vật có Ki, xuất thân và loop Ki/aura thành sprite/clip độc lập mặc định; bật/tắt và chạy cùng idle, di chuyển, tấn công mà không thay animation thân. Không yêu cầu Owner nhắc lại mỗi nhân vật. Thân nguyên vẹn một lớp; không tách chi/cánh theo chiều sâu. Ghi điểm neo, thứ tự vẽ, đồng hồ riêng và contract dùng chung Godot/localhost; giữ cùng trang atlas khi phù hợp. Có thêm quad khi bật FX, không nhận cả tổ hợp một draw call. Sheet gốc đã gộp không tách được thì báo giới hạn trước phần phụ thuộc, không AI vẽ lại để nhận là bảo toàn nguồn.
- **Không guard/win cho mọi nhân vật**: Owner đã loại hai chức năng này khỏi phạm vi chung; không hỏi lại hoặc tạo chúng để vượt kiểm thử. Giữ WARN của bộ tham chiếu nếu checker vẫn nhắc, ghi lý do loại theo Owner. Intro/ultimate và các kỹ năng khác vẫn theo từng nhân vật; không suy từ việc có/không ở một mẫu.
- Ki dạng sheet phải review nối vòng cuối→đầu; có thể sinh thêm frame nối khi Owner cho phép, ghi rõ frame mới so với frame nguồn. Không chỉ đảo thứ tự hai hình rồi nhận đã chứng minh loop mượt.

## 1. Lập hồ sơ nhân vật trước khi chọn động tác

Mở file ảnh thật, ghi nguồn, kích thước và SHA-256 khi xử lý asset. Tách rõ: **quan sát từ ảnh**, **Owner quy định**, **đề xuất thiết kế**, **cần xác nhận**. Ảnh tĩnh không chứng minh được dáng đi, khả năng bay, biến hình hoặc kỹ năng.

Hồ sơ cần làm rõ:

- Loại cơ thể: người, động vật, sinh vật tưởng tượng, máy móc; số chi và vai trò của chi. Không ép mọi sinh vật vào khung người.
- Cách di chuyển: hai/bốn chân, bò, trườn, bay, bơi; trọng tâm, vùng tiếp đất, đuôi/cánh và cách giữ thăng bằng.
- Phương tiện tấn công: tay/chân, hàm/răng, móng, sừng, đuôi, vũ khí, cơ quan phun lửa hoặc năng lượng theo yêu cầu. Ghi điểm phát và hướng tác động.
- Bản sắc phải giữ: silhouette, tỷ lệ, mặt, màu, trang phục, trang bị, chi tiết bất đối xứng, phong cách nét và góc nhìn.
- Phạm vi game: hành động Owner yêu cầu, hướng nhìn, kích thước hiển thị, timing và ràng buộc xuất cần cho bước thực hiện.

Nếu thiếu quyết định ảnh hưởng đến thiết kế, hỏi Owner bằng các lựa chọn và ưu/nhược điểm trước phần phụ thuộc. Không tự cấp thêm năng lực vì ảnh trông “mạnh”. Không hỏi lại thông tin Owner đã nói rõ.

## 2. Chuyển chức năng thành hành vi riêng của nhân vật

Dùng bảng dưới để rà độ bao phủ, không dùng như danh sách chiêu bắt buộc. Các ID ở cột giữa là bộ tham chiếu hiện tại của dự án; đây không phải schema mới cho exporter.

| Chức năng | Clip tham chiếu | Quy tắc thích nghi |
|---|---|---|
| Sẵn sàng/đứng yên | `idle` | Thở, giữ thăng bằng, chuyển trọng lượng theo cơ thể |
| Di chuyển | `walk`, `run` | Chu kỳ tiếp đất đúng số chân; xử lý đuôi, cánh, vũ khí |
| Rời mặt đất | `jump` | Chuẩn bị, bật, trên không, đáp; không mặc định bay |
| Phòng thủ | `guard` | Không tạo trong DR7 theo chỉ dẫn chung của Owner |
| Đòn gần cơ bản/mạnh | `attack_light`, `attack_heavy` | Cắn, húc, cào, đấm hay vung vũ khí theo phương tiện đã chốt |
| Chuẩn bị sức mạnh/duy trì FX | `power_up`, `aura_loop` | Chỉ thiết kế khi concept có cơ chế tương ứng; không ép sinh vật phải có aura |
| Phản ứng và thất bại | `hit`, `ko` | Hướng lực, mất thăng bằng, ngã và trạng thái kết thúc hợp giải phẫu |
| Biểu cảm thắng | `win` | Không tạo trong DR7 theo chỉ dẫn chung của Owner |
| Đòn xa/kỹ năng đặc trưng | ID riêng được chốt | Phun lửa, ném, bắn… đúng cơ quan/vũ khí, không mặc định ki blast |
| Chiêu mạnh/chiêu cuối | ID riêng được chốt | Chỉ thêm khi Owner yêu cầu; không sao beam, tên chiêu hoặc biến hình Vegeta |
| Vào trận/biến đổi/hồi phục | Theo phạm vi | Tách intro, transform, get-up nếu cần; không suy từ nhãn sheet |

Mỗi chức năng phải có trạng thái: **đã yêu cầu**, **đề xuất chờ chốt**, **không áp dụng có lý do**, hoặc **còn thiếu**. Không xóa âm thầm mục kiểm tra. Nếu dự án đang kiểm tra cứng ID clip chưa phù hợp concept, báo rõ chênh lệch và WARN; không tạo clip giả/alias rỗng để qua gate, không tự sửa checker.

Đọc [hồ sơ Vegeta](references/vegeta-ssjb-analysis.md) chỉ khi cần bằng chứng nguồn hoặc đối chiếu độ bao phủ. Các nhãn `KI/SUPERS/ULTIMATES` là nhóm trình bày của ví dụ, không phải năng lực phổ quát hay số clip cố định.

## 3. Thiết kế timeline và hợp đồng từng clip

Trước khi tạo chuyển động, lập bảng: `clip ID | chức năng | cơ quan/vũ khí | pha | loop/oneshot | hướng | điểm neo/điểm phát | FX | sự kiện | trạng thái xác nhận`.

- Đòn đánh cần đọc được chuẩn bị → tác động/phát chiêu → hồi thế. Không chỉ tạo các tư thế đẹp rời nhau. Đòn mạnh phải phân biệt bằng lực, biên độ, nhịp hoặc hồi thế theo thiết kế đã chốt.
- Di chuyển cần chu kỳ tiếp đất và chuyển trọng lượng; phân biệt chuyển động tại chỗ với dịch chuyển trong game. Đuôi/cánh chuyển động theo cơ thể, không làm chân trượt.
- Đòn xa cần cơ quan phát đúng vị trí xuyên suốt pha chuẩn bị/phóng/duy trì/kết thúc. Đầu lửa phải đi từ miệng với nhân vật phun lửa, không mọc từ tay theo mẫu Vegeta.
- Ghi thời lượng dưới dạng tick 60Hz khi xuất; 60Hz không có nghĩa 60 pose mới/giây hoặc mỗi pose chỉ giữ 1 tick. Số frame/timing là thiết kế cần kiểm chứng, không suy ra từ một ảnh tĩnh.
- Loop phải nối đầu/cuối hợp lý; oneshot phải có điểm kết thúc và chuyển về trạng thái phù hợp. Tách FX minh họa khỏi dữ liệu hitbox/gameplay; không lấy bbox ngọn lửa làm hitbox mặc định.
- Xoay/quật đuôi/đổi hướng: lập các keypose theo trục xoay, phối cảnh và thứ tự che khuất, có chuẩn bị, tăng tốc, tác động nhanh và hồi thế. Không dùng flip_h, rotate_quad, scale_x/warp một master để giả spin. Đổi hướng di chuyển cũng cần chuyển đầu/ngực/hông/điểm tỳ liên tục, không lật cả tấm ảnh ngay lập tức. Tick không chia đều máy móc; review tốc độ thật và silhouette trước khi chốt. Tăng tốc hành động không chữa được xé hình; cả anatomy và timing đều phải đạt.
- Chọn canvas từ envelope cả thân và FX, giữ tỷ lệ nhân vật nhất quán giữa clip; không thu nhỏ thân ở chiêu lớn để vừa ô. Không sao số frame, canvas, anchor hay bố cục hàng của sheet tham chiếu.

## 4. Ví dụ kiểm tra khả năng khái quát

**Owner yêu cầu: khủng long đi bằng hai chân, tấn công bằng hàm và phun lửa.**

- Đã chốt: di chuyển hai chân; đòn cắn xuất phát từ hàm; lửa phát từ miệng. Giữ hình dáng và chi tiết nhận diện của ảnh.
- Lập ứng viên idle giữ thăng bằng, walk/run luân phiên hai chân, cắn với cổ/hàm và thân phối hợp, phun lửa với hướng đầu ổn định, phản ứng trúng đòn/ngã phù hợp thân và đuôi. Đây là thiết kế đề xuất, không phải chuyển động quan sát được trong ảnh.
- Chưa tự chốt: cắn mạnh khác cắn thường ra sao, có jump hay không (guard/win đã loại theo mặc định dự án), lửa ngắn/dài/duy trì, có chiêu cuối hay không. Hỏi phần thiếu trước khi sinh clip tương ứng; không tự gán quật đuôi, bay hoặc biến hình.
- Không lấy tư thế đấm, tay bắn ki, aura xanh, tên chiêu Saiyan hoặc hai beam cuối Vegeta làm mặc định.

Áp cùng cách suy luận cho kiếm sĩ (điểm tác động ở vũ khí), thú bốn chân (chu kỳ bốn chân), sinh vật không chân (đường tiếp đất riêng). Không biến ví dụ khủng long thành preset bắt buộc thứ hai.

## 5. Thực hiện và kiểm chứng khi Owner yêu cầu tạo atlas

1. Chốt hồ sơ và bảng clip đủ rõ cho phần được tạo. Dùng ảnh Owner làm nguồn nhận diện; nếu cần master mới, duyệt một master theo hướng dẫn công cụ, không thay nhân vật bằng mẫu chung.
2. Đọc [generate2dsprite](../generate2dsprite/SKILL.md) khi sinh master/đóng gói; đọc [video2dsprite](../video2dsprite/SKILL.md) khi tạo chuyển động từ master. Xác minh API/CLI thực có trước khi gọi. Skill này quyết định yêu cầu; tooling thực hiện và QA, không tự mở rộng bộ chiêu.
3. Rà nhận diện trên mọi frame: số chi, tỷ lệ, mặt, palette, trang bị; kiểm tra tiếp đất, hướng lực, điểm phát FX, nối loop, pha hồi thế. Đo và ghi bằng chứng khi báo lỗi, không nhận chất lượng đã đạt chỉ từ prompt.
4. Xuất thân `combined_1layer` nguyên vẹn; Ki/aura là clip/sprite độc lập theo mặc định Owner, các FX khác theo contract nhân vật. Một trang atlas mỗi nhân vật, tối đa 4096²; canvas bội 16, anchor ổn định, nearest, timeline 60Hz, `.gdignore` ở `source/` và `clips/`. Nếu bộ clip vượt giới hạn, đưa ra lựa chọn cho Owner; không âm thầm giảm nét/cắt FX.
5. Công bố body/full-FX bbox, canvas, anchor, quy đổi PPU và số liệu sharpness theo AGENTS.md. Khi key nền: pocket-first rồi edge unmixing, `opaque_key_px=0`, `enclosed_key_pockets=0`, spill ≤0.005, alpha hardness ≥95% cho pixel art.
6. Mở xem từng filmstrip trên nền sáng/tối/ô cờ **và phát chuỗi ở tốc độ thật**, kiểm tra liên kết cơ thể, xoay/đổi hướng, nối vòng và nhịp lực. Bất kỳ xé hình/lật ảnh giả xoay nào là motion_quality FAIL; ảnh Owner báo lỗi phải vào hồ sơ. Sau motion review, chạy Godot headless, Rust cargo test và WASM; `./loop.sh check`, `./loop.sh test`. Chỉ báo technical_checks exit0 theo log; không đổi motion FAIL thành PASS vì technical exit0. Đồng bộ atlas/rect/timing/anchor/hash với localhost:8080 cho Human Test và hiển thị đúng trạng thái chưa nghiệm thu. Không dùng pass roster rỗng chứng minh bộ nhân vật hoàn thiện hoặc cam kết60FPS mobile.
7. Chỉ đưa bộ hoàn thiện vào roster. Cập nhật `state.json` sau task; chỉ ghi `skills.md` gốc khi Owner nghiệm thu Human Test thành công.

## Đường dẫn và khả năng dùng chung

Bản chuẩn là `.agents/skills/create_atlas/SKILL.md`; `.agent` là symlink tới `.agents`, không tạo bản độc lập hoặc đổi tên thư mục Owner chọn. `SKILL.md` là entrypoint của skill, khác `skills.md` gốc. Nội dung dùng được cho Codex/Antigravity; dùng khả năng xem ảnh thật của host, không nhận đã kiểm tra trực quan nếu chưa mở ảnh. Không tự sửa hooks/cài plugin hoặc nhận đã discovery trên cả hai CLI khi chưa kiểm chứng.

### Chu kỳ walk/run theo Owner (2026-11-12)
- Thiết kế một vòng tiến pha đầy đủ 0..N−1 rồi về0; không ping-pong hay đảo7..1 để vá loop. Không trùng pose đầu/cuối; lấy mẫu pha trong [0,360°). Review cả cuối→đầu, hai chân đổi vai trò trụ/vung, không chỉ xem pixel/hash khác nhau. Gần trùng pose hoặc lò cò = motion FAIL, phải sửa nguyên pose nguồn.
- Run: walk chỉ làm tham khảo concept/giải phẫu, không copy frame và tăng playback để làmrun. Theo Owner làm rõ2026-11-12, sinh pose chạy toàn thân riêng (sải/chúi thân/đẩy chân/thu chân/tiếp đất), kiểm vòng0..N−1→0 riêng. Quy định dùng chung frame/duration0.5 trước đây bị thay thế; không dùng làm mặc định nữa.
- Turn chỉ có khi thực sự nối đổi hướng trong runtime; nêu nơi dùng và timing, không sửa đòn xoay đã đạt chỉ vì thêm turn.

### Gate chạm đất trong chu kỳ chạy (Owner 2026-11-12)
- Review từng chân qua chuỗi tiến về trước → chạm đất nhận trọng lượng → đẩy/rút về sau, kể cả frame cuối→đầu. Không cho chân đổi từ trước sang sau chỉ vì mọi frame cóhashkhác. Pha bay không thay thế pose touchdown.
- Nếu Owner xác định phần đúng và điểm thiếu, giữ nguyên pose đã đúng, thêm whole-body contact ở đúng khoảng thiếu; không kéo dài hold để giả chạm đất, không cắt ghép chân. Cập nhật N, ticks/events/scrubber/loop test theo0..N−1→0; không ép8frame khi cầnthêmphase. Lập bảng newindex↔oldindex/contact để Owner đối chiếu.
