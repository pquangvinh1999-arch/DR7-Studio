class_name CharacterFighter2D
extends Node2D
## Prefab nhân vật chuẩn 1-Layer Combined của DR7-Studio trên Godot 4:
## - Đọc trực tiếp SpriteFrames (.tres) + engine-export.json (Nearest 1:1, khoá tâm chân offset = -anchor_px).
## - Tương thích 100% với kiến trúc Godot 4 Client + Lõi Rust Core (GDExtension / MultiMeshInstance2D).

signal action_event(event_name: String, frame_index: int, at_ms: int, payload: Dictionary)
signal action_finished(clip_name: StringName)

@export var character_id: String = "trunks_rage"
@export_file("*.json") var engine_export_json: String = "res://assets/trunks_rage/godot_bundle/engine-export.json"

var sprite: AnimatedSprite2D = null
var animator: SkillAnimator2D = null

func _ready() -> void:
	_ensure_nodes()

func _ensure_nodes() -> void:
	if sprite == null:
		sprite = get_node_or_null("Sprite") as AnimatedSprite2D
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
	_ensure_nodes()
	if sprite == null or sprite.sprite_frames == null:
		return false
	if not sprite.sprite_frames.has_animation(clip_name):
		return false
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
	action_event.emit(event_name, frame_index, at_ms, payload)

func _on_skill_finished(clip_name: StringName) -> void:
	action_finished.emit(clip_name)
