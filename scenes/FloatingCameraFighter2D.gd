extends CharacterFighter2D
## Combined 1-Layer Floating Camera monster: source pose faces +X (muzzle flash on its right).

const PROJECTILE_SPEED_PX_PER_S := 380.0
const PROJECTILE_LIFETIME_S := 0.7

var _projectile_time_left := 0.0
var _projectile_dir := 1.0
var _projectile_scale := 1.0
var external_projectile_managed: bool = false


func _get_projectile_origin_local() -> Vector2:
	var meta := _get_cached_export_meta()
	var proj: Dictionary = meta.get("render_contract", {}).get("projectile", {})
	var arr: Variant = proj.get("origin_local_px", [21.0, -6.0])
	if arr is Array and arr.size() >= 2:
		return Vector2(float(arr[0]), float(arr[1]))
	return Vector2(21.0, -6.0)


func _get_projectile_speed() -> float:
	var meta := _get_cached_export_meta()
	var proj: Dictionary = meta.get("render_contract", {}).get("projectile", {})
	var vel: Variant = proj.get("velocity_px_per_second", [PROJECTILE_SPEED_PX_PER_S, 0.0])
	if vel is Array and vel.size() >= 1 and float(vel[0]) > 0.0:
		return float(vel[0])
	return PROJECTILE_SPEED_PX_PER_S


func play_clip(clip_name: StringName) -> bool:
	if _turn_pending and clip_name != _turn_clip:
		return false
	_ensure_nodes()
	if sprite == null or sprite.sprite_frames == null:
		return false
	if not sprite.sprite_frames.has_animation(clip_name):
		return false
	if clip_name != &"ko":
		sprite.visible = true
	# Keep an active shot flying smoothly when returning to idle/walk hover after attack_light.
	if _projectile_time_left > 0.0 and (clip_name == &"idle" or clip_name == &"walk"):
		if animator != null:
			animator.play_skill(clip_name)
		else:
			sprite.play(clip_name)
		return true
	_projectile_time_left = 0.0
	if projectile_sprite != null:
		projectile_sprite.top_level = false
	return super.play_clip(clip_name)


func _physics_process(delta: float) -> void:
	if _projectile_time_left <= 0.0 or projectile_sprite == null:
		return
	_projectile_time_left -= delta
	var previous_projectile_pos := projectile_sprite.global_position
	projectile_sprite.global_position.x += _projectile_dir * _get_projectile_speed() * _projectile_scale * delta
	var stage := get_tree().current_scene
	var terrain_hit := stage != null and stage.has_method("terrain_blocks_segment") and bool(stage.call("terrain_blocks_segment", previous_projectile_pos, projectile_sprite.global_position))
	if terrain_hit or _projectile_time_left <= 0.0:
		_projectile_time_left = 0.0
		projectile_sprite.visible = false
		projectile_sprite.stop()
		projectile_sprite.top_level = false


func _on_skill_event(event_name: String, frame_index: int, at_ms: int, payload: Dictionary) -> void:
	if external_projectile_managed:
		action_event.emit(event_name, frame_index, at_ms, payload)
		return
	super._on_skill_event(event_name, frame_index, at_ms, payload)
	if event_name == "custom:launch" and projectile_sprite != null:
		var origin := _get_projectile_origin_local()
		var mag_x := absf(scale.x) if not is_zero_approx(scale.x) else 1.0
		var mag_y := absf(scale.y) if not is_zero_approx(scale.y) else 1.0
		_projectile_dir = -1.0 if scale.x < 0.0 else 1.0
		_projectile_scale = mag_x
		projectile_sprite.top_level = true
		projectile_sprite.z_index = 12
		projectile_sprite.scale = Vector2(_projectile_dir * mag_x, mag_y)
		projectile_sprite.global_position = global_position + Vector2(origin.x * _projectile_dir * mag_x, origin.y * mag_y)
		_projectile_time_left = PROJECTILE_LIFETIME_S


func _on_skill_finished(clip_name: StringName) -> void:
	super._on_skill_finished(clip_name)
	if external_projectile_managed:
		if clip_name == &"ko" and sprite != null:
			sprite.visible = false
		return
	if clip_name == &"hit":
		play_clip(&"ko")
	elif clip_name == &"ko":
		if sprite != null:
			sprite.visible = false
