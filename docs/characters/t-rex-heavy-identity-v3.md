# T-rex heavy: đồng bộ nhận diện theo mẫu chuẩn

Owner xác nhận động tác quật đuôi đã chuẩn nhưng nhân vật trong `image copy 4.png` khác mẫu `image copy 5.png`. Nghiệm thu đó chỉ áp dụng động tác, không áp dụng tạo hình heavy hoặc toàn atlas T-rex.

Mẫu nhận diện duy nhất của lần sửa này là idle0 hiện hành, cùng mẫu Owner chỉ ở ảnh5: `work/characters/t_rex/heavy-identity-v3/canonical-idle-00.png`, SHA `8c46b31b6fd328fef3b5b4bd8a1d1ebbd30d51f4d5720c673b3f2437ad565311`. Mẫu nét studio giữ nguyên, không đổi sang tạo hình heavy bị Owner loại.

Bản cũ heavy0 có10231pixel hữu hình và Sobel236.143; idle0 có8604pixel và Sobel245.516. Hai ảnh có bbox gần nhau nhưng đầu/cổ, độ đầy thân, chân và cách tô khác nhau. Vì vậy bbox và Sobel không đủ để xác nhận cùng một nhân vật.

Hai lần dùng ảnh heavy cũ làm edit target vẫn giữ thiên lệch tạo hình; chúng bị loại. Bản chọn chỉ dùng canonical master và ảnh5 làm input nhận diện, dùng chuỗi pha/timing đã duyệt dưới dạng chỉ dẫn động tác. Tái tạo nguyên cơ thể với đầu/hàm góc cạnh, cổ cao, thân/chân thon, chân xa tối và mảng ôliu/kem phẳng. Không ghép đầu/chi từ master lên thân pose khác.

Frame0 và11 dùng nguyên pose canonical, dịch nguyên frame[0,-2] để cùng mặt đấtCanvas y225. SHA RGBA của ảnh pose sau crop là `cea412dd07cf69800fdaeb87cd570ae4d0874235136b834a69b87e0ae62db7e3`, khớp master100%. Đây là tái sử dụng nguyên pose hoàn chỉnh ở hai đầu clip oneshot, không phải cắt ghép bộ phận. Frame1..10 là whole-pose imagegen; chỉ crop nguyên ô, một lần Nearest đăng ký tỷ lệ chung và căn mặt đất. Giữ phối cảnh thu ngắn tự nhiên, không kéo mọi góc về cùng chiều rộng bbox.

Giữ12frame,35tick60Hz `[5,4,2,1,1,1,1,2,3,4,5,6]`, thứ tự pha front4/back7/strike5, hit tại tick13, cùng events/keys/loop/hitstop. Toàn bộ metadata chuyển động của cả9clip được đối chiếu bằng nhau với bản động tác Owner đã duyệt. Đường nét/tỷ lệ cơ thể heavy được phục hồi; không nhận các PNG heavy mới là bảo toàn pixel bản bị loại.

61PNG của các clip khác giữ nguyên byte, cùng timing/sự kiện. Tổng73frame/72cell/9clip trên1atlas3494×2082, canvas384×256, anchor[176,224],Nearest. Atlas SHA `74393d80a74588ed5cce2189bf5d41976939bf633f99780fe0f6998e6498eacb`.

Đã xem filmstrip12frame trên sáng/tối/ô cờ và [ảnh đối chiếu](../../work/characters/t_rex/heavy-identity-v3/review/identity-comparison.png). Clip builder/exporter exit0,warnings0; Godotimport0; `./loop.sh test` exit0(26Python/E2E,3Godotbundle,2Rust); WASMreleasebuild0. HTTP PNG/WASM SHA khớp,parity=true;500file Spinosaurus/Pteranodon không đổi. Skill create_atlas quick_validate0. WARN thiếu clip đã Owner loại và chờ Human Test vẫn được giữ trong log.

QA gate bổ sung: `checks.character_identity=false` chặn bàn giao dù technical exit0; có kiểm thử hồi quy riêng. `create_atlas` yêu cầu so master riêng nhân vật, không lấy action bị báo sai làm identity reference. Gate đúng không chứng minh tự động rằng tạo hình đã được Owner duyệt: bản này vẫn `reviewed_pending_owner`, `identity_owner_approved=false`, không ghi workflow mới vào `skills.md`.

Báo cáo máy đọc: `docs/characters/t-rex-heavy-identity-v3-qa.json`. Nguồn/prompt/bản loại, bằng chứng frame và kiểm thử ở `work/characters/t_rex/heavy-identity-v3/`.
