extends "res://scenes/CharacterFighter2D.gd"
## Whole-body ground occlusion, target emergence, one growing mouth-condensing fireball and endpoint patrol.
signal combat_hit(kind: String, amount: int, target: Vector2)

var contract: Dictionary = {}
var creature: Dictionary = {}
var anchor := Vector2(176, 224)
var pivot := Vector2(176, 128)
@export var burrow_dust_scale: float = 2.65
var dust_sprite: AnimatedSprite2D
var fireball_sprite: AnimatedSprite2D
var target_ground_global := Vector2.ZERO
var target_override := false
var action_origin_global := Vector2.ZERO
var action_target_canvas := Vector2(304, 224)
var action_facing := 1.0
var bite_emitted := false
var fireball_emitted := false
var patrol_running := false
var patrol_min_x := 80.0
var patrol_max_x := 880.0

func _ready() -> void:
	super._ready()
	var meta = JSON.parse_string(FileAccess.get_file_as_string(engine_export_json))
	contract = meta.get("render_contract", {})
	creature = contract.get("chilopoda", {})
	anchor = _vec(creature.get("anchor_px", [176, 224]))
	pivot = _vec(contract.get("fx_pivot_px", [176, 128]))
	dust_sprite = get_node("DustFX") as AnimatedSprite2D
	fireball_sprite = get_node("FireballFX") as AnimatedSprite2D
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://scenes/ChilopodaGroundClip.gdshader")
	sprite.material = mat
	action_origin_global = global_position
	var stage_path := "res://assets/maps/rocky_plateau/arena-stage.json"
	if FileAccess.file_exists(stage_path):
		var stage_meta = JSON.parse_string(FileAccess.get_file_as_string(stage_path))
		if stage_meta is Dictionary:
			var gp = stage_meta.get("gameplay", {})
			if gp is Dictionary and gp.has("burrow_dust_scale_default"):
				burrow_dust_scale = clampf(float(gp["burrow_dust_scale_default"]), 1.0, 4.0)
	_hide_fx()

func _vec(value: Array) -> Vector2:
	return Vector2(float(value[0]), float(value[1]))

func set_combat_target_global(ground_point: Vector2) -> void:
	target_ground_global = ground_point
	target_override = true

func _capture_action() -> void:
	action_origin_global = global_position
	action_facing = -1.0 if scale.x < 0.0 else 1.0
	action_target_canvas = to_local(target_ground_global) + anchor if target_override else _vec(creature.get("target_ground_canvas_px", [304, 224]))
	bite_emitted = false
	fireball_emitted = false

func play_clip(clip_name: StringName) -> bool:
	if _turn_pending and clip_name != _turn_clip:
		return false
	if String(clip_name) in ["attack_light", "power_up", "hit", "ko"]:
		patrol_running = false
		_capture_action()
	_hide_fx()
	if sprite != null:
		sprite.visible = true
		sprite.position = Vector2.ZERO
		if sprite.material is ShaderMaterial:
			sprite.material.set_shader_parameter("clip_enabled", false)
	return super.play_clip(clip_name)

func _hide_fx() -> void:
	if dust_sprite != null:
		dust_sprite.visible = false
	if fireball_sprite != null:
		fireball_sprite.visible = false

func _frame_at_tick(clip: StringName, tick: float) -> int:
	var count := sprite.sprite_frames.get_frame_count(clip)
	for i in range(count):
		var duration := sprite.sprite_frames.get_frame_duration(clip, i)
		if tick < duration:
			return i
		tick -= duration
	return maxi(0, count - 1)

func _fx(node: AnimatedSprite2D, clip: StringName, tick: float, point: Vector2, angle := 0.0) -> void:
	_fx_frame(node, clip, _frame_at_tick(clip, tick), point, angle)

func _fx_frame(node: AnimatedSprite2D, clip: StringName, frame_idx: int, point: Vector2, angle := 0.0) -> void:
	if node == null or node.sprite_frames == null:
		return
	var count := node.sprite_frames.get_frame_count(clip)
	if count <= 0:
		return
	node.stop()
	node.animation = clip
	node.frame = clampi(frame_idx, 0, count - 1)
	node.offset = -pivot
	node.position = point - anchor
	node.rotation = angle
	node.scale = Vector2(burrow_dust_scale, burrow_dust_scale) if node == dust_sprite else Vector2.ONE
	node.visible = true

func _process(_dt: float) -> void:
	if sprite == null or creature.is_empty():
		return
	var tick := 0.0
	for i in range(sprite.frame):
		tick += sprite.sprite_frames.get_frame_duration(sprite.animation, i)
	tick += sprite.sprite_frames.get_frame_duration(sprite.animation, sprite.frame) * sprite.frame_progress
	render_action_tick(String(sprite.animation), tick)

func render_action_tick(clip: String, tick: float) -> void:
	if sprite == null or creature.is_empty():
		return
	var expected_frame := _frame_at_tick(StringName(clip), tick)
	if sprite.animation == StringName(clip) and sprite.frame != expected_frame:
		sprite.frame = expected_frame
	_hide_fx()
	sprite.visible = true
	sprite.position = Vector2.ZERO
	var mat = sprite.material as ShaderMaterial
	mat.set_shader_parameter("clip_enabled", false)
	if clip == String(creature["burrow"]["body_clip"]):
		_render_burrow(tick)
	elif creature.has("burrow_turn") and clip == String(creature["burrow_turn"]["body_clip"]):
		var turn: Dictionary = creature["burrow_turn"]
		if tick >= float(turn["hidden_start_tick"]) and _turn_pending:
			scale.x = -absf(scale.x) if _turn_target_left else absf(scale.x)
		_render_burrow(tick, turn)
	elif creature.has("fireball") and clip == String(creature["fireball"]["body_clip"]):
		_render_fireball(tick)

func _render_burrow(tick: float, b: Dictionary = {}) -> void:
	if b.is_empty():
		b = creature["burrow"]
	var relocate: bool = b.get("relocate", true)
	var dy := 0.0
	var dx := 0.0
	var pose := _frame_at_tick(StringName(b["body_clip"]), tick)
	var visible_depth := maxf(0.0, float(creature["ground_y"])-float(b["top_y_by_frame"][pose])-1.0)
	if tick >= float(b["dive_start_tick"]) and tick < float(b["hidden_start_tick"]):
		var t := clampf((tick - float(b["dive_start_tick"])) / (float(b["hidden_start_tick"]) - float(b["dive_start_tick"])), 0.0, 1.0)
		dy = visible_depth * t * t * (3.0 - 2.0 * t)
	sprite.visible = not (tick >= float(b["hidden_start_tick"]) and tick < float(b["emerge_start_tick"]))
	if tick >= float(b["emerge_start_tick"]):
		dx = action_target_canvas.x - float(b["bite_offset_x_px"]) - anchor.x if relocate else 0.0
		var t := clampf((tick - float(b["emerge_start_tick"])) / (float(b["emerge_end_tick"]) - float(b["emerge_start_tick"])), 0.0, 1.0)
		dy = visible_depth * (1.0 - t * t * (3.0 - 2.0 * t))
		if relocate:
			global_position = action_origin_global + Vector2(action_facing * dx, 0)
	sprite.position = Vector2(0, dy)
	sprite.material.set_shader_parameter("clip_enabled", true)
	sprite.material.set_shader_parameter("clip_y", -dy)
	var entry := float(b["entry_fx_start_tick"])
	var exit_tick := float(b["exit_fx_start_tick"])
	var lifetime := float(b["dust_lifetime_ticks"])
	if tick >= entry and tick < entry + lifetime:
		_fx(dust_sprite, StringName(b["dust_clip"]), tick-entry, anchor + Vector2(float(b.get("bite_offset_x_px", 0))-dx, 0))
	elif tick >= exit_tick and tick < exit_tick + lifetime:
		_fx(dust_sprite, StringName(b["dust_clip"]), tick-exit_tick, action_target_canvas - Vector2(dx, 0) if relocate else anchor)
	if b.has("bite_tick") and tick >= float(b["bite_tick"]) and not bite_emitted:
		bite_emitted = true
		combat_hit.emit("burrow_bite", 120, to_global(action_target_canvas - anchor - Vector2(dx, 0)))

func _render_fireball(tick: float) -> void:
	var f: Dictionary = creature["fireball"]
	var frame := _frame_at_tick(StringName(f["body_clip"]), tick)
	var charge_frames: Array = f.get("charge_frames", [0, 1, 2])
	var release_tick := float(f.get("release_tick", 16.0))
	var mouth_anchors: Array = f.get("mouth_anchors_by_frame", [])
	if mouth_anchors.is_empty():
		return
	if tick < release_tick:
		var charge_pos: Vector2 = _vec(mouth_anchors[mini(frame, mouth_anchors.size() - 1)])
		var charge_idx := int(charge_frames[mini(frame, charge_frames.size() - 1)])
		_fx_frame(fireball_sprite, StringName(f["projectile_clip"]), charge_idx, charge_pos)
		return
	var release_frame := mini(int(f.get("release_frame", 3)), mouth_anchors.size() - 1)
	var origin: Vector2 = _vec(mouth_anchors[release_frame])
	var target := action_target_canvas - Vector2(0, float(creature["target_hit_height_px"]))
	var delta := target - origin
	var min_ticks := float(f.get("min_flight_ticks", 14.0))
	var max_ticks := float(f.get("max_flight_ticks", 25.5))
	var speed := maxf(1.0, float(f.get("speed_px_per_tick", 26.0)))
	var raw_ticks := maxf(0.0, (delta.length() - float(f.get("target_radius_px", 2.0))) / speed)
	var flight_ticks := clampf(maxf(min_ticks, raw_ticks), min_ticks, max_ticks)
	var elapsed := tick - release_tick
	if elapsed < flight_ticks:
		var t := clampf(elapsed / maxf(1.0, flight_ticks), 0.0, 1.0)
		var point := origin.lerp(target, t)
		var flight_frames: Array = f.get("flight_frames", [3, 4, 5, 6, 7, 8, 9])
		var idx := mini(flight_frames.size() - 1, int(floor(t * float(flight_frames.size()))))
		_fx_frame(fireball_sprite, StringName(f["projectile_clip"]), int(flight_frames[idx]), point, delta.angle())
	elif not fireball_emitted:
		fireball_emitted = true
		combat_hit.emit("fireball", 250, to_global(target - anchor))

func start_patrol(minimum_x: float, maximum_x: float) -> void:
	patrol_min_x = minimum_x
	patrol_max_x = maximum_x
	patrol_running = true
	play_clip(&"walk")

func _physics_process(dt: float) -> void:
	advance_patrol(dt)

func advance_patrol(dt: float) -> void:
	if not patrol_running or _turn_pending:
		return
	var direction := -1.0 if scale.x < 0.0 else 1.0
	var loc: Dictionary = contract.get("locomotion", {})
	var patrol_cfg: Dictionary = loc.get("patrol", {})
	var speed := float(loc.get("speed_px_per_second", patrol_cfg.get("speed_px_per_second", 103.703704)))
	global_position.x = clampf(global_position.x + direction*speed*dt, patrol_min_x, patrol_max_x)
	if direction > 0.0 and global_position.x >= patrol_max_x:
		set_facing_left(true)
	elif direction < 0.0 and global_position.x <= patrol_min_x:
		set_facing_left(false)

func _on_skill_finished(clip_name: StringName) -> void:
	var was_turn := _turn_pending and clip_name == _turn_clip
	super._on_skill_finished(clip_name)
	if was_turn and patrol_running:
		play_clip(&"walk")
	elif String(clip_name) in ["attack_light", "power_up"]:
		play_clip(&"idle")
