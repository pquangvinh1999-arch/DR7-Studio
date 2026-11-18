extends "res://scenes/CharacterFighter2D.gd"
## The same 60Hz charge/projectile contract is consumed by the browser.
var charge_sprite: AnimatedSprite2D
var render_contract: Dictionary = {}
var body_anchor := Vector2.ZERO
var _contract_loaded: bool = false
## Initial/respawn facing ("default" -> contract default "right", or explicit "right"/"left"); locked for this life when sideways.
@export_enum("default", "right", "left") var spawn_facing: String = "default"
var _spawn_facing_locked_left: bool = false
var _spawn_facing_initialized: bool = false
var _patrol_active: bool = false
var _patrol_min_x: float = 80.0
var _patrol_max_x: float = 880.0
var _patrol_speed: float = 135.0
var _patrol_dir: int = 1
var _patrol_clip: StringName = &"walk"

func _ensure_contract_loaded() -> void:
	if _contract_loaded:
		return
	if engine_export_json.is_empty():
		return
	var meta = JSON.parse_string(FileAccess.get_file_as_string(engine_export_json))
	if meta is Dictionary:
		render_contract = meta.get("render_contract", {})
		var anchor = meta.get("anchor_px", [176, 224])
		body_anchor = Vector2(float(anchor[0]), float(anchor[1]))
		_contract_loaded = true

func _ready() -> void:
	super._ready()
	charge_sprite = get_node_or_null("ChargeFX") as AnimatedSprite2D
	_ensure_contract_loaded()

func _process(_dt: float) -> void:
	_ensure_spawn_facing_initialized()
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


func _physics_process(delta: float) -> void:
	_ensure_spawn_facing_initialized()
	if _patrol_active:
		step_patrol(delta)


func _locomotion_contract() -> Dictionary:
	_ensure_contract_loaded()
	var loc = render_contract.get("locomotion", {})
	return loc if typeof(loc) == TYPE_DICTIONARY else {}


func _has_turn_clip() -> bool:
	_ensure_contract_loaded()
	var raw_clip = render_contract.get("turning", {}).get("clip", "")
	var turn_clip := StringName(raw_clip if raw_clip is String else "")
	return turn_clip != &"" and has_clip(turn_clip)


## Returns true only when contract explicitly locks facing (no turn and no horizontal flip allowed).
func is_facing_locked() -> bool:
	var loc := _locomotion_contract()
	if bool(loc.get("lock_spawn_facing", false)) or bool(loc.get("sideways_strafe", false)):
		return true
	return loc.has("allow_turn_or_flip") and not bool(loc.get("allow_turn_or_flip", true))


## Canonical default initial/respawn facing from engine-export.json ("right" unless configured "left").
func default_spawn_facing() -> String:
	var loc := _locomotion_contract()
	var df := String(loc.get("default_spawn_facing", "right"))
	return "left" if df == "left" else "right"


func _set_root_flip_left(facing_left: bool) -> void:
	var mag := absf(scale.x)
	if is_zero_approx(mag):
		mag = 1.0
	scale.x = -mag if facing_left else mag


func _apply_locked_facing(facing_left: bool) -> void:
	_spawn_facing_locked_left = facing_left
	_spawn_facing_initialized = true
	spawn_facing = "left" if facing_left else "right"
	_set_root_flip_left(facing_left)


func _ensure_spawn_facing_initialized() -> void:
	if _spawn_facing_initialized or not is_facing_locked():
		return
	var chosen := spawn_facing if (spawn_facing == "left" or spawn_facing == "right") else default_spawn_facing()
	_apply_locked_facing(chosen == "left")


## Initialize facing at spawn or respawn; locked sideways characters keep this facing, unlocked rotate/flip freely.
func spawn_with_facing(target_facing: String = "") -> String:
	var chosen := target_facing
	if chosen != "left" and chosen != "right":
		chosen = default_spawn_facing()
	if is_facing_locked():
		_apply_locked_facing(chosen == "left")
	else:
		spawn_facing = chosen
		_turn_pending = false
		_set_root_flip_left(chosen == "left")
	return chosen


## Respawn at spawn_pos with optional facing ("right" | "left"; defaults to default_spawn_facing()) and reset idle.
func respawn(spawn_pos: Vector2, target_facing: String = "") -> String:
	position = spawn_pos
	_patrol_active = false
	var chosen := spawn_with_facing(target_facing)
	play_clip(&"idle")
	return chosen


func is_facing_left() -> bool:
	if is_facing_locked():
		_ensure_spawn_facing_initialized()
		return _spawn_facing_locked_left
	return scale.x < 0.0


func get_facing_name() -> String:
	return "left" if is_facing_left() else "right"


func set_facing_left(target_left: bool) -> bool:
	if is_facing_locked():
		_ensure_spawn_facing_initialized()
		_set_root_flip_left(_spawn_facing_locked_left)
		return _spawn_facing_locked_left == target_left
	if _has_turn_clip():
		return super.set_facing_left(target_left)
	_turn_pending = false
	_set_root_flip_left(target_left)
	return true


func _play_locomotion_cycle_if_needed(clip_name: StringName) -> bool:
	var body := get_node_or_null("Sprite") as AnimatedSprite2D
	if body != null and body.animation == clip_name and body.is_playing():
		return true
	return play_clip(clip_name)


## Move in direction dir (-1 left, +1 right, 0 idle); uses perspective turn when present, else mirrors horizontally.
func move_in_direction(dir: int, clip_name: StringName = &"walk") -> bool:
	_ensure_spawn_facing_initialized()
	if dir == 0:
		return play_clip(&"idle")
	if is_facing_locked():
		_set_root_flip_left(_spawn_facing_locked_left)
		return _play_locomotion_cycle_if_needed(clip_name)
	var target_left := dir < 0
	if is_facing_left() != target_left:
		if _has_turn_clip():
			return super.set_facing_left(target_left)
		_set_root_flip_left(target_left)
	return _play_locomotion_cycle_if_needed(clip_name)


## Start two-way patrol between bounds; flips horizontally without turn when character has no turn clip.
func start_patrol(min_x: float = 80.0, max_x: float = 880.0, speed: float = 135.0, clip_name: StringName = &"walk") -> bool:
	_ensure_spawn_facing_initialized()
	_patrol_min_x = min_x
	_patrol_max_x = max_x
	_patrol_speed = speed
	_patrol_clip = clip_name
	_patrol_dir = -1 if is_facing_left() else 1
	_patrol_active = true
	return move_in_direction(_patrol_dir, _patrol_clip)


func stop_patrol() -> void:
	_patrol_active = false
	play_clip(&"idle")


func step_patrol(delta: float) -> void:
	if not _patrol_active or _turn_pending:
		return
	position.x = clampf(position.x + float(_patrol_dir) * _patrol_speed * delta, _patrol_min_x, _patrol_max_x)
	if (_patrol_dir > 0 and position.x >= _patrol_max_x) or (_patrol_dir < 0 and position.x <= _patrol_min_x):
		_patrol_dir = -_patrol_dir
		if is_facing_locked():
			_set_root_flip_left(_spawn_facing_locked_left)
		else:
			set_facing_left(_patrol_dir < 0)
			if not _has_turn_clip():
				_play_locomotion_cycle_if_needed(_patrol_clip)
