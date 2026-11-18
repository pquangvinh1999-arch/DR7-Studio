extends Node2D
## Combined 1-Layer Drum fighter prefab with independent GBA electric charge/orb FX & 60Hz ticks.

@export var character_id: String = "drum"
@export_file("*.json") var engine_export_json: String = "res://assets/drum/godot_bundle/engine-export.json"

var sprite: AnimatedSprite2D = null
var charge_fx: AnimatedSprite2D = null
var projectile_fx: AnimatedSprite2D = null
var skill_animator: Node2D = null
var _nodes_initialized: bool = false

var facing_left: bool = false
var _turn_pending: bool = false
var _anchor_px: Vector2 = Vector2(56.0, 84.0)
var _fx_pivot_px: Vector2 = Vector2(64.0, 48.0)
var _orb_origin_local: Vector2 = Vector2(42.0, -28.0)
var _orb_active: bool = false
var _orb_dir: float = 1.0
var _orb_elapsed_s: float = 0.0
var _orb_lifetime_s: float = 0.45
var _orb_speed_px_per_s: float = 1260.0
var _orb_released: bool = false
var external_orb_managed: bool = false


func _ensure_nodes() -> void:
	if _nodes_initialized and is_instance_valid(sprite):
		return
	sprite = get_node_or_null("Sprite") as AnimatedSprite2D
	charge_fx = get_node_or_null("ChargeFX") as AnimatedSprite2D
	projectile_fx = get_node_or_null("ProjectileFX") as AnimatedSprite2D
	skill_animator = get_node_or_null("SkillAnimator")
	if is_instance_valid(sprite):
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		sprite.centered = false
		sprite.offset = -_anchor_px
		if not sprite.animation_finished.is_connected(_on_body_animation_finished):
			sprite.animation_finished.connect(_on_body_animation_finished)
	if is_instance_valid(charge_fx):
		charge_fx.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		charge_fx.centered = false
		charge_fx.offset = -_fx_pivot_px
		charge_fx.visible = false
	if is_instance_valid(projectile_fx):
		projectile_fx.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		projectile_fx.centered = false
		projectile_fx.offset = -_fx_pivot_px
		projectile_fx.visible = false
	_nodes_initialized = is_instance_valid(sprite)


func _ready() -> void:
	_ensure_nodes()


func set_facing_left(left: bool) -> bool:
	_ensure_nodes()
	facing_left = left
	var dir_x := -1.0 if left else 1.0
	if is_instance_valid(sprite):
		sprite.flip_h = left
	if is_instance_valid(charge_fx):
		charge_fx.flip_h = left
		charge_fx.position = Vector2(_orb_origin_local.x * dir_x, _orb_origin_local.y)
	if is_instance_valid(projectile_fx) and not _orb_active:
		projectile_fx.flip_h = left
		projectile_fx.position = Vector2(_orb_origin_local.x * dir_x, _orb_origin_local.y)
	return true


func has_clip(clip_name: StringName) -> bool:
	_ensure_nodes()
	return is_instance_valid(sprite) and sprite.sprite_frames != null and sprite.sprite_frames.has_animation(clip_name)


func play_clip(clip_name: StringName) -> bool:
	if not has_clip(clip_name):
		return false
	sprite.play(clip_name)
	_orb_released = false
	if is_instance_valid(charge_fx):
		if clip_name == &"power_up":
			var dir_x := -1.0 if facing_left else 1.0
			charge_fx.position = Vector2(_orb_origin_local.x * dir_x, _orb_origin_local.y)
			charge_fx.flip_h = facing_left
			charge_fx.visible = true
			charge_fx.play(&"electric_ring_fx")
		else:
			charge_fx.visible = false
			charge_fx.stop()
	return true


func _process(delta: float) -> void:
	if not external_orb_managed and is_instance_valid(sprite) and sprite.animation == &"power_up" and sprite.is_playing():
		if sprite.frame >= 10 and not _orb_released:
			_orb_released = true
			_launch_electric_orb()
	if _orb_active and is_instance_valid(projectile_fx):
		_orb_elapsed_s += delta
		var previous_orb_pos := projectile_fx.global_position
		projectile_fx.position.x += _orb_dir * _orb_speed_px_per_s * delta
		var stage := get_tree().current_scene
		var terrain_hit := stage != null and stage.has_method("terrain_blocks_segment") and bool(stage.call("terrain_blocks_segment", previous_orb_pos, projectile_fx.global_position))
		if terrain_hit or _orb_elapsed_s >= _orb_lifetime_s:
			_orb_active = false
			projectile_fx.visible = false
			projectile_fx.stop()


func _launch_electric_orb() -> void:
	if not is_instance_valid(projectile_fx):
		return
	_orb_dir = -1.0 if facing_left else 1.0
	_orb_elapsed_s = 0.0
	_orb_active = true
	projectile_fx.position = Vector2(_orb_origin_local.x * _orb_dir, _orb_origin_local.y)
	projectile_fx.flip_h = facing_left
	projectile_fx.visible = true
	projectile_fx.play("electric_orb_fx")


func _on_body_animation_finished() -> void:
	if is_instance_valid(charge_fx):
		charge_fx.visible = false
		charge_fx.stop()
	if is_instance_valid(sprite) and sprite.sprite_frames and sprite.sprite_frames.has_animation(&"idle"):
		sprite.play(&"idle")
