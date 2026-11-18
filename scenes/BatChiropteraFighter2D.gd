class_name BatChiropteraFighter2D
extends "res://scenes/CharacterFighter2D.gd"
## Bat - Chiroptera fighter controller:
## - Supports bidirectional perspective turning (`turn`: right <-> left) without card-flip spin.
## - Preserves all existing non-turn clips, timing, events, and purple sonic_screech_fx behavior.
## - Supports continuous two-endpoint patrol (`walk->turn->walk` and `run->turn->run`) and manual reversal.

var _patrol_active := false
var _patrol_min_x := 80.0
var _patrol_max_x := 880.0
var _patrol_speed := 104.545455
var _patrol_clip: StringName = &"walk"
var _patrol_dir := 1
var _post_turn_clip: StringName = &""

func _physics_process(delta: float) -> void:
	if _patrol_active:
		step_patrol(delta)

func play_clip(clip_name: StringName) -> bool:
	if clip_name != _turn_clip and clip_name != _patrol_clip and clip_name != &"idle" and clip_name != &"walk" and clip_name != &"run":
		_patrol_active = false
		_post_turn_clip = &""
	return super.play_clip(clip_name)

func is_turning() -> bool:
	return _turn_pending

func is_facing_left() -> bool:
	return scale.x < 0.0

func start_patrol(min_x: float = 80.0, max_x: float = 880.0, speed: float = 104.545455, clip_name: StringName = &"walk") -> bool:
	_ensure_nodes()
	if not has_clip(clip_name):
		return false
	_patrol_min_x = minf(min_x, max_x)
	_patrol_max_x = maxf(min_x, max_x)
	_patrol_speed = maxf(1.0, speed)
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
