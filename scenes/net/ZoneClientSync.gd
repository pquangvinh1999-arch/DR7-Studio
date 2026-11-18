class_name ZoneClientSync
extends RefCounted
## Client-side Zone state manager (<= 20 players + <= 20 monsters + drops = ~50 entities/zone).
## Handles WebSocket snapshot updates, 20Hz -> 60Hz interpolation targets, and zone switches without reload.

const MAX_ZONE_ENTITIES := 50
const SNAPSHOT_RATE_HZ := 20.0

var transport: NetworkTransport = null
var current_map_id: String = "rocky_plateau"
var current_zone_id: int = 0
var entities_by_id: Dictionary = {}
var last_snapshot_tick: int = -1


func attach_transport(t: NetworkTransport) -> void:
	transport = t
	if not transport.packet_received.is_connected(_on_packet):
		transport.packet_received.connect(_on_packet)


func request_zone_switch(map_id: String, zone_id: int) -> Error:
	current_map_id = map_id
	current_zone_id = clampi(zone_id, 0, 19)
	entities_by_id.clear()
	last_snapshot_tick = -1
	if transport == null or not transport.is_connected_state:
		return ERR_UNAVAILABLE
	return transport.send_packet({"op": "join_zone", "map_id": current_map_id, "zone_id": current_zone_id})


func send_player_intent(pos: Vector2, dir_x: int, action: String = "") -> Error:
	if transport == null or not transport.is_connected_state:
		return ERR_UNAVAILABLE
	return transport.send_packet({
		"op": "intent",
		"map_id": current_map_id,
		"zone_id": current_zone_id,
		"x": snappedf(pos.x, 0.1),
		"y": snappedf(pos.y, 0.1),
		"dir": dir_x,
		"act": action,
	})


func _on_packet(payload: Dictionary) -> void:
	var op := str(payload.get("op", ""))
	if op == "zone_snapshot":
		last_snapshot_tick = int(payload.get("tick", last_snapshot_tick + 1))
		var incoming: Array = payload.get("entities", [])
		var next_map := {}
		for i in range(mini(incoming.size(), MAX_ZONE_ENTITIES)):
			var item = incoming[i]
			if item is Dictionary and item.has("id"):
				next_map[str(item["id"])] = item
		entities_by_id = next_map
	elif op == "zone_leave" and payload.has("id"):
		entities_by_id.erase(str(payload["id"]))
