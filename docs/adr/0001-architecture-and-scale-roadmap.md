# ADR-0001: Client Architecture, Mobile Display Policy, Zone Netcode & 35,000-Entity Scale Roadmap

- **Status:** Accepted by Owner (`D1`–`D10`, `2026-11-16`)
- **Applies to:** `v0.15.0+`

## 1. Context & Scale Targets (`D8`, `D10`)

- **Gameplay Target (`D10`):** `7` major regions × `5` sub-maps (`35` sub-maps) × `20` zones/map = **`700` concurrent zones**, averaging **`50` entities/zone** (players + monsters) = **`35,000` total entities** world-wide.
- **Per-Client Viewport Load:** A player client only renders **1 active zone (`~50` fighters/monsters + FX/items)** at a time on Mobile (`Android` `.apk`/`.aab`, `iOS` `.ipa`) locked at **60 FPS (`<= 16.67 ms/frame`)**.
- **Budget Goal (`D8`):** **`0đ` operational budget during dev/alpha testing**, scaling cleanly to commercial VPS/DB without rewriting game rules or deviating from `AGENTS.md`.

## 2. Decided Architecture (Two-Phase Execution, Zero Documentation Drift)

### 2.1 Client Engine (`Godot 4.7.2 GDScript` + `Compatibility` Renderer)
- **Decision:** Client runs **100% Godot GDScript** on `gl_compatibility` (`Compatibility` renderer, `D3`) with `Combined 1-Layer` `AnimatedSprite2D` bundles (`1` PNG atlas page `<= 4096×4096`, `Nearest` filter, `60Hz` ticks).
- **No `GDExtension` on Client:** Because a single zone holds `<= 50` entities (`~0.03–0.10 ms/frame` in Godot 4.7.2 headless logic tests), `GDExtension` (Rust FFI + NDK/Xcode cross-compile) adds build friction without client CPU benefit. `GDExtension` + `MultiMeshInstance2D` would only be reconsidered if a single open screen must render `> 300–2,000` simultaneous entities without zone sharding.
- **Rust Crate Role (`engines/rust_combat_sim`):** Kept cleanly separated from Godot Client for: (1) browser `localhost:8080` `60Hz` WASM stepper (`rust_combat_sim.wasm`), and (2) **Phase 2 Authoritative Rust Dedicated Server** (`rlib`).

### 2.2 Display Scaling, Full-Width Phones & Device Profiles (`D1`, `D2`, `D4`)
- **Base Coordinates:** `1920×1080` logic height (`canvas_items`).
- **Aspect (`D1`):** Full horizontal expand (`expand` / `keep_height` behavior on landscape phones `W/H >= 16:9` — `0` black bars on phones). `Redmi K70E (2712×1220, 20:9)` expands horizontally from `1920` to `2400` logic px (`scale ≈ 1.130`). Gameplay/aggro distances MUST use world coordinates, never screen edges; UI/touch buttons MUST anchor via Godot `AnchorsPreset` + `DisplayServer.get_display_safe_area()`.
- **Stretch Scale Mode (`D2`):** Default `fractional`, plus a runtime `"Pixel Perfect"` toggle (`integer`) with empirical `< 1080px` safeguard (`Android 720p`: forced to `fractional` because Godot 4.7.2 clamps `floor(720/1080)` to `1.0`, clipping a `1080`-tall canvas out of a `720px` screen).
- **Target Device Matrix (`D4`):** `Redmi K70E (2712×1220)` + `Android 20:9 (2400×1080)` + `Android 720p (1600×720)` + `FHD 16:9 (1920×1080)`, plus `iPhone` once macOS build access is available.

### 2.3 Security, Proxy, Auth, DB & Netcode (`D5`, `D8`, `D10`)
- **Cloudflare (`0đ` Free Plan):** DNS + Orange-Cloud Proxy (`wss://` port `443`) + WAF Custom Rule blocking `VN` & `JP` IPs (`(ip.src.country in {"VN" "JP"})`).
  - **Protocol Constraint Verified:** Cloudflare Free Proxy supports **HTTP/HTTPS and WebSockets (`wss://` on port `443`, `8443`, etc.) only — NO raw UDP / ENet**. Therefore Phase 1 netcode **MUST** implement `WebSocketTransport` behind `INetworkTransport` so an `ENetTransport` drop-in remains clean if UDP ports are exposed later with VPS firewall GeoIP rules.
- **Supabase (`Free` in Dev → `Pro` at Scale):** **Auth (JWT) + PostgreSQL only** (account, character stats, inventory, guilds, transactions). **NEVER** use Supabase Realtime for `20 Hz` combat sync (`Free = 100 msg/s`, `Pro = 500 msg/s`). Game servers verify Supabase JWT on WebSocket handshake and flush dirty inventory/stats in batches every `30–60s` plus critical events (rare item pickup, trade, map change, disconnect).
- **Authoritative Zone Server & Rust Trigger Threshold (`D5`, `D10`):**
  - **Phase 1 (`0đ` Dev/Alpha):** **Godot Headless Dedicated Server** (`WebSocketTransport`, shared GDScript AI/zone rules, idle zones paused).
  - **Phase 2 Trigger (Switch Server to `Rust` on VPS behind Cloudflare IP Allowlist):** Trigger immediately when approaching `D10` multi-map scale (`> 20` active zones / multi-hundred CCU) OR when **server `p99` tick time > `25 ms` (`50%` of `50 ms` @ `20 Hz`)** after GDScript optimization, OR when infra cost per CCU becomes CPU/RAM bound.
