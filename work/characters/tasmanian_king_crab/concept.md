# Tasmanian King Crab — đề xuất master demo

Trạng thái: master demo đã sinh bằng built-in imagegen, chờ Owner duyệt tạo hình. Camera đã chốt: góc3/4 nhìn sang phải, càng lớn gần camera. Bản demo concept-v2.png, số đo/giới hạn ở master-review/review.json. Chưa đạt chuẩn sprite runtime:1536x1024 và alpha mềm/quầng còn tồn tại.

## Owner đã quy định

- Nhân vật tiếp theo là Tasmanian King Crab; tên kỹ thuật đề xuất `tasmanian_king_crab`.
- Phong cách hung tợn, có một càng to và một càng nhỏ.
- Dùng chuẩn nét hiện hành của dự án, đồng bộ ba nhân vật đã nghiệm thu.

## Cơ sở nhận diện

Fishing Tasmania xác định Pseudocarcinus gigas còn gọi là king crab/Tasmanian giant crab; mô tả mai đỏ cam có đốm kem, đầu càng đen, con đực có một càng lớn hơn nhiều so với càng kia.
Nguồn: https://fishing.tas.gov.au/species/crab-giant (xem 2026-11-12).
Đây là cơ sở loài; thiết kế hung tợn trong game là yêu cầu Owner, không phải tuyên bố ngoại hình khoa học.

## Đề xuất tạo hình chưa chốt

- Mai thấp, nặng, bề mặt giáp đỏ gạch/đỏ nâu sẫm, điểm kem ngà và mút càng đen; gai viền và mắt sắc thể hiện hung tợn.
- Giữ cấu trúc cua: hai càng bất đối xứng và bốn cặp chân bò; các khớp nối đúng với thân, che khuất theo phối cảnh; không thêm đầu/hàm khủng long hoặc tay chân người.
- Càng lớn dày, lực nghiền thể hiện bằng khối chắc và răng bên trong kìm; càng nhỏ thon, sắc, vẫn đủ rõ ở cỡ gameplay. Tỷ lệ cụ thể sẽ review bằng ảnh master.
- Chi tiết native1px, Nearest, alpha thân cứng; không ép palette16 màu, lưới100texel/2x hoặc scalar Sobel. Tham chiếu docs/art-standards/t-rex-sharpness-reference.png và JSON đi kèm.
- Bước đầu chỉ tạo một master tĩnh để khóa nhận diện. Canvas/bbox/anchor sẽ công bố sau đo ảnh; chưa tự chốt kích thước riêng của cua bằng kích thước T-rex.

## Quyết định camera đã được Owner chốt

Đã hỏi Owner chọn một trong: 3/4 nhìn sang phải với càng lớn gần camera (đề xuất); ngang nhìn phải càng lớn gần camera; hoặc chính diện càng lớn bên trái màn hình.
Phải ghi rõ bên giải phẫu của càng lớn sau lựa chọn; không đổi càng lớn/nhỏ tùy frame hoặc dùng mirror thay một bộ góc mới khi bất đối xứng cần bảo toàn.
Hướng bò trên map tách khỏi hướng mặt/càng; chưa mặc định bò ngang map hay tiến theo mặt. Chốt trước phần hoạt ảnh phụ thuộc.

## Bước sau master

Sau Owner duyệt nhận diện, xác định walk/run riêng theo chu kỳ nhiều chân, attack_light bằng càng nhỏ và attack_heavy bằng càng lớn là đề xuất để Owner review. Không mặc định thêm phun lửa, beam, Ki, jump hoặc aura. Không guard/win theo quy định chung. Tạo whole-body poses, không cắt chi rồi warp/ghép. Chưa có animation/atlas/technical PASS, chưa thêm roster và chưa ghi skills.md.

## Mẫu kích thước sau Owner chọn chiều ngang

Tasmanian133×64px (85% của chiều ngang Spino157px sau làm tròn),canvas384×256,anchor[176,224]. Mẫu mới ở work/reviews/character-size-v1/tasmanian_king_crab-sample.png; alpha thân100%,Nearest. Đây là bản chuẩn hóa kỹ thuật từconceptv2, không phải nghiệm thu nét/giải phẫu. Ảnhmaster1536×1024 ởtrên lànguồn, không phải gameplayframe. Chờduyệtmẫutrướcatlas.

## Nghiệm thu atlas v0.7.0

Owner chốt ngày2026-11-12T09:51:08.495780+00:00; receipt `assets/tasmanian_king_crab/owner_approval.json`, atlasSHA `bf079cf2fc96d59fc1cebb86012b39b1548a19c62c5a239e4a9528212efc51e1`. Dùng master-size133×64px và6bodyactions đãduyệt. Các ghi chú pending/concept ởtrên là lịch sử trước nghiệm thu.
