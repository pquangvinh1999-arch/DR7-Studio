class_name DragonBallItem2D
extends Node2D
## 1x (32x32) Dragon Ball game item with shared diagonal full-body sheen_fx,
## monster-death drop/roll animation (+10px jump, fall to ground, +10px roll),
## and shrink-to-collector pickup flight (60Hz Nearest, bag hides FX).

signal collected(ball_number: int)

const EXPORT_JSON_PATH := "res://assets/items/dragon_balls/item-export.json"

@export_range(1, 7) var ball_number: int = 1
@export_enum("map", "bag") var display_mode: String = "map"
@export var sparkle_enabled: bool = true

var body_sprite: AnimatedSprite2D = null
var sparkle_fx: AnimatedSprite2D = null
var _map_anchor_px: Vector2 = Vector2(16.0, 32.0)
var _bag_anchor_px: Vector2 = Vector2(16.0, 16.0)
var _initialized: bool = false

# Shared drop & pickup physics contract loaded from item-export.json
var _jump_height_px: float = 10.0
var _rise_duration_s: float = 10.0 / 60.0
var _fall_min_duration_s: float = 12.0 / 60.0
var _fall_gravity_px_per_s2: float = 1800.0
var _arc_dx_px: float = 8.0
var _roll_distance_px: float = 10.0
var _roll_duration_s: float = 18.0 / 60.0
var _roll_angle_rad: float = 0.625
var _pickup_duration_s: float = 30.0 / 60.0
var _pickup_end_scale_ratio: float = 0.05
var _pickup_arc_lift_px: float = 18.0

# Lifecycle state: "resting" | "dropping" | "collecting" | "collected" | "bag"
var lifecycle_state: String = "resting"
var drop_subphase: String = "rest"
var base_scale: float = 1.0
var _drop_spawn_pos: Vector2 = Vector2.ZERO
var _drop_ground_y: float = 840.0
var _drop_dir: float = -1.0
var _drop_fall_duration_s: float = 12.0 / 60.0
var _drop_elapsed_s: float = 0.0
var _drop_peak_y: float = 830.0
var _drop_land_x: float = 0.0
var _drop_target_x: float = 0.0

var _collect_elapsed_s: float = 0.0
var _collect_start_pos: Vector2 = Vector2.ZERO
var _collector_node: Node2D = null
var _collector_offset_y: float = -40.0
var _collect_fallback_target: Vector2 = Vector2.ZERO


func _load_contract() -> void:
	if not FileAccess.file_exists(EXPORT_JSON_PATH):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(EXPORT_JSON_PATH))
	if not (parsed is Dictionary):
		return
	var meta := parsed as Dictionary
	var ma: Variant = meta.get("map_anchor_px", [])
	if ma is Array and ma.size() >= 2:
		_map_anchor_px = Vector2(float(ma[0]), float(ma[1]))
	var ba: Variant = meta.get("bag_anchor_px", [])
	if ba is Array and ba.size() >= 2:
		_bag_anchor_px = Vector2(float(ba[0]), float(ba[1]))
	var dp: Variant = meta.get("drop_physics", {})
	if dp is Dictionary:
		_jump_height_px = float(dp.get("jump_height_px", 10.0))
		_rise_duration_s = float(dp.get("rise_ticks", 10)) / 60.0
		_fall_min_duration_s = float(dp.get("fall_min_ticks", 12)) / 60.0
		_fall_gravity_px_per_s2 = float(dp.get("fall_gravity_px_per_s2", 1800.0))
		_arc_dx_px = float(dp.get("arc_dx_px", 8.0))
		_roll_distance_px = float(dp.get("roll_distance_px", 10.0))
		_roll_duration_s = float(dp.get("roll_ticks", 18)) / 60.0
		_roll_angle_rad = float(dp.get("roll_angle_rad", 0.625))
	var pp: Variant = meta.get("pickup_physics", {})
	if pp is Dictionary:
		_pickup_duration_s = float(pp.get("duration_ticks", 30)) / 60.0
		_pickup_end_scale_ratio = float(pp.get("end_scale", 0.05))
		_pickup_arc_lift_px = float(pp.get("arc_lift_px", 18.0))


func _ensure_nodes() -> void:
	if _initialized and is_instance_valid(body_sprite):
		return
	_load_contract()
	body_sprite = get_node_or_null("BodySprite") as AnimatedSprite2D
	sparkle_fx = get_node_or_null("SparkleFX") as AnimatedSprite2D
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	if is_instance_valid(body_sprite):
		body_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		body_sprite.centered = false
	if is_instance_valid(sparkle_fx):
		sparkle_fx.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		sparkle_fx.centered = false
	_initialized = is_instance_valid(body_sprite)


func _ready() -> void:
	_ensure_nodes()
	if absf(scale.x) > 0.01:
		base_scale = absf(scale.x)
	_apply_state()


func _apply_state() -> void:
	_ensure_nodes()
	var n := clampi(ball_number, 1, 7)
	ball_number = n
	var is_bag := display_mode == "bag"
	if is_bag:
		lifecycle_state = "bag"
		drop_subphase = "bag"
	var off := -_bag_anchor_px if (is_bag or lifecycle_state == "collecting") else -_map_anchor_px
	var clip_name := StringName("ball_%02d" % n)
	if is_instance_valid(body_sprite):
		body_sprite.position = Vector2.ZERO
		body_sprite.rotation = 0.0
		body_sprite.offset = off
		if body_sprite.sprite_frames != null and body_sprite.sprite_frames.has_animation(clip_name):
			body_sprite.animation = clip_name
			body_sprite.frame = 0
			body_sprite.stop()
	var can_sheen := (not is_bag) and sparkle_enabled and lifecycle_state == "resting"
	if is_instance_valid(sparkle_fx):
		sparkle_fx.position = Vector2.ZERO
		sparkle_fx.rotation = 0.0
		sparkle_fx.offset = off
		sparkle_fx.visible = can_sheen
		if can_sheen and sparkle_fx.sprite_frames != null and sparkle_fx.sprite_frames.has_animation(&"sparkle_fx"):
			if sparkle_fx.animation != &"sparkle_fx" or not sparkle_fx.is_playing():
				sparkle_fx.play(&"sparkle_fx")
		else:
			sparkle_fx.stop()


func set_ball_number(num: int) -> bool:
	ball_number = clampi(num, 1, 7)
	_apply_state()
	return true


func set_display_mode(mode: String) -> void:
	display_mode = "bag" if mode == "bag" else "map"
	if display_mode == "map" and lifecycle_state == "bag":
		lifecycle_state = "resting"
		drop_subphase = "rest"
	_apply_state()


func set_sparkle_enabled(enabled: bool) -> void:
	sparkle_enabled = enabled
	_apply_state()


func start_drop_from(spawn_pos: Vector2, ground_y_pos: float, roll_dir: float = -1.0, item_scale: float = 1.0) -> void:
	_ensure_nodes()
	display_mode = "map"
	base_scale = clampf(item_scale, 0.5, 4.0)
	scale = Vector2(base_scale, base_scale)
	visible = true
	lifecycle_state = "dropping"
	drop_subphase = "rise"
	_drop_spawn_pos = spawn_pos
	_drop_ground_y = ground_y_pos
	_drop_dir = -1.0 if roll_dir < 0.0 else 1.0
	_drop_elapsed_s = 0.0
	_drop_peak_y = spawn_pos.y - _jump_height_px * base_scale
	var h_fall := maxf(0.0, ground_y_pos - _drop_peak_y)
	_drop_fall_duration_s = maxf(
		_fall_min_duration_s,
		sqrt(2.0 * h_fall / maxf(1.0, _fall_gravity_px_per_s2 * maxf(1.0, base_scale)))
	)
	_drop_land_x = spawn_pos.x + _drop_dir * _arc_dx_px * base_scale
	_drop_target_x = _drop_land_x + _drop_dir * _roll_distance_px * base_scale
	position = spawn_pos
	_apply_state()


func start_collect(collector_node: Node2D, center_offset_y: float = -40.0, fallback_target: Vector2 = Vector2.ZERO) -> bool:
	_ensure_nodes()
	if display_mode == "bag" or lifecycle_state == "collected" or lifecycle_state == "collecting":
		return false
	# Shift start position upward by half sprite height so switching to centered anchor has zero snap
	var anchor_shift := (_map_anchor_px.y - _bag_anchor_px.y) * base_scale
	_collect_start_pos = position - Vector2(0.0, anchor_shift)
	position = _collect_start_pos
	_collector_node = collector_node
	_collector_offset_y = center_offset_y
	_collect_fallback_target = fallback_target
	_collect_elapsed_s = 0.0
	lifecycle_state = "collecting"
	drop_subphase = "collecting"
	_apply_state()
	return true


func step_lifecycle(delta: float) -> void:
	var dt := maxf(0.0, delta)
	if lifecycle_state == "dropping":
		_drop_elapsed_s += dt
		var t_land := _rise_duration_s + _drop_fall_duration_s
		var t_end := t_land + _roll_duration_s
		if _drop_elapsed_s < _rise_duration_s:
			drop_subphase = "rise"
			var u := clampf(_drop_elapsed_s / maxf(0.001, _rise_duration_s), 0.0, 1.0)
			var ease_u := 1.0 - (1.0 - u) * (1.0 - u)
			position = Vector2(
				_drop_spawn_pos.x + _drop_dir * (_arc_dx_px * 0.5 * base_scale) * u,
				lerpf(_drop_spawn_pos.y, _drop_peak_y, ease_u)
			)
		elif _drop_elapsed_s < t_land:
			drop_subphase = "fall"
			var u := clampf((_drop_elapsed_s - _rise_duration_s) / maxf(0.001, _drop_fall_duration_s), 0.0, 1.0)
			position = Vector2(
				_drop_spawn_pos.x + _drop_dir * (_arc_dx_px * 0.5 * base_scale) * (1.0 + u),
				lerpf(_drop_peak_y, _drop_ground_y, u * u)
			)
		elif _drop_elapsed_s < t_end:
			drop_subphase = "roll"
			var u := clampf((_drop_elapsed_s - t_land) / maxf(0.001, _roll_duration_s), 0.0, 1.0)
			var ease_u := 1.0 - (1.0 - u) * (1.0 - u)
			position = Vector2(
				lerpf(_drop_land_x, _drop_target_x, ease_u),
				_drop_ground_y
			)
			if is_instance_valid(body_sprite):
				body_sprite.position = Vector2(0.0, -16.0)
				body_sprite.offset = Vector2(-16.0, -16.0)
				body_sprite.rotation = _drop_dir * _roll_angle_rad * ease_u
		else:
			position = Vector2(_drop_target_x, _drop_ground_y)
			lifecycle_state = "resting"
			drop_subphase = "rest"
			_apply_state()
			if is_instance_valid(sparkle_fx) and sparkle_fx.visible:
				sparkle_fx.frame = 0
				sparkle_fx.play(&"sparkle_fx")
	elif lifecycle_state == "collecting":
		_collect_elapsed_s += dt
		var t := clampf(_collect_elapsed_s / maxf(0.001, _pickup_duration_s), 0.0, 1.0)
		var tgt := _collector_node.position + Vector2(0.0, _collector_offset_y) if is_instance_valid(_collector_node) else _collect_fallback_target
		var pos_u := clampf(t * t * (1.35 - 0.35 * t), 0.0, 1.0)
		var lift := _pickup_arc_lift_px * sin(PI * t) * base_scale
		position = _collect_start_pos.lerp(tgt, pos_u) + Vector2(0.0, -lift)
		var cur_scale := maxf(0.0, lerpf(base_scale, base_scale * _pickup_end_scale_ratio, t))
		scale = Vector2(cur_scale, cur_scale)
		if t >= 1.0:
			lifecycle_state = "collected"
			drop_subphase = "collected"
			visible = false
			emit_signal("collected", ball_number)


func _process(delta: float) -> void:
	if Engine.is_editor_hint() or DisplayServer.get_name() == "headless":
		return
	if lifecycle_state == "dropping" or lifecycle_state == "collecting":
		step_lifecycle(delta)


func get_item_metrics() -> Dictionary:
	_ensure_nodes()
	return {
		"ball_number": ball_number,
		"display_mode": display_mode,
		"lifecycle_state": lifecycle_state,
		"drop_subphase": drop_subphase,
		"sparkle_enabled": sparkle_enabled,
		"sparkle_visible": is_instance_valid(sparkle_fx) and sparkle_fx.visible,
		"map_anchor_px": [_map_anchor_px.x, _map_anchor_px.y],
		"bag_anchor_px": [_bag_anchor_px.x, _bag_anchor_px.y],
		"body_offset": [body_sprite.offset.x, body_sprite.offset.y] if body_sprite != null else [0.0, 0.0],
		"sparkle_offset": [sparkle_fx.offset.x, sparkle_fx.offset.y] if sparkle_fx != null else [0.0, 0.0],
		"body_clip": str(body_sprite.animation) if body_sprite != null else "",
		"sparkle_clip": str(sparkle_fx.animation) if sparkle_fx != null else "",
	}
