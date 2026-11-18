class_name ArenaSandbox
extends Node2D
## Official DR7-Studio 16:9 (1920x1080) Landscape Mobile Arena Scene.
## Reads `res://assets/maps/rocky_plateau/arena-stage.json` and `res://assets/roster.json`
## directly so Godot 4 builds (Editor, Headless, Android APK, iOS IPA) and localhost:8080
## maintain exact 1:1 coordinate, scale, and visual parity.

const STAGE_JSON_PATH := "res://assets/maps/rocky_plateau/arena-stage.json"
const TERRAIN_JSON_PATH := "res://assets/maps/rocky_plateau/terrain.json"
const EXTENDED_MAP_PATH := "res://review/rocky_plateau_extension/combined-depth-review.png"
const FOREGROUND_PLANTED_TREES_PATH := "res://review/rocky_plateau_extension/planted-trees-review.png"
const FOREGROUND_TREES_PATH := "res://review/rocky_plateau_extension/three-trees-draft.png"
const FOREGROUND_TREES_COMPLETE_PATH := "res://review/rocky_plateau_extension/two-trees-complete-review.png"
const MAP_LEFT_X := -240.0
const MAP_RIGHT_X := 6360.0
const MAP_TOP_Y := -210.0
const MAP_BOTTOM_Y := 1140.0
const MAP_JOIN_X := 2160.0
const STEP_ONE_X := 2850.0
const STEP_ONE_WALL_X := 2876.0
const STEP_TWO_X := 3695.0
const STEP_TWO_WALL_X := 3724.0
const STEP_THREE_X := 4740.0
const STEP_THREE_WALL_X := 4778.0
const STEP_FOUR_X := 5560.0
const STEP_FOUR_WALL_X := 5582.0
const STEP_ONE_DROP_Y := 50.0
const STEP_TWO_DROP_Y := 105.0
const STEP_THREE_DROP_Y := 135.0
const STEP_FOUR_DROP_Y := 190.0
const ROSTER_JSON_PATH := "res://assets/roster.json"
const REVIEW_ROSTER_JSON_PATH := "res://review/review-roster.json"
const BODY_SILHOUETTES_JSON_PATH := "res://assets/body_silhouettes.json"
const Z_LAYER_MONSTER := 10
const Z_LAYER_HERO := 20
const Z_LAYER_BOSS := 30
const PLAYER_LIGHT_ATTACK_COOLDOWN_S: float = 0.2
const ShenronSummonScript := preload("res://scenes/ShenronSummon2D.gd")
const DragonBallItemScene := preload("res://scenes/items/DragonBallItem2D.tscn")
const DisplayPolicyScript := preload("res://scenes/runtime/DisplayPolicy.gd")
const TouchHudOverlayScript := preload("res://scenes/runtime/TouchHudOverlay.gd")
const PixelRulerModalScript := preload("res://scenes/runtime/PixelRulerModal.gd")
const ArenaThemeScript := preload("res://scenes/runtime/ArenaTheme.gd")
const MobileActionPadScript := preload("res://scenes/runtime/MobileActionPad.gd")
const FieldCombatManagerScript := preload("res://scenes/runtime/FieldCombatManager.gd")
const WebSocketTransportScript := preload("res://scenes/net/WebSocketTransport.gd")
const ZoneClientSyncScript := preload("res://scenes/net/ZoneClientSync.gd")

var shenron_summon: ShenronSummon2D
var summon_button: Button
var wish_panel: PanelContainer
var wish_notice_label: Label
var _wish_notice_timer_s: float = 0.0
var touch_hud: Control = null
var _arena_camera: Camera2D = null
var _bg_left_ext: Sprite2D = null
var _bg_right_ext: Sprite2D = null
var _foreground_trees: Node2D = null
var pixel_perfect_enabled: bool = false
var display_layout_info: Dictionary = {}
var net_transport: NetworkTransport = null
var zone_sync: ZoneClientSync = null

const UtilityAIControllerScript := preload("res://scenes/UtilityAIController.gd")

@export var default_character_id: String = "t_rex"

var stage_config: Dictionary = {}
var terrain_config: Dictionary = {}
var terrain_platforms: Array = []
var show_pixel_terrain: bool = true
var _terrain_root: Node2D = null
var _parallax_nodes: Array = []
var _ground_tilemap: TileMapLayer = null
var _dust_fx_layer: Node2D = null
var _dust_fx_tex: Texture2D = null
var _active_dust_fx: Array = []
var _player_drop_timer_s: float = 0.0
var _prev_player_on_ground: bool = true
var _step_dust_accum_px: float = 0.0
var roster_characters: Array = []
var _body_silhouettes: Dictionary = {}
var active_character_id: String = ""
var char_scale: float = 1.75
var enemy_scale: float = 1.75
var ground_y: float = 840.0
var walkable_min_x: float = 140.0
var walkable_max_x: float = 1780.0
var viewport_width: int = 1920
var viewport_height: int = 1080
var player_spawn_x: float = 560.0
var dummy_spawn_x: float = 1360.0
var fly_min_y: float = 60.0
var fly_default_y: float = 250.0
var fly_vertical_speed_px_per_s: float = 240.0
var jump_velocity_px_per_s: float = -780.0
var gravity_px_per_s2: float = 2000.0
var show_grid_overlay: bool = false

var enemy_character_id: String = ""
var _enemy_pinned: bool = false
var player_node: Node2D = null
var dummy_node: Node2D = null
var player_vy: float = 0.0
var enemy_vy: float = 0.0
var player_facing_left: bool = false
var enemy_facing_left: bool = true
var utility_ai_enabled: bool = false
var ai_controller = UtilityAIControllerScript.new()
var ai_last_decision: Dictionary = {}
var _ai_action_clip: String = ""
var _ai_action_timer_s: float = 0.0
var _ai_drum_teleport_relocated: bool = false
var _player_drum_teleport_relocated: bool = false
var player_light_cooldown_s: float = 0.0
var _player_light_clip_active: bool = false
var _enemy_orb_sprite: AnimatedSprite2D = null
var _enemy_orb_active: bool = false
var _enemy_orb_dir: float = 1.0
var _enemy_orb_elapsed_s: float = 0.0
var _enemy_orb_spawned_for_cast: bool = false
var _hero_skill_bar: HBoxContainer = null
var _role_mode_label: Label = null
var _player_select_opt: OptionButton = null
var _enemy_select_opt: OptionButton = null
var _hud_syncing: bool = false
var _player_turn_boost_s: float = 0.0
var _ai_turn_boost_s: float = 0.0
var _player_turn_elapsed_s: float = 0.0
var _player_turn_duration_s: float = 0.0
var _player_turn_prev_dir: int = 1
var _ai_turn_elapsed_s: float = 0.0
var _ai_turn_duration_s: float = 0.0
var _ai_turn_prev_dir: int = -1
var _ai_turn_target_left: bool = true
var _char_index: int = 0

var item_drop_enabled: bool = true
var item_drop_ball: int = 0
var item_drop_scale: float = 1.0
var _item_drop_layer: Node2D = null
var _dropped_item_nodes: Array[Node2D] = []
var _next_monster_drop_ball: int = 1
var collected_bag_balls: Array[int] = []
var item_toggle_button: Button = null
var item_drop_test_button: Button = null
var item_pickup_button: Button = null
var ruler_button: Button = null
var ruler_modal: PixelRulerModal = null
var ruler_modal_visible: bool = false
var ruler_pick_mode: bool = false
var ruler_grid_enabled: bool = false
var ruler_has_a: bool = false
var ruler_has_b: bool = false
var ruler_point_a: Vector2 = Vector2.ZERO
var ruler_point_b: Vector2 = Vector2.ZERO
var _ruler_dragging: bool = false
var _ruler_drag_start_screen: Vector2 = Vector2.ZERO
var _ruler_awaiting_b: bool = false
var _t_key_was_down: bool = false
var _tab_key_was_down: bool = false
var _last_touch_tap_msec: int = -10000
var _flight_vel: Vector2 = Vector2.ZERO

var field_mode_enabled: bool = false
var hud_ui_hidden: bool = false
var hero_immortal_enabled: bool = false
var show_monster_ranges_enabled: bool = false
var field_manager = null
var _field_overlay_node: Node2D = null
var mobile_pad = null
var pixel_perfect_button: Button = null
var toggle_hero_button: Button = null
var pad_settings_button: Button = null
var toggle_ui_button: Button = null
var immortal_button: Button = null
var monster_range_button: Button = null
var boss_spawn_button: Button = null
var _arena_theme: Theme = null

@onready var background_sprite: Sprite2D = get_node_or_null("BackgroundLayer/BackgroundSprite")
@onready var fighters_layer: Node2D = get_node_or_null("FightersLayer")
@onready var hud_label: Label = get_node_or_null("HUDLayer/HudLabel")


func _ready() -> void:
	load_stage_and_roster()
	_apply_stage_layout()
	_setup_camera_and_display_policy()
	_setup_network_client_stub()
	_apply_arena_theme()
	_setup_summon_control()
	_setup_item_controls()
	_setup_touch_hud()
	_setup_ruler_control()
	_setup_field_hud_controls()
	_ensure_field_manager()
	_refresh_dropped_items()
	if DisplayServer.get_name() != "headless":
		enable_field_mode(true, false)
	elif not roster_characters.is_empty():
		var start_id := default_character_id
		if _find_character_entry(start_id).is_empty():
			start_id = str(roster_characters[0].get("character_id", ""))
		select_character(start_id)


func _setup_camera_and_display_policy() -> void:
	if _arena_camera == null and get_viewport() != null:
		_arena_camera = Camera2D.new()
		_arena_camera.name = "ArenaCamera"
		_arena_camera.position = Vector2(float(viewport_width) * 0.5, float(viewport_height) * 0.5)
		_arena_camera.enabled = true
		add_child(_arena_camera)
		_arena_camera.make_current()
	_update_follow_camera()
	var root_win := get_tree().root if get_tree() != null else null
	display_layout_info = DisplayPolicyScript.apply_to_root_window(root_win, pixel_perfect_enabled)
	_update_background_cover()
	_apply_hud_safe_area()
	if root_win != null and not root_win.size_changed.is_connected(_on_root_window_resized):
		root_win.size_changed.connect(_on_root_window_resized)


func _on_root_window_resized() -> void:
	var root_win := get_tree().root if get_tree() != null else null
	display_layout_info = DisplayPolicyScript.apply_to_root_window(root_win, pixel_perfect_enabled)
	_update_background_cover()
	_apply_hud_safe_area()
	if touch_hud != null and is_instance_valid(touch_hud) and touch_hud.has_method("apply_safe_area"):
		touch_hud.call("apply_safe_area", display_layout_info)
	if mobile_pad != null and is_instance_valid(mobile_pad):
		mobile_pad.apply_safe_area(display_layout_info)


func set_pixel_perfect_enabled(enabled: bool, sim_win_size: Vector2i = Vector2i.ZERO, sim_safe_rect: Rect2i = Rect2i()) -> Dictionary:
	pixel_perfect_enabled = enabled
	var root_win := get_tree().root if get_tree() != null else null
	display_layout_info = DisplayPolicyScript.apply_to_root_window(root_win, pixel_perfect_enabled, sim_win_size, sim_safe_rect)
	_update_background_cover()
	_apply_hud_safe_area()
	if touch_hud != null and is_instance_valid(touch_hud) and touch_hud.has_method("apply_safe_area"):
		touch_hud.call("apply_safe_area", display_layout_info)
	if mobile_pad != null and is_instance_valid(mobile_pad):
		mobile_pad.apply_safe_area(display_layout_info)
	if pixel_perfect_button != null:
		pixel_perfect_button.text = "Pixel: Perfect" if pixel_perfect_enabled else "Pixel: Fractional"
	return display_layout_info


func apply_device_profile(profile_id: String) -> Dictionary:
	var doc: Dictionary = DisplayPolicyScript.load_device_profiles()
	var prof: Dictionary = DisplayPolicyScript.find_profile(doc, profile_id)
	if prof.is_empty():
		return display_layout_info
	var win_sz := Vector2i(int(prof.get("width_px", viewport_width)), int(prof.get("height_px", viewport_height)))
	var sr: Array = prof.get("safe_area_px", [0, 0, win_sz.x, win_sz.y])
	var safe_rect := Rect2i(int(sr[0]), int(sr[1]), int(sr[2]), int(sr[3])) if sr.size() == 4 else Rect2i(0, 0, win_sz.x, win_sz.y)
	return set_pixel_perfect_enabled(pixel_perfect_enabled, win_sz, safe_rect)


func _setup_network_client_stub() -> void:
	net_transport = WebSocketTransportScript.new()
	zone_sync = ZoneClientSyncScript.new()
	zone_sync.attach_transport(net_transport)


func _apply_arena_theme() -> void:
	_arena_theme = ArenaThemeScript.build_theme()
	if hud_label != null and _arena_theme != null:
		hud_label.theme = _arena_theme
		hud_label.add_theme_font_size_override("font_size", 21)
		hud_label.add_theme_color_override("font_color", Color(0.95, 0.97, 1.0, 1.0))
		hud_label.add_theme_color_override("font_outline_color", Color(0.03, 0.05, 0.10, 0.96))
		hud_label.add_theme_constant_override("outline_size", 3)
		var pill := StyleBoxFlat.new()
		pill.bg_color = Color(0.05, 0.08, 0.16, 0.62)
		pill.border_color = Color(0.75, 0.85, 0.98, 0.34)
		pill.set_border_width_all(1)
		pill.set_corner_radius_all(8)
		pill.content_margin_left = 10
		pill.content_margin_right = 10
		pill.content_margin_top = 4
		pill.content_margin_bottom = 4
		hud_label.add_theme_stylebox_override("normal", pill)


func _ensure_field_manager() -> void:
	if field_manager == null or not is_instance_valid(field_manager):
		field_manager = FieldCombatManagerScript.new()
		field_manager.name = "FieldCombatManager"
		add_child(field_manager)
		field_manager.setup(self)
		field_manager.player_state_changed.connect(_sync_field_pad_state)
		field_manager.pointer_changed.connect(func(_k: String) -> void:
			_sync_field_pad_state()
			if _field_overlay_node != null and is_instance_valid(_field_overlay_node):
				_field_overlay_node.queue_redraw()
		)
	if _field_overlay_node == null or not is_instance_valid(_field_overlay_node):
		_field_overlay_node = Node2D.new()
		_field_overlay_node.name = "FieldOverlayLayer"
		_field_overlay_node.z_index = 60
		add_child(_field_overlay_node)
		_field_overlay_node.draw.connect(_on_field_overlay_draw)


func _on_field_overlay_draw() -> void:
	if _field_overlay_node == null or not is_instance_valid(_field_overlay_node):
		return
	if field_mode_enabled and field_manager != null and field_manager.active:
		field_manager.draw_overlays(_field_overlay_node)


func _setup_touch_hud() -> void:
	if DisplayServer.get_name() == "headless":
		return
	var hud_layer := get_node_or_null("HUDLayer")
	if hud_layer == null:
		return
	mobile_pad = MobileActionPadScript.new()
	mobile_pad.name = "MobileActionPad"
	if _arena_theme != null:
		mobile_pad.theme = _arena_theme
	hud_layer.add_child(mobile_pad)
	mobile_pad.action_triggered.connect(_on_mobile_pad_action)
	mobile_pad.target_cycle_requested.connect(_on_target_cycle_requested)
	mobile_pad.apply_safe_area(display_layout_info)


func _collect_clip_names(fighter: Node2D) -> PackedStringArray:
	var out := PackedStringArray()
	if fighter == null:
		return out
	var spr := fighter.get_node_or_null("Sprite") as AnimatedSprite2D
	if spr != null and spr.sprite_frames != null:
		for anim in spr.sprite_frames.get_animation_names():
			out.append(String(anim))
	return out


func _align_player_facing_to_active_move_dir() -> void:
	if player_node == null:
		return
	var dir := 0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT) or Input.is_action_pressed(&"move_right"):
		dir += 1
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT) or Input.is_action_pressed(&"move_left"):
		dir -= 1
	if mobile_pad != null and is_instance_valid(mobile_pad) and mobile_pad.analog_dir_x != 0:
		dir = clampi(mobile_pad.analog_dir_x, -1, 1)
	if touch_hud != null and is_instance_valid(touch_hud) and int(touch_hud.get("touch_dir_x")) != 0:
		dir = clampi(int(touch_hud.get("touch_dir_x")), -1, 1)
	if dir != 0:
		player_facing_left = dir < 0
		player_node.scale = Vector2(-char_scale if player_facing_left else char_scale, char_scale)


func _on_mobile_pad_action(_slot_id: int, action_id: String) -> void:
	_on_touch_action(action_id)


func _on_target_cycle_requested() -> void:
	if field_manager != null and field_manager.active:
		field_manager.cycle_target_pointer()
		_sync_field_pad_state()


func _sync_field_pad_state() -> void:
	if mobile_pad == null or not is_instance_valid(mobile_pad) or field_manager == null:
		return
	mobile_pad.set_mana_and_pointer_state(field_manager.player_mana, field_manager.player_max_mana, field_manager.pointer_kind)


func _on_touch_action(action_name: String) -> void:
	if player_node == null:
		return
	if field_mode_enabled and field_manager != null and field_manager.active and field_manager.player_dead:
		return
	if action_name != "attack_light" and field_manager != null:
		field_manager.cancel_auto_approach()
	if action_name == "jump":
		if _is_flying_entry(_find_character_entry(active_character_id)):
			step_flight_vertical(-1.0, 1.0 / 60.0)
			return
		if not _has_clip_name(player_node, &"jump"):
			return
		var sup_y := get_nearest_support_y_below(player_node.position.x, player_node.position.y)
		if not _is_flying_entry(_find_character_entry(active_character_id)) and player_node.position.y >= sup_y - 2.0 and player_vy >= 0.0:
			player_vy = jump_velocity_px_per_s
			_spawn_ground_dust(player_node.position.x, sup_y, 0.9)
	elif action_name == "teleport":
		_align_player_facing_to_active_move_dir()
		_request_player_action("teleport")
	elif action_name == "pickup_items":
		pickup_dropped_items()
	elif action_name == "attack_light":
		if field_mode_enabled and field_manager != null and field_manager.active:
			field_manager.request_player_primary_action()
		else:
			_request_player_action("attack_light")
	elif action_name == "power_up":
		if field_mode_enabled and field_manager != null and field_manager.active:
			field_manager.request_player_power_up()
		else:
			_request_player_action("power_up")
	elif action_name in ["attack_heavy"]:
		_request_player_action(action_name)


func _is_fighter_turning(fighter: Node) -> bool:
	if fighter == null:
		return false
	var pending: Variant = fighter.get("_turn_pending")
	return bool(pending) if pending != null else false


func _is_light_attack_clip(clip_name: String) -> bool:
	return clip_name == "attack_light" or clip_name == "attack_nomal"


func can_player_light_attack() -> bool:
	if player_node == null:
		return false
	if player_light_cooldown_s > 0.0:
		return false
	if _is_fighter_turning(player_node) or _is_player_action_playing():
		return false
	return _has_clip_name(player_node, &"attack_light") or _has_clip_name(player_node, &"attack_nomal")


func _step_player_light_cooldown(delta: float) -> void:
	if player_node == null:
		return
	var spr := player_node.get_node_or_null("Sprite") as AnimatedSprite2D
	var light_playing_now := spr != null and spr.is_playing() and _is_light_attack_clip(String(spr.animation))
	if _player_light_clip_active and not light_playing_now:
		_player_light_clip_active = false
		player_light_cooldown_s = PLAYER_LIGHT_ATTACK_COOLDOWN_S
	elif not light_playing_now and player_light_cooldown_s > 0.0:
		player_light_cooldown_s = maxf(0.0, player_light_cooldown_s - delta)


func _request_player_action(clip_name: String) -> bool:
	if player_node == null:
		return false
	if clip_name == "attack_light" and not _has_clip_name(player_node, &"attack_light") and _has_clip_name(player_node, &"attack_nomal"):
		clip_name = "attack_nomal"
	if not _has_clip_name(player_node, StringName(clip_name)):
		return false
	if _is_light_attack_clip(clip_name):
		if player_light_cooldown_s > 0.0 or _is_fighter_turning(player_node) or _is_player_action_playing():
			return false
		if _play_fighter_clip(player_node, clip_name):
			_player_light_clip_active = true
			return true
		return false
	if _is_fighter_turning(player_node) or _is_player_action_playing():
		player_node.set_meta(&"_arena_queued_action", clip_name)
		return true
	return _play_fighter_clip(player_node, clip_name)


func _setup_summon_control() -> void:
	var hud_layer := get_node("HUDLayer")
	shenron_summon = ShenronSummonScript.new()
	add_child(shenron_summon)
	shenron_summon.summon_ready.connect(_on_shenron_summon_ready)
	shenron_summon.wish_selected.connect(_on_shenron_wish_selected)
	shenron_summon.dismissed.connect(_on_shenron_dismissed)
	summon_button = Button.new()
	summon_button.anchor_left = 1.0
	summon_button.anchor_right = 1.0
	summon_button.offset_left = -320.0
	summon_button.offset_right = -40.0
	summon_button.offset_top = 78.0
	summon_button.offset_bottom = 134.0
	summon_button.text = "Gọi Shenron"
	hud_layer.add_child(summon_button)
	summon_button.pressed.connect(_on_summon_button_pressed)
	wish_panel = PanelContainer.new()
	wish_panel.anchor_left = 1.0
	wish_panel.anchor_right = 1.0
	wish_panel.offset_left = -500.0
	wish_panel.offset_right = -40.0
	wish_panel.offset_top = 244.0
	wish_panel.custom_minimum_size = Vector2(460, 0)
	wish_panel.visible = false
	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 10)
	var title_lbl := Label.new()
	title_lbl.text = "Chọn Điều Ước Shenron"
	title_lbl.add_theme_color_override("font_color", Color(1.0, 0.85, 0.25))
	vbox.add_child(title_lbl)
	for wish in shenron_summon.config.get("wishes", []):
		var w_btn := Button.new()
		w_btn.text = str(wish.get("label", wish.get("id", "Wish")))
		w_btn.custom_minimum_size = Vector2(420, 44)
		var wid := str(wish.get("id", ""))
		w_btn.pressed.connect(func() -> void: _on_wish_button_pressed(wid))
		vbox.add_child(w_btn)
	wish_panel.add_child(vbox)
	hud_layer.add_child(wish_panel)
	wish_notice_label = Label.new()
	wish_notice_label.anchor_left = 0.5
	wish_notice_label.anchor_right = 0.5
	wish_notice_label.offset_left = -490.0
	wish_notice_label.offset_right = 490.0
	wish_notice_label.offset_top = 78.0
	wish_notice_label.offset_bottom = 118.0
	wish_notice_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	wish_notice_label.add_theme_color_override("font_color", Color(1.0, 0.9, 0.35))
	wish_notice_label.visible = false
	hud_layer.add_child(wish_notice_label)


func _setup_item_controls() -> void:
	var hud_layer := get_node_or_null("HUDLayer")
	if hud_layer == null:
		return
	item_toggle_button = Button.new()
	item_toggle_button.anchor_left = 1.0
	item_toggle_button.anchor_right = 1.0
	item_toggle_button.offset_left = -320.0
	item_toggle_button.offset_right = -184.0
	item_toggle_button.offset_top = 142.0
	item_toggle_button.offset_bottom = 184.0
	item_toggle_button.text = "Ẩn Ngọc"
	item_toggle_button.pressed.connect(func() -> void:
		toggle_dropped_items_visible()
	)
	hud_layer.add_child(item_toggle_button)

	item_drop_test_button = Button.new()
	item_drop_test_button.anchor_left = 1.0
	item_drop_test_button.anchor_right = 1.0
	item_drop_test_button.offset_left = -178.0
	item_drop_test_button.offset_right = -40.0
	item_drop_test_button.offset_top = 142.0
	item_drop_test_button.offset_bottom = 184.0
	item_drop_test_button.text = "Quái Rơi Ngọc"
	item_drop_test_button.pressed.connect(func() -> void:
		trigger_monster_death_drop(0)
	)
	hud_layer.add_child(item_drop_test_button)

	item_pickup_button = Button.new()
	item_pickup_button.anchor_left = 1.0
	item_pickup_button.anchor_right = 1.0
	item_pickup_button.offset_left = -320.0
	item_pickup_button.offset_right = -40.0
	item_pickup_button.offset_top = 190.0
	item_pickup_button.offset_bottom = 232.0
	item_pickup_button.text = "Nhặt Ngọc Vào Người"
	item_pickup_button.pressed.connect(func() -> void:
		pickup_dropped_items()
	)
	hud_layer.add_child(item_pickup_button)
	_apply_hud_safe_area()


func _apply_hud_safe_area() -> void:
	var insets: Dictionary = display_layout_info.get("safe_insets_logic", {})
	var ins_l := float(insets.get("left", 0.0))
	var ins_t := float(insets.get("top", 0.0))
	var ins_r := float(insets.get("right", 0.0))
	var vis := _get_visible_logic_size()
	var compact_top := vis.x < 1260.0
	if hud_label != null:
		hud_label.offset_left = 20.0 + ins_l
		hud_label.offset_top = 14.0 + ins_t
	if summon_button != null:
		summon_button.offset_left = -320.0 - ins_r
		summon_button.offset_right = -40.0 - ins_r
		summon_button.offset_top = 78.0 + ins_t
		summon_button.offset_bottom = 134.0 + ins_t
	if item_toggle_button != null:
		item_toggle_button.offset_left = -320.0 - ins_r
		item_toggle_button.offset_right = -184.0 - ins_r
		item_toggle_button.offset_top = 142.0 + ins_t
		item_toggle_button.offset_bottom = 184.0 + ins_t
	if item_drop_test_button != null:
		item_drop_test_button.offset_left = -178.0 - ins_r
		item_drop_test_button.offset_right = -40.0 - ins_r
		item_drop_test_button.offset_top = 142.0 + ins_t
		item_drop_test_button.offset_bottom = 184.0 + ins_t
	if item_pickup_button != null:
		item_pickup_button.offset_left = -320.0 - ins_r
		item_pickup_button.offset_right = -40.0 - ins_r
		item_pickup_button.offset_top = 190.0 + ins_t
		item_pickup_button.offset_bottom = 232.0 + ins_t
	if wish_panel != null:
		wish_panel.offset_left = -500.0 - ins_r
		wish_panel.offset_right = -40.0 - ins_r
		wish_panel.offset_top = (124.0 + ins_t) if hud_ui_hidden else (244.0 + ins_t)
	var row1_t := 68.0 + ins_t
	var row1_b := 112.0 + ins_t
	var row2_t := (120.0 + ins_t) if compact_top else row1_t
	var row2_b := (164.0 + ins_t) if compact_top else row1_b
	if pixel_perfect_button != null:
		pixel_perfect_button.offset_left = 20.0 + ins_l
		pixel_perfect_button.offset_right = 216.0 + ins_l
		pixel_perfect_button.offset_top = row1_t
		pixel_perfect_button.offset_bottom = row1_b
	if ruler_button != null:
		ruler_button.offset_left = 224.0 + ins_l
		ruler_button.offset_right = 376.0 + ins_l
		ruler_button.offset_top = row1_t
		ruler_button.offset_bottom = row1_b
	if toggle_hero_button != null:
		toggle_hero_button.offset_left = 384.0 + ins_l
		toggle_hero_button.offset_right = 632.0 + ins_l
		toggle_hero_button.offset_top = row1_t
		toggle_hero_button.offset_bottom = row1_b
	if pad_settings_button != null:
		pad_settings_button.offset_left = (20.0 + ins_l) if compact_top else (640.0 + ins_l)
		pad_settings_button.offset_right = (148.0 + ins_l) if compact_top else (768.0 + ins_l)
		pad_settings_button.offset_top = row2_t
		pad_settings_button.offset_bottom = row2_b
	if toggle_ui_button != null:
		toggle_ui_button.offset_left = (156.0 + ins_l) if compact_top else (776.0 + ins_l)
		toggle_ui_button.offset_right = (288.0 + ins_l) if compact_top else (908.0 + ins_l)
		toggle_ui_button.offset_top = row2_t
		toggle_ui_button.offset_bottom = row2_b
	var row2_only_t := 118.0 + ins_t
	var row2_only_b := 162.0 + ins_t
	if immortal_button != null:
		immortal_button.offset_left = (296.0 + ins_l) if compact_top else (20.0 + ins_l)
		immortal_button.offset_right = (464.0 + ins_l) if compact_top else (196.0 + ins_l)
		immortal_button.offset_top = row2_only_t
		immortal_button.offset_bottom = row2_only_b
	if monster_range_button != null:
		monster_range_button.offset_left = (472.0 + ins_l) if compact_top else (204.0 + ins_l)
		monster_range_button.offset_right = (676.0 + ins_l) if compact_top else (408.0 + ins_l)
		monster_range_button.offset_top = row2_only_t
		monster_range_button.offset_bottom = row2_only_b
	if boss_spawn_button != null:
		boss_spawn_button.offset_left = (20.0 + ins_l) if compact_top else (416.0 + ins_l)
		boss_spawn_button.offset_right = (236.0 + ins_l) if compact_top else (632.0 + ins_l)
		boss_spawn_button.offset_top = (row2_only_b + 6.0) if compact_top else row2_only_t
		boss_spawn_button.offset_bottom = (row2_only_b + 50.0) if compact_top else row2_only_b
	if ruler_modal != null and is_instance_valid(ruler_modal):
		ruler_modal.apply_safe_area(insets)
	if mobile_pad != null and is_instance_valid(mobile_pad):
		mobile_pad.apply_safe_area(display_layout_info)


func _setup_ruler_control() -> void:
	var hud_layer := get_node_or_null("HUDLayer")
	if hud_layer == null:
		return
	ruler_button = Button.new()
	ruler_button.name = "RulerModalButton"
	ruler_button.text = "📏 Thước PX"
	ruler_button.offset_left = 300.0
	ruler_button.offset_right = 446.0
	ruler_button.offset_top = 60.0
	ruler_button.offset_bottom = 98.0
	ruler_button.pressed.connect(func() -> void:
		set_ruler_modal_visible(not ruler_modal_visible)
	)
	hud_layer.add_child(ruler_button)

	ruler_modal = PixelRulerModalScript.new()
	ruler_modal.name = "PixelRulerModal"
	ruler_modal.visible = false
	hud_layer.add_child(ruler_modal)
	ruler_modal.pick_mode_changed.connect(func(enabled: bool) -> void:
		ruler_pick_mode = enabled
		_ruler_awaiting_b = false
		_ruler_dragging = false
	)
	ruler_modal.ruler_grid_toggled.connect(func(enabled: bool) -> void:
		ruler_grid_enabled = enabled
		queue_redraw()
	)
	ruler_modal.measure_pair_requested.connect(func() -> void:
		measure_player_enemy_distance()
	)
	ruler_modal.set_point_a_player_requested.connect(func() -> void:
		if player_node != null:
			ruler_point_a = player_node.position
			ruler_has_a = true
			_ruler_awaiting_b = true
			_sync_ruler_ui()
	)
	ruler_modal.snap_point_b_requested.connect(func(wx: float) -> void:
		ruler_point_b = Vector2(wx, _ground_y_at(wx))
		ruler_has_b = true
		if not ruler_has_a and player_node != null:
			ruler_point_a = player_node.position
			ruler_has_a = true
		_sync_ruler_ui()
	)
	ruler_modal.clear_points_requested.connect(func() -> void:
		ruler_has_a = false
		ruler_has_b = false
		_ruler_awaiting_b = false
		_ruler_dragging = false
		_sync_ruler_ui()
	)
	ruler_modal.modal_closed.connect(func() -> void:
		set_ruler_modal_visible(false)
	)
	_apply_hud_safe_area()


func _setup_field_hud_controls() -> void:
	var hud_layer := get_node_or_null("HUDLayer")
	if hud_layer == null:
		return
	if DisplayServer.get_name() != "headless":
		pixel_perfect_button = Button.new()
		pixel_perfect_button.name = "PixelPerfectButton"
		pixel_perfect_button.text = "Pixel: Perfect" if pixel_perfect_enabled else "Pixel: Fractional"
		pixel_perfect_button.pressed.connect(func() -> void:
			set_pixel_perfect_enabled(not pixel_perfect_enabled)
		)
		hud_layer.add_child(pixel_perfect_button)

		toggle_hero_button = Button.new()
		toggle_hero_button.name = "ToggleHeroButton"
		toggle_hero_button.text = "👤 Hiện Tướng (Drum)"
		toggle_hero_button.pressed.connect(func() -> void:
			var spawned_now: bool = field_manager != null and bool(field_manager.player_spawned)
			set_field_hero_visible(not spawned_now)
		)
		hud_layer.add_child(toggle_hero_button)

		pad_settings_button = Button.new()
		pad_settings_button.name = "PadSettingsButton"
		pad_settings_button.text = "⚙️ Phím"
		pad_settings_button.pressed.connect(func() -> void:
			if mobile_pad != null and is_instance_valid(mobile_pad):
				mobile_pad.toggle_settings_modal()
		)
		hud_layer.add_child(pad_settings_button)

		toggle_ui_button = Button.new()
		toggle_ui_button.name = "ToggleUiButton"
		toggle_ui_button.text = "👁️ Ẩn UI"
		toggle_ui_button.pressed.connect(func() -> void:
			set_hud_ui_hidden(not hud_ui_hidden)
		)
		hud_layer.add_child(toggle_ui_button)

		immortal_button = Button.new()
		immortal_button.name = "ImmortalModeButton"
		immortal_button.pressed.connect(func() -> void:
			set_hero_immortal(not hero_immortal_enabled)
		)
		hud_layer.add_child(immortal_button)
		_sync_immortal_button()

		monster_range_button = Button.new()
		monster_range_button.name = "MonsterRangeButton"
		monster_range_button.pressed.connect(func() -> void:
			set_show_monster_ranges(not show_monster_ranges_enabled)
		)
		hud_layer.add_child(monster_range_button)
		_sync_monster_range_button()

		boss_spawn_button = Button.new()
		boss_spawn_button.name = "SpawnBossButton"
		boss_spawn_button.text = "⚡ Gọi Boss Drum"
		boss_spawn_button.add_theme_color_override("font_color", Color(1.0, 0.35, 0.35, 1.0))
		boss_spawn_button.pressed.connect(func() -> void:
			spawn_boss_drum_now()
		)
		hud_layer.add_child(boss_spawn_button)

	if _arena_theme != null:
		for c in hud_layer.get_children():
			if c is Control and c != mobile_pad:
				(c as Control).theme = _arena_theme
	_apply_hud_safe_area()


func _sync_immortal_button() -> void:
	if immortal_button == null or not is_instance_valid(immortal_button):
		return
	if hero_immortal_enabled:
		immortal_button.text = "🛡️ Bất tử: BẬT"
		immortal_button.add_theme_color_override("font_color", Color(1.0, 0.90, 0.30, 1.0))
	else:
		immortal_button.text = "🛡️ Bất tử: TẮT"
		immortal_button.remove_theme_color_override("font_color")


func _sync_monster_range_button() -> void:
	if monster_range_button == null or not is_instance_valid(monster_range_button):
		return
	if show_monster_ranges_enabled:
		monster_range_button.text = "🎯 Tầm quái: BẬT"
		monster_range_button.add_theme_color_override("font_color", Color(0.45, 0.96, 0.62, 1.0))
	else:
		monster_range_button.text = "🎯 Tầm quái: TẮT"
		monster_range_button.remove_theme_color_override("font_color")


func set_hero_immortal(enabled: bool) -> void:
	hero_immortal_enabled = enabled
	_ensure_field_manager()
	field_manager.set_player_immortal(enabled)
	_sync_immortal_button()
	_update_hud()
	queue_redraw()


func set_show_monster_ranges(enabled: bool) -> void:
	show_monster_ranges_enabled = enabled
	show_grid_overlay = enabled
	_ensure_field_manager()
	field_manager.show_monster_ranges = enabled
	_sync_monster_range_button()
	_update_hud()
	queue_redraw()


func spawn_boss_drum_now() -> Dictionary:
	if not field_mode_enabled:
		enable_field_mode(true, true)
	elif field_manager != null and (not field_manager.player_spawned or player_node == null):
		set_field_hero_visible(true)
	if field_manager == null:
		return {}
	var b := field_manager.spawn_boss_drum() as Dictionary
	_update_hud()
	queue_redraw()
	return b


func set_hud_ui_hidden(hidden: bool) -> void:
	hud_ui_hidden = hidden
	var vis_flag := not hidden
	for n in [hud_label, pixel_perfect_button, ruler_button, pad_settings_button, immortal_button, monster_range_button, boss_spawn_button, summon_button, item_toggle_button, item_drop_test_button, item_pickup_button]:
		if n != null and is_instance_valid(n):
			n.visible = vis_flag
	if toggle_ui_button != null:
		toggle_ui_button.text = "👁️ Hiện UI" if hidden else "👁️ Ẩn UI"
	_apply_hud_safe_area()


func enable_field_mode(enabled: bool, spawn_hero: bool = false) -> void:
	field_mode_enabled = enabled
	_ensure_field_manager()
	if not enabled:
		field_manager.clear_all()
		var role_hud := get_node_or_null("ArenaRoleHud") as CanvasLayer
		if role_hud != null:
			role_hud.visible = true
		return
	utility_ai_enabled = false
	_clear_fighter(dummy_node)
	dummy_node = null
	_clear_fighter(player_node)
	player_node = null
	_clear_dropped_items()
	var role_hud := get_node_or_null("ArenaRoleHud") as CanvasLayer
	if role_hud != null:
		role_hud.visible = false
	field_manager.start_field(false)
	set_field_hero_visible(spawn_hero)
	_update_follow_camera()
	_update_hud()
	queue_redraw()


func _spawn_field_hero(char_id: String) -> bool:
	var entry := _find_character_entry(char_id)
	if entry.is_empty():
		return false
	var prefab_path := _resolve_prefab_path(entry)
	if prefab_path.is_empty() or not ResourceLoader.exists(prefab_path):
		return false
	var loaded_res: Resource = ResourceLoader.load(prefab_path)
	if not (loaded_res is PackedScene):
		return false
	var packed := loaded_res as PackedScene
	_clear_fighter(player_node)
	var p_inst: Node = packed.instantiate()
	if not (p_inst is Node2D):
		return false
	player_node = p_inst as Node2D
	var parent_layer: Node = fighters_layer if fighters_layer != null else self
	parent_layer.add_child(player_node)
	player_node.name = "PlayerFighter"
	active_character_id = char_id
	player_facing_left = false
	player_vy = 0.0
	_player_drop_timer_s = 0.0
	_prev_player_on_ground = not _is_flying_entry(entry)
	_step_dust_accum_px = 0.0
	char_scale = _get_entry_default_scale(entry)
	_player_turn_boost_s = 0.0
	_player_turn_elapsed_s = 0.0
	_player_turn_duration_s = 0.0
	player_light_cooldown_s = 0.0
	_player_light_clip_active = false
	if player_node.get("external_orb_managed") != null:
		player_node.set("external_orb_managed", true)
	_update_walkable_bounds()
	var spawn_x := walkable_min_x + 24.0
	var spawn_y := _get_entry_flight_y(entry) if _is_flying_entry(entry) else _ground_y_at(spawn_x)
	_configure_fighter_instance(player_node, spawn_x, spawn_y, false, char_scale)
	player_node.z_index = get_fighter_layer_z(char_id, true)
	return true


func set_field_hero_visible(visible_flag: bool) -> void:
	_ensure_field_manager()
	active_character_id = "drum"
	if visible_flag:
		if _spawn_field_hero("drum"):
			field_manager.player_spawned = true
			field_manager.player_hp = field_manager.player_max_hp
			field_manager.player_mana = 0.0
			field_manager.player_dead = false
			field_manager.player_respawn_timer_s = 0.0
			field_manager.refresh_pointer_valid()
			if mobile_pad != null and is_instance_valid(mobile_pad):
				mobile_pad.visible = true
				mobile_pad.configure_for_character("drum", _collect_clip_names(player_node), false)
				_sync_field_pad_state()
	else:
		_clear_fighter(player_node)
		player_node = null
		field_manager.player_spawned = false
		field_manager.player_dead = false
		field_manager.pointer_slot_id = ""
		field_manager.pointer_item_node = null
		if mobile_pad != null and is_instance_valid(mobile_pad):
			mobile_pad.configure_for_character("", PackedStringArray(), false)
			mobile_pad.visible = false
	if toggle_hero_button != null:
		toggle_hero_button.text = "👤 Ẩn Tướng (Drum)" if (field_manager != null and field_manager.player_spawned) else "👤 Hiện Tướng (Drum)"
	_update_follow_camera()
	_update_hud()
	queue_redraw()


func set_ruler_modal_visible(visible_flag: bool) -> void:
	ruler_modal_visible = visible_flag
	if ruler_modal != null and is_instance_valid(ruler_modal):
		ruler_modal.visible = visible_flag
	if visible_flag:
		_sync_ruler_ui()
	else:
		ruler_pick_mode = false
		_ruler_dragging = false
		_ruler_awaiting_b = false
		if ruler_modal != null and is_instance_valid(ruler_modal):
			ruler_modal.set_pick_mode(false)
	queue_redraw()


func screen_to_world_pos(screen_pos: Vector2) -> Vector2:
	if DisplayServer.get_name() != "headless" and get_viewport() != null:
		var xf := get_viewport().get_canvas_transform()
		if xf != Transform2D.IDENTITY:
			return xf.affine_inverse() * screen_pos
	var vis := _get_visible_logic_size()
	var cam_pos := _arena_camera.position if _arena_camera != null else Vector2(float(viewport_width) * 0.5, float(viewport_height) * 0.5)
	var cam_z := _arena_camera.zoom if _arena_camera != null else Vector2.ONE
	return cam_pos + (screen_pos - vis * 0.5) / Vector2(maxf(0.01, cam_z.x), maxf(0.01, cam_z.y))


func set_ruler_points(point_a: Vector2, point_b: Vector2) -> Dictionary:
	ruler_point_a = Vector2(roundf(point_a.x), roundf(point_a.y))
	ruler_point_b = Vector2(roundf(point_b.x), roundf(point_b.y))
	ruler_has_a = true
	ruler_has_b = true
	_sync_ruler_ui()
	return get_ruler_metrics()


func measure_player_enemy_distance() -> Dictionary:
	if player_node != null and dummy_node != null:
		ruler_point_a = Vector2(roundf(player_node.position.x), roundf(player_node.position.y))
		ruler_point_b = Vector2(roundf(dummy_node.position.x), roundf(dummy_node.position.y))
		ruler_has_a = true
		ruler_has_b = true
	_sync_ruler_ui()
	return get_ruler_metrics()


func get_ruler_metrics() -> Dictionary:
	var p_entry := _find_character_entry_ro(active_character_id)
	var e_entry := _find_character_entry_ro(enemy_character_id)
	var p_dims := _get_body_dims(p_entry)
	var e_dims := _get_body_dims(e_entry)
	var pw := float(p_dims.x) if p_dims.x > 0 else 140.0
	var ph := float(p_dims.y) if p_dims.y > 0 else 140.0
	var ew := float(e_dims.x) if e_dims.x > 0 else 140.0
	var eh := float(e_dims.y) if e_dims.y > 0 else 140.0
	var p_pos := player_node.position if player_node != null else Vector2(player_spawn_x, ground_y)
	var e_pos := dummy_node.position if dummy_node != null else Vector2(dummy_spawn_x, ground_y)
	var r_a: Rect2 = UtilityAIControllerScript.compute_body_rect(p_pos.x, p_pos.y, pw, ph, char_scale)
	var r_b: Rect2 = UtilityAIControllerScript.compute_body_rect(e_pos.x, e_pos.y, ew, eh, enemy_scale)
	var edge_gap: float = UtilityAIControllerScript.compute_edge_distance(r_a, r_b)
	var dx := absf(ruler_point_b.x - ruler_point_a.x) if (ruler_has_a and ruler_has_b) else 0.0
	var dy := absf(ruler_point_b.y - ruler_point_a.y) if (ruler_has_a and ruler_has_b) else 0.0
	var dist := ruler_point_a.distance_to(ruler_point_b) if (ruler_has_a and ruler_has_b) else 0.0
	var vis := _get_visible_logic_size()
	var cam_pos := _arena_camera.position if _arena_camera != null else Vector2(float(viewport_width) * 0.5, float(viewport_height) * 0.5)
	var cam_z := _arena_camera.zoom.x if _arena_camera != null else 1.0
	return {
		"modal_visible": ruler_modal_visible,
		"pick_mode": ruler_pick_mode,
		"grid_enabled": ruler_grid_enabled,
		"has_a": ruler_has_a,
		"has_b": ruler_has_b,
		"point_a": [ruler_point_a.x, ruler_point_a.y],
		"point_b": [ruler_point_b.x, ruler_point_b.y],
		"dx_world_px": dx,
		"dy_world_px": dy,
		"dist_world_px": dist,
		"player_pos": [p_pos.x, p_pos.y],
		"enemy_pos": [e_pos.x, e_pos.y],
		"player_size_px": [pw * char_scale, ph * char_scale],
		"enemy_size_px": [ew * enemy_scale, eh * enemy_scale],
		"player_enemy_center_dx": absf(e_pos.x - p_pos.x),
		"player_enemy_dy": absf(e_pos.y - p_pos.y),
		"player_enemy_edge_gap": edge_gap,
		"effective_scale": float(display_layout_info.get("effective_scale", 1.0)),
		"camera_zoom": cam_z,
		"camera_pos": [cam_pos.x, cam_pos.y],
		"visible_logic_size": [vis.x, vis.y],
	}


func _sync_ruler_ui() -> void:
	if ruler_modal != null and is_instance_valid(ruler_modal):
		ruler_modal.update_metrics(get_ruler_metrics())
	queue_redraw()

func _on_shenron_summon_ready() -> void:
	if wish_panel != null:
		wish_panel.visible = true

func _on_wish_button_pressed(wish_id: String) -> void:
	if shenron_summon != null:
		shenron_summon.select_wish(wish_id)

func _on_shenron_wish_selected(wish: Dictionary) -> void:
	if wish_panel != null:
		wish_panel.visible = false
	if wish_notice_label != null:
		wish_notice_label.text = str(wish.get("notice", ""))
		wish_notice_label.visible = not wish_notice_label.text.is_empty()
		_wish_notice_timer_s = 2.8
	if summon_button != null and shenron_summon != null and shenron_summon.dismissing:
		summon_button.text = "Đang thu hồi..."
		summon_button.disabled = true

func _on_shenron_dismissed() -> void:
	if wish_panel != null:
		wish_panel.visible = false
	if summon_button != null:
		summon_button.text = "Gọi Shenron"
		summon_button.disabled = false

func _on_summon_button_pressed() -> void:
	if shenron_summon.active:
		if not shenron_summon.dismissing:
			if wish_panel != null:
				wish_panel.visible = false
			if shenron_summon.begin_dismiss():
				summon_button.text = "Đang thu hồi..."
				summon_button.disabled = true
	elif player_node != null:
		var entry := _find_character_entry(active_character_id)
		var dims := _get_body_dims(entry)
		var source_pos := player_node.position - Vector2(0, float(dims.y) * char_scale * 0.5)
		var camera_x := _arena_camera.position.x if _arena_camera != null else player_node.position.x
		shenron_summon.position = Vector2(camera_x - float(viewport_width) * 0.5, _ground_y_at(player_node.position.x) - ground_y)
		if wish_notice_label != null:
			wish_notice_label.visible = false
		_wish_notice_timer_s = 0.0
		if shenron_summon.start_from(source_pos - shenron_summon.position):
			_play_fighter_clip(player_node, "idle")
			player_vy = 0.0
			summon_button.text = "Thu hồi Shenron"
			summon_button.disabled = false



func load_stage_and_roster() -> void:
	stage_config = _read_json_dict(STAGE_JSON_PATH)
	var vp: Dictionary = stage_config.get("viewport", {})
	viewport_width = int(vp.get("width", 1920))
	viewport_height = int(vp.get("height", 1080))
	var gp: Dictionary = stage_config.get("gameplay", {})
	ground_y = float(gp.get("ground_y", 840.0))
	var bounds: Array = gp.get("walkable_bounds_x", [140, 1780])
	if bounds.size() >= 2:
		walkable_min_x = float(bounds[0])
		walkable_max_x = float(bounds[1])
	player_spawn_x = float(gp.get("player_spawn_x", 560.0))
	dummy_spawn_x = float(gp.get("dummy_spawn_x", 1360.0))
	char_scale = float(gp.get("character_scale_default", 2.0))
	enemy_scale = char_scale
	var fl: Dictionary = gp.get("flight", {})
	fly_min_y = float(fl.get("min_y", 60.0))
	fly_default_y = float(fl.get("default_y", 250.0))
	fly_vertical_speed_px_per_s = float(fl.get("vertical_speed_px_per_s", 240.0))
	jump_velocity_px_per_s = float(gp.get("jump_velocity_px_per_s", -780.0))
	gravity_px_per_s2 = float(gp.get("gravity_px_per_s2", 2000.0))
	ai_controller.configure_from_stage(stage_config)

	terrain_config = _read_json_dict(TERRAIN_JSON_PATH)
	terrain_platforms.clear()
	var raw_plats: Variant = terrain_config.get("platforms", [])
	if raw_plats is Array:
		for p in raw_plats:
			if p is Dictionary:
				terrain_platforms.append(p)

	var roster := _read_json_dict(ROSTER_JSON_PATH)
	var chars_variant: Variant = roster.get("characters", [])
	roster_characters = chars_variant if chars_variant is Array else []
	var review_roster := _read_json_dict(REVIEW_ROSTER_JSON_PATH)
	var review_chars: Variant = review_roster.get("characters", [])
	if review_chars is Array:
		for review_entry in review_chars:
			if review_entry is Dictionary:
				roster_characters.append(review_entry)
	var sil_doc := _read_json_dict(BODY_SILHOUETTES_JSON_PATH)
	var sil_chars: Variant = sil_doc.get("characters", {})
	_body_silhouettes = sil_chars if sil_chars is Dictionary else {}
	_update_walkable_bounds()


func _read_json_dict(res_path: String) -> Dictionary:
	if not FileAccess.file_exists(res_path):
		return {}
	var txt := FileAccess.get_file_as_string(res_path)
	var parsed: Variant = JSON.parse_string(txt)
	return parsed if parsed is Dictionary else {}


func _load_texture_2d(res_path: String) -> Texture2D:
	if res_path.is_empty():
		return null
	if ResourceLoader.exists(res_path):
		var loaded := ResourceLoader.load(res_path)
		if loaded is Texture2D:
			return loaded
	if FileAccess.file_exists(res_path):
		var bytes := FileAccess.get_file_as_bytes(res_path)
		var img := Image.new()
		var lower := res_path.to_lower()
		var err := ERR_FILE_UNRECOGNIZED
		if lower.ends_with(".jpg") or lower.ends_with(".jpeg"):
			err = img.load_jpg_from_buffer(bytes)
		elif lower.ends_with(".png"):
			err = img.load_png_from_buffer(bytes)
		if err == OK:
			return ImageTexture.create_from_image(img)
	return null


func _apply_stage_layout() -> void:
	var map_cfg: Dictionary = stage_config.get("map", {})
	var bg_path := str(map_cfg.get("background_res_path", "res://assets/maps/rocky_plateau/rocky-plateau-bg.jpg"))
	var bg_tex := _load_texture_2d(bg_path)
	if background_sprite != null and bg_tex != null:
		background_sprite.texture = bg_tex
		background_sprite.centered = false
		_update_background_cover()
	_setup_terrain_layer()
	queue_redraw()


func _get_visible_logic_size() -> Vector2:
	var vis: Variant = display_layout_info.get("visible_logic_size", [float(viewport_width), float(viewport_height)])
	if DisplayServer.get_name() == "headless" and display_layout_info.get("window_size", []) == [64, 64]:
		return Vector2(float(viewport_width), float(viewport_height))
	if vis is Array and vis.size() >= 2:
		return Vector2(maxf(1.0, float(vis[0])), maxf(1.0, float(vis[1])))
	return Vector2(float(viewport_width), float(viewport_height))


func _has_extended_terrain_steps() -> bool:
	return ResourceLoader.exists(EXTENDED_MAP_PATH)


func _get_terrain_sections() -> Array:
	if not _has_extended_terrain_steps():
		return [{"left_x": MAP_LEFT_X, "right_x": MAP_RIGHT_X, "ground_y": ground_y}]
	return [
		{"left_x": MAP_LEFT_X, "right_x": STEP_ONE_X, "ground_y": ground_y},
		{"left_x": STEP_ONE_X, "right_x": STEP_TWO_X, "ground_y": ground_y + STEP_ONE_DROP_Y},
		{"left_x": STEP_TWO_X, "right_x": STEP_THREE_X, "ground_y": ground_y + STEP_TWO_DROP_Y},
		{"left_x": STEP_THREE_X, "right_x": STEP_FOUR_X, "ground_y": ground_y + STEP_THREE_DROP_Y},
		{"left_x": STEP_FOUR_X, "right_x": MAP_RIGHT_X, "ground_y": ground_y + STEP_FOUR_DROP_Y},
	]


func _get_terrain_step_edges() -> Array[float]:
	if not _has_extended_terrain_steps():
		return []
	return [STEP_ONE_X, STEP_TWO_X, STEP_THREE_X, STEP_FOUR_X]


func _get_fighter_walk_bounds_x(entry: Dictionary, sc: float) -> Vector2:
	var vis_w := _get_visible_logic_size().x
	var center_x := float(viewport_width) * 0.5
	var view_left := MAP_LEFT_X if _has_extended_terrain_steps() else (center_x - vis_w * 0.5)
	var view_right := MAP_RIGHT_X if _has_extended_terrain_steps() else (center_x + vis_w * 0.5)
	var dims := _get_body_dims(entry)
	var raw_half := (float(dims.x) * sc * 0.5) if dims.x > 0 else (70.0 * sc)
	var pad := clampf(raw_half, 16.0, maxf(16.0, vis_w * 0.45))
	return Vector2(view_left + pad, view_right - pad)


func _update_walkable_bounds() -> void:
	var pid := active_character_id if not active_character_id.is_empty() else default_character_id
	var p_entry := _find_character_entry_ro(pid)
	var p_bounds := _get_fighter_walk_bounds_x(p_entry, char_scale)
	walkable_min_x = p_bounds.x
	walkable_max_x = p_bounds.y
	if player_node != null:
		player_node.position.x = clampf(player_node.position.x, walkable_min_x, walkable_max_x)
	if is_instance_valid(ai_controller):
		var e_entry := _find_character_entry_ro(enemy_character_id if not enemy_character_id.is_empty() else pid)
		var e_bounds := _get_fighter_walk_bounds_x(e_entry, enemy_scale)
		if dummy_node != null:
			dummy_node.position.x = clampf(dummy_node.position.x, e_bounds.x, e_bounds.y)
		ai_controller.zone_min_x = clampf(ai_controller.zone_min_x, e_bounds.x, e_bounds.y)
		ai_controller.zone_max_x = clampf(ai_controller.zone_max_x, ai_controller.zone_min_x, e_bounds.y)


func _update_background_cover() -> void:
	if background_sprite == null or background_sprite.texture == null:
		_update_walkable_bounds()
		return
	var tex_size := background_sprite.texture.get_size()
	if tex_size.x <= 0.0 or tex_size.y <= 0.0:
		_update_walkable_bounds()
		return
	var vis := _get_visible_logic_size()
	if _has_extended_terrain_steps():
		var extension := _load_texture_2d(EXTENDED_MAP_PATH)
		if extension != null:
			background_sprite.texture = extension
			background_sprite.scale = Vector2.ONE
			background_sprite.position = Vector2(MAP_LEFT_X, MAP_TOP_Y)
			_setup_foreground_trees()
			_update_walkable_bounds()
			_update_follow_camera()
			queue_redraw()
			return
	var vis_w := vis.x
	var vis_h := vis.y
	var cover := maxf(vis_w / float(viewport_width), vis_h / float(viewport_height))
	var render_w := float(viewport_width) * cover
	background_sprite.scale = Vector2(render_w / tex_size.x, float(viewport_height) * cover / tex_size.y)
	background_sprite.position = Vector2(float(viewport_width) * 0.5 - render_w * 0.5, ground_y * (1.0 - cover))
	if _bg_left_ext != null:
		_bg_left_ext.visible = false
	if _bg_right_ext != null:
		_bg_right_ext.visible = false
	_update_walkable_bounds()
	_update_follow_camera()
	queue_redraw()


func _setup_foreground_trees() -> void:
	if _foreground_trees != null and is_instance_valid(_foreground_trees):
		return
	var planted_texture := _load_texture_2d(FOREGROUND_PLANTED_TREES_PATH)
	var tree_texture := _load_texture_2d(FOREGROUND_TREES_PATH)
	var complete_texture := _load_texture_2d(FOREGROUND_TREES_COMPLETE_PATH)
	if planted_texture == null and (tree_texture == null or complete_texture == null):
		return
	_foreground_trees = Node2D.new()
	_foreground_trees.name = "ReviewForegroundTrees"
	_foreground_trees.z_index = -20
	add_child(_foreground_trees)
	# All 3 trees keep their flared roots embedded into the rear grass band (planted-trees-review.png)
	# so they grow naturally out of the ground instead of stopping abruptly at the trunk cut.
	var tree_regions := [Rect2(0.0, 0.0, 598.0, 907.0), Rect2(598.0, 0.0, 741.0, 1067.0), Rect2(1339.0, 0.0, 688.0, 1088.0)]
	var fallback_regions := [Rect2(0.0, 0.0, 470.0, 880.0), Rect2(0.0, 0.0, 724.0, 995.0), Rect2(724.0, 0.0, 724.0, 1015.0)]
	var trunk_source_x := [264.51, 298.61, 312.60]
	var trunk_world_x := [4695.0, 5420.0, 6050.0]
	var root_bottom_src_y := [904.0, 1064.0, 1085.0]
	var rear_grass_world_y := [828.0, 888.0, 954.0]
	for i in range(3):
		var atlas := AtlasTexture.new()
		if planted_texture != null:
			atlas.atlas = planted_texture
			atlas.region = tree_regions[i]
		else:
			atlas.atlas = tree_texture if i == 0 else complete_texture
			atlas.region = fallback_regions[i]
		var tree_sprite := Sprite2D.new()
		tree_sprite.name = "ForegroundTree%d" % (i + 1)
		tree_sprite.texture = atlas
		tree_sprite.centered = false
		tree_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		tree_sprite.scale = Vector2(0.70, 0.94)
		tree_sprite.position = Vector2(trunk_world_x[i] - trunk_source_x[i] * tree_sprite.scale.x, rear_grass_world_y[i] - root_bottom_src_y[i] * tree_sprite.scale.y)
		_foreground_trees.add_child(tree_sprite)


func _update_follow_camera() -> void:
	if _arena_camera == null:
		return
	var vis := _get_visible_logic_size()
	var has_ext := _has_extended_terrain_steps()
	var left_b := MAP_LEFT_X if has_ext else 0.0
	var right_b := MAP_RIGHT_X if has_ext else float(viewport_width)
	var top_b := MAP_TOP_Y if has_ext else 0.0
	var bottom_b := MAP_BOTTOM_Y if has_ext else float(viewport_height)
	var map_w := maxf(1.0, right_b - left_b)
	var map_h := maxf(1.0, bottom_b - top_b)

	var cam_zoom := maxf(1.0, maxf(vis.x / map_w, vis.y / map_h)) if has_ext else 1.0
	_arena_camera.zoom = Vector2(cam_zoom, cam_zoom)

	var eff_half_w := (vis.x / cam_zoom) * 0.5
	var eff_half_h := (vis.y / cam_zoom) * 0.5
	var min_cam_x := left_b + eff_half_w
	var max_cam_x := right_b - eff_half_w
	var min_cam_y := top_b + eff_half_h
	var max_cam_y := bottom_b - eff_half_h

	var target_x := player_node.position.x if player_node != null else ((left_b + eff_half_w) if field_mode_enabled else float(viewport_width) * 0.5)
	var cam_x := (left_b + right_b) * 0.5 if min_cam_x >= max_cam_x else clampf(target_x, min_cam_x, max_cam_x)

	var base_cam_y := float(viewport_height) * 0.5
	var follow_dy := 0.0
	if player_node != null:
		if player_node.position.y > ground_y:
			follow_dy = minf(60.0, (player_node.position.y - ground_y) * 0.45)
		elif player_node.position.y < 180.0:
			follow_dy = maxf(-120.0, (player_node.position.y - 180.0) * 0.6)
	var target_y := base_cam_y + follow_dy
	var cam_y := (top_b + bottom_b) * 0.5 if min_cam_y >= max_cam_y else clampf(target_y, min_cam_y, max_cam_y)
	_arena_camera.position = Vector2(cam_x, cam_y)


func _get_terrain_step_specs() -> Array[Dictionary]:
	if not _has_extended_terrain_steps():
		return []
	return [
		{"drop_x": STEP_ONE_X, "wall_x": STEP_ONE_WALL_X, "upper_y": ground_y, "lower_y": ground_y + STEP_ONE_DROP_Y},
		{"drop_x": STEP_TWO_X, "wall_x": STEP_TWO_WALL_X, "upper_y": ground_y + STEP_ONE_DROP_Y, "lower_y": ground_y + STEP_TWO_DROP_Y},
		{"drop_x": STEP_THREE_X, "wall_x": STEP_THREE_WALL_X, "upper_y": ground_y + STEP_TWO_DROP_Y, "lower_y": ground_y + STEP_THREE_DROP_Y},
		{"drop_x": STEP_FOUR_X, "wall_x": STEP_FOUR_WALL_X, "upper_y": ground_y + STEP_THREE_DROP_Y, "lower_y": ground_y + STEP_FOUR_DROP_Y},
	]


static func _step_wall_x_at_y(spec: Dictionary, y: float) -> float:
	var drop_x := float(spec["drop_x"])
	var wall_x := float(spec["wall_x"])
	var upper_y := float(spec["upper_y"])
	var lower_y := float(spec["lower_y"])
	if y <= upper_y:
		return drop_x
	if y >= lower_y:
		return wall_x
	var t := (y - upper_y) / maxf(1.0, lower_y - upper_y)
	return lerpf(drop_x, wall_x, t)


func _ground_y_at(world_x: float) -> float:
	if not _has_extended_terrain_steps():
		return ground_y
	if world_x < STEP_ONE_X:
		return ground_y
	if world_x < STEP_TWO_X:
		return ground_y + STEP_ONE_DROP_Y
	if world_x < STEP_THREE_X:
		return ground_y + STEP_TWO_DROP_Y
	if world_x < STEP_FOUR_X:
		return ground_y + STEP_THREE_DROP_Y
	return ground_y + STEP_FOUR_DROP_Y


func terrain_blocks_segment(from_pos: Vector2, to_pos: Vector2) -> bool:
	# The same painted cliff cross-section drives projectile hits and solid step walls.
	if to_pos.y >= _ground_y_at(to_pos.x):
		return true
	for spec in _get_terrain_step_specs():
		var upper_y := float(spec["upper_y"])
		var lower_y := float(spec["lower_y"])
		var drop_x := float(spec["drop_x"])
		var wall_x := float(spec["wall_x"])
		var to_wall_x := _step_wall_x_at_y(spec, to_pos.y)
		if to_pos.y >= upper_y and to_pos.x <= to_wall_x:
			return true
		var min_sx := minf(from_pos.x, to_pos.x)
		var max_sx := maxf(from_pos.x, to_pos.x)
		if max_sx >= drop_x and min_sx <= wall_x:
			for frac in [0.25, 0.5, 0.75, 1.0]:
				var pt := from_pos.lerp(to_pos, frac)
				if pt.y >= upper_y and pt.y <= lower_y + 2.0 and pt.x <= _step_wall_x_at_y(spec, pt.y):
					return true
	return false


func _can_cross_terrain_step(from_x: float, to_x: float, foot_y: float, flying: bool = false) -> bool:
	var min_x := minf(from_x, to_x)
	var max_x := maxf(from_x, to_x)
	var clearance := 0.0 if flying else 2.0
	for spec in _get_terrain_step_specs():
		var drop_x := float(spec["drop_x"])
		var upper_y := float(spec["upper_y"])
		var wall_x := _step_wall_x_at_y(spec, foot_y)
		var guard_x := wall_x + 52.0 if not flying else wall_x
		if to_x < from_x and min_x <= guard_x and max_x >= drop_x:
			if foot_y > upper_y - clearance:
				return false
	return true


func _get_fighter_half_width_px(char_id: String, sc: float) -> float:
	var entry := _find_character_entry_ro(char_id)
	var dims := _get_body_dims(entry)
	return (float(dims.x) * sc * 0.5) if dims.x > 0 else (56.0 * sc)


func _resolve_terrain_horizontal_move(from_x: float, raw_target_x: float, foot_y: float, flying: bool, min_bound: float, max_bound: float, body_half_w: float = 0.0) -> float:
	var target_x := clampf(raw_target_x, min_bound, max_bound)
	if is_equal_approx(from_x, target_x):
		return target_x
	var clearance := 0.0 if flying else 2.0
	var base_pad := 0.0 if flying else clampf(body_half_w * 0.65, 14.0, 48.0)
	var specs := _get_terrain_step_specs()
	if target_x < from_x:
		for i in range(specs.size() - 1, -1, -1):
			var spec: Dictionary = specs[i]
			var drop_x := float(spec["drop_x"])
			var upper_y := float(spec["upper_y"])
			var lower_y := float(spec["lower_y"])
			if foot_y > upper_y - clearance:
				var wall_x_at_foot := _step_wall_x_at_y(spec, foot_y)
				var height_ratio := clampf((foot_y - upper_y) / maxf(1.0, lower_y - upper_y), 0.25, 1.0)
				var eff_pad := base_pad * height_ratio
				var wall_stop_x := wall_x_at_foot + eff_pad
				if from_x >= wall_stop_x and target_x < wall_stop_x:
					target_x = maxf(target_x, wall_stop_x)
				elif from_x >= drop_x and target_x < from_x and from_x < wall_stop_x:
					target_x = from_x
	else:
		# Left-facing uphill checks remain no-op for right-descending rocky plateau steps.
		for spec in specs:
			var edge_x := float(spec["drop_x"])
			var left_y := float(spec["upper_y"])
			var right_y := float(spec["lower_y"])
			if right_y < left_y and foot_y > right_y - clearance:
				var stop_x := (edge_x - base_pad) if from_x <= edge_x - base_pad else (edge_x - 0.01)
				if from_x < edge_x and target_x > stop_x:
					target_x = minf(target_x, stop_x)
	return clampf(target_x, min_bound, max_bound)


func _move_node_horizontal(node: Node2D, distance: float, flying: bool, min_bound: float, max_bound: float, body_half_w: float = 0.0) -> float:
	if node == null:
		return 0.0
	var from_x := node.position.x
	var resolved_x := _resolve_terrain_horizontal_move(from_x, from_x + distance, node.position.y, flying, min_bound, max_bound, body_half_w)
	node.position.x = resolved_x
	return resolved_x - from_x


func _move_player_horizontal(distance: float, flying: bool = false) -> void:
	if player_node == null:
		return
	var half_w := _get_fighter_half_width_px(active_character_id, char_scale)
	_move_node_horizontal(player_node, distance, flying, walkable_min_x, walkable_max_x, half_w)


func _setup_terrain_layer() -> void:
	if _terrain_root != null and is_instance_valid(_terrain_root):
		_terrain_root.queue_free()
	_parallax_nodes.clear()
	_ground_tilemap = null
	if terrain_config.is_empty():
		return

	_terrain_root = Node2D.new()
	_terrain_root.name = "TerrainLayer"
	_terrain_root.z_index = -10
	_terrain_root.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_terrain_root.visible = show_pixel_terrain
	add_child(_terrain_root)

	var keep_orig_bg := str((terrain_config.get("backdrop", {}) as Dictionary).get("mode", "")) == "original_jpg"
	if background_sprite != null:
		var bg_parent := background_sprite.get_parent() as Node2D
		if bg_parent != null:
			bg_parent.z_index = -30
			bg_parent.visible = true if keep_orig_bg else (not show_pixel_terrain)

	var p_dict: Dictionary = terrain_config.get("parallax", {})
	for lid in ["sky_clouds", "far_canyon_river", "mid_cliffs"]:
		if not p_dict.has(lid):
			continue
		var pinfo: Dictionary = p_dict[lid]
		var tex := _load_texture_2d(str(pinfo.get("res_path", "")))
		if tex == null:
			continue
		var p_sc := float(pinfo.get("render_scale", 2.0))
		var top_y := float(pinfo.get("top_y_world_px", 0.0))
		var scroll := float(pinfo.get("scroll_factor", 0.2))
		var span_w := tex.get_size().x * p_sc
		var base_x := (float(viewport_width) - span_w) * 0.5
		var copies: Array[Sprite2D] = []
		for off_i in [-1, 0, 1]:
			var sp := Sprite2D.new()
			sp.name = "Parallax_%s_%d" % [lid, off_i]
			sp.texture = tex
			sp.centered = false
			sp.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			sp.scale = Vector2(p_sc, p_sc)
			sp.position = Vector2(base_x + float(off_i) * span_w, top_y)
			_terrain_root.add_child(sp)
			copies.append(sp)
		_parallax_nodes.append({"base_x": base_x, "span_w": span_w, "top_y": top_y, "scroll": scroll, "sprites": copies})

	# Ground TileMapLayer + TileSet (32x32 @ 2x = 64x64)
	var ts_cfg: Dictionary = terrain_config.get("tileset", {})
	var g_cfg: Dictionary = terrain_config.get("ground", {})
	var ts_tex := _load_texture_2d(str(ts_cfg.get("res_path", "")))
	if ts_tex != null:
		var tile_px := int(ts_cfg.get("tile_px", 32))
		var cols := maxi(1, int(ts_cfg.get("columns", 10)))
		var g_scale := float(g_cfg.get("render_scale", 2.0))
		var surf_top_y := float(g_cfg.get("surface_top_y", ground_y - 16.0))
		var tset := TileSet.new()
		tset.tile_size = Vector2i(tile_px, tile_px)
		var atlas_src := TileSetAtlasSource.new()
		atlas_src.texture = ts_tex
		atlas_src.texture_region_size = Vector2i(tile_px, tile_px)
		var rows := maxi(1, int(ts_cfg.get("rows", 3)))
		for r in range(rows):
			for c in range(cols):
				atlas_src.create_tile(Vector2i(c, r))
		tset.add_source(atlas_src, 0)

		_ground_tilemap = TileMapLayer.new()
		_ground_tilemap.name = "GroundTileMap"
		_ground_tilemap.tile_set = tset
		_ground_tilemap.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		_ground_tilemap.scale = Vector2(g_scale, g_scale)
		_ground_tilemap.position = Vector2(0.0, surf_top_y)
		# The review panorama contains its own foreground; the old tiled overlay ended mid-step.
		_ground_tilemap.visible = not ResourceLoader.exists(EXTENDED_MAP_PATH)
		for gx in range(-16, 56):
			var c_idx := posmod(gx, cols)
			for gy in range(12):
				_ground_tilemap.set_cell(Vector2i(gx, gy), 0, Vector2i(c_idx, mini(gy, rows - 1)))
		_terrain_root.add_child(_ground_tilemap)

	# Solid stepped terrain: tops support actors and vertical faces stop skills/projectiles.
	var ground_body := StaticBody2D.new()
	ground_body.name = "GroundFloorCollider"
	for section in _get_terrain_sections():
		var left_x := float(section["left_x"])
		var right_x := float(section["right_x"])
		var top_y := float(section["ground_y"])
		var ground_shape := CollisionShape2D.new()
		var ground_rect := RectangleShape2D.new()
		ground_rect.size = Vector2(right_x - left_x, 1400.0 - top_y)
		ground_shape.shape = ground_rect
		ground_shape.position = Vector2((left_x + right_x) * 0.5, (top_y + 1400.0) * 0.5)
		ground_body.add_child(ground_shape)
	_terrain_root.add_child(ground_body)

	# One-Way Rocky Platforms (Sprite2D + StaticBody2D collider)
	var ps_cfg: Dictionary = terrain_config.get("platforms_sheet", {})
	var ps_tex := _load_texture_2d(str(ps_cfg.get("res_path", "")))
	var pieces: Dictionary = ps_cfg.get("pieces", {})
	for plat in terrain_platforms:
		var px := float(plat.get("x", 0.0))
		var py := float(plat.get("y", ground_y))
		var pw := float(plat.get("w", 256.0))
		var pkey := str(plat.get("tile_key", ""))
		if ps_tex != null and pieces.has(pkey):
			var pm: Dictionary = pieces[pkey]
			var rect_arr: Array = pm.get("rect_px", [0, 0, 160, 50])
			var off_y_2x := float(pm.get("surface_offset_y_2x", 10.0))
			var sp := Sprite2D.new()
			sp.name = "Platform_%s" % str(plat.get("id", pkey))
			sp.texture = ps_tex
			sp.region_enabled = true
			sp.region_rect = Rect2(float(rect_arr[0]), float(rect_arr[1]), float(rect_arr[2]), float(rect_arr[3]))
			sp.centered = false
			sp.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			sp.scale = Vector2(2.0, 2.0)
			sp.position = Vector2(px, py - off_y_2x)
			_terrain_root.add_child(sp)
		var body := StaticBody2D.new()
		body.name = "PlatformBody_%s" % str(plat.get("id", pkey))
		var cs := CollisionShape2D.new()
		var rect_shape := RectangleShape2D.new()
		rect_shape.size = Vector2(pw, 16.0)
		cs.shape = rect_shape
		cs.one_way_collision = bool(plat.get("one_way", true))
		cs.position = Vector2(px + pw * 0.5, py + 8.0)
		body.add_child(cs)
		_terrain_root.add_child(body)

	var dust_cfg: Dictionary = terrain_config.get("dust_fx", {})
	_dust_fx_tex = _load_texture_2d(str(dust_cfg.get("res_path", "")))
	if _dust_fx_layer == null or not is_instance_valid(_dust_fx_layer):
		_dust_fx_layer = Node2D.new()
		_dust_fx_layer.name = "GroundDustLayer"
		_dust_fx_layer.z_index = 9
		_dust_fx_layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		add_child(_dust_fx_layer)


func get_nearest_support_y_below(pos_x: float, pos_y: float) -> float:
	var best_y := _ground_y_at(pos_x)
	for plat in terrain_platforms:
		if not (plat is Dictionary):
			continue
		var px := float(plat.get("x", 0.0))
		var pw := float(plat.get("w", 0.0))
		var py := float(plat.get("y", ground_y))
		if pos_x >= px - 10.0 and pos_x <= px + pw + 10.0 and pos_y <= py + 6.0 and py < best_y:
			best_y = py
	return best_y


func _try_start_player_jump(jump_pressed: bool, drop_pressed: bool) -> bool:
	if player_node == null:
		return false
	var px := player_node.position.x
	var prev_y := player_node.position.y
	if drop_pressed and prev_y < _ground_y_at(px) - 4.0:
		_player_drop_timer_s = 0.22
		player_node.position.y = prev_y + 2.0
		return false
	var pre_sup_y := get_nearest_support_y_below(px, prev_y)
	if jump_pressed and prev_y >= pre_sup_y - 2.0 and player_vy >= 0.0:
		player_vy = jump_velocity_px_per_s
		_spawn_ground_dust(px, pre_sup_y, 0.9)
		return true
	return false


func _integrate_player_vertical(delta: float, jumped: bool = false) -> Dictionary:
	if player_node == null:
		return {"y": ground_y, "vy": 0.0, "support_y": ground_y, "on_ground": true, "landed": false, "jumped": false}
	var px := player_node.position.x
	var prev_y := player_node.position.y
	if _player_drop_timer_s > 0.0:
		_player_drop_timer_s = maxf(0.0, _player_drop_timer_s - delta)

	var sup_y := _ground_y_at(px)
	if not jumped and prev_y < sup_y - 0.5 and player_vy == 0.0:
		player_vy = gravity_px_per_s2 * delta
	var step_dy := player_vy * delta
	if not jumped and prev_y < sup_y - 0.5 and player_vy >= 0.0 and step_dy < 2.0:
		step_dy = minf(2.0, sup_y - prev_y)
	var next_y := prev_y + step_dy
	var landed := false
	if _player_drop_timer_s <= 0.0 and player_vy >= 0.0:
		for plat in terrain_platforms:
			if not (plat is Dictionary):
				continue
			var plat_x := float(plat.get("x", 0.0))
			var plat_w := float(plat.get("w", 0.0))
			var plat_y := float(plat.get("y", ground_y))
			if px >= plat_x - 10.0 and px <= plat_x + plat_w + 10.0 and prev_y <= plat_y + 6.0 and next_y >= plat_y and plat_y < sup_y:
				sup_y = plat_y

	if next_y >= sup_y:
		if not _prev_player_on_ground and player_vy >= 160.0:
			landed = true
			_spawn_ground_dust(px, sup_y, clampf(player_vy / 780.0, 0.65, 1.3))
		player_node.position.y = sup_y
		player_vy = 0.0
		_prev_player_on_ground = true
	else:
		player_node.position.y = next_y
		player_vy += gravity_px_per_s2 * delta
		_prev_player_on_ground = false

	# Keep descending fighters clear of painted cliff faces instead of landing inside [drop_x..wall_x].
	var post_y := player_node.position.y
	if not jumped and player_vy >= 0.0:
		for spec in _get_terrain_step_specs():
			var drop_x := float(spec["drop_x"])
			var upper_y := float(spec["upper_y"])
			var clear_x := _step_wall_x_at_y(spec, post_y) + 6.0
			if post_y > upper_y + 10.0 and player_node.position.x >= drop_x and player_node.position.x < clear_x:
				player_node.position.x = minf(walkable_max_x, clear_x)

	return {
		"y": player_node.position.y,
		"vy": player_vy,
		"support_y": sup_y,
		"on_ground": _prev_player_on_ground,
		"landed": landed,
		"jumped": jumped,
	}


func step_player_vertical_physics(delta: float, jump_pressed: bool, drop_pressed: bool) -> Dictionary:
	if player_node == null:
		return {"y": ground_y, "vy": 0.0, "support_y": ground_y, "on_ground": true, "landed": false, "jumped": false}
	var jumped := _try_start_player_jump(jump_pressed, drop_pressed)
	return _integrate_player_vertical(delta, jumped)


func _spawn_ground_dust(world_x: float, surface_y: float, scale_mult: float = 1.0) -> void:
	if _dust_fx_tex == null:
		var dust_cfg: Dictionary = terrain_config.get("dust_fx", {})
		_dust_fx_tex = _load_texture_2d(str(dust_cfg.get("res_path", "")))
	if _dust_fx_tex == null:
		return
	if _dust_fx_layer == null or not is_instance_valid(_dust_fx_layer):
		_dust_fx_layer = Node2D.new()
		_dust_fx_layer.name = "GroundDustLayer"
		_dust_fx_layer.z_index = 9
		_dust_fx_layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		add_child(_dust_fx_layer)
	var dust_cfg2: Dictionary = terrain_config.get("dust_fx", {})
	var fcount := maxi(1, int(dust_cfg2.get("frame_count", 6)))
	var tpf := maxi(1, int(dust_cfg2.get("ticks_per_frame", 3)))
	var base_scale := float(dust_cfg2.get("scale", 2.0)) * clampf(scale_mult, 0.7, 1.5)
	var sp := Sprite2D.new()
	sp.texture = _dust_fx_tex
	sp.hframes = fcount
	sp.frame = 0
	sp.centered = true
	sp.offset = Vector2(0.0, -7.0)
	sp.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sp.scale = Vector2(base_scale, base_scale)
	sp.position = Vector2(world_x, surface_y)
	_dust_fx_layer.add_child(sp)
	_active_dust_fx.append({"sprite": sp, "elapsed_s": 0.0, "frame_count": fcount, "ticks_per_frame": tpf})


func _step_ground_dust(delta: float) -> void:
	for i in range(_active_dust_fx.size() - 1, -1, -1):
		var d: Dictionary = _active_dust_fx[i]
		var sp := d.get("sprite") as Sprite2D
		if sp == null or not is_instance_valid(sp):
			_active_dust_fx.remove_at(i)
			continue
		var elapsed := float(d["elapsed_s"]) + maxf(0.0, delta)
		d["elapsed_s"] = elapsed
		var fcount := int(d["frame_count"])
		var tpf := int(d["ticks_per_frame"])
		var fidx := int(floor(elapsed * 60.0 / float(tpf)))
		if fidx >= fcount:
			sp.queue_free()
			_active_dust_fx.remove_at(i)
		else:
			sp.frame = fidx


func compute_contact_shadow_params(pos_x: float, pos_y: float, base_half_w: float = 56.0, visible_flag: bool = true) -> Dictionary:
	if not visible_flag:
		return {"visible": false, "support_y": ground_y, "half_w": 0.0, "alpha": 0.0}
	var sup_y := get_nearest_support_y_below(pos_x, pos_y)
	var h := maxf(0.0, sup_y - pos_y)
	var max_h := float(terrain_config.get("contact_shadow", {}).get("max_height_px", 320.0))
	var ratio := clampf(1.0 - (h / maxf(1.0, max_h)), 0.25, 1.0)
	var min_hw := float(terrain_config.get("contact_shadow", {}).get("min_half_w_px", 18.0))
	var hw := roundf(lerpf(min_hw, maxf(min_hw, base_half_w), ratio))
	return {"visible": true, "support_y": sup_y, "half_w": hw, "alpha": ratio}


func _is_fighter_surface_visible(fighter: Node2D, char_id: String) -> bool:
	if fighter == null or not is_instance_valid(fighter) or not fighter.visible:
		return false
	if char_id == "chilopoda":
		var spr := fighter.get_node_or_null("Sprite") as AnimatedSprite2D
		if spr != null and String(spr.animation) == "attack_light":
			if spr.frame >= 6 and spr.frame <= 9:
				return false
	return true


func _update_parallax_scroll() -> void:
	if player_node == null:
		return
	var offset_from_center := player_node.position.x - float(viewport_width) * 0.5
	for p in _parallax_nodes:
		var base_x := float(p["base_x"])
		var span_w := float(p["span_w"])
		var scroll := float(p["scroll"])
		var shift := fmod(-offset_from_center * scroll, span_w)
		var sprites: Array = p["sprites"]
		for idx in range(sprites.size()):
			var sp := sprites[idx] as Sprite2D
			if sp != null and is_instance_valid(sp):
				sp.position.x = base_x + shift + float(idx - 1) * span_w


func _find_character_entry(char_id: String) -> Dictionary:
	for idx in range(roster_characters.size()):
		var entry: Variant = roster_characters[idx]
		if entry is Dictionary and str(entry.get("character_id", "")) == char_id:
			_char_index = idx
			return entry
	return {}


func _resolve_prefab_path(entry: Dictionary) -> String:
	var modes: Dictionary = entry.get("modes", {})
	var comb: Dictionary = modes.get("combined_1layer", {})
	return str(comb.get("godot_prefab", ""))


func select_character(char_id: String) -> bool:
	var entry := _find_character_entry(char_id)
	if entry.is_empty():
		return false
	var prefab_path := _resolve_prefab_path(entry)
	if prefab_path.is_empty() or not ResourceLoader.exists(prefab_path):
		return false
	var loaded_res: Resource = ResourceLoader.load(prefab_path)
	if not (loaded_res is PackedScene):
		return false
	var packed := loaded_res as PackedScene

	if shenron_summon != null and shenron_summon.active:
		shenron_summon.dismiss()
	_clear_fighter(player_node)

	active_character_id = char_id
	player_facing_left = false
	player_vy = 0.0
	_player_drop_timer_s = 0.0
	_prev_player_on_ground = not _is_flying_entry(entry)
	_step_dust_accum_px = 0.0
	char_scale = _get_entry_default_scale(entry)
	_player_turn_boost_s = 0.0
	_player_turn_elapsed_s = 0.0
	_player_turn_duration_s = 0.0
	player_light_cooldown_s = 0.0
	_player_light_clip_active = false

	var p_inst: Node = packed.instantiate()
	if not (p_inst is Node2D):
		return false

	player_node = p_inst as Node2D
	var parent_layer: Node = fighters_layer if fighters_layer != null else self
	parent_layer.add_child(player_node)
	player_node.name = "PlayerFighter"
	var spawn_y := _get_entry_flight_y(entry) if _is_flying_entry(entry) else ground_y
	_configure_fighter_instance(player_node, player_spawn_x, spawn_y, false, char_scale)
	if touch_hud != null and is_instance_valid(touch_hud):
		touch_hud.set_jump_available(_is_flying_entry(entry) or _has_clip_name(player_node, &"jump"), _is_flying_entry(entry))

	var target_enemy := enemy_character_id if (_enemy_pinned and not enemy_character_id.is_empty()) else char_id
	if not select_enemy_character(target_enemy, false):
		_clear_fighter(dummy_node)
		dummy_node = null
		return false
	_update_walkable_bounds()
	_sync_role_hud(entry, _find_character_entry_ro(enemy_character_id))
	_update_hud()
	return true


func select_enemy_character(char_id: String, pin_enemy: bool = true) -> bool:
	var entry := _find_character_entry(char_id)
	if entry.is_empty():
		return false
	var prefab_path := _resolve_prefab_path(entry)
	if prefab_path.is_empty() or not ResourceLoader.exists(prefab_path):
		return false
	var loaded_res: Resource = ResourceLoader.load(prefab_path)
	if not (loaded_res is PackedScene):
		return false
	var packed := loaded_res as PackedScene

	_clear_fighter(dummy_node)
	var d_inst: Node = packed.instantiate()
	if not (d_inst is Node2D):
		return false

	enemy_character_id = char_id
	_enemy_pinned = pin_enemy
	enemy_facing_left = true
	enemy_scale = _get_entry_default_scale(entry)
	_ai_action_clip = ""
	_ai_action_timer_s = 0.0
	_ai_turn_boost_s = 0.0
	_ai_turn_elapsed_s = 0.0
	_ai_turn_duration_s = 0.0
	dummy_node = d_inst as Node2D
	var parent_layer: Node = fighters_layer if fighters_layer != null else self
	parent_layer.add_child(dummy_node)
	if player_node != null and dummy_node.get_index() > player_node.get_index():
		parent_layer.move_child(dummy_node, player_node.get_index())
	dummy_node.name = "SparringDummy"
	var enemy_spawn_y := _get_entry_flight_y(entry) if _is_flying_entry(entry) else ground_y
	_configure_fighter_instance(dummy_node, dummy_spawn_x, enemy_spawn_y, true, enemy_scale)
	enemy_facing_left = dummy_node.scale.x < 0.0
	var enemy_bounds := _get_fighter_walk_bounds_x(entry, enemy_scale)
	ai_controller.reset_zone(dummy_spawn_x, enemy_bounds.x, enemy_bounds.y)
	ai_last_decision = {}
	_sync_role_hud(_find_character_entry_ro(active_character_id), entry)
	_update_hud()
	queue_redraw()
	return true


func _clear_fighter(node: Node2D) -> void:
	if node != null and is_instance_valid(node):
		if node.get_parent() != null:
			node.get_parent().remove_child(node)
		node.queue_free()


func _configure_fighter_instance(fighter: Node2D, pos_x: float, pos_y: float, facing_left: bool, scale_override: float = -1.0) -> void:
	var sc := scale_override if scale_override > 0.0 else char_scale
	fighter.position = Vector2(pos_x, pos_y)
	fighter.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	fighter.scale = Vector2(-sc if facing_left else sc, sc)
	if fighter.has_method(&"spawn_with_facing"):
		fighter.call(&"spawn_with_facing", "left" if facing_left else "right")
	var spr := fighter.get_node_or_null("Sprite")
	if spr is AnimatedSprite2D:
		(spr as AnimatedSprite2D).texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		(spr as AnimatedSprite2D).centered = false
		(spr as AnimatedSprite2D).play(&"idle")


func set_character_scale(new_scale: float) -> void:
	char_scale = clampf(snappedf(new_scale, 0.05), 0.5, 3.5)
	enemy_scale = char_scale
	if player_node != null:
		player_node.scale = Vector2(-char_scale if player_facing_left else char_scale, char_scale)
	if dummy_node != null:
		var dummy_left := dummy_node.scale.x < 0.0
		dummy_node.scale = Vector2(-enemy_scale if dummy_left else enemy_scale, enemy_scale)
	_update_walkable_bounds()
	_update_hud()
	queue_redraw()


func set_utility_ai_enabled(enabled: bool) -> void:
	utility_ai_enabled = enabled
	_ai_drum_teleport_relocated = false
	_enemy_orb_spawned_for_cast = false
	_enemy_orb_active = false
	if is_instance_valid(_enemy_orb_sprite):
		_enemy_orb_sprite.visible = false
	if is_instance_valid(ai_controller) and ai_controller.has_method("reset_drum_state"):
		ai_controller.reset_drum_state()
	_ai_action_clip = ""
	_ai_action_timer_s = 0.0
	ai_last_decision = {}
	if dummy_node != null:
		var enemy_bounds := _get_fighter_walk_bounds_x(_find_character_entry_ro(enemy_character_id), enemy_scale)
		ai_controller.reset_zone(dummy_spawn_x, enemy_bounds.x, enemy_bounds.y)
		if not enabled:
			_play_fighter_clip(dummy_node, "idle")
	_update_hud()
	queue_redraw()


func _resolve_enemy_capabilities(entry: Dictionary, fighter: Node2D) -> Dictionary:
	var spr := fighter.get_node_or_null("Sprite") as AnimatedSprite2D
	var frames := spr.sprite_frames if spr != null else null
	var has_heavy := frames != null and frames.has_animation(&"attack_heavy")
	var has_power_up := frames != null and frames.has_animation(&"power_up")
	var light_clip := "attack_light"
	if frames != null and not frames.has_animation(&"attack_light") and frames.has_animation(&"attack_nomal"):
		light_clip = "attack_nomal"
	var loco_clip := "fly" if (frames != null and frames.has_animation(&"fly")) else "walk"
	return {
		"character_id": str(entry.get("character_id", enemy_character_id)),
		"is_stationary": _is_stationary_entry(entry),
		"is_flying": _is_flying_entry(entry),
		"sideways_locked": _is_sideways_locked(entry),
		"has_heavy": has_heavy,
		"has_power_up": has_power_up,
		"preserve_idle_walk_phase": _should_preserve_idle_walk_phase(entry),
		"light_clip": light_clip,
		"locomotion_clip": loco_clip,
	}


func _get_clip_duration_s(fighter: Node2D, clip_name: String) -> float:
	var spr := fighter.get_node_or_null("Sprite") as AnimatedSprite2D
	if spr == null or spr.sprite_frames == null:
		return 0.5
	var sname := StringName(clip_name)
	if not spr.sprite_frames.has_animation(sname):
		return 0.5
	var count := spr.sprite_frames.get_frame_count(sname)
	var ticks := 0.0
	for i in range(count):
		ticks += spr.sprite_frames.get_frame_duration(sname, i)
	var fps := maxf(1.0, spr.sprite_frames.get_animation_speed(sname))
	return maxf(0.1, ticks / fps)


func _play_fighter_clip(fighter: Node2D, clip_name: String) -> bool:
	if fighter == player_node:
		_player_drum_teleport_relocated = false
	var sname := StringName(clip_name)
	if fighter.has_method(&"play_clip"):
		return bool(fighter.call(&"play_clip", sname))
	var spr := fighter.get_node_or_null("Sprite") as AnimatedSprite2D
	if spr != null and spr.sprite_frames != null and spr.sprite_frames.has_animation(sname):
		spr.play(sname)
		return true
	return false


func _should_preserve_idle_walk_phase(entry: Dictionary) -> bool:
	var loc: Dictionary = entry.get("render_contract", {}).get("locomotion", {})
	return bool(loc.get("preserve_phase_on_idle_walk", false))


func _play_locomotion_preserving_phase(spr: AnimatedSprite2D, target_clip: StringName, preserve_phase: bool, fighter: Node2D = null) -> void:
	if spr == null:
		return
	var cur_anim := spr.animation
	var keep_phase := preserve_phase and spr.sprite_frames != null and ((cur_anim == &"idle" and target_clip == &"walk") or (cur_anim == &"walk" and target_clip == &"idle"))
	var prev_frame := spr.frame
	var prev_prog := spr.frame_progress
	if fighter != null:
		_play_fighter_clip(fighter, String(target_clip))
	else:
		spr.play(target_clip)
	if keep_phase and spr.sprite_frames.has_animation(target_clip) and spr.sprite_frames.get_frame_count(target_clip) > 0:
		var clamped := clampi(prev_frame, 0, spr.sprite_frames.get_frame_count(target_clip) - 1)
		spr.set_frame_and_progress(clamped, prev_prog)


func _ensure_fighter_locomotion(fighter: Node2D, clip_name: String, preserve_phase: bool = false) -> void:
	var spr := fighter.get_node_or_null("Sprite") as AnimatedSprite2D
	var sname := StringName(clip_name)
	if spr != null and (spr.animation != sname or not spr.is_playing()):
		_play_locomotion_preserving_phase(spr, sname, preserve_phase, fighter)


func _find_character_entry_ro(char_id: String) -> Dictionary:
	for entry in roster_characters:
		if entry is Dictionary and str(entry.get("character_id", "")) == char_id:
			return entry
	return {}


func step_utility_ai(delta: float) -> Dictionary:
	if player_node == null or dummy_node == null:
		return {}
	if not (enemy_character_id == "drum" and not _ai_action_clip.is_empty()):
		ai_controller.tick_cooldown(delta)
	_ai_turn_boost_s = maxf(0.0, _ai_turn_boost_s - maxf(0.0, delta))
	if _ai_action_timer_s > 0.0:
		_ai_action_timer_s = maxf(0.0, _ai_action_timer_s - maxf(0.0, delta))
	var turn_pending := _is_fighter_turning(dummy_node)
	var spr := dummy_node.get_node_or_null("Sprite") as AnimatedSprite2D
	if not turn_pending and not _ai_action_clip.is_empty():
		var clip_finished_early := spr != null and String(spr.animation) == _ai_action_clip and not spr.is_playing()
		if _ai_action_timer_s <= 0.0 or clip_finished_early:
			_ai_action_clip = ""
			_ai_action_timer_s = 0.0
	var is_busy := turn_pending or not _ai_action_clip.is_empty()

	var p_entry := _find_character_entry_ro(active_character_id)
	var e_entry := _find_character_entry_ro(enemy_character_id)
	if e_entry.is_empty():
		e_entry = p_entry
	var caps := _resolve_enemy_capabilities(e_entry, dummy_node)
	var p_dims := _get_body_dims(p_entry)
	var e_dims := _get_body_dims(e_entry)
	var pw := float(p_dims.x) if p_dims.x > 0 else 140.0
	var ph := float(p_dims.y) if p_dims.y > 0 else 140.0
	var ew := float(e_dims.x) if e_dims.x > 0 else 140.0
	var eh := float(e_dims.y) if e_dims.y > 0 else 140.0
	_step_enemy_orb_projectile(delta, pw, ph)
	_sync_role_hud(p_entry, e_entry)
	if str(caps["character_id"]) == "drum" and not _ai_action_clip.is_empty():
		_step_drum_midclip(spr, pw, ew)
		is_busy = turn_pending or not _ai_action_clip.is_empty()

	if turn_pending and str(caps["character_id"]) != "chilopoda" and _ai_turn_duration_s > 0.0:
		_ai_turn_elapsed_s += maxf(0.0, delta)
		var turn_mom := _turn_momentum_factor(_ai_turn_elapsed_s, _ai_turn_duration_s, _ai_turn_prev_dir, -1 if _ai_turn_target_left else 1)
		var turn_spd := _get_walk_speed_px_per_s(e_entry, enemy_scale) * turn_mom
		_move_node_horizontal(dummy_node, turn_spd * maxf(0.0, delta), bool(caps["is_flying"]), ai_controller.zone_min_x, ai_controller.zone_max_x, ew * enemy_scale * 0.5)

	var target_rect: Rect2 = UtilityAIControllerScript.compute_body_rect(player_node.position.x, player_node.position.y, pw, ph, char_scale)
	var self_rect: Rect2 = UtilityAIControllerScript.compute_body_rect(dummy_node.position.x, dummy_node.position.y, ew, eh, enemy_scale)

	var res := ai_controller.evaluate({
		"character_id": caps["character_id"],
		"is_stationary": caps["is_stationary"],
		"facing_left": enemy_facing_left,
		"is_flying": caps["is_flying"],
		"has_heavy": caps["has_heavy"],
		"has_power_up": caps["has_power_up"],
		"light_clip": caps["light_clip"],
		"self_rect": self_rect,
		"target_rect": target_rect,
		"self_x": dummy_node.position.x,
		"target_x": player_node.position.x,
		"is_busy": is_busy,
	})

	if res.get("intent", "") == "busy":
		ai_last_decision = res
		return res

	var desired_left := bool(res.get("desired_face_left", enemy_facing_left))
	if not bool(caps["sideways_locked"]):
		var cur_left := dummy_node.scale.x < 0.0
		if cur_left != desired_left:
			var started_turn := false
			if dummy_node.has_method(&"set_facing_left") and _has_turn_clip(e_entry):
				dummy_node.set_meta("_arena_turn_resume_clip", str(caps["locomotion_clip"]))
				started_turn = bool(dummy_node.call(&"set_facing_left", desired_left))
			if started_turn and _is_fighter_turning(dummy_node):
				_ai_turn_prev_dir = -1 if cur_left else 1
				_ai_turn_target_left = desired_left
				_ai_turn_elapsed_s = 0.0
				_ai_turn_duration_s = _get_clip_duration_s(dummy_node, "turn")
				_ai_action_clip = "turn"
				_ai_action_timer_s = _ai_turn_duration_s
				ai_last_decision = res
				queue_redraw()
				return res
			# Prefabs without a perspective turn clip (e.g. Pteranodon, King Crab) reorient horizontally cleanly + burst boost
			enemy_facing_left = desired_left
			dummy_node.scale = Vector2(-enemy_scale if enemy_facing_left else enemy_scale, enemy_scale)
			_ai_turn_boost_s = 0.26

	var intent := str(res.get("intent", "idle"))
	if intent == "attack":
		var clip := str(res.get("attack_clip", caps["light_clip"]))
		if str(caps["character_id"]) == "chilopoda" and dummy_node.has_method(&"set_combat_target_global"):
			var clamped_tx := clampf(player_node.position.x, walkable_min_x, walkable_max_x)
			dummy_node.call(&"set_combat_target_global", Vector2(clamped_tx, _ground_y_at(clamped_tx)))
		elif str(caps["character_id"]) == "dilophosaurus" and dummy_node.has_method(&"set_slash_target_global"):
			dummy_node.call(&"set_slash_target_global", player_node.position)
		if _play_fighter_clip(dummy_node, clip):
			_ai_action_clip = clip
			_ai_action_timer_s = _get_clip_duration_s(dummy_node, clip)
			if clip == "teleport":
				_ai_drum_teleport_relocated = false
			elif clip == "power_up":
				_enemy_orb_spawned_for_cast = false
	elif intent == "patrol" or intent == "chase":
		var move_dir := int(res.get("move_dir", 0))
		if move_dir != 0:
			var boost := _get_turn_speed_multiplier(e_entry) if _ai_turn_boost_s > 0.0 else 1.0
			var spd := _get_walk_speed_px_per_s(e_entry, enemy_scale) * boost
			_move_node_horizontal(dummy_node, float(move_dir) * spd * delta, bool(caps["is_flying"]), ai_controller.zone_min_x, ai_controller.zone_max_x, ew * enemy_scale * 0.5)
			if bool(caps["is_flying"]):
				dummy_node.position.y = clampf(dummy_node.position.y, fly_min_y, _ground_y_at(dummy_node.position.x))
			_ensure_fighter_locomotion(dummy_node, str(caps["locomotion_clip"]), bool(caps["preserve_idle_walk_phase"]))
		else:
			_ensure_fighter_locomotion(dummy_node, "idle", bool(caps["preserve_idle_walk_phase"]))
	elif intent == "wait_cooldown":
		_ensure_fighter_locomotion(dummy_node, "idle", bool(caps["preserve_idle_walk_phase"]))
	elif intent == "idle":
		_ensure_fighter_locomotion(dummy_node, "idle", bool(caps["preserve_idle_walk_phase"]))
		if str(caps["character_id"]) == "drum" and ai_controller.has_method("reset_drum_state"):
			ai_controller.reset_drum_state()

	_reconcile_chilopoda_terrain(dummy_node, str(caps["character_id"]), ai_controller.zone_min_x, ai_controller.zone_max_x, enemy_scale)
	enemy_facing_left = dummy_node.scale.x < 0.0
	if not bool(caps["is_flying"]) and not bool(caps["is_stationary"]):
		var enemy_floor := _ground_y_at(dummy_node.position.x)
		if dummy_node.position.y < enemy_floor - 0.5:
			if enemy_vy == 0.0:
				enemy_vy = gravity_px_per_s2 * delta
			else:
				enemy_vy += gravity_px_per_s2 * delta
			var dy_enemy := maxf(2.0, enemy_vy * delta)
			dummy_node.position.y = minf(enemy_floor, dummy_node.position.y + dy_enemy)
		else:
			dummy_node.position.y = enemy_floor
			enemy_vy = 0.0
	ai_last_decision = res
	queue_redraw()
	return res


func _step_drum_midclip(spr: AnimatedSprite2D, pw: float, ew: float) -> void:
	if _ai_action_clip == "teleport" and not _ai_drum_teleport_relocated:
		var mid_reached := _ai_action_timer_s <= 0.17 or (spr != null and String(spr.animation) == "teleport" and spr.frame >= 2)
		if mid_reached:
			var target_dist: float = (pw * float(char_scale) + ew * float(enemy_scale)) * 0.5 + float(ai_controller.close_edge_px)
			var side: float = -1.0 if dummy_node.position.x <= player_node.position.x else 1.0
			var enemy_bounds := _get_fighter_walk_bounds_x(_find_character_entry_ro(enemy_character_id), enemy_scale)
			var min_b: float = maxf(enemy_bounds.x, float(ai_controller.zone_min_x))
			var max_b: float = minf(enemy_bounds.y, float(ai_controller.zone_max_x))
			var cand_x: float = player_node.position.x + side * target_dist
			if cand_x < min_b or cand_x > max_b or not _can_cross_terrain_step(dummy_node.position.x, cand_x, dummy_node.position.y, false):
				var alt_x: float = player_node.position.x - side * target_dist
				if alt_x >= min_b and alt_x <= max_b and _can_cross_terrain_step(dummy_node.position.x, alt_x, dummy_node.position.y, false):
					cand_x = alt_x
			dummy_node.position.x = _resolve_terrain_horizontal_move(dummy_node.position.x, cand_x, dummy_node.position.y, false, min_b, max_b, ew * enemy_scale * 0.5)
			enemy_facing_left = player_node.position.x < dummy_node.position.x
			dummy_node.scale = Vector2(-enemy_scale if enemy_facing_left else enemy_scale, enemy_scale)
			_ai_drum_teleport_relocated = true
	elif _ai_action_clip == "power_up" and not _enemy_orb_spawned_for_cast:
		var cast_reached := _ai_action_timer_s <= 0.14 or (spr != null and String(spr.animation) == "power_up" and spr.frame >= 10)
		if cast_reached:
			_enemy_orb_spawned_for_cast = true
			_spawn_drum_enemy_orb()


func _spawn_drum_enemy_orb() -> void:
	var spr := dummy_node.get_node_or_null("Sprite") as AnimatedSprite2D
	if spr == null or spr.sprite_frames == null or not spr.sprite_frames.has_animation(&"electric_orb_fx"):
		return
	if not is_instance_valid(_enemy_orb_sprite):
		_enemy_orb_sprite = AnimatedSprite2D.new()
		_enemy_orb_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		_enemy_orb_sprite.centered = false
		_enemy_orb_sprite.offset = Vector2(-64.0, -48.0)
		add_child(_enemy_orb_sprite)
	_enemy_orb_sprite.sprite_frames = spr.sprite_frames
	_enemy_orb_dir = -1.0 if enemy_facing_left else 1.0
	_enemy_orb_elapsed_s = 0.0
	_enemy_orb_active = true
	_enemy_orb_sprite.flip_h = enemy_facing_left
	_enemy_orb_sprite.scale = Vector2(enemy_scale, enemy_scale)
	_enemy_orb_sprite.position = dummy_node.position + Vector2(42.0 * _enemy_orb_dir * enemy_scale, -28.0 * enemy_scale)
	_enemy_orb_sprite.visible = true
	_enemy_orb_sprite.play(&"electric_orb_fx")


func _step_enemy_orb_projectile(delta: float, pw: float, _ph: float) -> void:
	if not _enemy_orb_active or not is_instance_valid(_enemy_orb_sprite):
		return
	_enemy_orb_elapsed_s += maxf(0.0, delta)
	var prev_pos := _enemy_orb_sprite.position
	_enemy_orb_sprite.position.x += _enemy_orb_dir * (18.0 * 60.0 * enemy_scale) * maxf(0.0, delta)
	var terrain_hit := terrain_blocks_segment(prev_pos, _enemy_orb_sprite.position)
	var hit_x := absf(_enemy_orb_sprite.position.x - player_node.position.x) <= maxf(24.0, pw * char_scale * 0.45)
	if terrain_hit or hit_x or _enemy_orb_elapsed_s >= 0.65:
		_enemy_orb_active = false
		_enemy_orb_sprite.visible = false
		_enemy_orb_sprite.stop()


func _sync_role_hud(p_entry: Dictionary, e_entry: Dictionary) -> void:
	if DisplayServer.get_name() == "headless":
		return
	if field_mode_enabled:
		var existing_hud := get_node_or_null("ArenaRoleHud") as CanvasLayer
		if existing_hud != null:
			existing_hud.visible = false
		return
	var p_id := str(p_entry.get("character_id", ""))
	var role := str(p_entry.get("combat_role", "sandbox"))
	var e_role := str(e_entry.get("combat_role", "sandbox"))
	var is_npc := role == "npc" or p_id == "shenron"
	if _hero_skill_bar == null and get_viewport() != null:
		var hud := get_node_or_null("ArenaRoleHud") as CanvasLayer
		if hud == null:
			hud = CanvasLayer.new()
			hud.name = "ArenaRoleHud"
			add_child(hud)
		var bar := HBoxContainer.new()
		bar.name = "HeroSkillBar"
		bar.anchor_left = 0.5
		bar.anchor_right = 0.5
		bar.anchor_top = 1.0
		bar.anchor_bottom = 1.0
		bar.offset_left = -260.0
		bar.offset_right = 260.0
		bar.offset_top = -86.0
		bar.offset_bottom = -44.0
		_hero_skill_bar = bar
		for spec in [
			{"label": "Đánh nhẹ (Light)", "clip": "attack_light"},
			{"label": "Tốc biến (Teleport)", "clip": "teleport"},
			{"label": "Đánh nặng (Heavy)", "clip": "attack_heavy"},
			{"label": "Power Up", "clip": "power_up"},
		]:
			var btn := Button.new()
			btn.text = str(spec["label"])
			var clip_name := str(spec["clip"])
			btn.set_meta(&"clip_name", clip_name)
			btn.pressed.connect(func() -> void:
				_request_player_action(clip_name)
			)
			bar.add_child(btn)
		hud.add_child(bar)

		var switch_bar := HBoxContainer.new()
		switch_bar.name = "ArenaSwitcherBar"
		switch_bar.anchor_left = 0.5
		switch_bar.anchor_right = 0.5
		switch_bar.anchor_top = 1.0
		switch_bar.anchor_bottom = 1.0
		switch_bar.offset_left = -330.0
		switch_bar.offset_right = 330.0
		switch_bar.offset_top = -40.0
		switch_bar.offset_bottom = -8.0
		var p_lbl := Label.new()
		p_lbl.text = "Thao tác:"
		switch_bar.add_child(p_lbl)
		_player_select_opt = OptionButton.new()
		_player_select_opt.custom_minimum_size = Vector2(200.0, 32.0)
		switch_bar.add_child(_player_select_opt)
		var e_lbl := Label.new()
		e_lbl.text = "AI Tự thao tác:"
		switch_bar.add_child(e_lbl)
		_enemy_select_opt = OptionButton.new()
		_enemy_select_opt.custom_minimum_size = Vector2(200.0, 32.0)
		switch_bar.add_child(_enemy_select_opt)
		for idx in range(roster_characters.size()):
			var ch: Variant = roster_characters[idx]
			if not (ch is Dictionary):
				continue
			var cid_item := str(ch.get("character_id", ""))
			var label_item := str(ch.get("display_name", cid_item))
			_player_select_opt.add_item(label_item, idx)
			_player_select_opt.set_item_metadata(idx, cid_item)
			_enemy_select_opt.add_item(label_item, idx)
			_enemy_select_opt.set_item_metadata(idx, cid_item)
		_player_select_opt.item_selected.connect(func(sel_idx: int) -> void:
			if _hud_syncing:
				return
			var picked_id := str(_player_select_opt.get_item_metadata(sel_idx))
			if not picked_id.is_empty():
				select_character(picked_id)
		)
		_enemy_select_opt.item_selected.connect(func(sel_idx: int) -> void:
			if _hud_syncing:
				return
			var picked_id := str(_enemy_select_opt.get_item_metadata(sel_idx))
			if not picked_id.is_empty():
				select_enemy_character(picked_id, true)
		)
		hud.add_child(switch_bar)

		_role_mode_label = Label.new()
		_role_mode_label.name = "RoleModeLabel"
		_role_mode_label.anchor_left = 0.5
		_role_mode_label.anchor_right = 0.5
		_role_mode_label.anchor_top = 1.0
		_role_mode_label.anchor_bottom = 1.0
		_role_mode_label.offset_left = -280.0
		_role_mode_label.offset_right = 280.0
		_role_mode_label.offset_top = -114.0
		_role_mode_label.offset_bottom = -90.0
		_role_mode_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		hud.add_child(_role_mode_label)
	if is_instance_valid(_hero_skill_bar):
		_hero_skill_bar.visible = not is_npc
		var pspr := player_node.get_node_or_null("Sprite") as AnimatedSprite2D if player_node != null else null
		for child in _hero_skill_bar.get_children():
			if child is Button:
				var c_clip := str(child.get_meta(&"clip_name", ""))
				var has_c := pspr != null and pspr.sprite_frames != null and (pspr.sprite_frames.has_animation(StringName(c_clip)) or (c_clip == "attack_light" and pspr.sprite_frames.has_animation(&"attack_nomal")))
				(child as Button).visible = has_c
	_hud_syncing = true
	if is_instance_valid(_player_select_opt):
		for i in range(_player_select_opt.item_count):
			if str(_player_select_opt.get_item_metadata(i)) == active_character_id:
				_player_select_opt.select(i)
				break
	if is_instance_valid(_enemy_select_opt):
		for i in range(_enemy_select_opt.item_count):
			if str(_enemy_select_opt.get_item_metadata(i)) == enemy_character_id:
				_enemy_select_opt.select(i)
				break
	_hud_syncing = false
	if is_instance_valid(_role_mode_label):
		if e_role in ["monster", "boss"] or utility_ai_enabled:
			_role_mode_label.text = "Test Sân Tập (%s) | AI[%s]: %s" % [str(p_entry.get("display_name", "")), str(e_entry.get("display_name", "")), ai_controller.last_reason]
		else:
			_role_mode_label.text = "Test Sân Tập (%s): Nút Skill Vật Lý" % str(p_entry.get("display_name", ""))


func _get_entry_default_scale(entry: Dictionary) -> float:
	var rc: Dictionary = entry.get("render_contract", {})
	var loc: Dictionary = rc.get("locomotion", {})
	if loc.has("default_scale") and float(loc.get("default_scale", 0.0)) > 0.0:
		return float(loc.get("default_scale", 2.0))
	var gp: Dictionary = stage_config.get("gameplay", {})
	return float(gp.get("character_scale_default", 2.0))


func _get_entry_flight_y(entry: Dictionary) -> float:
	var loc: Dictionary = entry.get("render_contract", {}).get("locomotion", {})
	return float(loc.get("flight_default_y", fly_default_y))


func _get_turn_speed_multiplier(entry: Dictionary) -> float:
	var rc: Dictionary = entry.get("render_contract", {})
	var turning: Variant = rc.get("turning", {})
	if turning is Dictionary and turning.has("turn_speed_multiplier"):
		return maxf(1.0, float(turning.get("turn_speed_multiplier", 1.0)))
	return 1.0


func _has_turn_clip(entry: Dictionary) -> bool:
	var rc: Dictionary = entry.get("render_contract", {})
	var turning: Variant = rc.get("turning", {})
	if turning is Dictionary:
		var clip_val: Variant = turning.get("clip", null)
		return clip_val != null and not str(clip_val).is_empty()
	return false


func _turn_momentum_factor(elapsed_s: float, duration_s: float, prev_dir: int, target_dir: int) -> float:
	if duration_s <= 0.0:
		return float(target_dir)
	var p := clampf(elapsed_s / duration_s, 0.0, 1.0)
	if p < 0.38:
		return float(prev_dir) * (1.0 - p / 0.38) * 0.45
	return float(target_dir) * ((p - 0.38) / 0.62)


func _has_clip_name(fighter: Node2D, clip_name: StringName) -> bool:
	var spr := fighter.get_node_or_null("Sprite") as AnimatedSprite2D
	return spr != null and spr.sprite_frames != null and spr.sprite_frames.has_animation(clip_name)


func _is_player_action_playing() -> bool:
	if player_node == null:
		return false
	var spr := player_node.get_node_or_null("Sprite") as AnimatedSprite2D
	return spr != null and spr.is_playing() and String(spr.animation) not in ["idle", "walk", "run", "fly", "jump", "turn"]


func _is_sideways_locked(entry: Dictionary) -> bool:
	var rc: Dictionary = entry.get("render_contract", {})
	var loc: Dictionary = rc.get("locomotion", {})
	return bool(loc.get("sideways_strafe", false) or loc.get("lock_spawn_facing", false) or not loc.get("allow_turn_or_flip", true))


func _is_flying_entry(entry: Dictionary) -> bool:
	var rc: Dictionary = entry.get("render_contract", {})
	var loc: Dictionary = rc.get("locomotion", {})
	return str(loc.get("kind", "ground")) == "flight"


func _is_stationary_entry(entry: Dictionary) -> bool:
	return str(entry.get("render_contract", {}).get("locomotion", {}).get("kind", "")) == "stationary"


func _get_body_dims(entry: Dictionary) -> Vector2i:
	var m: Dictionary = entry.get("map_sync_metrics", {})
	var bbox: Variant = m.get("body_only_bbox_px", null)
	if bbox is Dictionary:
		return Vector2i(int(bbox.get("w", 0)), int(bbox.get("h", 0)))
	if bbox is Array and bbox.size() >= 2:
		return Vector2i(int(bbox[0]), int(bbox[1]))
	return Vector2i.ZERO


func get_fighter_body_rect(node: Node2D, char_id: String, scale_val: float) -> Rect2:
	if node == null or not is_instance_valid(node):
		return Rect2()
	var sc := maxf(0.1, scale_val)
	var entry := _find_character_entry_ro(char_id)
	var m: Dictionary = entry.get("map_sync_metrics", {})
	var bbox: Variant = m.get("body_only_bbox_px", null)
	var anchor: Variant = m.get("foot_anchor_px", null)
	if bbox is Dictionary and anchor is Array and (anchor as Array).size() >= 2:
		var bx := float(bbox.get("x", 0.0))
		var by := float(bbox.get("y", 0.0))
		var bw := float(bbox.get("w", 0.0))
		var bh := float(bbox.get("h", 0.0))
		var ax := float(anchor[0])
		var ay := float(anchor[1])
		if bw > 0.0 and bh > 0.0:
			var facing_left := node.scale.x < 0.0
			var local_l := (ax - (bx + bw)) if facing_left else (bx - ax)
			var local_r := (ax - bx) if facing_left else (bx + bw - ax)
			var local_t := by - ay
			var local_b := by + bh - ay
			return Rect2(
				node.position.x + local_l * sc,
				node.position.y + local_t * sc,
				maxf(16.0, (local_r - local_l) * sc),
				maxf(16.0, (local_b - local_t) * sc)
			)
	var dims := _get_body_dims(entry)
	var fw := float(dims.x) if dims.x > 0 else 140.0
	var fh := float(dims.y) if dims.y > 0 else 140.0
	return UtilityAIControllerScript.compute_body_rect(node.position.x, node.position.y, fw, fh, sc)


func get_fighter_layer_z(char_id: String, is_hero: bool) -> int:
	var entry := _find_character_entry_ro(char_id)
	var role := str(entry.get("combat_role", ""))
	if role == "boss":
		return Z_LAYER_BOSS
	return Z_LAYER_HERO if is_hero else Z_LAYER_MONSTER


func get_fighter_core_world_pos(node: Node2D, char_id: String, scale_val: float) -> Vector2:
	if node == null or not is_instance_valid(node):
		return Vector2.ZERO
	var sc := maxf(0.1, scale_val)
	var sil: Variant = _body_silhouettes.get(char_id, {})
	if sil is Dictionary and sil.has("core_offset_px"):
		var co: Array = sil.get("core_offset_px", [0.0, -40.0])
		if co.size() >= 2:
			var facing_left := node.scale.x < 0.0
			var cx := -float(co[0]) if facing_left else float(co[0])
			var cy := float(co[1])
			return node.position + Vector2(cx * sc, cy * sc)
	return get_fighter_body_rect(node, char_id, sc).get_center()


func get_fighter_silhouette_rects(node: Node2D, char_id: String, scale_val: float) -> Array[Rect2]:
	var out: Array[Rect2] = []
	if node == null or not is_instance_valid(node):
		return out
	var sc := maxf(0.1, scale_val)
	var sil: Variant = _body_silhouettes.get(char_id, {})
	if sil is Dictionary and sil.has("bands"):
		var bands: Variant = sil.get("bands", [])
		if bands is Array and not (bands as Array).is_empty():
			var facing_left := node.scale.x < 0.0
			var px := node.position.x
			var py := node.position.y
			for b in (bands as Array):
				if not (b is Array) or (b as Array).size() < 4:
					continue
				var y0 := float(b[0]) * sc
				var y1 := float(b[1]) * sc
				var x0 := float(b[2]) * sc
				var x1 := float(b[3]) * sc
				var lx := -x1 if facing_left else x0
				var rx := -x0 if facing_left else x1
				out.append(Rect2(px + lx, py + y0, maxf(2.0, rx - lx), maxf(2.0, y1 - y0)))
			if not out.is_empty():
				return out
	out.append(get_fighter_body_rect(node, char_id, sc))
	return out


func silhouette_contains_point(node: Node2D, char_id: String, scale_val: float, world_pos: Vector2, pad_px: float = 0.0) -> bool:
	var rects := get_fighter_silhouette_rects(node, char_id, scale_val)
	for r in rects:
		if r.grow(pad_px).has_point(world_pos):
			return true
	return false


func silhouette_intersects_rect(node: Node2D, char_id: String, scale_val: float, q_rect: Rect2) -> bool:
	var rects := get_fighter_silhouette_rects(node, char_id, scale_val)
	for r in rects:
		if r.intersects(q_rect):
			return true
	return false


func compute_silhouette_edge_gap(node_a: Node2D, cid_a: String, sc_a: float, node_b: Node2D, cid_b: String, sc_b: float) -> float:
	var rects_a := get_fighter_silhouette_rects(node_a, cid_a, sc_a)
	var rects_b := get_fighter_silhouette_rects(node_b, cid_b, sc_b)
	if rects_a.is_empty() or rects_b.is_empty():
		return 99999.0
	var best := 99999.0
	for ra in rects_a:
		for rb in rects_b:
			var d := UtilityAIControllerScript.compute_edge_distance(ra, rb)
			if d < best:
				best = d
				if best <= 0.0:
					return 0.0
	return best


func compute_nearest_silhouette_point(node: Node2D, char_id: String, scale_val: float, from_pos: Vector2) -> Vector2:
	var rects := get_fighter_silhouette_rects(node, char_id, scale_val)
	if rects.is_empty():
		return get_fighter_core_world_pos(node, char_id, scale_val)
	var best_pt := get_fighter_core_world_pos(node, char_id, scale_val)
	var best_d2 := 999999999.0
	for r in rects:
		var cx := clampf(from_pos.x, r.position.x, r.end.x)
		var cy := clampf(from_pos.y, r.position.y, r.end.y)
		var pt := Vector2(cx, cy)
		var d2 := pt.distance_squared_to(from_pos)
		if d2 < best_d2:
			best_d2 = d2
			best_pt = pt
	return best_pt


func _get_walk_speed_px_per_s(entry: Dictionary, scale_override: float = -1.0) -> float:
	if _is_stationary_entry(entry):
		return 0.0
	var sc := scale_override if scale_override > 0.0 else char_scale
	var rc: Dictionary = entry.get("render_contract", {})
	var loc: Dictionary = rc.get("locomotion", {})
	if loc.has("speed_px_per_second") and float(loc.get("speed_px_per_second", 0.0)) > 0.0:
		return float(loc.get("speed_px_per_second", 135.0)) * sc
	var patrol: Variant = loc.get("patrol", {})
	if patrol is Dictionary and patrol.has("speed_px_per_second"):
		return float(patrol.get("speed_px_per_second", 135.0)) * sc
	return 270.0 * (sc / 2.0)


func step_flight_vertical(fly_dir_y: float, delta: float) -> float:
	if player_node == null:
		return fly_default_y
	var max_y := _ground_y_at(player_node.position.x)
	player_node.position.y = clampf(
		player_node.position.y + fly_dir_y * fly_vertical_speed_px_per_s * (char_scale / 2.0) * delta,
		fly_min_y,
		max_y
	)
	player_vy = 0.0
	return player_node.position.y


func _flush_player_queued_action() -> void:
	if player_node == null:
		return
	if not _is_fighter_turning(player_node) and not _is_player_action_playing() and player_node.has_meta(&"_arena_queued_action"):
		var queued_action := String(player_node.get_meta(&"_arena_queued_action"))
		player_node.remove_meta(&"_arena_queued_action")
		_request_player_action(queued_action)


func _step_player_drum_midclip() -> void:
	if player_node == null or active_character_id != "drum" or _player_drum_teleport_relocated:
		return
	var spr := player_node.get_node_or_null("Sprite") as AnimatedSprite2D
	if spr != null and spr.is_playing() and spr.animation == &"teleport" and spr.frame >= 2:
		var move_dir := -1.0 if player_node.scale.x < 0.0 else 1.0
		_move_player_horizontal(move_dir * 120.0 * char_scale, false)
		_player_drum_teleport_relocated = true


func _reconcile_chilopoda_terrain(node: Node2D, char_id: String, min_b: float, max_b: float, sc: float = -1.0) -> void:
	if node == null or char_id != "chilopoda":
		return
	var spr := node.get_node_or_null("Sprite") as AnimatedSprite2D
	if spr != null and spr.is_playing() and spr.animation == &"attack_light":
		var orig: Variant = node.get("action_origin_global")
		var origin_x: float = orig.x if orig is Vector2 else node.position.x
		var use_sc := sc if sc > 0.0 else char_scale
		var resolved_x := _resolve_terrain_horizontal_move(origin_x, node.position.x, _ground_y_at(origin_x), false, min_b, max_b, _get_fighter_half_width_px(char_id, use_sc))
		node.position.x = resolved_x
		node.position.y = _ground_y_at(resolved_x)


func step_player_movement(delta: float, move_dir: int, fly_dir_y: int = 0, jump_req: bool = false, drop_req: bool = false, is_run: bool = false, analog_vec: Vector2 = Vector2.ZERO) -> void:
	if player_node == null or delta <= 0.0:
		return
	_step_player_light_cooldown(delta)
	_flush_player_queued_action()

	var entry := _find_character_entry(active_character_id)
	var is_flying := _is_flying_entry(entry)
	var is_stationary := _is_stationary_entry(entry)
	var action_playing := _is_player_action_playing()
	var dir := 0 if (is_stationary or action_playing) else clampi(move_dir, -1, 1)
	var eff_fly_dir_y := 0 if action_playing else clampi(fly_dir_y, -1, 1)
	var fly_input_vec := Vector2.ZERO
	if is_flying and not is_stationary and not action_playing:
		if analog_vec.length() > 0.12:
			fly_input_vec = analog_vec.limit_length(1.0)
			if absf(fly_input_vec.x) > 0.18:
				dir = -1 if fly_input_vec.x < 0.0 else 1
			else:
				dir = 0
		elif dir != 0 or eff_fly_dir_y != 0:
			fly_input_vec = Vector2(float(dir), float(eff_fly_dir_y)).normalized()

	var jumped_now := false
	if not is_flying and not is_stationary:
		_flight_vel = Vector2.ZERO
		jumped_now = _try_start_player_jump(jump_req, drop_req)

	var prev_px := player_node.position.x
	_step_player_drum_midclip()

	var sideways_locked := _is_sideways_locked(entry)
	var walk_speed := _get_walk_speed_px_per_s(entry)
	var base_speed := walk_speed * 1.6 if is_run else walk_speed
	_player_turn_boost_s = maxf(0.0, _player_turn_boost_s - delta)
	var turning_now := _is_fighter_turning(player_node)

	if not sideways_locked and not turning_now and not action_playing and dir != 0:
		var want_left := dir < 0
		if want_left != player_facing_left:
			if _has_turn_clip(entry) and player_node.has_method(&"set_facing_left"):
				var resume_name := "run" if is_run else ("fly" if (is_flying and _has_clip_name(player_node, &"fly")) else "walk")
				player_node.set_meta("_arena_turn_resume_clip", resume_name)
				var turn_clip_name := str(entry.get("render_contract", {}).get("turning", {}).get("clip", "turn"))
				var prev_dir_val := -1 if player_facing_left else 1
				if bool(player_node.call(&"set_facing_left", want_left)) and _is_fighter_turning(player_node):
					_player_turn_prev_dir = prev_dir_val
					_player_turn_elapsed_s = 0.0
					_player_turn_duration_s = _get_clip_duration_s(player_node, turn_clip_name)
					turning_now = true
			if not turning_now:
				player_facing_left = want_left
				player_node.scale = Vector2(-char_scale if player_facing_left else char_scale, char_scale)
				_player_turn_boost_s = 0.26

	if turning_now:
		if active_character_id != "chilopoda" and _player_turn_duration_s > 0.0:
			_player_turn_elapsed_s += delta
			var tgt_left_v: Variant = player_node.get("_turn_target_left")
			var tgt_dir := -1 if (bool(tgt_left_v) if tgt_left_v != null else (dir < 0)) else 1
			var mom := _turn_momentum_factor(_player_turn_elapsed_s, _player_turn_duration_s, _player_turn_prev_dir, tgt_dir)
			_move_player_horizontal(base_speed * mom * delta, is_flying)
	else:
		player_facing_left = player_node.scale.x < 0.0
		var p_boost := _get_turn_speed_multiplier(entry) if _player_turn_boost_s > 0.0 else 1.0
		if is_flying:
			var target_fvel := fly_input_vec * (base_speed * p_boost)
			_flight_vel = _flight_vel.lerp(target_fvel, minf(1.0, delta * 12.0))
			if _flight_vel.length() < 2.0 and fly_input_vec == Vector2.ZERO:
				_flight_vel = Vector2.ZERO
			_move_player_horizontal(_flight_vel.x * delta, true)
		else:
			_move_player_horizontal(float(dir) * base_speed * p_boost * delta, is_flying)

	_reconcile_chilopoda_terrain(player_node, active_character_id, walkable_min_x, walkable_max_x)

	if is_flying:
		var max_fly_y := _ground_y_at(player_node.position.x)
		player_node.position.y = clampf(player_node.position.y + _flight_vel.y * delta, fly_min_y, max_fly_y)
		player_vy = 0.0
	elif is_stationary:
		player_vy = 0.0
	else:
		_integrate_player_vertical(delta, jumped_now)

	var sup_now := get_nearest_support_y_below(player_node.position.x, player_node.position.y)
	if not is_flying and not is_stationary and player_node.position.y >= sup_now - 2.0 and dir != 0 and not turning_now:
		_step_dust_accum_px += absf(player_node.position.x - prev_px)
		if _step_dust_accum_px >= 96.0:
			_step_dust_accum_px = 0.0
			_spawn_ground_dust(player_node.position.x, sup_now, 0.72)
	elif dir == 0:
		_step_dust_accum_px = 64.0

	if not turning_now:
		var spr := player_node.get_node_or_null("Sprite")
		if spr is AnimatedSprite2D and not action_playing:
			var aspr := spr as AnimatedSprite2D
			var target_clip := &"idle"
			var moving_fly := is_flying and fly_input_vec.length() > 0.12
			if not is_flying and player_node.position.y < sup_now - 3.0 and aspr.sprite_frames != null and aspr.sprite_frames.has_animation(&"jump"):
				target_clip = &"jump"
			elif (dir != 0 or eff_fly_dir_y != 0 or moving_fly) and aspr.sprite_frames != null:
				if is_run and aspr.sprite_frames.has_animation(&"run"):
					target_clip = &"run"
				elif aspr.sprite_frames.has_animation(&"walk"):
					target_clip = &"walk"
				elif aspr.sprite_frames.has_animation(&"fly"):
					target_clip = &"fly"
			if aspr.animation != target_clip or not aspr.is_playing():
				_play_locomotion_preserving_phase(aspr, target_clip, _should_preserve_idle_walk_phase(entry))


func _physics_process(delta: float) -> void:
	if Engine.is_editor_hint() or DisplayServer.get_name() == "headless":
		return

	if _wish_notice_timer_s > 0.0:
		_wish_notice_timer_s = maxf(0.0, _wish_notice_timer_s - delta)
		if _wish_notice_timer_s == 0.0 and wish_notice_label != null:
			wish_notice_label.visible = false
	if shenron_summon != null and shenron_summon.is_casting():
		player_vy = 0.0
		return

	var t_down := Input.is_key_pressed(KEY_T)
	var tab_down := Input.is_key_pressed(KEY_TAB)
	var t_just := t_down and not _t_key_was_down
	var tab_just := tab_down and not _tab_key_was_down
	_t_key_was_down = t_down
	_tab_key_was_down = tab_down

	if player_node == null:
		if field_mode_enabled and field_manager != null and field_manager.active:
			field_manager.step(delta)
			_update_follow_camera()
			_step_ground_dust(delta)
			_update_parallax_scroll()
			_update_hud()
			queue_redraw()
		return

	var field_dead: bool = field_mode_enabled and field_manager != null and bool(field_manager.active) and bool(field_manager.player_dead)
	if not field_dead:
		if tab_just and field_mode_enabled and field_manager != null and field_manager.active:
			field_manager.cycle_target_pointer()
			_sync_field_pad_state()
		if t_just:
			if field_manager != null:
				field_manager.cancel_auto_approach()
			_align_player_facing_to_active_move_dir()
			_request_player_action("teleport")
		for action_name in [&"attack_light", &"attack_heavy", &"power_up"]:
			if Input.is_action_just_pressed(action_name):
				var aname := String(action_name)
				if aname != "attack_light" and field_manager != null:
					field_manager.cancel_auto_approach()
				if field_mode_enabled and field_manager != null and field_manager.active:
					if aname == "attack_light":
						field_manager.request_player_primary_action()
					elif aname == "power_up":
						field_manager.request_player_power_up()
					else:
						_request_player_action(aname)
				else:
					_request_player_action(aname)

		var dir := 0
		if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT) or Input.is_action_pressed(&"move_right"):
			dir += 1
		if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT) or Input.is_action_pressed(&"move_left"):
			dir -= 1
		if mobile_pad != null and is_instance_valid(mobile_pad) and mobile_pad.analog_dir_x != 0:
			dir = clampi(mobile_pad.analog_dir_x, -1, 1)
		elif touch_hud != null and is_instance_valid(touch_hud) and int(touch_hud.get("touch_dir_x")) != 0:
			dir = clampi(int(touch_hud.get("touch_dir_x")), -1, 1)
		var is_run := Input.is_key_pressed(KEY_SHIFT)

		var fly_dir_y := 0
		if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP) or Input.is_action_pressed(&"move_up"):
			fly_dir_y -= 1
		if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN) or Input.is_action_pressed(&"move_down"):
			fly_dir_y += 1
		if mobile_pad != null and is_instance_valid(mobile_pad) and _is_flying_entry(_find_character_entry_ro(active_character_id)) and mobile_pad.analog_dir_y != 0:
			fly_dir_y = clampi(mobile_pad.analog_dir_y, -1, 1)
		elif touch_hud != null and is_instance_valid(touch_hud) and int(touch_hud.get("touch_dir_y")) != 0:
			fly_dir_y = clampi(int(touch_hud.get("touch_dir_y")), -1, 1)

		var jump_req := Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_UP) or Input.is_action_pressed(&"jump")
		var drop_req := Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN) or Input.is_action_pressed(&"move_down")
		var pad_vec: Vector2 = mobile_pad.analog_vector if (mobile_pad != null and is_instance_valid(mobile_pad)) else Vector2.ZERO
		var has_manual_move := dir != 0 or fly_dir_y != 0 or jump_req or drop_req or pad_vec.length() > 0.12
		if has_manual_move and field_manager != null:
			field_manager.cancel_auto_approach()
		if not (field_mode_enabled and field_manager != null and field_manager.active and bool(field_manager.auto_approach_active)):
			step_player_movement(delta, dir, fly_dir_y, jump_req, drop_req, is_run, pad_vec)
	else:
		player_vy = 0.0

	_update_follow_camera()

	if field_mode_enabled and field_manager != null and field_manager.active:
		field_manager.step(delta)
		_sync_field_pad_state()
	elif utility_ai_enabled:
		step_utility_ai(delta)

	_step_ground_dust(delta)
	_update_parallax_scroll()
	_update_hud()
	queue_redraw()


func _is_ruler_ui_hit(screen_pos: Vector2) -> bool:
	if ruler_button != null and is_instance_valid(ruler_button) and ruler_button.get_global_rect().has_point(screen_pos):
		return true
	if ruler_modal != null and is_instance_valid(ruler_modal) and ruler_modal.is_screen_point_inside(screen_pos):
		return true
	return false


func _input(event: InputEvent) -> void:
	if not ruler_pick_mode:
		return
	var is_press := false
	var is_release := false
	var is_drag := false
	var pos := Vector2.ZERO
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index != MOUSE_BUTTON_LEFT:
			return
		pos = mb.position
		is_press = mb.pressed
		is_release = not mb.pressed
	elif event is InputEventMouseMotion:
		if not _ruler_dragging:
			return
		pos = (event as InputEventMouseMotion).position
		is_drag = true
	elif event is InputEventScreenTouch:
		var st := event as InputEventScreenTouch
		if st.index != 0:
			return
		pos = st.position
		is_press = st.pressed
		is_release = not st.pressed
	elif event is InputEventScreenDrag:
		var sd := event as InputEventScreenDrag
		if sd.index != 0 or not _ruler_dragging:
			return
		pos = sd.position
		is_drag = true
	else:
		return

	if is_press:
		if _is_ruler_ui_hit(pos):
			return
		var wp := screen_to_world_pos(pos)
		var snapped := Vector2(roundf(wp.x), roundf(wp.y))
		_ruler_dragging = true
		_ruler_drag_start_screen = pos
		if _ruler_awaiting_b and ruler_has_a:
			ruler_point_b = snapped
			ruler_has_b = true
		else:
			ruler_point_a = snapped
			ruler_has_a = true
			ruler_point_b = snapped
			ruler_has_b = false
		_sync_ruler_ui()
		get_viewport().set_input_as_handled()
	elif is_drag and _ruler_dragging:
		var wp := screen_to_world_pos(pos)
		ruler_point_b = Vector2(roundf(wp.x), roundf(wp.y))
		ruler_has_b = true
		_sync_ruler_ui()
		get_viewport().set_input_as_handled()
	elif is_release and _ruler_dragging:
		var wp := screen_to_world_pos(pos)
		var snapped := Vector2(roundf(wp.x), roundf(wp.y))
		var moved_px := pos.distance_to(_ruler_drag_start_screen)
		_ruler_dragging = false
		if moved_px >= 8.0:
			ruler_point_b = snapped
			ruler_has_b = true
			_ruler_awaiting_b = false
		elif _ruler_awaiting_b:
			ruler_point_b = snapped
			ruler_has_b = true
			_ruler_awaiting_b = false
		else:
			ruler_point_a = snapped
			ruler_has_a = true
			ruler_has_b = false
			_ruler_awaiting_b = true
		_sync_ruler_ui()
		get_viewport().set_input_as_handled()


func _is_point_over_hud_controls(screen_pos: Vector2) -> bool:
	if _is_ruler_ui_hit(screen_pos):
		return true
	if mobile_pad != null and is_instance_valid(mobile_pad) and bool(mobile_pad.call("is_screen_point_over_pad", screen_pos)):
		return true
	for ctrl in [summon_button, wish_panel, item_toggle_button, item_drop_test_button, item_pickup_button, pixel_perfect_button, toggle_hero_button, pad_settings_button, toggle_ui_button, immortal_button, monster_range_button]:
		if ctrl != null and is_instance_valid(ctrl) and (ctrl as Control).visible:
			if (ctrl as Control).get_global_rect().has_point(screen_pos):
				return true
	return false


func _unhandled_input(event: InputEvent) -> void:
	if field_mode_enabled and field_manager != null and field_manager.active and not ruler_pick_mode:
		var tap_pos := Vector2.ZERO
		var is_tap := false
		if event is InputEventScreenTouch:
			var st := event as InputEventScreenTouch
			if st.pressed:
				_last_touch_tap_msec = Time.get_ticks_msec()
				tap_pos = st.position
				is_tap = true
		elif event is InputEventMouseButton:
			var mb := event as InputEventMouseButton
			if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
				if Time.get_ticks_msec() - _last_touch_tap_msec < 60:
					return
				tap_pos = mb.position
				is_tap = true
		if is_tap:
			if _is_point_over_hud_controls(tap_pos):
				return
			var wp := screen_to_world_pos(tap_pos)
			var picked: Dictionary = field_manager.select_target_at_world_pos(wp)
			if bool(picked.get("selected", false)):
				_sync_field_pad_state()
				get_viewport().set_input_as_handled()
			return
	if not (event is InputEventKey):
		return
	var kev := event as InputEventKey
	if not kev.pressed or kev.echo:
		return
	if kev.keycode == KEY_1:
		set_character_scale(1.0)
	elif kev.keycode == KEY_2:
		set_character_scale(2.0)
	elif kev.keycode == KEY_3:
		set_character_scale(3.0)
	elif kev.keycode == KEY_MINUS or kev.keycode == KEY_BRACKETLEFT:
		set_character_scale(char_scale - 0.05)
	elif kev.keycode == KEY_EQUAL or kev.keycode == KEY_BRACKETRIGHT:
		set_character_scale(char_scale + 0.05)
	elif kev.keycode == KEY_G:
		show_grid_overlay = not show_grid_overlay
		queue_redraw()
	elif kev.keycode == KEY_Q or (kev.keycode == KEY_TAB and not field_mode_enabled):
		if not roster_characters.is_empty():
			_char_index = (_char_index + 1) % roster_characters.size()
			var next_id := str(roster_characters[_char_index].get("character_id", ""))
			if not next_id.is_empty():
				select_character(next_id)


func _draw_pixel_contact_shadow(pos_x: float, pos_y: float, body_w: float, scale_val: float, visible_flag: bool) -> void:
	var half_w := clampf(body_w * scale_val * 0.36, 22.0, 88.0) if body_w > 0.0 else 52.0
	var sp := compute_contact_shadow_params(pos_x, pos_y, half_w, visible_flag)
	if not bool(sp["visible"]):
		return
	var hw := float(sp["half_w"])
	var sy := float(sp["support_y"])
	var alpha := float(sp["alpha"])
	var cfg: Dictionary = terrain_config.get("contact_shadow", {})
	var outer: Array = cfg.get("outer_rgba", [35, 22, 16, 60])
	var inner: Array = cfg.get("inner_rgba", [24, 14, 10, 85])
	var sec_left := MAP_LEFT_X
	var sec_right := MAP_RIGHT_X
	for sec in _get_terrain_sections():
		var sl := float(sec["left_x"])
		var sr := float(sec["right_x"])
		if pos_x >= sl and pos_x < sr:
			sec_left = sl
			sec_right = sr
			break
	var ox0 := maxf(pos_x - hw, sec_left) if pos_y <= sy + 24.0 else (pos_x - hw)
	var ox1 := minf(pos_x + hw, sec_right) if pos_y <= sy + 24.0 else (pos_x + hw)
	if ox1 > ox0:
		draw_rect(Rect2(ox0, sy - 4.0, ox1 - ox0, 8.0), Color8(int(outer[0]), int(outer[1]), int(outer[2]), int(round(float(outer[3]) * alpha))))
	var ix0 := maxf(pos_x - hw * 0.68, sec_left) if pos_y <= sy + 24.0 else (pos_x - hw * 0.68)
	var ix1 := minf(pos_x + hw * 0.68, sec_right) if pos_y <= sy + 24.0 else (pos_x + hw * 0.68)
	if ix1 > ix0:
		draw_rect(Rect2(ix0, sy - 6.0, ix1 - ix0, 10.0), Color8(int(inner[0]), int(inner[1]), int(inner[2]), int(round(float(inner[3]) * alpha))))


func _draw_ruler_overlay() -> void:
	var font := ThemeDB.fallback_font
	if ruler_grid_enabled:
		var start_x := int(MAP_LEFT_X)
		var end_x := int(MAP_RIGHT_X)
		for wx in range(start_x, end_x + 1, 100):
			var fx := float(wx)
			var major := (wx % 200 == 0)
			var gy := _ground_y_at(fx)
			draw_line(Vector2(fx, gy - (16.0 if major else 8.0)), Vector2(fx, gy + (12.0 if major else 6.0)), Color(0.22, 0.74, 0.97, 0.75 if major else 0.45), 1.5 if major else 1.0)
			if major and font != null:
				draw_string(font, Vector2(fx + 3.0, gy + 24.0), "%d" % wx, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(0.72, 0.92, 1.0, 0.9))
		for edge_x in _get_terrain_step_edges():
			draw_line(Vector2(edge_x, MAP_TOP_Y), Vector2(edge_x, MAP_BOTTOM_Y), Color(0.98, 0.45, 0.09, 0.7), 2.0)
			if font != null:
				draw_string(font, Vector2(edge_x + 6.0, _ground_y_at(edge_x - 1.0) - 24.0), "STEP %d" % int(round(edge_x)), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(1.0, 0.78, 0.45, 0.95))
	if ruler_has_a:
		draw_line(ruler_point_a - Vector2(14.0, 0.0), ruler_point_a + Vector2(14.0, 0.0), Color(0.13, 0.83, 0.93, 0.95), 2.5)
		draw_line(ruler_point_a - Vector2(0.0, 14.0), ruler_point_a + Vector2(0.0, 14.0), Color(0.13, 0.83, 0.93, 0.95), 2.5)
		if font != null:
			draw_string(font, ruler_point_a + Vector2(8.0, -10.0), "A(%d,%d)" % [int(round(ruler_point_a.x)), int(round(ruler_point_a.y))], HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color(0.56, 0.95, 1.0, 1.0))
	if ruler_has_a and ruler_has_b:
		draw_line(ruler_point_b - Vector2(14.0, 0.0), ruler_point_b + Vector2(14.0, 0.0), Color(0.98, 0.80, 0.08, 0.95), 2.5)
		draw_line(ruler_point_b - Vector2(0.0, 14.0), ruler_point_b + Vector2(0.0, 14.0), Color(0.98, 0.80, 0.08, 0.95), 2.5)
		var corner := Vector2(ruler_point_b.x, ruler_point_a.y)
		draw_line(ruler_point_a, corner, Color(0.22, 0.74, 0.97, 0.7), 2.0)
		draw_line(corner, ruler_point_b, Color(0.98, 0.80, 0.08, 0.7), 2.0)
		draw_line(ruler_point_a, ruler_point_b, Color(0.35, 0.95, 0.62, 0.95), 3.0)
		if font != null:
			draw_string(font, ruler_point_b + Vector2(8.0, -10.0), "B(%d,%d)" % [int(round(ruler_point_b.x)), int(round(ruler_point_b.y))], HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color(1.0, 0.92, 0.45, 1.0))
			var mid := (ruler_point_a + ruler_point_b) * 0.5
			var dx := absf(ruler_point_b.x - ruler_point_a.x)
			var dy := absf(ruler_point_b.y - ruler_point_a.y)
			var dist := ruler_point_a.distance_to(ruler_point_b)
			var txt := "dX=%.0fpx | dY=%.0fpx | D=%.1fpx" % [dx, dy, dist]
			draw_rect(Rect2(mid.x - 115.0, mid.y - 28.0, 230.0, 22.0), Color(0.04, 0.07, 0.14, 0.86))
			draw_string(font, Vector2(mid.x - 108.0, mid.y - 12.0), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(0.55, 0.98, 0.72, 1.0))


func _draw() -> void:
	# Dynamic Pixel Contact Shadows on exact surface below each fighter/item (zero ellipse)
	if player_node != null:
		var p_dims := _get_body_dims(_find_character_entry_ro(active_character_id))
		_draw_pixel_contact_shadow(player_node.position.x, player_node.position.y, float(p_dims.x), char_scale, _is_fighter_surface_visible(player_node, active_character_id))
	if dummy_node != null:
		var e_dims := _get_body_dims(_find_character_entry_ro(enemy_character_id))
		_draw_pixel_contact_shadow(dummy_node.position.x, dummy_node.position.y, float(e_dims.x), enemy_scale, _is_fighter_surface_visible(dummy_node, enemy_character_id))
	if field_mode_enabled and field_manager != null and field_manager.active:
		for slot in field_manager.slots:
			if bool(slot.get("alive", false)):
				var mnode := slot.get("node") as Node2D
				if mnode != null and is_instance_valid(mnode):
					var cid := str(slot.get("character_id", ""))
					var m_dims := _get_body_dims(_find_character_entry_ro(cid))
					_draw_pixel_contact_shadow(mnode.position.x, mnode.position.y, float(m_dims.x), float(slot.get("scale_val", 2.0)), _is_fighter_surface_visible(mnode, cid))
	if item_drop_enabled:
		for item_n in _dropped_item_nodes:
			if is_instance_valid(item_n) and item_n.visible:
				_draw_pixel_contact_shadow(item_n.position.x, item_n.position.y, 28.0, item_n.scale.x, true)

	if _field_overlay_node != null and is_instance_valid(_field_overlay_node):
		_field_overlay_node.visible = field_mode_enabled and field_manager != null and field_manager.active
		_field_overlay_node.queue_redraw()

	_draw_ruler_overlay()

	if not show_grid_overlay:
		return
	for plat in terrain_platforms:
		if plat is Dictionary:
			var px := float(plat.get("x", 0.0))
			var py := float(plat.get("y", ground_y))
			var pw := float(plat.get("w", 0.0))
			draw_line(Vector2(px, py), Vector2(px + pw, py), Color(0.22, 0.90, 0.55, 0.72), 2.0)
	if utility_ai_enabled:
		var zy := ground_y + 12.0
		draw_line(Vector2(ai_controller.zone_min_x, zy), Vector2(ai_controller.zone_max_x, zy), Color(0.96, 0.62, 0.04, 0.90), 3.0)
		draw_line(Vector2(ai_controller.zone_min_x, zy - 16.0), Vector2(ai_controller.zone_min_x, zy + 8.0), Color(0.96, 0.62, 0.04, 0.90), 2.0)
		draw_line(Vector2(ai_controller.zone_max_x, zy - 16.0), Vector2(ai_controller.zone_max_x, zy + 8.0), Color(0.96, 0.62, 0.04, 0.90), 2.0)


func _update_hud() -> void:
	if hud_label == null:
		return
	var entry := _find_character_entry(active_character_id)
	var dims := _get_body_dims(entry)
	var scaled_w := int(round(float(dims.x) * char_scale))
	var scaled_h := int(round(float(dims.y) * char_scale))
	var pct_h := (float(scaled_h) / float(viewport_height) * 100.0) if viewport_height > 0 else 0.0
	var spd := int(round(_get_walk_speed_px_per_s(entry)))
	var px := int(round(player_node.position.x)) if player_node != null else int(player_spawn_x)
	var py := int(round(player_node.position.y)) if player_node != null else int(ground_y)
	var ai_txt := ""
	if utility_ai_enabled:
		var edge_d := int(round(float(ai_last_decision.get("edge_dist", -1.0))))
		ai_txt = " | AI[%s]: %s gap=%dpx chain=%d/%d zone=[%d..%d]" % [
			enemy_character_id,
			str(ai_controller.last_reason),
			edge_d,
			ai_controller.light_chain_count,
			ai_controller.light_hits_before_heavy,
			int(round(ai_controller.zone_min_x)),
			int(round(ai_controller.zone_max_x)),
		]
	var vis := _get_visible_logic_size()
	if field_mode_enabled and field_manager != null and field_manager.active:
		var alive_cnt := 0
		for s in field_manager.slots:
			if bool(s.get("alive", false)):
				alive_cnt += 1
		var hero_txt := "Ẩn (bấm Hiện Tướng)"
		if field_manager.player_spawned and player_node != null:
			if field_manager.player_dead:
				hero_txt = "Drum KO (%.1fs)" % field_manager.player_respawn_timer_s
			else:
				var imm_tag := " [BẤT TỬ]" if field_manager.player_immortal else ""
				hero_txt = "Drum %d/%d HP%s | %d/%d MP (%d,%d)" % [int(round(field_manager.player_hp)), int(round(field_manager.player_max_hp)), imm_tag, int(round(field_manager.player_mana)), int(round(field_manager.player_max_mana)), px, py]
		var boss_txt := ""
		var bslot: Dictionary = field_manager.boss_slot
		if not bslot.is_empty() and bool(bslot.get("alive", false)):
			boss_txt = " | Boss Drum: %d/%d HP" % [int(round(float(bslot.get("hp", 0.0)))), int(round(float(bslot.get("max_hp", 5000.0))))]
		elif field_manager.boss_has_spawned_once:
			boss_txt = " | Boss hồi: %.0fs" % field_manager.boss_respawn_timer_s
		elif field_manager.player_spawned:
			boss_txt = " | Boss: %.0fs" % field_manager.boss_spawn_timer_s
		else:
			boss_txt = " | Boss: Chờ Tướng (5')"
		hud_label.text = "%dx%d | FPS %d/60 | Quái: %d/%d | %s%s | Ngọc: %d" % [
			int(round(vis.x)), int(round(vis.y)), Engine.get_frames_per_second(), alive_cnt, field_manager.slots.size(), hero_txt, boss_txt, collected_bag_balls.size()
		]
	else:
		hud_label.text = "%dx%d | %s | %.2fx Nearest (%dx%dpx, %.1f%% 1080p) | FPS: %d/60 | Speed: %d px/s | Pos: (%d, %d) | [1/2/3/-/+] Scale%s" % [
			int(round(vis.x)), int(round(vis.y)), active_character_id, char_scale, scaled_w, scaled_h, pct_h, Engine.get_frames_per_second(), spd, px, py, ai_txt
		]
	if ruler_modal_visible and ruler_modal != null and is_instance_valid(ruler_modal):
		ruler_modal.update_metrics(get_ruler_metrics())


func set_item_drop_preview(enabled: bool, ball_number: int = 0, item_scale: float = 1.0) -> void:
	item_drop_enabled = enabled
	item_drop_ball = clampi(ball_number, 0, 7)
	item_drop_scale = clampf(item_scale, 0.5, 4.0)
	_sync_item_toggle_button()
	_refresh_dropped_items()


func toggle_dropped_items_visible() -> bool:
	item_drop_enabled = not item_drop_enabled
	if _item_drop_layer != null and is_instance_valid(_item_drop_layer):
		_item_drop_layer.visible = item_drop_enabled
	if item_drop_enabled and _dropped_item_nodes.is_empty():
		_refresh_dropped_items()
	_sync_item_toggle_button()
	return item_drop_enabled


func _sync_item_toggle_button() -> void:
	if item_toggle_button != null:
		item_toggle_button.text = "Ẩn Ngọc" if item_drop_enabled else "Hiện Ngọc"


func _ensure_item_drop_layer() -> Node2D:
	if _item_drop_layer == null or not is_instance_valid(_item_drop_layer):
		_item_drop_layer = Node2D.new()
		_item_drop_layer.name = "ItemDropsLayer"
		_item_drop_layer.z_index = 50
		_item_drop_layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		add_child(_item_drop_layer)
	else:
		_item_drop_layer.z_index = 50
	_item_drop_layer.visible = item_drop_enabled
	return _item_drop_layer


func _clear_dropped_items() -> void:
	for node in _dropped_item_nodes:
		if is_instance_valid(node):
			if node.get_parent() != null:
				node.get_parent().remove_child(node)
			node.queue_free()
	_dropped_item_nodes.clear()


func _refresh_dropped_items() -> void:
	_clear_dropped_items()
	if not item_drop_enabled:
		if _item_drop_layer != null and is_instance_valid(_item_drop_layer):
			_item_drop_layer.visible = false
		return
	var layer := _ensure_item_drop_layer()
	var center_x := float(viewport_width) * 0.5
	if item_drop_ball == 0:
		var step_x := roundf(44.0 * maxf(1.0, item_drop_scale))
		var start_x := center_x - 3.0 * step_x
		for i in range(7):
			var item := DragonBallItemScene.instantiate() as Node2D
			item.set("display_mode", "map")
			item.set("ball_number", i + 1)
			var ix := start_x + float(i) * step_x
			item.position = Vector2(ix, _ground_y_at(ix))
			item.scale = Vector2(item_drop_scale, item_drop_scale)
			if item.has_signal("collected"):
				item.connect("collected", _on_dropped_item_collected)
			layer.add_child(item)
			_dropped_item_nodes.append(item)
	else:
		var item := DragonBallItemScene.instantiate() as Node2D
		item.set("display_mode", "map")
		item.set("ball_number", item_drop_ball)
		item.position = Vector2(center_x, _ground_y_at(center_x))
		item.scale = Vector2(item_drop_scale, item_drop_scale)
		if item.has_signal("collected"):
			item.connect("collected", _on_dropped_item_collected)
		layer.add_child(item)
		_dropped_item_nodes.append(item)


func trigger_monster_death_drop(ball_num: int = 0) -> Node2D:
	item_drop_enabled = true
	_sync_item_toggle_button()
	var layer := _ensure_item_drop_layer()
	var n := clampi(ball_num, 1, 7) if ball_num > 0 else _next_monster_drop_ball
	if ball_num <= 0:
		_next_monster_drop_ball = (_next_monster_drop_ball % 7) + 1
	if dummy_node != null:
		_play_fighter_clip(dummy_node, "ko")
	var spawn_pos := dummy_node.position if dummy_node != null else Vector2(dummy_spawn_x, _ground_y_at(dummy_spawn_x))
	var drop_floor_y := _ground_y_at(spawn_pos.x)
	var px := player_node.position.x if player_node != null else player_spawn_x
	var roll_dir := -1.0 if px <= spawn_pos.x else 1.0
	var item := DragonBallItemScene.instantiate() as Node2D
	item.set("ball_number", n)
	if item.has_signal("collected"):
		item.connect("collected", _on_dropped_item_collected)
	layer.add_child(item)
	item.call("start_drop_from", spawn_pos, drop_floor_y, roll_dir, item_drop_scale)
	_dropped_item_nodes.append(item)
	return item


func pickup_dropped_items() -> int:
	if player_node == null:
		return 0
	var p_entry := _find_character_entry(active_character_id)
	var dims := _get_body_dims(p_entry)
	var center_off_y := -maxf(28.0, float(dims.y) * char_scale * 0.5)
	var started := 0
	for node in _dropped_item_nodes:
		if is_instance_valid(node) and node.has_method("start_collect"):
			if bool(node.call("start_collect", player_node, center_off_y, player_node.position + Vector2(0.0, center_off_y))):
				started += 1
	return started


func step_dropped_items(delta: float) -> void:
	for node in _dropped_item_nodes:
		if is_instance_valid(node) and node.has_method("step_lifecycle"):
			node.call("step_lifecycle", delta)


func _on_dropped_item_collected(ball_num: int) -> void:
	if not collected_bag_balls.has(ball_num):
		collected_bag_balls.append(ball_num)


func get_item_drop_metrics() -> Dictionary:
	var nodes_info: Array = []
	for node in _dropped_item_nodes:
		if is_instance_valid(node) and node.has_method("get_item_metrics"):
			var info: Dictionary = node.call("get_item_metrics")
			info["position"] = [node.position.x, node.position.y]
			info["scale"] = [node.scale.x, node.scale.y]
			nodes_info.append(info)
	return {
		"enabled": item_drop_enabled,
		"ball_number": item_drop_ball,
		"item_scale": item_drop_scale,
		"count": nodes_info.size(),
		"collected_bag_balls": collected_bag_balls.duplicate(),
		"items": nodes_info,
	}


func get_stage_metrics() -> Dictionary:
	return {
		"viewport_width": viewport_width,
		"viewport_height": viewport_height,
		"stretch_mode": str(ProjectSettings.get_setting("display/window/stretch/mode", "canvas_items")),
		"stretch_aspect": str(ProjectSettings.get_setting("display/window/stretch/aspect", "expand")),
		"renderer": str(ProjectSettings.get_setting("rendering/renderer/rendering_method", "gl_compatibility")),
		"display_layout": display_layout_info.duplicate(true),
		"ground_y": ground_y,
		"terrain_loaded": not terrain_config.is_empty(),
		"platforms_count": terrain_platforms.size(),
		"active_dust_fx_count": _active_dust_fx.size(),
		"fly_min_y": fly_min_y,
		"fly_default_y": fly_default_y,
		"walkable_min_x": walkable_min_x,
		"walkable_max_x": walkable_max_x,
		"player_spawn_x": player_spawn_x,
		"dummy_spawn_x": dummy_spawn_x,
		"char_scale": char_scale,
		"enemy_scale": enemy_scale,
		"active_character_id": active_character_id,
		"enemy_character_id": enemy_character_id,
		"player_position": [player_node.position.x, player_node.position.y] if player_node != null else [0.0, 0.0],
		"dummy_position": [dummy_node.position.x, dummy_node.position.y] if dummy_node != null else [0.0, 0.0],
		"utility_ai": {
			"enabled": utility_ai_enabled,
			"enemy_character_id": enemy_character_id,
			"zone_min_x": ai_controller.zone_min_x,
			"zone_max_x": ai_controller.zone_max_x,
			"light_chain_count": ai_controller.light_chain_count,
			"cooldown_remaining": ai_controller.cooldown_remaining,
			"last_intent": ai_controller.last_intent,
			"last_reason": ai_controller.last_reason,
			"last_attack_clip": str(ai_last_decision.get("attack_clip", "")),
			"last_edge_dist": float(ai_last_decision.get("edge_dist", -1.0)),
		},
	}
