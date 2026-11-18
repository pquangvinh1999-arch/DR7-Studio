class_name MobileActionPad
extends Control
## Mobile Analog Stick (bottom-left) + Circular Skill Arc 1..8 + World Position Mini-Map
## Styled cleanly after Owner HUD reference (image copy 8.png): dark frosted glass,
## crisp white double rings, neon-green attack & target reticle accents, vector icons,
## and flexible Button Assignment Settings Modal (buttons 2..7 customizable; 1 & 8 locked).

signal action_triggered(slot_id: int, action_id: String)
signal target_cycle_requested()
signal slot_binding_changed(slot_id: int, action_id: String)

const ACTION_LABELS := {
	"attack_light": "Đánh",
	"jump": "Nhảy",
	"teleport": "Tốc biến",
	"power_up": "Chưởng",
	"attack_heavy": "Đánh nặng",
	"pickup_items": "Nhặt",
	"empty": "Trống",
}

const SHORT_LABELS := {
	"attack_light": "ĐÁNH",
	"jump": "NHẢY",
	"teleport": "TỐC BIẾN",
	"power_up": "CHƯỞNG",
	"attack_heavy": "NẶNG",
	"pickup_items": "NHẶT",
	"cycle_target": "TRỎ",
}

const ASSIGNABLE_ACTIONS := ["jump", "teleport", "power_up", "attack_heavy", "pickup_items", "empty"]

var analog_dir_x: int = 0
var analog_dir_y: int = 0
var analog_vector: Vector2 = Vector2.ZERO

var safe_root: MarginContainer = null
var _anchor_ctrl: Control = null
var _analog_ctrl: Control = null
var _buttons_root: Control = null
var _slot_buttons: Dictionary = {}
var _slot_visuals: Dictionary = {}
var _slot_bindings: Dictionary = {
	1: "attack_light",
	2: "jump",
	3: "teleport",
	4: "power_up",
	5: "empty",
	6: "empty",
	7: "empty",
	8: "cycle_target",
}
var _available_actions: PackedStringArray = PackedStringArray(["attack_light", "jump", "teleport", "power_up"])
var _settings_panel: PanelContainer = null
var _settings_rows: VBoxContainer = null
var _current_mana: float = 0.0
var _max_mana: float = 100.0
var _jump_enabled: bool = true
var _flight_mode: bool = false
var _pointer_kind: String = "enemy"

# Analog drag tracking
var _analog_touch_idx: int = -1
var _analog_mouse_down: bool = false
var _analog_radius: float = 64.0
var _knob_radius: float = 27.0


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_ui()


func _make_circle_style(bg_col: Color, border_col: Color, border_w: int = 2) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg_col
	sb.border_color = border_col
	sb.set_border_width_all(border_w)
	sb.set_corner_radius_all(999)
	return sb


func _apply_circle_button_theme(btn: Button, slot_id: int) -> void:
	var empty_sb := StyleBoxEmpty.new()
	btn.add_theme_stylebox_override("normal", empty_sb)
	btn.add_theme_stylebox_override("hover", empty_sb)
	btn.add_theme_stylebox_override("pressed", empty_sb)
	btn.add_theme_stylebox_override("disabled", empty_sb)
	btn.add_theme_stylebox_override("focus", empty_sb)
	btn.flat = true
	btn.text = ""
	btn.set_meta(&"slot_id", slot_id)


func _build_ui() -> void:
	safe_root = MarginContainer.new()
	safe_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	safe_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(safe_root)

	_anchor_ctrl = Control.new()
	_anchor_ctrl.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_anchor_ctrl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	safe_root.add_child(_anchor_ctrl)

	# Bottom-Left Virtual Analog Stick
	_analog_ctrl = _AnalogCanvas.new()
	_analog_ctrl.name = "AnalogStick"
	_analog_ctrl.anchor_left = 0.0
	_analog_ctrl.anchor_right = 0.0
	_analog_ctrl.anchor_top = 1.0
	_analog_ctrl.anchor_bottom = 1.0
	_analog_ctrl.offset_left = 26.0
	_analog_ctrl.offset_top = -188.0
	_analog_ctrl.offset_right = 190.0
	_analog_ctrl.offset_bottom = -24.0
	_analog_ctrl.mouse_filter = Control.MOUSE_FILTER_STOP
	_analog_ctrl.set("pad_owner", self)
	_anchor_ctrl.add_child(_analog_ctrl)

	# Bottom-Right Circular Button Cluster (1 primary + 2..7 arc + 8 target reticle)
	_buttons_root = Control.new()
	_buttons_root.name = "CircularSkillCluster"
	_buttons_root.anchor_left = 1.0
	_buttons_root.anchor_right = 1.0
	_buttons_root.anchor_top = 1.0
	_buttons_root.anchor_bottom = 1.0
	_buttons_root.offset_left = -392.0
	_buttons_root.offset_top = -296.0
	_buttons_root.offset_right = -18.0
	_buttons_root.offset_bottom = -14.0
	_buttons_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_anchor_ctrl.add_child(_buttons_root)

	# Coordinates inside 374x282 cluster box (bottom-right)
	var layout_specs := {
		1: Rect2(236, 148, 112, 112),
		2: Rect2(298, 72, 68, 68),
		3: Rect2(158, 208, 68, 68),
		4: Rect2(294, 0, 68, 68),
		5: Rect2(214, 46, 66, 66),
		6: Rect2(146, 116, 66, 66),
		7: Rect2(80, 196, 68, 68),
		8: Rect2(12, 200, 62, 62),
	}
	for sid in [1, 2, 3, 4, 5, 6, 7, 8]:
		var r: Rect2 = layout_specs[sid]
		var btn := Button.new()
		btn.name = "SkillCircle_%d" % sid
		btn.position = r.position
		btn.size = r.size
		btn.custom_minimum_size = r.size
		_apply_circle_button_theme(btn, int(sid))
		var vis := _SkillButtonVisual.new()
		vis.name = "Visual"
		vis.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		vis.mouse_filter = Control.MOUSE_FILTER_IGNORE
		vis.set("pad_owner", self)
		vis.set("owner_btn", btn)
		vis.set("slot_id", int(sid))
		btn.add_child(vis)
		var cap_id := int(sid)
		btn.pressed.connect(func() -> void:
			_on_slot_pressed(cap_id)
		)
		var redraw_fn := func() -> void:
			vis.queue_redraw()
		btn.button_down.connect(redraw_fn)
		btn.button_up.connect(redraw_fn)
		btn.mouse_entered.connect(redraw_fn)
		btn.mouse_exited.connect(redraw_fn)
		_buttons_root.add_child(btn)
		_slot_buttons[sid] = btn
		_slot_visuals[sid] = vis

	_build_settings_modal()
	_refresh_slot_buttons()


func _build_settings_modal() -> void:
	_settings_panel = PanelContainer.new()
	_settings_panel.name = "ButtonBindingSettingsModal"
	_settings_panel.anchor_left = 0.5
	_settings_panel.anchor_right = 0.5
	_settings_panel.anchor_top = 0.5
	_settings_panel.anchor_bottom = 0.5
	_settings_panel.offset_left = -250.0
	_settings_panel.offset_right = 250.0
	_settings_panel.offset_top = -190.0
	_settings_panel.offset_bottom = 190.0
	_settings_panel.visible = false
	_settings_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_settings_panel)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 8)
	_settings_panel.add_child(vbox)

	var hdr := HBoxContainer.new()
	var title := Label.new()
	title.text = "⚙️ Cài đặt gán nút chiêu (2..7)"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hdr.add_child(title)
	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.pressed.connect(func() -> void:
		_settings_panel.visible = false
	)
	hdr.add_child(close_btn)
	vbox.add_child(hdr)

	var lock_note := Label.new()
	lock_note.text = "Nút 1 (Đánh/Nhặt) & Nút 8 (Xoay Trỏ) cố định; nút 2..7 tùy chỉnh:"
	lock_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vbox.add_child(lock_note)

	_settings_rows = VBoxContainer.new()
	_settings_rows.add_theme_constant_override("separation", 6)
	vbox.add_child(_settings_rows)
	_rebuild_settings_rows()


func _rebuild_settings_rows() -> void:
	if _settings_rows == null:
		return
	for ch in _settings_rows.get_children():
		ch.queue_free()
	for sid in [2, 3, 4, 5, 6, 7]:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		var lbl := Label.new()
		lbl.text = "Nút số %d:" % sid
		lbl.custom_minimum_size = Vector2(110.0, 0.0)
		row.add_child(lbl)

		var opt := OptionButton.new()
		opt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var cur_act := str(_slot_bindings.get(sid, "empty"))
		var sel_idx := 0
		var idx := 0
		for act_id in ASSIGNABLE_ACTIONS:
			if act_id != "empty" and act_id != "pickup_items" and not _available_actions.has(act_id):
				continue
			opt.add_item(str(ACTION_LABELS.get(act_id, act_id)), idx)
			opt.set_item_metadata(idx, act_id)
			if act_id == cur_act:
				sel_idx = idx
			idx += 1
		opt.select(sel_idx)
		var cap_sid := int(sid)
		opt.item_selected.connect(func(picked_idx: int) -> void:
			var act_name := str(opt.get_item_metadata(picked_idx))
			set_slot_binding(cap_sid, act_name)
		)
		row.add_child(opt)
		_settings_rows.add_child(row)


func toggle_settings_modal() -> void:
	if _settings_panel == null:
		return
	_settings_panel.visible = not _settings_panel.visible
	if _settings_panel.visible:
		_rebuild_settings_rows()


func is_screen_point_over_pad(screen_pos: Vector2) -> bool:
	if not visible:
		return false
	if _settings_panel != null and is_instance_valid(_settings_panel) and _settings_panel.visible:
		if _settings_panel.get_global_rect().has_point(screen_pos):
			return true
	if _analog_ctrl != null and is_instance_valid(_analog_ctrl) and _analog_ctrl.visible:
		if _analog_ctrl.get_global_rect().has_point(screen_pos):
			return true
	for sid in _slot_buttons:
		var btn := _slot_buttons.get(sid) as Button
		if btn != null and is_instance_valid(btn) and btn.visible:
			if btn.get_global_rect().has_point(screen_pos):
				return true
	return false


func set_slot_binding(slot_id: int, action_id: String) -> void:
	if slot_id == 1 or slot_id == 8:
		return
	_slot_bindings[slot_id] = action_id
	_refresh_slot_buttons()
	slot_binding_changed.emit(slot_id, action_id)


func get_slot_binding(slot_id: int) -> String:
	return str(_slot_bindings.get(slot_id, "empty"))


func configure_for_character(char_id: String, available_clips: PackedStringArray, is_flying: bool) -> void:
	_flight_mode = is_flying
	var avail := PackedStringArray(["attack_light"])
	if is_flying or available_clips.has("jump"):
		avail.append("jump")
	if available_clips.has("teleport"):
		avail.append("teleport")
	if available_clips.has("power_up"):
		avail.append("power_up")
	if available_clips.has("attack_heavy"):
		avail.append("attack_heavy")
	_available_actions = avail
	_jump_enabled = is_flying or available_clips.has("jump")

	# Default bindings per character (Drum: 1=Đánh, 2=Nhảy, 3=Tốc biến, 4=Chưởng Orb, 5..7=empty)
	_slot_bindings[1] = "attack_light"
	_slot_bindings[2] = "jump" if _jump_enabled else "empty"
	_slot_bindings[3] = "teleport" if avail.has("teleport") else ("attack_heavy" if avail.has("attack_heavy") else "empty")
	_slot_bindings[4] = "power_up" if avail.has("power_up") else "empty"
	_slot_bindings[5] = "attack_heavy" if (avail.has("attack_heavy") and _slot_bindings[3] != "attack_heavy") else "empty"
	_slot_bindings[6] = "empty"
	_slot_bindings[7] = "empty"
	_slot_bindings[8] = "cycle_target"
	if char_id == "drum":
		_slot_bindings[2] = "jump"
		_slot_bindings[3] = "teleport"
		_slot_bindings[4] = "power_up"
		_slot_bindings[5] = "empty"
	_rebuild_settings_rows()
	_refresh_slot_buttons()


func set_mana_and_pointer_state(mana: float, max_mana: float, pointer_kind: String) -> void:
	_current_mana = mana
	_max_mana = max_mana
	_pointer_kind = pointer_kind
	_refresh_slot_buttons()


func set_jump_available(enabled: bool, flight: bool = false) -> void:
	_jump_enabled = enabled
	_flight_mode = flight
	_refresh_slot_buttons()


func _refresh_slot_buttons() -> void:
	for sid in [1, 2, 3, 4, 5, 6, 7, 8]:
		var btn := _slot_buttons.get(sid) as Button
		if btn == null:
			continue
		var vis := _slot_visuals.get(sid) as Control
		if sid == 8:
			btn.visible = true
			btn.disabled = false
			btn.tooltip_text = "Đổi mục tiêu (Tab)"
			if vis != null:
				vis.queue_redraw()
			continue
		var act := str(_slot_bindings.get(sid, "empty"))
		if sid >= 2 and act == "empty":
			btn.visible = false
			continue
		btn.visible = true
		if sid == 1:
			if _pointer_kind == "item":
				btn.tooltip_text = "Nhặt vật phẩm"
			elif _pointer_kind == "npc":
				btn.tooltip_text = "Nói chuyện"
			else:
				btn.tooltip_text = "Đánh thường"
			btn.disabled = false
			if vis != null:
				vis.queue_redraw()
			continue
		var lbl := str(ACTION_LABELS.get(act, act))
		if act == "jump" and _flight_mode:
			lbl = "Bay lên"
		if act == "power_up":
			btn.tooltip_text = "%s (%d/%d MP)" % [lbl, int(floor(_current_mana)), int(round(_max_mana))]
			btn.disabled = _current_mana < 100.0
		elif act == "jump":
			btn.tooltip_text = lbl
			btn.disabled = not _jump_enabled
		else:
			btn.tooltip_text = lbl
			btn.disabled = false
		if vis != null:
			vis.queue_redraw()


func _on_slot_pressed(slot_id: int) -> void:
	if slot_id == 8:
		target_cycle_requested.emit()
		return
	var act := str(_slot_bindings.get(slot_id, "empty"))
	if act == "empty":
		return
	action_triggered.emit(slot_id, act)


func apply_safe_area(layout_info: Dictionary) -> void:
	if safe_root == null:
		return
	var insets: Dictionary = layout_info.get("safe_insets_logic", {})
	safe_root.add_theme_constant_override("margin_left", int(round(float(insets.get("left", 0.0)))))
	safe_root.add_theme_constant_override("margin_top", int(round(float(insets.get("top", 0.0)))))
	safe_root.add_theme_constant_override("margin_right", int(round(float(insets.get("right", 0.0)))))
	safe_root.add_theme_constant_override("margin_bottom", int(round(float(insets.get("bottom", 0.0)))))


func _update_analog_from_local(local_pos: Vector2) -> void:
	if _analog_ctrl == null:
		return
	var center := _analog_ctrl.size * 0.5
	var delta := local_pos - center
	var max_r := maxf(16.0, _analog_radius - _knob_radius * 0.4)
	if delta.length() > max_r:
		delta = delta.normalized() * max_r
	analog_vector = delta / max_r
	analog_dir_x = -1 if analog_vector.x < -0.22 else (1 if analog_vector.x > 0.22 else 0)
	analog_dir_y = -1 if analog_vector.y < -0.28 else (1 if analog_vector.y > 0.28 else 0)
	_analog_ctrl.queue_redraw()


func _reset_analog() -> void:
	_analog_touch_idx = -1
	_analog_mouse_down = false
	analog_vector = Vector2.ZERO
	analog_dir_x = 0
	analog_dir_y = 0
	if _analog_ctrl != null:
		_analog_ctrl.queue_redraw()


class _AnalogCanvas extends Control:
	var pad_owner = null

	func _gui_input(event: InputEvent) -> void:
		if pad_owner == null:
			return
		if event is InputEventScreenTouch:
			var st := event as InputEventScreenTouch
			if st.pressed and pad_owner._analog_touch_idx == -1:
				pad_owner._analog_touch_idx = st.index
				pad_owner._update_analog_from_local(st.position)
				accept_event()
			elif not st.pressed and st.index == pad_owner._analog_touch_idx:
				pad_owner._reset_analog()
				accept_event()
		elif event is InputEventScreenDrag:
			var sd := event as InputEventScreenDrag
			if sd.index == pad_owner._analog_touch_idx:
				pad_owner._update_analog_from_local(sd.position)
				accept_event()
		elif event is InputEventMouseButton:
			var mb := event as InputEventMouseButton
			if mb.button_index == MOUSE_BUTTON_LEFT:
				if mb.pressed:
					pad_owner._analog_mouse_down = true
					pad_owner._update_analog_from_local(mb.position)
				else:
					pad_owner._reset_analog()
				accept_event()
		elif event is InputEventMouseMotion and pad_owner._analog_mouse_down:
			pad_owner._update_analog_from_local((event as InputEventMouseMotion).position)
			accept_event()

	func _draw() -> void:
		if pad_owner == null:
			return
		var center := size * 0.5
		var base_r := minf(size.x, size.y) * 0.45
		pad_owner._analog_radius = base_r
		# Frosted dark pad with crisp white outer ring (matching image copy 8.png)
		draw_arc(center, base_r + 2.5, 0.0, TAU, 56, Color(0.95, 0.98, 1.0, 0.16), 4.0, true)
		draw_circle(center, base_r, Color(0.08, 0.11, 0.16, 0.66))
		draw_arc(center, base_r, 0.0, TAU, 56, Color(0.94, 0.97, 1.0, 0.90), 2.5, true)
		draw_arc(center, base_r * 0.86, 0.0, TAU, 48, Color(0.88, 0.94, 1.0, 0.18), 1.0, true)
		var knob_pos: Vector2 = center + pad_owner.analog_vector * (base_r - pad_owner._knob_radius * 0.4)
		var active_drag: bool = pad_owner.analog_vector.length() > 0.08
		draw_circle(knob_pos, pad_owner._knob_radius, Color(0.12, 0.18, 0.25, 0.84) if active_drag else Color(0.10, 0.13, 0.19, 0.72))
		draw_arc(knob_pos, pad_owner._knob_radius, 0.0, TAU, 36, Color(0.28, 0.96, 0.58, 0.96) if active_drag else Color(0.94, 0.97, 1.0, 0.92), 2.5, true)


class _SkillButtonVisual extends Control:
	var pad_owner = null
	var owner_btn: Button = null
	var slot_id: int = 1

	func _draw() -> void:
		if pad_owner == null or owner_btn == null:
			return
		var center := size * 0.5
		var r := minf(size.x, size.y) * 0.47
		var pressed_now := owner_btn.button_pressed
		var hovered_now := owner_btn.is_hovered()
		var disabled_now := owner_btn.disabled
		var alpha_mul := 0.42 if disabled_now else 1.0
		var font := ThemeDB.fallback_font

		if slot_id == 8:
			# Green segmented target reticle inspired by image copy 8.png
			var col_g := Color(0.22, 0.96, 0.52, (0.98 if not pressed_now else 1.0) * alpha_mul)
			draw_circle(center, r * 0.88, Color(0.07, 0.10, 0.15, 0.68 if not hovered_now else 0.84))
			for q in range(4):
				var a0 := float(q) * PI * 0.5 + 0.18
				var a1 := float(q + 1) * PI * 0.5 - 0.18
				draw_arc(center, r * 0.82, a0, a1, 14, col_g, 3.0, true)
			for dir_v in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
				draw_line(center + dir_v * (r * 0.54), center + dir_v * (r * 0.96), col_g, 3.0, true)
			draw_circle(center, 3.5, col_g)
			if font != null:
				draw_string(font, Vector2(center.x - 16.0, size.y - 6.0), "TRỎ", HORIZONTAL_ALIGNMENT_CENTER, 32.0, 11, Color(0.95, 0.99, 1.0, alpha_mul))
			return

		var act := str(pad_owner._slot_bindings.get(slot_id, "empty"))
		var base_bg := Color(0.16, 0.22, 0.28, 0.88) if pressed_now else (Color(0.12, 0.16, 0.23, 0.82) if hovered_now else Color(0.09, 0.12, 0.18, 0.76))
		base_bg.a *= alpha_mul
		draw_circle(center, r, base_bg)
		draw_arc(center, r, 0.0, TAU, 48, Color(0.94, 0.97, 1.0, 0.90 * alpha_mul), 2.4, true)
		draw_arc(center, r * 0.87, 0.0, TAU, 40, Color(0.88, 0.95, 1.0, 0.24 * alpha_mul), 1.2, true)

		if slot_id == 1:
			# Primary large button: 4 cardinal ticks + neon-green segmented inner ring + fist/pickup vector icon
			var green_ring := Color(0.20, 0.96, 0.48, 0.95 * alpha_mul)
			if pad_owner._pointer_kind == "item":
				green_ring = Color(0.32, 0.88, 1.0, 0.95 * alpha_mul)
			elif pad_owner._pointer_kind == "npc":
				green_ring = Color(1.0, 0.84, 0.30, 0.95 * alpha_mul)
			for q in range(4):
				var a0 := float(q) * PI * 0.5 + 0.24
				var a1 := float(q + 1) * PI * 0.5 - 0.24
				draw_arc(center, r * 0.62, a0, a1, 14, green_ring, 3.2, true)
			# 4 small white directional triangle ticks inside outer ring
			for dir_a in [0.0, PI * 0.5, PI, PI * 1.5]:
				var dir_v := Vector2(cos(dir_a), sin(dir_a))
				var perp := Vector2(-dir_v.y, dir_v.x)
				var tip := center + dir_v * (r * 0.90)
				var b1 := center + dir_v * (r * 0.77) + perp * 4.5
				var b2 := center + dir_v * (r * 0.77) - perp * 4.5
				draw_colored_polygon(PackedVector2Array([tip, b1, b2]), Color(0.96, 0.98, 1.0, 0.90))
			if pad_owner._pointer_kind == "item":
				_draw_pickup_icon(center + Vector2(0.0, -5.0), r * 0.34, green_ring)
				if font != null:
					draw_string(font, Vector2(center.x - 28.0, center.y + r * 0.50), "NHẶT", HORIZONTAL_ALIGNMENT_CENTER, 56.0, 12, Color(0.95, 0.99, 1.0, 0.95))
			elif pad_owner._pointer_kind == "npc":
				_draw_talk_icon(center + Vector2(0.0, -5.0), r * 0.32, green_ring)
				if font != null:
					draw_string(font, Vector2(center.x - 32.0, center.y + r * 0.50), "N.CHUYỆN", HORIZONTAL_ALIGNMENT_CENTER, 64.0, 11, Color(0.95, 0.99, 1.0, 0.95))
			else:
				_draw_fist_icon(center + Vector2(0.0, -6.0), r * 0.32, green_ring)
				if font != null:
					draw_string(font, Vector2(center.x - 28.0, center.y + r * 0.50), "ĐÁNH", HORIZONTAL_ALIGNMENT_CENTER, 56.0, 12, Color(0.95, 0.99, 1.0, 0.95))
			return

		# Secondary skill buttons (Jump, Teleport/Dash, PowerUp, AttackHeavy, Pickup)
		var icon_col := Color(0.95, 0.98, 1.0, 0.96 * alpha_mul)
		var accent_col := Color(0.32, 0.88, 1.0, 0.95 * alpha_mul)
		var short_lbl := str(SHORT_LABELS.get(act, act.to_upper()))
		if act == "jump":
			if pad_owner._flight_mode:
				short_lbl = "BAY"
			_draw_jump_icon(center + Vector2(0.0, -6.0), r * 0.42, icon_col)
		elif act == "teleport":
			_draw_dash_icon(center + Vector2(0.0, -6.0), r * 0.44, icon_col, accent_col)
		elif act == "power_up":
			var ratio: float = clampf(pad_owner._current_mana / maxf(1.0, pad_owner._max_mana), 0.0, 1.0)
			if ratio > 0.01:
				draw_arc(center, r * 0.93, -PI * 0.5, -PI * 0.5 + TAU * ratio, 36, Color(0.24, 0.86, 1.0, 0.96 if ratio >= 1.0 else 0.72), 3.2, true)
			_draw_ki_icon(center + Vector2(0.0, -8.0), r * 0.36, accent_col if ratio >= 1.0 else icon_col)
			short_lbl = "%d/%d" % [int(floor(pad_owner._current_mana)), int(round(pad_owner._max_mana))]
		elif act == "attack_heavy":
			_draw_heavy_icon(center + Vector2(0.0, -6.0), r * 0.40, Color(1.0, 0.80, 0.34, 0.96 * alpha_mul))
		elif act == "pickup_items":
			_draw_pickup_icon(center + Vector2(0.0, -6.0), r * 0.40, accent_col)

		if font != null:
			draw_string(font, Vector2(center.x - 30.0, center.y + r * 0.64), short_lbl, HORIZONTAL_ALIGNMENT_CENTER, 60.0, 10, Color(0.96, 0.99, 1.0, 0.95 * alpha_mul))

	func _draw_fist_icon(c: Vector2, s: float, col: Color) -> void:
		# Stylized angled fist outline (inspired by primary green attack icon in image copy 8.png)
		var pts := PackedVector2Array([
			c + Vector2(-s * 0.65, s * 0.25),
			c + Vector2(-s * 0.72, -s * 0.25),
			c + Vector2(-s * 0.25, -s * 0.78),
			c + Vector2(s * 0.55, -s * 0.60),
			c + Vector2(s * 0.78, -s * 0.05),
			c + Vector2(s * 0.42, s * 0.68),
			c + Vector2(-s * 0.35, s * 0.68),
		])
		draw_polyline(pts + PackedVector2Array([pts[0]]), col, 2.4, true)
		for k in [-0.25, 0.08, 0.40]:
			draw_line(c + Vector2(s * k - s * 0.12, -s * 0.42), c + Vector2(s * k + s * 0.10, -s * 0.05), col, 2.0, true)

	func _draw_jump_icon(c: Vector2, s: float, col: Color) -> void:
		draw_arc(c + Vector2(0.0, s * 0.85), s * 0.95, PI * 1.18, PI * 1.82, 16, Color(col.r, col.g, col.b, col.a * 0.55), 2.0, true)
		draw_circle(c + Vector2(s * 0.12, -s * 0.52), s * 0.20, col)
		draw_line(c + Vector2(s * 0.05, -s * 0.30), c + Vector2(-s * 0.10, s * 0.14), col, 2.8, true)
		draw_line(c + Vector2(-s * 0.38, -s * 0.16), c + Vector2(s * 0.42, -s * 0.26), col, 2.2, true)
		draw_line(c + Vector2(-s * 0.10, s * 0.14), c + Vector2(-s * 0.42, s * 0.44), col, 2.4, true)
		draw_line(c + Vector2(-s * 0.10, s * 0.14), c + Vector2(s * 0.32, s * 0.32), col, 2.4, true)

	func _draw_dash_icon(c: Vector2, s: float, col: Color, portal_col: Color) -> void:
		draw_arc(c + Vector2(s * 0.34, 0.0), s * 0.62, -PI * 0.46, PI * 0.46, 18, portal_col, 2.6, true)
		for sy in [-0.36, -0.10, 0.16]:
			draw_line(c + Vector2(-s * 0.82, s * sy), c + Vector2(-s * 0.36, s * sy), col, 1.8, true)
		draw_circle(c + Vector2(s * 0.08, -s * 0.44), s * 0.18, col)
		draw_line(c + Vector2(0.0, -s * 0.22), c + Vector2(-s * 0.18, s * 0.18), col, 2.6, true)
		draw_line(c + Vector2(-s * 0.18, s * 0.18), c + Vector2(s * 0.24, s * 0.44), col, 2.2, true)

	func _draw_ki_icon(c: Vector2, s: float, col: Color) -> void:
		draw_circle(c, s * 0.48, Color(col.r, col.g, col.b, col.a * 0.30))
		draw_arc(c, s * 0.48, 0.0, TAU, 24, col, 2.2, true)
		draw_circle(c, s * 0.22, Color(1.0, 1.0, 1.0, col.a))
		for a in [0.0, PI * 0.5, PI, PI * 1.5, PI * 0.25, PI * 0.75, PI * 1.25, PI * 1.75]:
			var dv := Vector2(cos(a), sin(a))
			draw_line(c + dv * (s * 0.62), c + dv * (s * 0.92), col, 1.8, true)

	func _draw_heavy_icon(c: Vector2, s: float, col: Color) -> void:
		draw_line(c + Vector2(-s * 0.62, -s * 0.52), c + Vector2(s * 0.56, s * 0.44), col, 3.0, true)
		draw_line(c + Vector2(s * 0.48, -s * 0.48), c + Vector2(-s * 0.52, s * 0.48), col, 2.2, true)
		draw_arc(c, s * 0.68, -PI * 0.2, PI * 0.7, 16, col, 2.0, true)

	func _draw_pickup_icon(c: Vector2, s: float, col: Color) -> void:
		draw_circle(c + Vector2(0.0, s * 0.16), s * 0.38, Color(1.0, 0.74, 0.18, col.a * 0.85))
		draw_arc(c + Vector2(0.0, s * 0.16), s * 0.38, 0.0, TAU, 20, col, 2.0, true)
		draw_line(c + Vector2(0.0, -s * 0.72), c + Vector2(0.0, -s * 0.24), col, 2.2, true)
		draw_line(c + Vector2(-s * 0.24, -s * 0.48), c + Vector2(0.0, -s * 0.72), col, 2.2, true)
		draw_line(c + Vector2(s * 0.24, -s * 0.48), c + Vector2(0.0, -s * 0.72), col, 2.2, true)

	func _draw_talk_icon(c: Vector2, s: float, col: Color) -> void:
		draw_rect(Rect2(c.x - s * 0.65, c.y - s * 0.45, s * 1.30, s * 0.82), Color(col.r, col.g, col.b, 0.22), true)
		draw_rect(Rect2(c.x - s * 0.65, c.y - s * 0.45, s * 1.30, s * 0.82), col, false, 2.0)
