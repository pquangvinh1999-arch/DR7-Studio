extends SceneTree

var total_checks: int = 0
var failed_checks: int = 0

func check(cond: bool, msg: String) -> void:
	total_checks += 1
	if cond:
		print("  [PASS] ", msg)
	else:
		failed_checks += 1
		printerr("  [FAIL] ", msg)

func _init() -> void:
	print("============================================================")
	print("Godot 4.7.2 CLI Verification — Skill Sphere of Destruction")
	print("============================================================")

	var bundles := [
		{
			"name": "Bundle 1: Registered Character + Skill (512x400)",
			"dir": "res://assets/sphere_of_destruction/godot_registered",
			"scene_2d": "res://assets/sphere_of_destruction/godot_registered/godot/sphere_of_destruction.tscn",
			"frames_2d": "res://assets/sphere_of_destruction/godot_registered/godot/sphere_of_destruction.tres",
			"scene_3d": "res://assets/sphere_of_destruction/godot_registered/godot-sprite3d/sphere_of_destruction.tscn",
			"export_json": "res://assets/sphere_of_destruction/godot_registered/engine-export.json",
			"expected_offset": Vector2(-148.0, -364.0),
			"expected_frame_size": Vector2(512.0, 400.0),
			"main_anim": &"sphere_of_destruction",
			"expected_frames": 9,
		},
		{
			"name": "Bundle 2: Standalone Sphere FX (384x386)",
			"dir": "res://assets/sphere_of_destruction/godot_sphere_fx",
			"scene_2d": "res://assets/sphere_of_destruction/godot_sphere_fx/godot/sphere_fx.tscn",
			"frames_2d": "res://assets/sphere_of_destruction/godot_sphere_fx/godot/sphere_fx.tres",
			"scene_3d": "res://assets/sphere_of_destruction/godot_sphere_fx/godot-sprite3d/sphere_fx.tscn",
			"export_json": "res://assets/sphere_of_destruction/godot_sphere_fx/engine-export.json",
			"expected_offset": Vector2(-240.0, -198.0),
			"expected_frame_size": Vector2(384.0, 386.0),
			"main_anim": &"sphere_charge_and_detonate",
			"expected_frames": 7,
		},
		{
			"name": "Bundle 3: Raw Keyed Canvas (439x386)",
			"dir": "res://assets/sphere_of_destruction/godot_raw_keyed",
			"scene_2d": "res://assets/sphere_of_destruction/godot_raw_keyed/godot/sphere_of_destruction_raw.tscn",
			"frames_2d": "res://assets/sphere_of_destruction/godot_raw_keyed/godot/sphere_of_destruction_raw.tres",
			"scene_3d": "res://assets/sphere_of_destruction/godot_raw_keyed/godot-sprite3d/sphere_of_destruction_raw.tscn",
			"export_json": "res://assets/sphere_of_destruction/godot_raw_keyed/engine-export.json",
			"expected_offset": Vector2(-218.0, -375.0),
			"expected_frame_size": Vector2(439.0, 386.0),
			"main_anim": &"sphere_of_destruction",
			"expected_frames": 9,
		},
	]

	for b in bundles:
		print("\n--- Testing ", b["name"], " ---")
		_verify_bundle(b)

	print("\n============================================================")
	print("SUMMARY: %d / %d checks passed (%d failed)" % [total_checks - failed_checks, total_checks, failed_checks])
	print("============================================================")
	quit(1 if failed_checks > 0 else 0)

func _verify_bundle(b: Dictionary) -> void:
	# 1. Load SpriteFrames (.tres)
	var sf: SpriteFrames = load(b["frames_2d"])
	check(sf != null, "Loaded SpriteFrames: " + b["frames_2d"])
	if sf == null:
		return

	var anim_names := sf.get_animation_names()
	check(anim_names.size() >= 3, "SpriteFrames has %d animations: %s" % [anim_names.size(), str(anim_names)])

	var main_anim: StringName = b["main_anim"]
	check(sf.has_animation(main_anim), "Has main animation '%s'" % String(main_anim))
	if sf.has_animation(main_anim):
		var fcount := sf.get_frame_count(main_anim)
		check(fcount == b["expected_frames"], "Animation '%s' has %d frames (expected %d)" % [String(main_anim), fcount, b["expected_frames"]])
		var fps := sf.get_animation_speed(main_anim)
		check(is_equal_approx(fps, 60.0), "Animation '%s' speed is %.1f Hz (60 Hz tick)" % [String(main_anim), fps])

		# Verify each frame's AtlasTexture & non-empty pixel data
		var all_tex_ok := true
		var all_alpha_clean := true
		for i in range(fcount):
			var tex: Texture2D = sf.get_frame_texture(main_anim, i)
			if tex == null or tex.get_size() != b["expected_frame_size"]:
				all_tex_ok = false
				printerr("    Frame %d invalid size: %s" % [i, str(tex.get_size() if tex else Vector2.ZERO)])
			else:
				var img: Image = tex.get_image()
				if img == null or img.is_empty():
					all_alpha_clean = false
				else:
					var w := img.get_width()
					var h := img.get_height()
					# Top-left and bottom-left corners must be 100% transparent (no border/backdrop leak)
					if img.get_pixel(0, 0).a > 0.01 or img.get_pixel(0, h - 1).a > 0.01:
						all_alpha_clean = false
						printerr("    Frame %d has non-zero corner alpha!" % i)
		check(all_tex_ok, "All %d frames have valid AtlasTexture of size %s" % [fcount, str(b["expected_frame_size"])])
		check(all_alpha_clean, "All %d frames pass Godot Image pixel alpha check (transparent corners, valid buffer)" % fcount)

	# 2. Instantiate 2D Scene (.tscn)
	var packed_2d: PackedScene = load(b["scene_2d"])
	check(packed_2d != null, "Loaded 2D PackedScene: " + b["scene_2d"])
	if packed_2d != null:
		var node_2d := packed_2d.instantiate() as AnimatedSprite2D
		check(node_2d != null, "Instantiated AnimatedSprite2D node: " + node_2d.name)
		if node_2d != null:
			check(node_2d.texture_filter == CanvasItem.TEXTURE_FILTER_NEAREST, "AnimatedSprite2D texture_filter == TEXTURE_FILTER_NEAREST (1)")
			check(node_2d.centered == false, "AnimatedSprite2D centered == false (top-left + anchor offset)")
			check(node_2d.offset.is_equal_approx(b["expected_offset"]), "AnimatedSprite2D offset == %s (expected %s)" % [str(node_2d.offset), str(b["expected_offset"])])
			root.add_child(node_2d)
			node_2d.play(main_anim)
			check(node_2d.is_playing() and node_2d.animation == main_anim, "AnimatedSprite2D.play('%s') active in SceneTree" % String(main_anim))
			node_2d.queue_free()

	# 3. Instantiate 3D Scene (.tscn)
	var packed_3d: PackedScene = load(b["scene_3d"])
	check(packed_3d != null, "Loaded 3D PackedScene: " + b["scene_3d"])
	if packed_3d != null:
		var node_3d := packed_3d.instantiate() as AnimatedSprite3D
		check(node_3d != null, "Instantiated AnimatedSprite3D node: " + node_3d.name)
		if node_3d != null:
			check(node_3d.sprite_frames != null, "AnimatedSprite3D has valid SpriteFrames")
			root.add_child(node_3d)
			node_3d.play(main_anim)
			check(node_3d.is_playing(), "AnimatedSprite3D.play('%s') active in SceneTree" % String(main_anim))
			node_3d.queue_free()

	# 4. Verify engine-export.json gameplay event metadata (hit / impact) & simulate frame progression
	var f := FileAccess.open(b["export_json"], FileAccess.READ)
	check(f != null, "Opened engine-export.json: " + b["export_json"])
	if f != null:
		var parsed = JSON.parse_string(f.get_as_text())
		check(typeof(parsed) == TYPE_DICTIONARY and parsed.has("clips"), "Parsed engine-export.json clips array")
		if typeof(parsed) == TYPE_DICTIONARY and parsed.has("clips"):
			var clips_dict: Dictionary = parsed["clips"]
			var main_clip_meta: Dictionary = clips_dict.get(String(main_anim), {})
			check(not main_clip_meta.is_empty(), "Found clip metadata for '%s' in engine-export.json" % String(main_anim))
			if not main_clip_meta.is_empty():
				var events: Array = main_clip_meta.get("events_ms", [])
				var event_names: Array[String] = []
				for ev in events:
					event_names.append("%s@f%d(%dms)" % [ev.get("name", ""), int(ev.get("position", 0)), int(ev.get("at_ms", 0))])
				check(events.size() >= 3, "Verified gameplay events_ms for '%s': %s" % [String(main_anim), ", ".join(event_names)])

				# 5. Simulate SkillAnimator2D stepping through all frames and firing signals
				var anim_ctrl := preload("res://tests/SkillAnimator2D.gd").new()
				var inst_2d := packed_2d.instantiate() as AnimatedSprite2D
				anim_ctrl.sprite = inst_2d
				anim_ctrl.engine_export_json = b["export_json"]
				anim_ctrl.add_child(inst_2d)
				root.add_child(anim_ctrl)
				var fired_signals: Array[String] = []
				anim_ctrl.skill_event.connect(func(ev_name: String, f_idx: int, _ms: int, _payload: Dictionary):
					fired_signals.append("%s@f%d" % [ev_name, f_idx])
				)
				anim_ctrl.play_skill(main_anim)
				var fcount := sf.get_frame_count(main_anim)
				for step_f in range(1, fcount):
					inst_2d.frame = step_f
				check(fired_signals.size() == events.size(), "SkillAnimator2D emitted all %d runtime signals: %s" % [fired_signals.size(), ", ".join(fired_signals)])
				anim_ctrl.queue_free()

