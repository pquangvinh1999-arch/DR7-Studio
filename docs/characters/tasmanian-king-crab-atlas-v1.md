# Tasmanian King Crab — atlas demo v1

Owner đã nghiệm thu toàn bộ bản v0.7.0; biên nhận `assets/tasmanian_king_crab/owner_approval.json` ràng buộc SHA atlas, TRES và prefab. Các ghi chú pending trong phần lịch sử dưới đây được thay bằng nghiệm thu này. Dùng mẫu133×64px Owner chốt, canvas384×256, anchor[176,224], Nearest, thân nguyên1lớp. Giữ idle0 byte-for-byte từ size-master.

## Phạm vi Owner xác nhận

6clip thân: idle8,walk8,attack_nomal8,power_up8,hit6,ko8 =46pose. Khôngrun/jump/attack_heavy/aura_loop/guard/win. Giữ đúng tên attack_nomal của Owner. Đòn thường dùng càng lớn phía gần camera hướng+X; nguồnimagegen toàn thân, không cắt chi rồi xoay/warp/ghép. Pixel dissolve nằm trong art của pha vung nhanh3/4; gốc càng và thân giữ kết nối. Đây là demo chờ Owner đánh giá cường độ dissolve và chuyển động, không dùng technicalexit0 thay motionapproval.

Master/work: work/characters/tasmanian_king_crab/size-master/. Càng lớn anatomicalright gần camera; càng nhỏ anatomicalleft xa. Camera3/4 nhìnphải,+X. Walk tiếnpha0..7→0, khôngpingpong, 8pose khác PNG; vai trò các chân/nhịp cuối→đầu cần Owner kiểm khi phát. Lật ngang trongUI chỉ chọn hướng hiển thị; không nhận là pose mặt lưng hay clipxoay.

## FX và chuỗi power_up

NguồnOwner600×86,nềnRGB(0,0,128),SHA2772a0e7e7b6cef7062cb47221c8c55b84d1311d19f0ee29b404a3745079c5ee. 6pose đọc phải→trái, tách bằng2Downership, loại toàn bộkeypocket trước edgeunmix chỉ1px. KhôngAIredraw6pose; thu toànFX cùng1/2Nearest để vừa càng, từ khoảng75px xuống37–38px. Hình mới6/7 đượcimagegen riêng, không gọi là ảnh cósẵn củaOwner. FXsource-evidence ghi tọađộ/SHA/nguồn vàpixel biến đổi.

power_orb_loop dùng[0,1,2,3,4,5,6,7],4ticks/pha. Hai hình6/7 thu core/tan năng lượng sauwhitepeak5, rồiwrap vềringmờ0. Không nhảy5→1→0.

power_up thân cóticks[8,16,5,5,5,6,7,8], tổng60ticks(1s). Trongtick0..23, FXpha0..5tăng dần, neo theo gapcàng của body0[196,203] vàbody1[220,149]. Frame thân2bắt đầu tại tick24: ChargeFXẩn vàProjectileFXphóng từ[267,157]. Projectile dùng[5,6,7,0],4ticks/pha, vận tốc[4,0]px/tick, lifetime16ticks. Tick40ẩn hẳn. Hai hình mới được dùng trước khi trở vềringmờ/biếnmất; không tạo aura_loop.

Contract charge/projectile cùng dữ liệu trong roster.json vàengine-export.json. Godot scenes/TasmanianFighter2D.gd vàgetLayerFramesForStep của localhost đọc cùngcontract; 60Hz lấy trực tiếp authoredticks. Body1quad; khiFXhiện thêm1quad.

## Đóng gói và kiểm chứng

54PNG/frame nguồn duy nhất, 58clip-frame refs,8clip tổng(6thân+2FX),1page3106×1822. AtlasSHAbf079cf2fc96d59fc1cebb86012b39b1548a19c62c5a239e4a9528212efc51e1. FullFXbboxRect(92,109,254,115), restbodyRect(110,160,133,64). Quyđổi64PPU/32px tile trong QA/roster.

Builder strictwarnings0;exporterpass1page. Looptest32Python/E2E+4Godotbundle+Godot60tickcharge+2Rust exit0. WASMreleasebuild0,FrontendE2EtrênWASMmới0. Chromium chạy bằngRustWASM vàghi đủframe của6clip; khôngpageerror. Có capture3nềnvàWebM, nhưng không dùng headlesscapture làm benchmarkFPSmobile. GóiZIPCRC vàGodotstandaloneimport/bundles/charge exit0; HTTPatlas/WASMbytes khớp đĩa, APIparity4bundle.

Đã mở9filmstrip gồm8clip+power_up-composite trênsáng/tối/ôcờ. SourceRGBA/độ nét/bbox từngpose ởmeasurements.json; khôngLUT/sharpen hoặc épSobel. FXđược phép alpha mềm, thân100%alpha cứng. Kiểmsourcekey/spill định nghĩa trongverification/alpha-and-peer-proof.json; không quy mọi màu tím/xanh củaFX lànền.

QA: docs/characters/tasmanian-king-crab-atlas-v1-qa.json. Review/prompt/generated/source vàregistration tại work/characters/tasmanian_king_crab/atlas-v1/. Đã có receipt hiện hành vàPIPE-004 sau Owner nghiệm thu.

## Lỗi timing tìm được khi kiểm thử

Ép --godot-fps60 khiến exporter lấyduration_ms làm tròn: FX4tick thành4.02/3.96tick; Godottest báo `[FAIL] Wrong charge at tick4`. Đã xuất --godot-fpsauto để lấy authoredticks, vẫnspeed60Hz vàcácduration4/4 chínhxác. Sửa cùng lỗi trongPteranodon size-sync mới(3filemetadata/tres), không đổiPNG của cả3nhânvật cũ. 474peerPNGgiữSHA.

T-rex đãduyệt từtrước vẫn cóGodotidle[7.02,6.96,…] so với authored[7,7,…]; đây là issuelegacy ngoài phạm vi, đã ghi state.json, không tự sửa nhân vật đó. HashparityGodot↔localhost vẫn khớp; issue này liênquan nguồn tick gốc và không được coi là đã sửa.
