extends "res://scenes/CharacterFighter2D.gd"
## Whole-body ground occlusion, target emergence, two red bolts and endpoint patrol.
signal combat_hit(kind: String, amount: int, target: Vector2)

var contract: Dictionary = {}
var creature: Dictionary = {}
var anchor := Vector2(176, 224)
var pivot := Vector2(176, 128)
var dust_sprite: AnimatedSprite2D
var glows: Array[AnimatedSprite2D] = []
var lasers: Array[AnimatedSprite2D] = []
var target_ground_global := Vector2.ZERO
var target_override := false
var action_origin_global := Vector2.ZERO
var action_target_canvas := Vector2(304, 224)
var action_facing := 1.0
var bite_emitted := false
var laser_emitted := [false, false]
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
	glows = [get_node("Glow0") as AnimatedSprite2D, get_node("Glow1") as AnimatedSprite2D]
	lasers = [get_node("Laser0") as AnimatedSprite2D, get_node("Laser1") as AnimatedSprite2D]
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://scenes/ChilopodaGroundClip.gdshader")
	sprite.material = mat
	action_origin_global = global_position
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
	laser_emitted = [false, false]

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
	for node in glows + lasers:
		node.visible = false

func _frame_at_tick(clip: StringName, tick: float) -> int:
	var count := sprite.sprite_frames.get_frame_count(clip)
	for i in range(count):
		var duration := sprite.sprite_frames.get_frame_duration(clip, i)
		if tick < duration:
			return i
		tick -= duration
	return maxi(0, count - 1)

func _fx(node: AnimatedSprite2D, clip: StringName, tick: float, point: Vector2, angle := 0.0) -> void:
	node.stop()
	node.animation = clip
	node.frame = _frame_at_tick(clip, tick)
	node.offset = -pivot
	node.position = point - anchor
	node.rotation = angle
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
	elif clip == String(creature["laser"]["body_clip"]):
		_render_laser(tick)

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

func _render_laser(tick: float) -> void:
	var l: Dictionary = creature["laser"]
	var frame := _frame_at_tick(StringName(l["body_clip"]), tick)
	if tick < float(l["glow_end_tick"]):
		var phase := mini(3, int(tick/4.0)) if tick < float(l["release_tick"]) else mini(5, 4+int((tick-float(l["release_tick"]))/4.0))
		for i in range(2):
			_fx(glows[i], StringName(l["glow_clip"]), float(phase*2), _vec(l["tip_anchors_by_frame"][frame][i]))
	if tick < float(l["release_tick"]):
		return
	var target := action_target_canvas - Vector2(0, float(creature["target_hit_height_px"]))
	for i in range(2):
		var origin := _vec(l["tip_anchors_by_frame"][int(l["release_frame"])][i])
		var delta := target - origin
		var elapsed := tick - float(l["release_tick"])
		var arrival := float(l["release_tick"]) + maxf(0.0, (delta.length()-float(l["target_radius_px"]))/float(l["speed_px_per_tick"]))
		if tick < arrival:
			var point := origin + delta.normalized() * float(l["speed_px_per_tick"]) * elapsed
			_fx(lasers[i], StringName(l["projectile_clip"]), fmod(elapsed, 4.0), point, delta.angle())
		elif not laser_emitted[i]:
			laser_emitted[i] = true
			combat_hit.emit("red_laser_%d" % i, 125, to_global(target-anchor))

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
	var speed := float(contract["locomotion"]["patrol"]["speed_px_per_second"])
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
