class_name TRexFighter2D
extends "res://scenes/CharacterFighter2D.gd"
## T-rex fighter controller (`Combined 1-Layer`):
## - Supports bidirectional perspective turning (`turn`: right <-> left) without card-flip spin.
## - Preserves all v0.6.0 non-turn clips, timing, events, and `fireball_fx` behavior.
## - Supports continuous two-endpoint patrol (`walk->turn->walk` and `run->turn->run`) and manual reversal.

const DEFAULT_WALK_SPEED := 68.571429
const DEFAULT_RUN_SPEED := 108.0

var _patrol_active := false
var _patrol_min_x := 80.0
var _patrol_max_x := 880.0
var _patrol_speed := DEFAULT_WALK_SPEED
var _patrol_clip: StringName = &"walk"
var _patrol_dir := 1
var _post_turn_clip: StringName = &""

func _ensure_projectile_fx_node() -> void:
	if get_node_or_null("ProjectileFX") != null:
		return
	var body_sprite := get_node_or_null("Sprite") as AnimatedSprite2D
	if body_sprite == null or body_sprite.sprite_frames == null:
		return
	var meta := _get_cached_export_meta()
	var rc: Dictionary = meta.get("render_contract", {})
	var proj: Dictionary = rc.get("projectile", {})
	var proj_clip := StringName(String(proj.get("projectile_clip", "fireball_fx")))
	if not body_sprite.sprite_frames.has_animation(proj_clip):
		return
	var anchor_arr: Variant = meta.get("anchor_px", [176.0, 224.0])
	var pivot_arr: Variant = rc.get("fx_pivot_px", [176.0, 128.0])
	var origin_arr: Variant = proj.get("origin_canvas_px", [304.0, 138.0])
	var anchor := Vector2(float(anchor_arr[0]), float(anchor_arr[1])) if anchor_arr is Array and anchor_arr.size() >= 2 else Vector2(176.0, 224.0)
	var pivot := Vector2(float(pivot_arr[0]), float(pivot_arr[1])) if pivot_arr is Array and pivot_arr.size() >= 2 else Vector2(176.0, 128.0)
	var origin := Vector2(float(origin_arr[0]), float(origin_arr[1])) if origin_arr is Array and origin_arr.size() >= 2 else Vector2(304.0, 138.0)
	var pfx := AnimatedSprite2D.new()
	pfx.name = "ProjectileFX"
	pfx.visible = false
	pfx.position = origin - anchor
	pfx.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	pfx.sprite_frames = body_sprite.sprite_frames
	pfx.animation = proj_clip
	pfx.centered = false
	pfx.offset = -pivot
	add_child(pfx)

func _ensure_nodes() -> void:
	_ensure_projectile_fx_node()
	super._ensure_nodes()

func _physics_process(delta: float) -> void:
	if _patrol_active:
		step_patrol(delta)

func play_clip(clip_name: StringName) -> bool:
	_ensure_nodes()
	if clip_name != _turn_clip and clip_name != _patrol_clip and clip_name != &"idle" and clip_name != &"walk" and clip_name != &"run":
		_patrol_active = false
		_post_turn_clip = &""
	if projectile_sprite != null and clip_name in [&"power_up", &"hit", &"ko", _turn_clip]:
		projectile_sprite.visible = false
		projectile_sprite.stop()
		projectile_sprite.frame = 0
	return super.play_clip(clip_name)

func is_turning() -> bool:
	return _turn_pending

func is_facing_left() -> bool:
	return scale.x < 0.0

func _resolve_locomotion_speed(clip_name: StringName, requested_speed: float) -> float:
	if requested_speed > 0.0:
		return requested_speed
	return DEFAULT_RUN_SPEED if clip_name == &"run" else DEFAULT_WALK_SPEED

func start_patrol(min_x: float = 80.0, max_x: float = 880.0, speed: float = -1.0, clip_name: StringName = &"walk") -> bool:
	_ensure_nodes()
	if not has_clip(clip_name):
		return false
	_patrol_min_x = minf(min_x, max_x)
	_patrol_max_x = maxf(min_x, max_x)
	_patrol_speed = _resolve_locomotion_speed(clip_name, speed)
	_patrol_clip = clip_name
	_patrol_dir = -1 if is_facing_left() else 1
	_patrol_active = true
	position.x = clampf(position.x, _patrol_min_x, _patrol_max_x)
	if not _turn_pending:
		return play_clip(_patrol_clip)
	return true

func stop_patrol() -> void:
	_patrol_active = false
	_post_turn_clip = &""
	if not _turn_pending:
		play_clip(&"idle")

func move_in_direction(dir: int, clip_name: StringName = &"walk") -> bool:
	_ensure_nodes()
	if _turn_pending:
		return false
	if dir == 0:
		_post_turn_clip = &""
		return play_clip(&"idle")
	var target_left := dir < 0
	if is_facing_left() != target_left:
		_post_turn_clip = clip_name if has_clip(clip_name) else &"idle"
		return set_facing_left(target_left)
	if sprite != null and (sprite.animation != clip_name or not sprite.is_playing()):
		return play_clip(clip_name)
	return true

func step_patrol(delta: float) -> void:
	if not _patrol_active or _turn_pending or delta <= 0.0:
		return
	_ensure_nodes()
	if sprite != null and (sprite.animation != _patrol_clip or not sprite.is_playing()):
		play_clip(_patrol_clip)
	position.x += float(_patrol_dir) * _patrol_speed * delta
	if _patrol_dir > 0 and position.x >= _patrol_max_x:
		position.x = _patrol_max_x
		_patrol_dir = -1
		_post_turn_clip = _patrol_clip
		set_facing_left(true)
	elif _patrol_dir < 0 and position.x <= _patrol_min_x:
		position.x = _patrol_min_x
		_patrol_dir = 1
		_post_turn_clip = _patrol_clip
		set_facing_left(false)

func _on_skill_finished(clip_name: StringName) -> void:
	if _turn_pending and clip_name == _turn_clip:
		scale.x = -absf(scale.x) if _turn_target_left else absf(scale.x)
		_turn_pending = false
		var resume_clip: StringName = _post_turn_clip
		_post_turn_clip = &""
		if resume_clip == &"":
			resume_clip = StringName(String(get_meta("_arena_turn_resume_clip", "")))
		set_meta("_arena_turn_resume_clip", "")
		if resume_clip == &"":
			resume_clip = _patrol_clip if _patrol_active else &"idle"
		play_clip(resume_clip)
		if sprite != null and (resume_clip == &"walk" or resume_clip == &"run") and sprite.sprite_frames != null and sprite.sprite_frames.get_frame_count(resume_clip) > 1:
			sprite.frame = 1
		action_finished.emit(clip_name)
		return
	super._on_skill_finished(clip_name)
