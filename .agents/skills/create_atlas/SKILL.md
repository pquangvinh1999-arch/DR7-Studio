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
6. Mở xem từng filmstrip trên nền sáng/tối/ô cờ. Chạy kiểm thử Godot headless, Rust cargo test và WASM theo dự án; `./loop.sh check`, `./loop.sh test`; giữ nguyên WARN/FAIL và sửa lỗi trước bàn giao. Đồng bộ atlas/rect/timing/anchor/hash với localhost:8080 cho Human Test. Không dùng pass roster rỗng chứng minh bộ nhân vật hoàn thiện hoặc cam kết 60 FPS mobile.
7. Chỉ đưa bộ hoàn thiện vào roster. Cập nhật `state.json` sau task; chỉ ghi `skills.md` gốc khi Owner nghiệm thu Human Test thành công.

## Đường dẫn và khả năng dùng chung

Bản chuẩn là `.agents/skills/create_atlas/SKILL.md`; `.agent` là symlink tới `.agents`, không tạo bản độc lập hoặc đổi tên thư mục Owner chọn. `SKILL.md` là entrypoint của skill, khác `skills.md` gốc. Nội dung dùng được cho Codex/Antigravity; dùng khả năng xem ảnh thật của host, không nhận đã kiểm tra trực quan nếu chưa mở ảnh. Không tự sửa hooks/cài plugin hoặc nhận đã discovery trên cả hai CLI khi chưa kiểm chứng.
