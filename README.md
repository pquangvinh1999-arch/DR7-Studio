# DR7-Studio — Dragon Ball 2D Mobile Action / RPG

Mục tiêu dự án: game 2D **Dragon Ball** trên nền tảng Mobile (**Android `.apk`/`.aab`** & **iOS `.ipa`**), tối ưu **0đ** ở giai đoạn Test/Alpha và sẵn sàng scale theo lộ trình **[ADR-0001](docs/adr/0001-architecture-and-scale-roadmap.md)**.

## Kiến Trúc Chính Thức (Theo Giai Đoạn)

1. **Client (`Godot 4.7.2` + `GDScript`, `GL Compatibility`)**:
   - Render **`Combined 1-Layer`**, `Nearest` (`texture_filter=0`), tick chuẩn `60Hz`, đồng bộ SHA-256 1:1 với preview.
   - Màn hình (`D1–D4`): base `1920×1080`, `canvas_items` + `expand`, mặc định `fractional` + công tắc `"Pixel Perfect"` (`integer` cho màn `>= 1080px`, tự khóa `fractional` dưới `1080p` theo [DisplayPolicy.gd](scenes/runtime/DisplayPolicy.gd) và [device-profiles.json](assets/maps/rocky_plateau/device-profiles.json)).
   - Điều khiển cảm ứng đa chạm Safe Area ([TouchHudOverlay.gd](scenes/runtime/TouchHudOverlay.gd)) và lớp vận chuyển mạng hoán đổi ([NetworkTransport.gd](scenes/net/NetworkTransport.gd) -> `WebSocketTransport` `wss://`).
2. **Backend & Hạ Tầng Theo Ngưỡng Scale (`D5`, `D8`, `D10`)**:
   - **Pha 1 (`0đ` Test/Alpha — `<= 50` thực thể/khu)**: Client `Godot 4 GDScript` + Server `Godot Headless WebSocket` (`wss://` port `443` qua Cloudflare Free Proxy + WAF chặn IP `VN`/`JP`) + **Supabase** (JWT Auth + ghi Postgres theo lô).
   - **Pha 2 (Vượt ngưỡng `7 map lớn × 5 map nhỏ × 20 khu × 50 thực thể = 35,000 thực thể` hoặc `p99 > 25ms @ 20Hz`)**: Giữ nguyên Client Godot & `NetworkTransport`; nâng Server Combat sang **Rust Core** (`engines/rust_combat_sim`) trên VPS.

## Lệnh Phát Triển & Kiểm Thử

- Kiểm tra trạng thái governance & session: `./loop.sh status`
- Đối soát Hiến pháp & Parity 1:1 SHA-256 (`Godot ⇄ Localhost`): `./loop.sh check`
- Chạy toàn bộ kiểm thử (`Governance + Python + Frontend WASM E2E + Godot Headless + Rust`): `./loop.sh test`
- Xuất bản Godot Web Compatibility (phục vụ trong preview tab): `./loop.sh web-export`
- Xuất gói Android Debug APK (khi có SDK/keystore): `./loop.sh apk-debug`
- Mở trạm kiểm thử Human Test (`http://127.0.0.1:8080`): `python3 tools/preview/server.py`
