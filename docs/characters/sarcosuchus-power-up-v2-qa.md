# Sarcosuchus power_up v2 — v0.8.1

Cầu hiện/lớn dần theo hàm mở:10tick FX1→10px, alpha32→255; cực đại10×9px. Anchor Canvas(236,201) ở thân0 và(239,193) ở thân1; phóng tại thân2/tick10 ở(244,194). PNG cuối gồng bằng chính xác PNG đầu bay, không tăng cỡ khi phóng. Sáu FX nguồn tiếp tục chạy trái→phải một lượt,ẩn tick28.

55PNG thân,tick/events,7bodyactions và716file của4nhân vật trước giữ nguyênSHA. ChỉresampleFX nguồn đãkey, không AIredraw/thaypose. Bản cũ có10/24/28pixel răng sáng bịphủ ởthân0/1/2; bản mới0pixel qua11mốc0..10, phép đoROI/RGB chỉ hỗ trợ review bằng mắt. Đã mởfilmstrip/composite3nền và runtime screenshots; Owner đã nghiệm thu toàn bộ nhân vật và bản sửa power_up.

Kỹthuật:loop.sh testexit0,36Python/E2E,5Godotbundle,2charge-tests,2Rust;WASMrelease0. Chromium kiểm46tick,phát0..8→0 trên3nền,0pageerrors. HTTPbyteparity vàGodotZIPimport/bundle/power-testexit0. Atlas1page3494×2082,69cell/71PNG/71cliprefs,Nearest60Hz. WARN clipthamchiếuđãloại vàcác clip đã loại vẫn giữ; motion đã được Owner nghiệm thu.

[Demo](http://localhost:8080/?character=sarcosuchus&clip=power_up&frame=0&paused=1). [Số đo/bằng chứng](sarcosuchus-power-up-v2-qa.json). Đã chốt PIPE-005; biên nhận assets/sarcosuchus/owner_approval.json ràng buộc đúng atlas/TRES/prefab/manifest và PNG runtime.
