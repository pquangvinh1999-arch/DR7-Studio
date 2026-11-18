class_name WebSocketTransport
extends NetworkTransport
## Phase 1 WebSocketTransport (Godot 4 WebSocketPeer) compatible with Cloudflare Free Proxy (port 443 wss://).

var peer: WebSocketPeer = WebSocketPeer.new()
var active_endpoint: String = ""
var active_map_id: String = ""
var active_zone_id: int = 0
var _was_open: bool = false


func connect_to_zone(endpoint_url: String, map_id: String, zone_id: int, supabase_jwt: String) -> Error:
	close_connection("reconnecting")
	active_endpoint = endpoint_url
	active_map_id = map_id
	active_zone_id = zone_id
	var sep := "&" if endpoint_url.contains("?") else "?"
	var url := "%s%smap=%s&zone=%d" % [endpoint_url, sep, map_id.uri_encode(), zone_id]
	if not supabase_jwt.is_empty():
		peer.handshake_headers = PackedStringArray(["Authorization: Bearer " + supabase_jwt])
	var err := peer.connect_to_url(url)
	_was_open = false
	is_connected_state = false
	return err


func send_packet(payload: Dictionary) -> Error:
	if peer.get_ready_state() != WebSocketPeer.STATE_OPEN:
		return ERR_CONNECTION_ERROR
	return peer.send_text(JSON.stringify(payload))


func poll_events() -> void:
	peer.poll()
	var state := peer.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		if not _was_open:
			_was_open = true
			is_connected_state = true
			connected.emit({"transport": "websocket", "map_id": active_map_id, "zone_id": active_zone_id})
		while peer.get_available_packet_count() > 0:
			var raw := peer.get_packet().get_string_from_utf8()
			var parsed = JSON.parse_string(raw)
			if parsed is Dictionary:
				packet_received.emit(parsed)
	elif state == WebSocketPeer.STATE_CLOSED and (_was_open or is_connected_state):
		_was_open = false
		is_connected_state = false
		disconnected.emit(peer.get_close_reason())


func close_connection(reason: String = "client_close") -> void:
	if peer.get_ready_state() == WebSocketPeer.STATE_OPEN or peer.get_ready_state() == WebSocketPeer.STATE_CONNECTING:
		peer.close(1000, reason)
	_was_open = false
	is_connected_state = false
