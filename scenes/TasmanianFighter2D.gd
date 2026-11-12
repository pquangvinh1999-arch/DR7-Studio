extends "res://scenes/CharacterFighter2D.gd"
## The same 60Hz charge/projectile contract is consumed by the browser.
var charge_sprite: AnimatedSprite2D
var render_contract: Dictionary = {}
var body_anchor := Vector2.ZERO

func _ready() -> void:
	super._ready()
	charge_sprite = get_node_or_null("ChargeFX") as AnimatedSprite2D
	var meta = JSON.parse_string(FileAccess.get_file_as_string(engine_export_json))
	if meta is Dictionary:
		render_contract = meta.get("render_contract", {})
		var anchor = meta.get("anchor_px", [176, 224])
		body_anchor = Vector2(float(anchor[0]), float(anchor[1]))

func _process(_dt: float) -> void:
	if sprite == null or charge_sprite == null:
		return
	if String(sprite.animation) != String(render_contract.get("charge", {}).get("body_clip", "")):
		charge_sprite.visible = false
		return
	var tick := 0.0
	for i in range(sprite.frame):
		tick += sprite.sprite_frames.get_frame_duration(sprite.animation, i)
	tick += sprite.sprite_frames.get_frame_duration(sprite.animation, sprite.frame) * sprite.frame_progress
	render_power_tick(tick)

func _frame_at_tick(clip: StringName, tick: float) -> int:
	var count := sprite.sprite_frames.get_frame_count(clip)
	for i in range(count):
		var duration := sprite.sprite_frames.get_frame_duration(clip, i)
		if tick < duration:
			return i
		tick -= duration
	return maxi(0, count - 1)

func _show_fx(node: AnimatedSprite2D, clip: StringName, tick: float, point: Vector2, pivot: Vector2) -> void:
	node.stop()
	node.animation = clip
	node.frame = _frame_at_tick(clip, tick)
	node.offset = -pivot
	node.position = point - body_anchor
	node.visible = true

func render_power_tick(tick: float) -> void:
	var charge: Dictionary = render_contract.get("charge", {})
	var proj: Dictionary = render_contract.get("projectile", {})
	if charge.is_empty() or proj.is_empty():
		return
	var pivot_data = render_contract["fx_pivot_px"]
	var pivot := Vector2(float(pivot_data[0]), float(pivot_data[1]))
	var release := 0.0
	var body_clip := StringName(String(proj["body_clip"]))
	for i in range(int(proj["release_frame"])):
		release += sprite.sprite_frames.get_frame_duration(body_clip, i)
	charge_sprite.visible = false
	projectile_sprite.visible = false
	if tick < release:
		var body_frame := _frame_at_tick(body_clip, tick)
		var hand = charge["origin_canvas_px_by_frame"][body_frame]
		_show_fx(charge_sprite, StringName(String(charge["effect_clip"])), tick, Vector2(float(hand[0]), float(hand[1])), pivot)
	else:
		var elapsed := tick - release
		if elapsed < float(proj["lifetime_ticks"]):
			var origin = proj["origin_canvas_px"]
			var velocity = proj["velocity_px_per_tick"]
			var point := Vector2(float(origin[0]), float(origin[1])) + elapsed * Vector2(float(velocity[0]), float(velocity[1]))
			_show_fx(projectile_sprite, StringName(String(proj["projectile_clip"])), elapsed, point, pivot)
