class_name TouchHudOverlay
extends Control
## Responsive Mobile Safe-Area Touch Controls & Pixel-Perfect / Device Profile HUD (D1, D2, D4).
## Emits virtual touch actions synced directly with keyboard controls in ArenaSandbox.gd.

signal pixel_perfect_toggled(enabled: bool)
signal touch_action_triggered(action_name: String)

var touch_dir_x: int = 0
var touch_dir_y: int = 0
var pixel_perfect_button: Button = null
var safe_root: MarginContainer = null
var _dpad_box: HBoxContainer = null
var _actions_box: HBoxContainer = null
var _jump_button: Button = null


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_controls()


func _build_controls() -> void:
	safe_root = MarginContainer.new()
	safe_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	safe_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(safe_root)

	var anchor_ctrl := Control.new()
	anchor_ctrl.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	anchor_ctrl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	safe_root.add_child(anchor_ctrl)

	pixel_perfect_button = Button.new()
	pixel_perfect_button.text = "Pixel Perfect: OFF (Fractional)"
	pixel_perfect_button.anchor_left = 0.0
	pixel_perfect_button.anchor_top = 0.0
	pixel_perfect_button.offset_left = 20.0
	pixel_perfect_button.offset_top = 60.0
	pixel_perfect_button.custom_minimum_size = Vector2(270, 38)
	pixel_perfect_button.pressed.connect(func() -> void:
		var next_state := not pixel_perfect_button.text.contains(": ON")
		pixel_perfect_toggled.emit(next_state)
	)
	anchor_ctrl.add_child(pixel_perfect_button)

	# Bottom-left mobile movement pad
	_dpad_box = HBoxContainer.new()
	_dpad_box.anchor_left = 0.0
	_dpad_box.anchor_top = 1.0
	_dpad_box.anchor_right = 0.0
	_dpad_box.anchor_bottom = 1.0
	_dpad_box.offset_left = 24.0
	_dpad_box.offset_top = -92.0
	_dpad_box.offset_right = 330.0
	_dpad_box.offset_bottom = -20.0
	_dpad_box.add_theme_constant_override("separation", 10)
	anchor_ctrl.add_child(_dpad_box)

	_add_hold_button(_dpad_box, "◀ Trái", func(down: bool) -> void:
		touch_dir_x = -1 if down else (0 if touch_dir_x == -1 else touch_dir_x)
	)
	_add_hold_button(_dpad_box, "▶ Phải", func(down: bool) -> void:
		touch_dir_x = 1 if down else (0 if touch_dir_x == 1 else touch_dir_x)
	)
	_jump_button = _add_hold_button(_dpad_box, "▲ Lên/Nhảy", func(down: bool) -> void:
		touch_dir_y = -1 if down else (0 if touch_dir_y == -1 else touch_dir_y)
		if down:
			touch_action_triggered.emit("jump")
	)

	# Bottom-right mobile skill/item buttons
	_actions_box = HBoxContainer.new()
	_actions_box.anchor_left = 1.0
	_actions_box.anchor_top = 1.0
	_actions_box.anchor_right = 1.0
	_actions_box.anchor_bottom = 1.0
	_actions_box.offset_left = -380.0
	_actions_box.offset_top = -92.0
	_actions_box.offset_right = -24.0
	_actions_box.offset_bottom = -20.0
	_actions_box.alignment = BoxContainer.ALIGNMENT_END
	_actions_box.add_theme_constant_override("separation", 10)
	anchor_ctrl.add_child(_actions_box)

	for spec in [["Đánh", "attack_light"], ["Tụ Ki", "power_up"], ["Nhặt", "pickup_items"]]:
		var btn := Button.new()
		btn.text = spec[0]
		btn.custom_minimum_size = Vector2(96, 60)
		var act: String = spec[1]
		btn.pressed.connect(func() -> void: touch_action_triggered.emit(act))
		_actions_box.add_child(btn)


func _add_hold_button(parent: Control, label_txt: String, on_state: Callable) -> Button:
	var btn := Button.new()
	btn.text = label_txt
	btn.custom_minimum_size = Vector2(92, 60)
	btn.button_down.connect(func() -> void: on_state.call(true))
	btn.button_up.connect(func() -> void: on_state.call(false))
	parent.add_child(btn)
	return btn


func set_jump_available(enabled: bool, flight: bool = false) -> void:
	if _jump_button != null:
		_jump_button.disabled = not enabled
		_jump_button.text = "▲ Bay lên" if flight else "▲ Nhảy"


func apply_safe_area(layout_info: Dictionary) -> void:
	if safe_root == null:
		return
	var insets: Dictionary = layout_info.get("safe_insets_logic", {})
	safe_root.add_theme_constant_override("margin_left", int(round(float(insets.get("left", 0.0)))))
	safe_root.add_theme_constant_override("margin_top", int(round(float(insets.get("top", 0.0)))))
	safe_root.add_theme_constant_override("margin_right", int(round(float(insets.get("right", 0.0)))))
	safe_root.add_theme_constant_override("margin_bottom", int(round(float(insets.get("bottom", 0.0)))))
	if pixel_perfect_button != null:
		var applied := bool(layout_info.get("pixel_perfect_applied", false))
		var req := bool(layout_info.get("pixel_perfect_requested", false))
		var guarded := bool(layout_info.get("below_1080p_guard", false))
		if guarded and req:
			pixel_perfect_button.text = "Pixel Perfect: Khóa <1080p (Fractional)"
		elif applied:
			pixel_perfect_button.text = "Pixel Perfect: ON (Integer 1:1)"
		else:
			pixel_perfect_button.text = "Pixel Perfect: OFF (Fractional)"
