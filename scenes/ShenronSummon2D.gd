class_name ShenronSummon2D
extends Node2D
## Shared JSON60Hz ritual; props remain separate from Shenron's combined body.
const CONTRACT := "res://assets/rituals/shenron_summon/sequence.json"
signal summon_ready
signal wish_selected(wish: Dictionary)
signal dismissed

var config: Dictionary = {}
var body_export: Dictionary = {}
var atlas: Texture2D
var tick: float = 0.0
var active: bool = false
var dismissing: bool = false
var dismiss_tick: float = 0.0
var selected_wish: Dictionary = {}
var _ready_emitted: bool = false
var manual_clock: bool = false
var origin: Vector2 = Vector2.ZERO
var dragon: Node2D
var dragon_sprite: AnimatedSprite2D
var flash_overlay: ColorRect
var dissolve_material: ShaderMaterial

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	z_index = 40
	var flash_layer := CanvasLayer.new()
	flash_layer.layer = 90
	add_child(flash_layer)
	flash_overlay = ColorRect.new()
	flash_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	flash_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	flash_overlay.color = Color(1, 1, 1, 0)
	flash_layer.add_child(flash_overlay)
	config = JSON.parse_string(FileAccess.get_file_as_string(CONTRACT))
	atlas = load("res://" + str(config["atlas"])) as Texture2D
	body_export = JSON.parse_string(FileAccess.get_file_as_string("res://" + str(config["behavior"]["body_bundle"])))

func start_from(caster_origin: Vector2) -> bool:
	if active or config.is_empty():
		return false
	if dragon == null:
		var roster: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/roster.json"))
		for entry in roster.get("characters", []):
			if entry["character_id"] == config["behavior"]["dragon_character_id"]:
				var prefab := load(str(entry["modes"]["combined_1layer"]["godot_prefab"])) as PackedScene
				dragon = prefab.instantiate() as Node2D
				add_child(dragon)
				dragon_sprite = dragon.get_node("Sprite") as AnimatedSprite2D
				dissolve_material = ShaderMaterial.new()
				dissolve_material.shader = load("res://scenes/ShenronPixelDissolve.gdshader")
				var reveal: Dictionary = config["reveal"]
				var mask_size_arr: Array = reveal["mask_size_px"]
				dissolve_material.set_shader_parameter("threshold_mask", load("res://" + str(reveal["mask"])))
				dissolve_material.set_shader_parameter("canvas_anchor", -dragon_sprite.offset)
				dissolve_material.set_shader_parameter("mask_size", Vector2(float(mask_size_arr[0]), float(mask_size_arr[1])))
				dissolve_material.set_shader_parameter("cell_size", float(reveal["cell_size_canvas_px"]))
				dissolve_material.set_shader_parameter("edge_width", float(reveal["edge_width"]))
				var rgb: Array = reveal["edge_color_rgb"]
				dissolve_material.set_shader_parameter("edge_color", Color(float(rgb[0])/255.0, float(rgb[1])/255.0, float(rgb[2])/255.0))
				dragon_sprite.material = dissolve_material
				break
	if dragon == null:
		return false
	origin = caster_origin
	tick = 0.0
	dismissing = false
	dismiss_tick = 0.0
	selected_wish = {}
	_ready_emitted = false
	active = true
	seek_tick(0.0)
	return true

func dismiss() -> void:
	active = false
	dismissing = false
	dismiss_tick = 0.0
	selected_wish = {}
	_ready_emitted = false
	if flash_overlay != null:
		flash_overlay.color.a = 0.0
	if dragon != null:
		dragon.visible = false
	queue_redraw()
	dismissed.emit()

func begin_dismiss() -> bool:
	if not active or dismissing or config.is_empty():
		return false
	dismissing = true
	dismiss_tick = 0.0
	seek_dismiss_tick(0.0)
	return true

func is_ready_for_wish() -> bool:
	if not active or dismissing or config.is_empty() or not selected_wish.is_empty():
		return false
	return tick >= float(config["timeline"]["ready_tick"])

func select_wish(wish_id: String) -> Dictionary:
	if not active or dismissing or config.is_empty():
		return {}
	for entry in config.get("wishes", []):
		if str(entry.get("id", "")) == wish_id:
			selected_wish = entry.duplicate(true)
			wish_selected.emit(selected_wish)
			if bool(config.get("behavior", {}).get("auto_dismiss_after_wish", true)):
				begin_dismiss()
			return selected_wish
	return {}

func is_casting() -> bool:
	return active and (dismissing or tick < float(config["timeline"]["ready_tick"]))

func _physics_process(delta: float) -> void:
	if active and not manual_clock:
		var hz := float(config["tick_hz"])
		if dismissing:
			seek_dismiss_tick(dismiss_tick + delta * hz)
			if dismiss_tick >= float(config["dismiss_timeline"]["end_tick"]):
				dismiss()
		else:
			seek_tick(tick + delta * hz)

static func flight_progress(at_tick: float, index: int, stride: float, duration: float) -> float:
	var elapsed := at_tick - float(index) * stride
	return -1.0 if elapsed < 0.0 else clampf(elapsed / maxf(1.0, duration), 0.0, 1.0)

static func _double_flash_alpha(at_tick: float, flash_starts: Array, rise: float, hold: float, fall: float) -> float:
	var flash_alpha := 0.0
	for start in flash_starts:
		var elapsed := at_tick - float(start)
		if elapsed >= 0.0:
			flash_alpha = maxf(flash_alpha, minf(clampf(elapsed / rise, 0, 1), clampf((rise + hold + fall - elapsed) / fall, 0, 1)))
	return flash_alpha

static func _ground_rect_for_config(cfg: Dictionary) -> Rect2:
	var layout: Dictionary = cfg["layout"]
	var center_array: Array = layout["map_center_px"]
	var center := Vector2(float(center_array[0]), float(center_array[1]))
	var gr: Array = cfg["regions"]["ground"]
	var ground_width := float(layout["ground_display_width_px"])
	var ground_height := float(gr[3]) * ground_width / float(gr[2])
	return Rect2(center.x - ground_width * 0.5, float(layout["ground_y"]) - ground_height, ground_width, ground_height)

static func _dragon_pos_for_config(cfg: Dictionary, body_cfg: Dictionary, ground_rect: Rect2) -> Vector2:
	var layout: Dictionary = cfg["layout"]
	var center_array: Array = layout["map_center_px"]
	var anchor: Array = body_cfg["anchor_px"]
	var dragon_scale := float(layout["dragon_scale"])
	return Vector2(float(center_array[0]), ground_rect.position.y + (float(anchor[1]) - float(layout["dragon_reference_bottom_canvas_y"])) * dragon_scale - float(layout["dragon_gap_px"]))

static func _idle_frame_at_tick(body_cfg: Dictionary, cfg: Dictionary, elapsed_ticks: float) -> int:
	var durations: Array = body_cfg["clips"][cfg["behavior"]["dragon_clip"]]["godot"]["relative_durations"]
	var total := 0.0
	for duration in durations:
		total += float(duration)
	var rest := fmod(maxf(0.0, elapsed_ticks), maxf(1.0, total))
	var frame := 0
	while frame < durations.size() - 1 and rest >= float(durations[frame]):
		rest -= float(durations[frame])
		frame += 1
	return frame

func sample_state(at_tick: float) -> Dictionary:
	var t: Dictionary = config["timeline"]
	var layout: Dictionary = config["layout"]
	var center_array: Array = layout["map_center_px"]
	var center := Vector2(float(center_array[0]), float(center_array[1]))
	var vanish := 1.0 - clampf((at_tick - float(t["vanish_start_tick"])) / float(t["flash_start_ticks"][0] - t["vanish_start_tick"]), 0.0, 1.0)
	var flash_alpha := _double_flash_alpha(at_tick, t["flash_start_ticks"], float(t["flash_rise_ticks"]), float(t["flash_hold_ticks"]), float(t["flash_fall_ticks"]))
	var balls: Array = []
	for index in range(config["items"].size()):
		var item: Dictionary = config["items"][index]
		var p := flight_progress(at_tick, index, float(t["launch_stride_ticks"]), float(t["flight_ticks"]))
		var u := maxf(0.0, p)
		var ease := u * u * (3.0 - 2.0 * u)
		var off: Array = item["formation_offset_px"]
		var target := center + Vector2(float(off[0]), float(off[1]))
		var pos := origin.lerp(target, ease)
		pos.y -= float(layout["flight_arc_height_px"]) * 4.0 * u * (1.0 - u)
		balls.append({"number": item["number"], "region": item["region"], "visible": p >= 0.0 and at_tick < float(t["flash_start_ticks"][0]), "alpha": vanish, "position": pos})
	var ground_rect := _ground_rect_for_config(config)
	var ground_fade := float(t.get("ground_fade_ticks", 24.0))
	var ground_alpha := (1.0 if at_tick >= float(t["ground_start_tick"]) else 0.0) if ground_fade <= 0.0 else clampf((at_tick - float(t["ground_start_tick"])) / ground_fade, 0.0, 1.0)
	var glow_alpha := ground_alpha * (0.78 + 0.22 * (0.5 + 0.5 * sin(TAU * (at_tick - float(t["ground_start_tick"])) / float(t["glow_period_ticks"]))))
	var dragon_pos := _dragon_pos_for_config(config, body_export, ground_rect)
	var dragon_u := clampf((at_tick - float(t["dragon_start_tick"])) / float(t["ready_tick"] - t["dragon_start_tick"]), 0.0, 1.0)
	var dragon_alpha := (1.0 - (1.0 - dragon_u) * (1.0 - dragon_u)) if str(t.get("dragon_reveal_curve", "linear")) == "ease_out_quad" else dragon_u
	var frame := _idle_frame_at_tick(body_export, config, maxf(0.0, at_tick - float(t["dragon_start_tick"])))
	var phase := "ready"
	if at_tick < float(t["last_arrival_tick"]): phase = "flight"
	elif at_tick < float(t["vanish_start_tick"]): phase = "gather"
	elif at_tick < float(t["flash_start_ticks"][0]): phase = "vanish"
	elif at_tick < float(t["ground_start_tick"]): phase = "flash"
	elif at_tick < float(t["dragon_start_tick"]): phase = "ground_glow"
	elif at_tick < float(t["ready_tick"]): phase = "dragon_reveal"
	return {"reveal_top": 0.0, "flash_alpha": flash_alpha, "phase": phase, "balls": balls, "ground_rect": ground_rect, "ground_alpha": ground_alpha, "glow_alpha": glow_alpha, "dragon_position": dragon_pos, "dragon_alpha": dragon_alpha, "dragon_frame": frame}

func sample_dismiss_state(at_dismiss_tick: float, base_summon_tick: float = -1.0) -> Dictionary:
	var t: Dictionary = config["timeline"]
	var dt: Dictionary = config["dismiss_timeline"]
	var flash_alpha := _double_flash_alpha(at_dismiss_tick, dt["flash_start_ticks"], float(dt["flash_rise_ticks"]), float(dt["flash_hold_ticks"]), float(dt["flash_fall_ticks"]))
	var elements_visible := at_dismiss_tick < float(dt["vanish_tick"])
	var ground_rect := _ground_rect_for_config(config)
	var dragon_pos := _dragon_pos_for_config(config, body_export, ground_rect)
	var ref_tick := (tick if base_summon_tick < 0.0 else base_summon_tick) + at_dismiss_tick
	var ground_alpha := 1.0 if elements_visible else 0.0
	var dragon_alpha := 1.0 if elements_visible else 0.0
	var glow_alpha := (0.78 + 0.22 * (0.5 + 0.5 * sin(TAU * (ref_tick - float(t["ground_start_tick"])) / float(t["glow_period_ticks"])))) if elements_visible else 0.0
	var frame := _idle_frame_at_tick(body_export, config, maxf(0.0, ref_tick - float(t["dragon_start_tick"])))
	return {"flash_alpha": flash_alpha, "phase": "dismiss_flash" if elements_visible else "dismissed", "balls": [], "ground_rect": ground_rect, "ground_alpha": ground_alpha, "glow_alpha": glow_alpha, "dragon_position": dragon_pos, "dragon_alpha": dragon_alpha, "dragon_frame": frame, "elements_visible": elements_visible, "finished": at_dismiss_tick >= float(dt["end_tick"])}

func seek_tick(value: float) -> void:
	tick = maxf(0.0, value)
	if active and not dismissing and dragon != null:
		var state := sample_state(tick)
		flash_overlay.color.a = float(state["flash_alpha"])
		dragon.visible = float(state["dragon_alpha"]) > 0.0
		dragon.position = state["dragon_position"]
		dissolve_material.set_shader_parameter("progress", float(state["dragon_alpha"]))
		dragon.scale = Vector2.ONE * float(config["layout"]["dragon_scale"])
		dragon.modulate = Color.WHITE
		dragon_sprite.stop()
		dragon_sprite.animation = StringName(config["behavior"]["dragon_clip"])
		dragon_sprite.frame = int(state["dragon_frame"])
		if not _ready_emitted and tick >= float(config["timeline"]["ready_tick"]):
			_ready_emitted = true
			summon_ready.emit()
	queue_redraw()

func seek_dismiss_tick(value: float) -> void:
	dismiss_tick = maxf(0.0, value)
	if active and dismissing and dragon != null:
		var state := sample_dismiss_state(dismiss_tick)
		flash_overlay.color.a = float(state["flash_alpha"])
		dragon.visible = bool(state["elements_visible"])
		dragon.position = state["dragon_position"]
		dissolve_material.set_shader_parameter("progress", float(state["dragon_alpha"]))
		dragon.scale = Vector2.ONE * float(config["layout"]["dragon_scale"])
		dragon.modulate = Color.WHITE
		dragon_sprite.stop()
		dragon_sprite.animation = StringName(config["behavior"]["dragon_clip"])
		dragon_sprite.frame = int(state["dragon_frame"])
	queue_redraw()

func _draw_region(region: Array, destination: Rect2, alpha: float) -> void:
	if alpha > 0.0:
		draw_texture_rect_region(atlas, destination, Rect2(float(region[0]), float(region[1]), float(region[2]), float(region[3])), Color(1.0, 1.0, 1.0, alpha))

func _draw() -> void:
	if not active or atlas == null:
		return
	var state := sample_dismiss_state(dismiss_tick) if dismissing else sample_state(tick)
	var width := float(config["layout"]["ball_display_width_px"])
	for ball in state["balls"]:
		if not ball["visible"]: continue
		var region: Array = ball["region"]
		var size := Vector2(width, width * float(region[3]) / float(region[2]))
		_draw_region(region, Rect2(Vector2(ball["position"]) - size * 0.5, size), float(ball["alpha"]))
	if float(state["ground_alpha"]) <= 0.0 and float(state["glow_alpha"]) <= 0.0:
		return
	var rect: Rect2 = state["ground_rect"]
	var glow: Array = config["regions"]["glow"]
	var glow_scale := float(config["layout"]["ground_display_width_px"]) / 256.0
	var glow_rect := Rect2(rect.position - Vector2.ONE * 32.0 * glow_scale, Vector2(float(glow[2]), float(glow[3])) * glow_scale)
	var aura_width := float(config["layout"]["aura_width_px"])
	var aura_height := float(config["layout"]["aura_height_px"])
	var aura_rect := Rect2(rect.get_center().x - aura_width * 0.5, rect.end.y - aura_height, aura_width, aura_height)
	_draw_region(glow, aura_rect, float(state["glow_alpha"]) * 0.75)
	_draw_region(glow, glow_rect.grow(56.0), float(state["glow_alpha"]))
	_draw_region(config["regions"]["ground"], rect, float(state["ground_alpha"]))
	_draw_region(config["regions"]["core"], glow_rect.grow(12.0), float(state["glow_alpha"]) * 0.86)
