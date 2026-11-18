class_name CharacterFighter2D
extends Node2D
## Prefab nhân vật chuẩn 1-Layer Combined của DR7-Studio trên Godot 4:
## - Đọc trực tiếp SpriteFrames (.tres) + engine-export.json (Nearest 1:1, khoá tâm chân offset = -anchor_px).
## - Chạy 100% Godot 4 GDScript trên Compatibility renderer (ADR-0001; không dùng GDExtension ở quy mô <= 50 thực thể/khu).

signal action_event(event_name: String, frame_index: int, at_ms: int, payload: Dictionary)
signal action_finished(clip_name: StringName)

@export var character_id: String = ""
@export_file("*.json") var engine_export_json: String = ""

var sprite: AnimatedSprite2D = null
var projectile_sprite: AnimatedSprite2D = null
var animator: SkillAnimator2D = null
var _turn_pending := false
var _turn_target_left := false
var _turn_clip: StringName = &""
var _cached_export_meta: Dictionary = {}
var _cached_export_path: String = ""

func _get_cached_export_meta() -> Dictionary:
	if engine_export_json.is_empty():
		return {}
	if _cached_export_path == engine_export_json and not _cached_export_meta.is_empty():
		return _cached_export_meta
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(engine_export_json))
	if parsed is Dictionary:
		_cached_export_meta = parsed
		_cached_export_path = engine_export_json
		return _cached_export_meta
	return {}

func set_facing_left(target_left: bool) -> bool:
	_ensure_nodes()
	if _turn_pending:
		return false
	if (scale.x < 0.0) == target_left:
		return true
	var meta := _get_cached_export_meta()
	if meta.is_empty():
		return false
	var turning = meta.get("render_contract", {}).get("turning", {})
	var raw_clip = turning.get("clip", "") if turning is Dictionary else ""
	_turn_clip = StringName(raw_clip if raw_clip is String else "")
	if _turn_clip == &"" or not has_clip(_turn_clip):
		if turning is Dictionary and str(turning.get("method", "")) == "instant_flip":
			var mag_x := absf(scale.x) if not is_zero_approx(scale.x) else 1.0
			scale.x = -mag_x if target_left else mag_x
			return true
		return false
	_turn_target_left = target_left
	_turn_pending = true
	return play_clip(_turn_clip)

func _ready() -> void:
	_ensure_nodes()

func _ensure_nodes() -> void:
	_get_cached_export_meta()
	if sprite == null:
		sprite = get_node_or_null("Sprite") as AnimatedSprite2D
	if projectile_sprite == null:
		projectile_sprite = get_node_or_null("ProjectileFX") as AnimatedSprite2D
		if projectile_sprite != null and not projectile_sprite.animation_finished.is_connected(_on_projectile_finished):
			projectile_sprite.animation_finished.connect(_on_projectile_finished)
	if animator == null:
		animator = get_node_or_null("SkillAnimator") as SkillAnimator2D
	if animator != null and sprite != null:
		animator.sprite = sprite
		animator.engine_export_json = engine_export_json
		animator._ensure_initialized()
		if not animator.skill_event.is_connected(_on_skill_event):
			animator.skill_event.connect(_on_skill_event)
		if not animator.skill_finished.is_connected(_on_skill_finished):
			animator.skill_finished.connect(_on_skill_finished)

func play_clip(clip_name: StringName) -> bool:
	if _turn_pending and clip_name != _turn_clip:
		return false
	_ensure_nodes()
	if sprite == null or sprite.sprite_frames == null:
		return false
	if not sprite.sprite_frames.has_animation(clip_name):
		return false
	if projectile_sprite != null:
		projectile_sprite.visible = false
		projectile_sprite.stop()
	if animator != null:
		animator.play_skill(clip_name)
	else:
		sprite.play(clip_name)
	return true

func has_clip(clip_name: StringName) -> bool:
	_ensure_nodes()
	return sprite != null and sprite.sprite_frames != null and sprite.sprite_frames.has_animation(clip_name)

func list_clips() -> PackedStringArray:
	_ensure_nodes()
	if sprite == null or sprite.sprite_frames == null:
		return PackedStringArray()
	return sprite.sprite_frames.get_animation_names()

func _on_skill_event(event_name: String, frame_index: int, at_ms: int, payload: Dictionary) -> void:
	if projectile_sprite != null and payload.has("projectile"):
		var proj_clip := StringName(String(payload["projectile"]))
		if projectile_sprite.sprite_frames != null and projectile_sprite.sprite_frames.has_animation(proj_clip):
			projectile_sprite.visible = true
			projectile_sprite.frame = 0
			projectile_sprite.play(proj_clip)
	action_event.emit(event_name, frame_index, at_ms, payload)

func _on_projectile_finished() -> void:
	if projectile_sprite != null:
		projectile_sprite.visible = false

func _on_skill_finished(clip_name: StringName) -> void:
	if _turn_pending and clip_name == _turn_clip:
		scale.x = -absf(scale.x) if _turn_target_left else absf(scale.x)
		_turn_pending = false
		var arena_resume := String(get_meta("_arena_turn_resume_clip", ""))
		if not arena_resume.is_empty():
			set_meta("_arena_turn_resume_clip", "")
			var r_clip := StringName(arena_resume)
			if has_clip(r_clip):
				play_clip(r_clip)
				if sprite != null and (r_clip == &"walk" or r_clip == &"run" or r_clip == &"fly") and sprite.sprite_frames.get_frame_count(r_clip) > 1:
					sprite.frame = 1
				action_finished.emit(clip_name)
				return
		play_clip(&"idle")
	action_finished.emit(clip_name)
