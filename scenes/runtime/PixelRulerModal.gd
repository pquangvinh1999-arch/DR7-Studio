class_name PixelRulerModal
extends Control
## 1:1 World-PX Ruler Modal for ArenaSandbox (synced identically across Godot Web, Desktop, and Android APK).

signal pick_mode_changed(enabled: bool)
signal ruler_grid_toggled(enabled: bool)
signal measure_pair_requested()
signal set_point_a_player_requested()
signal snap_point_b_requested(world_x: float)
signal clear_points_requested()
signal modal_closed()

var panel: PanelContainer = null
var pick_button: Button = null
var grid_button: Button = null
var readout_label: Label = null
var status_label: Label = null
var _pick_enabled: bool = false
var _grid_enabled: bool = false
var _last_copy_text: String = ""


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_ui()


func _build_ui() -> void:
	panel = PanelContainer.new()
	panel.name = "RulerModalPanel"
	panel.anchor_left = 0.5
	panel.anchor_right = 0.5
	panel.anchor_top = 0.0
	panel.anchor_bottom = 0.0
	panel.offset_left = -290.0
	panel.offset_right = 290.0
	panel.offset_top = 64.0
	panel.custom_minimum_size = Vector2(580.0, 0.0)
	panel.mouse_filter = Control.MOUSE_FILTER_STOP

	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.05, 0.09, 0.16, 0.92)
	style.border_color = Color(0.22, 0.74, 0.97, 0.85)
	style.set_border_width_all(2)
	style.set_corner_radius_all(10)
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 10
	style.content_margin_bottom = 12
	panel.add_theme_stylebox_override("panel", style)
	add_child(panel)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 8)
	panel.add_child(vbox)

	var header := HBoxContainer.new()
	var title := Label.new()
	title.text = "📏 Thước Đo PX (1:1 World PX ⇄ APK)"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.add_theme_color_override("font_color", Color(0.38, 0.86, 1.0))
	header.add_child(title)

	var close_btn := Button.new()
	close_btn.text = "✕ Đóng"
	close_btn.pressed.connect(func() -> void:
		modal_closed.emit()
	)
	header.add_child(close_btn)
	vbox.add_child(header)

	var row1 := HBoxContainer.new()
	row1.add_theme_constant_override("separation", 6)
	pick_button = Button.new()
	pick_button.text = "🎯 Chạm/Kéo Đo 2 Điểm: TẮT"
	pick_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pick_button.pressed.connect(func() -> void:
		set_pick_mode(not _pick_enabled)
		pick_mode_changed.emit(_pick_enabled)
	)
	row1.add_child(pick_button)

	grid_button = Button.new()
	grid_button.text = "📐 Lưới PX: TẮT"
	grid_button.pressed.connect(func() -> void:
		set_grid_enabled(not _grid_enabled)
		ruler_grid_toggled.emit(_grid_enabled)
	)
	row1.add_child(grid_button)

	var clr_btn := Button.new()
	clr_btn.text = "🗑️ Xóa A/B"
	clr_btn.pressed.connect(func() -> void:
		clear_points_requested.emit()
	)
	row1.add_child(clr_btn)
	vbox.add_child(row1)

	var row2 := HBoxContainer.new()
	row2.add_theme_constant_override("separation", 6)
	var pair_btn := Button.new()
	pair_btn.text = "⚔️ Đo Player ⇄ Quái"
	pair_btn.pressed.connect(func() -> void: measure_pair_requested.emit())
	row2.add_child(pair_btn)

	var set_a_btn := Button.new()
	set_a_btn.text = "📍 A = Player"
	set_a_btn.pressed.connect(func() -> void: set_point_a_player_requested.emit())
	row2.add_child(set_a_btn)

	var snap1_btn := Button.new()
	snap1_btn.text = "🧱 B = Bậc 1 (2850)"
	snap1_btn.pressed.connect(func() -> void: snap_point_b_requested.emit(2850.0))
	row2.add_child(snap1_btn)

	var snap2_btn := Button.new()
	snap2_btn.text = "🧱 B = Bậc 2 (3695)"
	snap2_btn.pressed.connect(func() -> void: snap_point_b_requested.emit(3695.0))
	row2.add_child(snap2_btn)
	vbox.add_child(row2)

	readout_label = Label.new()
	readout_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	readout_label.add_theme_color_override("font_color", Color(0.93, 0.96, 1.0))
	readout_label.text = "Chạm 'Đo Player ⇄ Quái' hoặc bật 'Chạm/Kéo Đo 2 Điểm' rồi chạm/kéo trực tiếp trên map."
	vbox.add_child(readout_label)

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 8)
	var copy_btn := Button.new()
	copy_btn.text = "📋 Copy Thông Số [DR7-RULER]"
	copy_btn.pressed.connect(_on_copy_pressed)
	footer.add_child(copy_btn)

	status_label = Label.new()
	status_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	status_label.add_theme_color_override("font_color", Color(0.55, 0.95, 0.68))
	status_label.text = ""
	footer.add_child(status_label)
	vbox.add_child(footer)


func set_pick_mode(enabled: bool) -> void:
	_pick_enabled = enabled
	if pick_button != null:
		pick_button.text = "🎯 Chạm/Kéo Đo 2 Điểm: BẬT" if enabled else "🎯 Chạm/Kéo Đo 2 Điểm: TẮT"


func set_grid_enabled(enabled: bool) -> void:
	_grid_enabled = enabled
	if grid_button != null:
		grid_button.text = "📐 Lưới PX: BẬT" if enabled else "📐 Lưới PX: TẮT"


func apply_safe_area(insets: Dictionary) -> void:
	if panel == null:
		return
	var ins_t := float(insets.get("top", 0.0))
	panel.offset_top = 64.0 + ins_t


func is_screen_point_inside(screen_pos: Vector2) -> bool:
	if not visible or panel == null or not panel.visible:
		return false
	return panel.get_global_rect().has_point(screen_pos)


func update_metrics(metrics: Dictionary) -> void:
	if readout_label == null:
		return
	var p_pos: Array = metrics.get("player_pos", [0.0, 0.0])
	var e_pos: Array = metrics.get("enemy_pos", [0.0, 0.0])
	var p_box: Array = metrics.get("player_size_px", [0.0, 0.0])
	var e_box: Array = metrics.get("enemy_size_px", [0.0, 0.0])
	var center_dx := float(metrics.get("player_enemy_center_dx", 0.0))
	var edge_gap := float(metrics.get("player_enemy_edge_gap", 0.0))
	var pair_dy := float(metrics.get("player_enemy_dy", 0.0))
	var eff_sc := float(metrics.get("effective_scale", 1.0))
	var cam_z := float(metrics.get("camera_zoom", 1.0))
	var vis: Array = metrics.get("visible_logic_size", [1920.0, 1080.0])
	var cam_p: Array = metrics.get("camera_pos", [960.0, 540.0])
	var screen_factor := eff_sc / maxf(0.01, cam_z)

	var lines := PackedStringArray()
	if bool(metrics.get("has_a", false)) and bool(metrics.get("has_b", false)):
		var pa: Array = metrics.get("point_a", [0.0, 0.0])
		var pb: Array = metrics.get("point_b", [0.0, 0.0])
		var dx := float(metrics.get("dx_world_px", 0.0))
		var dy := float(metrics.get("dy_world_px", 0.0))
		var dist := float(metrics.get("dist_world_px", 0.0))
		lines.append("• Điểm A = (%.1f, %.1f)  →  Điểm B = (%.1f, %.1f)" % [float(pa[0]), float(pa[1]), float(pb[0]), float(pb[1])])
		lines.append("• World PX (1:1 chung & APK): ΔX = %.1f px | ΔY = %.1f px | Thẳng = %.1f px" % [dx, dy, dist])
		lines.append("• Device PX (màn hiện tại ×%.3f): ΔX = %.0f px | ΔY = %.0f px" % [screen_factor, dx * screen_factor, dy * screen_factor])
	elif bool(metrics.get("has_a", false)):
		var pa2: Array = metrics.get("point_a", [0.0, 0.0])
		lines.append("• Điểm A = (%.1f, %.1f) — chạm/kéo thêm điểm B trên map" % [float(pa2[0]), float(pa2[1])])
	else:
		lines.append("• Thước 2 điểm: chưa chọn A/B (bật Chạm/Kéo hoặc bấm Đo Player ⇄ Quái)")

	lines.append("• Player: (%.1f, %.1f) [%dx%dpx] | Quái: (%.1f, %.1f) [%dx%dpx]" % [
		float(p_pos[0]), float(p_pos[1]), int(round(float(p_box[0]))), int(round(float(p_box[1]))),
		float(e_pos[0]), float(e_pos[1]), int(round(float(e_box[0]))), int(round(float(e_box[1]))),
	])
	lines.append("• Player ⇄ Quái: Tâm↔Tâm ΔX = %.1f px | Mép↔Mép = %.1f px | ΔY = %.1f px" % [center_dx, edge_gap, pair_dy])
	lines.append("• Đồng bộ 1:1 (Godot ⇄ APK): vis=%.0fx%.0f | cam=(%.0f,%.0f) | zoom=%.2f | scale=%.3f" % [
		float(vis[0]), float(vis[1]), float(cam_p[0]), float(cam_p[1]), cam_z, eff_sc
	])
	readout_label.text = "\n".join(lines)

	var a_txt := "(%.1f,%.1f)" % [float(metrics.get("point_a", [0.0, 0.0])[0]), float(metrics.get("point_a", [0.0, 0.0])[1])] if bool(metrics.get("has_a", false)) else "none"
	var b_txt := "(%.1f,%.1f)" % [float(metrics.get("point_b", [0.0, 0.0])[0]), float(metrics.get("point_b", [0.0, 0.0])[1])] if bool(metrics.get("has_b", false)) else "none"
	_last_copy_text = "[DR7-RULER] A=%s B=%s dX=%.1fpx dY=%.1fpx dist=%.1fpx | Player=(%.1f,%.1f) Enemy=(%.1f,%.1f) center_dx=%.1fpx edge_gap=%.1fpx | vis=%.0fx%.0f cam=(%.0f,%.0f) zoom=%.2f scale=%.3f" % [
		a_txt, b_txt,
		float(metrics.get("dx_world_px", 0.0)), float(metrics.get("dy_world_px", 0.0)), float(metrics.get("dist_world_px", 0.0)),
		float(p_pos[0]), float(p_pos[1]), float(e_pos[0]), float(e_pos[1]),
		center_dx, edge_gap, float(vis[0]), float(vis[1]), float(cam_p[0]), float(cam_p[1]), cam_z, eff_sc
	]


func _on_copy_pressed() -> void:
	if _last_copy_text.is_empty():
		return
	DisplayServer.clipboard_set(_last_copy_text)
	if status_label != null:
		status_label.text = "✅ Đã copy thông số!"
