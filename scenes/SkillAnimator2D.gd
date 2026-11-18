class_name SkillAnimator2D
extends Node2D
## Helper component đọc trực tiếp engine-export.json của Agent Sprite Forge
## và phát sự kiện gameplay (tell, hit, impact, end) chuẩn theo từng frame của AnimatedSprite2D.

signal skill_event(event_name: String, frame_index: int, at_ms: int, payload: Dictionary)
signal skill_finished(clip_name: StringName)

@export var sprite: AnimatedSprite2D
@export_file("*.json") var engine_export_json: String

var _clips_meta: Dictionary = {}
var _events_by_clip_frame: Dictionary = {}

func _ready() -> void:
	_ensure_initialized()

func _ensure_initialized() -> void:
	if _events_by_clip_frame.is_empty() and not engine_export_json.is_empty():
		load_export_metadata(engine_export_json)
	if sprite != null:
		if not sprite.frame_changed.is_connected(_on_frame_changed):
			sprite.frame_changed.connect(_on_frame_changed)
		if not sprite.animation_finished.is_connected(_on_animation_finished):
			sprite.animation_finished.connect(_on_animation_finished)

func load_export_metadata(json_path: String) -> bool:
	var f := FileAccess.open(json_path, FileAccess.READ)
	if f == null:
		push_error("SkillAnimator2D: Cannot open " + json_path)
		return false
	var parsed = JSON.parse_string(f.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY or not parsed.has("clips"):
		push_error("SkillAnimator2D: Invalid engine-export.json " + json_path)
		return false
	_clips_meta = parsed["clips"]
	_events_by_clip_frame.clear()
	for clip_name in _clips_meta.keys():
		var cmeta: Dictionary = _clips_meta[clip_name]
		var fmap: Dictionary = {}
		for ev in cmeta.get("events_ms", []):
			var pos := int(ev.get("position", -1))
			if not fmap.has(pos):
				fmap[pos] = []
			fmap[pos].append(ev)
		_events_by_clip_frame[clip_name] = fmap
	return true

func play_skill(clip_name: StringName) -> void:
	_ensure_initialized()
	if sprite == null:
		return
	sprite.play(clip_name)
	_emit_events_for_frame(String(clip_name), sprite.frame)

func _on_frame_changed() -> void:
	if sprite == null:
		return
	_emit_events_for_frame(String(sprite.animation), sprite.frame)

func _on_animation_finished() -> void:
	if sprite == null:
		return
	skill_finished.emit(sprite.animation)

func _emit_events_for_frame(clip_name: String, frame_idx: int) -> void:
	var fmap: Dictionary = _events_by_clip_frame.get(clip_name, {})
	if fmap.has(frame_idx):
		for ev in fmap[frame_idx]:
			skill_event.emit(
				String(ev.get("name", "")),
				frame_idx,
				int(ev.get("at_ms", 0)),
				ev.get("data", {})
			)
