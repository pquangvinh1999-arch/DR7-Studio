extends "res://scenes/CharacterFighter2D.gd"
## Target slashes have their own atlas clips; nothing is emitted from neck frills.
var slash_sprite: AnimatedSprite2D
var slash_contract: Dictionary = {}
var body_anchor := Vector2.ZERO
var slash_pivot := Vector2.ZERO
var target_canvas_px := Vector2.ZERO

func _ready() -> void:
	super._ready()
	slash_sprite = get_node_or_null("SlashFX") as AnimatedSprite2D
	var meta = JSON.parse_string(FileAccess.get_file_as_string(engine_export_json))
	if meta is Dictionary:
		var contract: Dictionary = meta.get("render_contract", {})
		slash_contract = contract.get("target_slashes", {})
		var anchor = meta.get("anchor_px", [176, 224])
		body_anchor = Vector2(float(anchor[0]), float(anchor[1]))
		var pivot = contract.get("fx_pivot_px", [176, 128])
		slash_pivot = Vector2(float(pivot[0]), float(pivot[1]))
		var target = slash_contract.get("default_target_canvas_px", [320, 168])
		target_canvas_px = Vector2(float(target[0]), float(target[1]))

func set_slash_target_canvas(point: Vector2) -> void:
	target_canvas_px = point

func set_slash_target_global(point: Vector2) -> void:
	target_canvas_px = to_local(point) + body_anchor

func _process(_dt: float) -> void:
	if sprite == null or slash_sprite == null:
		return
	if String(sprite.animation) != String(slash_contract.get("body_clip", "")):
		slash_sprite.visible = false
		return
	var tick := 0.0
	for i in range(sprite.frame):
		tick += sprite.sprite_frames.get_frame_duration(sprite.animation, i)
	tick += sprite.sprite_frames.get_frame_duration(sprite.animation, sprite.frame) * sprite.frame_progress
	render_power_tick(tick)

func render_power_tick(tick: float) -> void:
	if slash_sprite == null:
		return
	slash_sprite.visible = false
	for strike in slash_contract.get("strikes", []):
		var elapsed := tick - float(strike["at_tick"])
		if elapsed < 0.0 or elapsed >= float(strike["duration_ticks"]):
			continue
		var clip := StringName(String(strike["clip"]))
		slash_sprite.stop()
		slash_sprite.animation = clip
		var frame := 0
		while frame < sprite.sprite_frames.get_frame_count(clip) - 1:
			var duration := sprite.sprite_frames.get_frame_duration(clip, frame)
			if elapsed < duration:
				break
			elapsed -= duration
			frame += 1
		slash_sprite.frame = frame
		slash_sprite.offset = -slash_pivot
		slash_sprite.position = target_canvas_px - body_anchor
		slash_sprite.visible = true
		return
