class_name NetworkTransport
extends RefCounted
## Abstract transport boundary (D5 / ADR-0001).
## Phase 1 uses WebSocketTransport (wss:// compatible with Cloudflare Free Proxy & WAF VN/JP block).
## Later APK/VPS UDP deployments can swap in an ENetTransport implementation without touching gameplay code.

signal connected(session_info: Dictionary)
signal packet_received(payload: Dictionary)
signal disconnected(reason: String)

var is_connected_state: bool = false


func connect_to_zone(_endpoint_url: String, _map_id: String, _zone_id: int, _supabase_jwt: String) -> Error:
	return ERR_UNAVAILABLE


func send_packet(_payload: Dictionary) -> Error:
	return ERR_UNAVAILABLE


func poll_events() -> void:
	pass


func close_connection(_reason: String = "client_close") -> void:
	is_connected_state = false
