# TODO bàn giao: APK Android trên Ramus (2026-11-16)

## Trạng thái đã xác minh

- `codex mcp add ramus --url https://api.ramus.dev/api/mcp` đã chạy; OAuth MCP và `ramus-cli` device login đã hoàn tất. Không cần xin Owner đăng nhập lại nếu token còn hiệu lực.
- Android SDK cài tại `/home/codespace/android-sdk`; Godot editor settings trỏ tới SDK này. `export_presets.cfg` đã bật `architectures/x86_64=true` cho emulator, vẫn giữ `arm64`. `project.godot` đã bật `rendering/textures/vram_compression/import_etc2_astc=true` để export Android.
- `./loop.sh apk-debug` exit 0, tạo `build/android/dr7-studio-debug.apk` (~65 MB). `apksigner verify --verbose` xác nhận chữ ký v2/v3; APK có `lib/x86_64/libgodot_android.so`. `./loop.sh test` exit 0 sau thay đổi cấu hình; log `/tmp/dr7_apk_current_test.log`. Đây chỉ là test kỹ thuật, chưa đạt Human Test trên APK.
- APK đã upload và khởi chạy trên Ramus: session `645aa9ef-cb77-446f-b446-a3c0bc872473`, màn emulator `1616×720`, package `com.dr7studio.dragonball2d`. Link xem: https://ramus.dev/share#rshr_KQPuvzI5BwJ0yxFuSPqH4Pz_vtuBHEA9mltZtQSK7u8 . Session có thể hết hạn; tạo session mới nếu cần.
- ADB tunnel được tạo bằng `ramus adb --session 645aa9ef-cb77-446f-b446-a3c0bc872473`, serial hiện tại `127.0.0.1:34095`; kết nối này cũng có thể hết hạn. Log khởi động mới nằm ở `/tmp/dr7_relaunch_logcat.txt`.
- **[ĐÃ SỬA 2026-11-16]** Dependency `res://tests/SkillAnimator2D.gd`: `export_presets.cfg` đã đổi `exclude_filter` từ `tests/*` sang `tests/test_*,tests/bench_*,tests/__pycache__/*,tests/*.py,tests/*.mjs,tests/*.json,tests/*.sh`. APK `build/android/dr7-studio-debug.apk` đóng gói đủ `assets/tests/SkillAnimator2D.gdc` + `assets/scenes/SkillAnimator2D.gdc`; chạy lại trên Ramus (`b98488fe-7f85-4d90-8a9b-defc2979c38c`) xác nhận `OnGodotSetupCompleted` / `OnGodotMainLoopStarted` với **0 lỗi script/resource**.
- **[ĐÃ XÁC MINH NGUYÊN NHÂN SHADER]** Dù đã đặt `limits/opengl/max_renderable_lights=2` và `limits/opengl/max_lights_per_object=2` (ngưỡng tối thiểu `hint_string=2,...` của Godot 4.7.2) trong `project.godot`, `gl_compatibility` trên Ramus (`OpenGL ES 3.0 SwiftShader 4.0.0.1`) vẫn báo `SceneShaderGLES3` và `CanvasShaderGLES3: Fragment shader active uniforms exceed GL_MAX_FRAGMENT_UNIFORM_VECTORS (261)` và hiển thị màn xám. Kiểm tra `libgodot_android.so` xác nhận `#define MAX_GLOBAL_SHADER_UNIFORMS 256` được hardcode vào mọi shader GLES3 (lỗi upstream Godot #109550 với `Android Emulator OpenGL ES Translator (Google SwiftShader)`).
- **[ĐÃ THỬ ĐỐI CHIẾU VULKAN MOBILE]** Xuất thử APK tạm bằng `renderer/rendering_method.mobile="mobile"` (sau đó đã khôi phục `project.godot` về `gl_compatibility` theo Hiến pháp Điều 4) và chạy trên Ramus (`973c789a-b8ef-4ca1-be22-cc05c9f63486`, `Vulkan 1.3.0 - Forward Mobile - Goldfish GFXStream (SwiftShader Device (Subzero))`): **0 lỗi Godot / 0 lỗi shader**, hiển thị đầy đủ sân Rocky Plateau `cover` trên `1616×720`, 2 `T-rex` `1.75x Nearest`, 7 ngọc rồng, nút skill và Touch HUD (`FPS: 9/60` do CPU SwiftShader). Ghi nhận thêm trên `1616×720`: `HUDLayer/HudLabel` chữ trắng đặt sát góc trên trái chưa có nền/safe-area nên hơi khó đọc trên nền trời.

## Việc cần Owner quyết định trước khi tiếp tục

1. **Giữ `gl_compatibility` trên Android hay bật `renderer/rendering_method.mobile="mobile"` (Vulkan)?**
   - Phương án A (giữ nguyên Hiến pháp ADR-0001): Giữ `gl_compatibility` cho cả Web & Mobile; chỉ kiểm tra thực tế trên máy Android thật (ví dụ Redmi K70E) hoặc emulator GPU passthrough thật vì lỗi `(261)` chỉ xảy ra trên phần mềm SwiftShader 4.0.0.1 (Godot #109550).
   - Phương án B (cần Owner chốt sửa `AGENTS.md` & `ADR-0001`): Giữ `gl_compatibility` cho Web/Desktop, nhưng chuyển `rendering/renderer/rendering_method.mobile="mobile"` (Vulkan) cho Android/iOS để chạy được trên cả Ramus emulator lẫn máy Android hiện đại (Android 10+); nhược điểm là thiết bị Android quá cũ không hỗ trợ Vulkan 1.0+ sẽ không chạy được hoặc phải fallback riêng.
2. Sau khi Owner chốt phương án + kiểm/sửa thêm safe-area cho `HUDLayer/HudLabel` (nếu cần), chạy kiểm chứng di chuyển 2 hướng, turn, skill liên tục và 60 FPS trên thiết bị mục tiêu rồi mới đóng `ISS-ANDROID-SDK-20261116`.

## Lưu ý bảo mật

Không sao chép OAuth callback code, access token, URL upload một lần hoặc nội dung `.credentials.json` vào repo/log báo cáo.
