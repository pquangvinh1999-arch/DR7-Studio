class_name DisplayPolicy
extends RefCounted
## D1 / D2 / D4 Mobile Display & Safe-Area Policy (ADR-0001).
## - Base height = 1080 logic px with full horizontal expand (`expand` / `keep_height` on landscape phones).
## - Default `fractional` stretch; optional `Pixel Perfect (integer)` toggle with measured <1080p guard.

const PROFILES_JSON_PATH := "res://assets/maps/rocky_plateau/device-profiles.json"
const BASE_W := 1920
const BASE_H := 1080


static func load_device_profiles(path: String = PROFILES_JSON_PATH) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


static func find_profile(profiles_doc: Dictionary, profile_id: String) -> Dictionary:
	for p in profiles_doc.get("profiles", []):
		if p is Dictionary and str(p.get("id", "")) == profile_id:
			return p
	return {}


static func compute_profile_layout(win_w: int, win_h: int, pixel_perfect_requested: bool, safe_rect_px: Rect2i = Rect2i()) -> Dictionary:
	var safe_w := maxi(1, win_w)
	var safe_h := maxi(1, win_h)
	var safe_box := safe_rect_px if safe_rect_px.size.x > 0 and safe_rect_px.size.y > 0 else Rect2i(0, 0, safe_w, safe_h)

	# Empirical Godot 4.7 guard: on screens < 1080px tall (e.g. 720p), CONTENT_SCALE_STRETCH_INTEGER
	# clamps floor(720/1080) up to 1.0 and clips the 1080p viewport off-screen; keep fractional active.
	var below_1080p := safe_h < BASE_H
	var integer_applied := pixel_perfect_requested and not below_1080p

	var scale_f := float(safe_h) / float(BASE_H)
	if float(safe_w) / float(safe_h) < float(BASE_W) / float(BASE_H):
		scale_f = float(safe_w) / float(BASE_W)
	var scale_val := float(maxi(1, int(floor(scale_f)))) if integer_applied else scale_f

	var vis_w := maxf(float(BASE_W), float(safe_w) / maxf(0.01, scale_val))
	var vis_h := maxf(float(BASE_H), float(safe_h) / maxf(0.01, scale_val))
	if integer_applied:
		vis_w = maxf(float(BASE_W), float(safe_w) / maxf(1.0, scale_val))
		vis_h = maxf(float(BASE_H), float(safe_h) / maxf(1.0, scale_val))

	var left_inset_logic := float(safe_box.position.x) / maxf(0.01, scale_val)
	var top_inset_logic := float(safe_box.position.y) / maxf(0.01, scale_val)
	var right_inset_logic := float(maxi(0, safe_w - (safe_box.position.x + safe_box.size.x))) / maxf(0.01, scale_val)
	var bottom_inset_logic := float(maxi(0, safe_h - (safe_box.position.y + safe_box.size.y))) / maxf(0.01, scale_val)

	return {
		"window_size": [safe_w, safe_h],
		"pixel_perfect_requested": pixel_perfect_requested,
		"pixel_perfect_applied": integer_applied,
		"below_1080p_guard": below_1080p,
		"stretch_mode": "canvas_items",
		"stretch_aspect": "expand",
		"scale_mode": "integer" if integer_applied else "fractional",
		"effective_scale": scale_val,
		"visible_logic_size": [vis_w, vis_h],
		"safe_insets_logic": {
			"left": left_inset_logic,
			"top": top_inset_logic,
			"right": right_inset_logic,
			"bottom": bottom_inset_logic,
		},
	}


static func apply_to_root_window(root_win: Window, pixel_perfect_requested: bool, sim_win_size: Vector2i = Vector2i.ZERO, sim_safe_rect: Rect2i = Rect2i()) -> Dictionary:
	if root_win == null:
		return compute_profile_layout(BASE_W, BASE_H, pixel_perfect_requested, sim_safe_rect)
	var win_sz := sim_win_size if (sim_win_size.x > 0 and sim_win_size.y > 0) else root_win.size
	if win_sz.x <= 0 or win_sz.y <= 0:
		win_sz = Vector2i(BASE_W, BASE_H)
	var safe_box := sim_safe_rect
	if safe_box.size.x <= 0 or safe_box.size.y <= 0:
		safe_box = DisplayServer.get_display_safe_area()
	var info := compute_profile_layout(win_sz.x, win_sz.y, pixel_perfect_requested, safe_box)
	root_win.content_scale_size = Vector2i(BASE_W, BASE_H)
	root_win.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root_win.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
	root_win.content_scale_stretch = (
		Window.CONTENT_SCALE_STRETCH_INTEGER
		if bool(info.get("pixel_perfect_applied", false))
		else Window.CONTENT_SCALE_STRETCH_FRACTIONAL
	)
	return info
