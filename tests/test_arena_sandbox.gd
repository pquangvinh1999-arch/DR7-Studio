extends SceneTree

const UtilityAIScript := preload("res://scenes/UtilityAIController.gd")
const OverheadBarsDrawScript := preload("res://scenes/runtime/OverheadBarsDraw.gd")


func fail(msg: String) -> void:
	printerr("[FAIL] " + msg)
	quit(1)


func _init() -> void:
	call_deferred("run_test")


func run_test() -> void:
	if str(ProjectSettings.get_setting("application/run/main_scene", "")) != "res://scenes/ArenaSandbox.tscn":
		fail("project.godot main_scene must be res://scenes/ArenaSandbox.tscn")
		return
	if int(ProjectSettings.get_setting("display/window/size/viewport_width", 0)) != 1920:
		fail("project.godot viewport_width must be 1920")
		return
	if int(ProjectSettings.get_setting("display/window/size/viewport_height", 0)) != 1080:
		fail("project.godot viewport_height must be 1080")
		return
	if str(ProjectSettings.get_setting("display/window/stretch/mode", "")) != "canvas_items":
		fail("project.godot stretch/mode must be canvas_items")
		return
	if str(ProjectSettings.get_setting("display/window/stretch/aspect", "")) != "expand":
		fail("project.godot stretch/aspect must be expand (Owner D1 full-width phones)")
		return
	if str(ProjectSettings.get_setting("display/window/stretch/scale_mode", "")) != "fractional":
		fail("project.godot stretch/scale_mode must default to fractional (Owner D2)")
		return
	if str(ProjectSettings.get_setting("rendering/renderer/rendering_method", "")) != "gl_compatibility":
		fail("project.godot rendering_method must be gl_compatibility (Owner D3)")
		return
	if int(ProjectSettings.get_setting("display/window/handheld/orientation", -1)) != 0:
		fail("project.godot handheld/orientation must be 0 (Landscape)")
		return
	if int(ProjectSettings.get_setting("rendering/textures/canvas_textures/default_texture_filter", -1)) != 0:
		fail("project.godot default_texture_filter must be 0 (Nearest)")
		return

	var loaded_scene: Resource = ResourceLoader.load("res://scenes/ArenaSandbox.tscn")
	if not (loaded_scene is PackedScene):
		fail("Unable to load res://scenes/ArenaSandbox.tscn")
		return
	var packed := loaded_scene as PackedScene

	var arena := packed.instantiate()
	if arena == null or not arena.has_method("_get_walk_speed_px_per_s"):
		fail("ArenaSandbox failed to load script cleanly")
		return
	var stationary_entry := {"render_contract": {"locomotion": {"kind": "stationary", "speed_px_per_second": 123.0}}}
	if arena._get_walk_speed_px_per_s(stationary_entry) != 0.0:
		fail("Stationary entry must never fall back to walk speed")
		return
	var stationary_ai := UtilityAIScript.new()
	var stationary_decision := stationary_ai.evaluate({"is_stationary": true, "facing_left": true, "target_x": 9000.0})
	if stationary_decision["intent"] != "idle" or stationary_decision["move_dir"] != 0 or not stationary_decision["desired_face_left"]:
		fail("Stationary AI must idle and preserve facing outside its zone")
		return
	if not arena.has_method("get_stage_metrics"):
		fail("ArenaSandbox script failed to attach cleanly")
		return
	root.add_child(arena)
	await process_frame

	if arena.viewport_width != 1920 or arena.viewport_height != 1080:
		fail("ArenaSandbox viewport mismatch: %sx%s" % [str(arena.viewport_width), str(arena.viewport_height)])
		return
	if arena.show_grid_overlay:
		fail("ArenaSandbox show_grid_overlay must default to false (no yellow/blue boundary lines)")
		return
	var expected_trex_half_w := 187.0 * 1.75 * 0.5
	if arena.ground_y != 840.0 or absf(arena.walkable_min_x - (-240.0 + expected_trex_half_w)) > 1.0 or absf(arena.walkable_max_x - (6360.0 - expected_trex_half_w)) > 1.0:
		fail("ArenaSandbox gameplay bounds mismatch: ground=%s bounds=[%s,%s]" % [str(arena.ground_y), str(arena.walkable_min_x), str(arena.walkable_max_x)])
		return
	if absf(arena.char_scale - 1.75) > 0.001:
		fail("ArenaSandbox default scale must match t_rex 1.75, got " + str(arena.char_scale))
		return

	var bg_sprite := arena.get_node_or_null("BackgroundLayer/BackgroundSprite") as Sprite2D
	if bg_sprite == null or bg_sprite.texture == null:
		fail("Missing BackgroundSprite texture on ArenaSandbox")
		return
	var rendered_bg_size := bg_sprite.texture.get_size() * bg_sprite.scale
	if absf(rendered_bg_size.x - 6600.0) > 0.5 or absf(rendered_bg_size.y - 1350.0) > 0.5:
		fail("Extended BackgroundSprite size mismatch: " + str(rendered_bg_size))
		return
	var terrain_body := arena.get_node_or_null("TerrainLayer/GroundFloorCollider") as StaticBody2D
	if terrain_body == null or terrain_body.get_child_count() != 5 or arena._ground_tilemap == null or arena._ground_tilemap.visible:
		fail("Review terrain must use five solid step colliders and no foreground tile overlay")
		return
	var foreground := arena.get_node_or_null("ReviewForegroundTrees") as Node2D
	var map_layer := arena.get_node_or_null("BackgroundLayer") as Node2D
	if foreground == null or foreground.get_child_count() != 3 or map_layer == null or not (map_layer.z_index < foreground.z_index and foreground.z_index < 0):
		fail("Review extension needs exactly three trees between map and fighters")
		return
	var expected_tree_min_h := [900.0, 1060.0, 1080.0]
	var expected_tree_bottom_y := [828.0, 888.0, 954.0]
	for tree_i in range(3):
		var tree_sprite := foreground.get_child(tree_i) as Sprite2D
		if tree_sprite == null or tree_sprite.texture.get_size().y < float(expected_tree_min_h[tree_i]):
			fail("Tree %d must include full planted roots and +30%% canopy (h >= %s)" % [tree_i, str(expected_tree_min_h[tree_i])])
			return
		var visual_bottom := tree_sprite.position.y + tree_sprite.texture.get_size().y * tree_sprite.scale.y
		if absf(visual_bottom - float(expected_tree_bottom_y[tree_i])) > 14.0:
			fail("Tree %d roots must plant into the rear ground rim near y=%s, got %s" % [tree_i, str(expected_tree_bottom_y[tree_i]), str(visual_bottom)])
			return
		if tree_i == 0 and (tree_sprite.position.x + 264.51 * tree_sprite.scale.x) >= arena.STEP_THREE_X:
			fail("First tree must stand on the left upper plateau before Step 3 cliff cut, trunk_x=%s" % str(tree_sprite.position.x + 264.51 * tree_sprite.scale.x))
			return
		var tree_left := tree_sprite.position.x
		var tree_right := tree_sprite.position.x + tree_sprite.texture.get_size().x * tree_sprite.scale.x
		if tree_left < arena.MAP_LEFT_X or tree_right > arena.MAP_RIGHT_X:
			fail("Tree %d canopy must fit inside map world bounds [%s, %s]: [%s, %s]" % [tree_i, str(arena.MAP_LEFT_X), str(arena.MAP_RIGHT_X), str(tree_left), str(tree_right)])
			return

	# Verify DisplayPolicy D1/D2/D4 across Redmi K70E (2712x1220), 720p (<1080p guard), and 16:9 FHD
	var k70e_frac: Dictionary = arena.apply_device_profile("redmi_k70e")
	if absf(float(k70e_frac.get("visible_logic_size", [0.0, 0.0])[0]) - 2400.7869) > 1.5:
		fail("Redmi K70E horizontal expand width mismatch: " + str(k70e_frac))
		return
	var k70e_visible_w := float(k70e_frac["visible_logic_size"][0])
	var bg_w := bg_sprite.texture.get_size().x * bg_sprite.scale.x
	var view_left := 960.0 - k70e_visible_w * 0.5
	var view_right := 960.0 + k70e_visible_w * 0.5
	if absf(arena.walkable_min_x - (-240.0 + expected_trex_half_w)) > 1.0 or absf(arena.walkable_max_x - (6360.0 - expected_trex_half_w)) > 1.0:
		fail("K70E T-rex world bounds mismatch: bounds=[%s,%s]" % [str(arena.walkable_min_x), str(arena.walkable_max_x)])
		return
	var camera := arena.get_node_or_null("ArenaCamera") as Camera2D
	if camera == null or arena.player_node == null:
		fail("Extended map requires player and Camera2D")
		return
	var original_player_x: float = float(arena.player_node.position.x)
	arena.player_node.position.x = 2800.0
	arena._update_follow_camera()
	if absf(camera.position.x - 2800.0) > 1.0 or absf(arena._ground_y_at(2800.0) - 840.0) > 0.1:
		fail("Camera must follow player through the flat map join")
		return
	if absf(arena._ground_y_at(3200.0) - 890.0) > 0.1:
		fail("Middle plateau (platform 2) must use walkable floor y=890")
		return
	if absf(arena._ground_y_at(4200.0) - 945.0) > 0.1:
		fail("Existing third plateau must retain shared world ground height y=945")
		return
	if absf(arena._ground_y_at(5200.0) - 975.0) > 0.1 or absf(arena._ground_y_at(6000.0) - 1030.0) > 0.1:
		fail("New descending plateaus must use walkable floor heights y=975 and y=1030")
		return
	if arena._can_cross_terrain_step(4741.0, 4739.0, 975.0) or not arena._can_cross_terrain_step(4741.0, 4739.0, 940.0):
		fail("Third step must block uphill walking and allow a high jump")
		return
	if not arena.terrain_blocks_segment(Vector2(5567.0, 1010.0), Vector2(5553.0, 1010.0)):
		fail("Skill projectile must hit the fourth step face")
		return
	for edge_case in [[4740.0, 945.0, 975.0], [5560.0, 975.0, 1030.0]]:
		var step_edge := float(edge_case[0])
		var upper_y := float(edge_case[1])
		var lower_y := float(edge_case[2])
		arena.player_node.position = Vector2(step_edge - 1.0, upper_y)
		arena.player_vy = 0.0
		arena._move_player_horizontal(2.0)
		var fall_result: Dictionary = arena.step_player_vertical_physics(1.0 / 60.0, false, false)
		if arena.player_node.position.x <= step_edge or float(fall_result["y"]) <= upper_y or float(fall_result["support_y"]) != lower_y:
			fail("Actor must fall on first tick beyond painted step edge %s: x=%s y=%s" % [str(step_edge), str(arena.player_node.position.x), str(fall_result["y"])])
			return
	if arena._can_cross_terrain_step(3696.0, 3694.0, 945.0) or not arena._can_cross_terrain_step(3696.0, 3694.0, 885.0):
		fail("Walking uphill must be blocked until the player jumps above the upper surface")
		return
	if not arena._can_cross_terrain_step(3694.0, 3696.0, 890.0):
		fail("Walking downhill must allow an automatic drop")
		return
	if not arena.terrain_blocks_segment(Vector2(3708.0, 940.0), Vector2(3682.0, 940.0)):
		fail("A skill projectile must hit the vertical step face")
		return
	arena.player_node.position = Vector2(2849.0, 840.0)
	arena.player_vy = 0.0
	arena._move_player_horizontal(3.0)
	for _fall_tick in range(30):
		arena.step_player_vertical_physics(1.0 / 60.0, false, false)
	if absf(arena.player_node.position.y - 890.0) > 1.0:
		fail("Walking off the first step must fall to the lower floor y=890")
		return
	arena._move_player_horizontal(-3.0)
	if arena.player_node.position.x < 2876.0:
		fail("Lower floor must block walking uphill before penetrating cliff base")
		return
	arena.step_player_vertical_physics(1.0 / 60.0, true, false)
	for _jump_tick in range(8):
		arena.step_player_vertical_physics(1.0 / 60.0, false, false)
	arena._move_player_horizontal(-40.0)
	if arena.player_node.position.x >= 2850.0:
		fail("A high enough jump must allow crossing back onto the upper floor")
		return
	# Verify Drum walking left against Step 4 & Step 3 painted cliff walls stops BEFORE entering the rock cut, and can still walk-jump up Step 4.
	arena.select_character("drum")
	await process_frame
	arena.player_node.position = Vector2(5720.0, 1030.0)
	arena.player_vy = 0.0
	for _wl in range(90):
		arena.step_player_movement(1.0 / 60.0, -1, 0, false, false, false, Vector2.ZERO)
	if arena.player_node.position.x < 5620.0:
		fail("Drum walking left against Step 4 cliff wall must stop cleanly outside cliff cut (>=5620), got x=%s" % str(arena.player_node.position.x))
		return
	for _wj in range(42):
		arena.step_player_movement(1.0 / 60.0, -1, 0, _wj == 0, false, false, Vector2.ZERO)
	if arena.player_node.position.x >= 5560.0 or arena.player_node.position.y > 980.0:
		fail("Drum must still be able to jump from Step 4 cliff stop onto upper floor, got pos=%s" % str(arena.player_node.position))
		return
	arena.player_node.position = Vector2(4910.0, 975.0)
	arena.player_vy = 0.0
	for _wl3 in range(90):
		arena.step_player_movement(1.0 / 60.0, -1, 0, false, false, false, Vector2.ZERO)
	if arena.player_node.position.x < 4815.0:
		fail("Drum walking left against Step 3 cliff wall must stop cleanly outside cliff cut (>=4815), got x=%s" % str(arena.player_node.position.x))
		return
	arena.select_character("t_rex")
	await process_frame
	arena.player_vy = 0.0
	arena.player_node.position.x = original_player_x
	arena._update_follow_camera()
	arena.player_node.position = Vector2(4200.0, 945.0)
	arena._update_follow_camera()
	arena._on_summon_button_pressed()
	if not arena.shenron_summon.active or absf(arena.shenron_summon.global_position.x + 960.0 - camera.position.x) > 1.0 or absf(arena.shenron_summon.global_position.y - 105.0) > 1.0:
		fail("Shenron ritual must center on the current camera and local ground")
		return
	arena.shenron_summon.dismiss()
	arena.player_node.position = Vector2(original_player_x, 840.0)
	arena._update_follow_camera()
	if bg_sprite.position.x > view_left + 1.0 or bg_sprite.position.x + bg_w < 960.0 + k70e_visible_w * 0.5 - 1.0:
		fail("K70E original background fails to cover the full width")
		return
	if arena._bg_left_ext != null and arena._bg_left_ext.visible or arena._bg_right_ext != null and arena._bg_right_ext.visible:
		fail("K70E must show the original image without wing inserts")
		return
	if absf(bg_sprite.scale.x * bg_sprite.texture.get_size().x / 6600.0 - bg_sprite.scale.y * bg_sprite.texture.get_size().y / 1350.0) > 0.001:
		fail("Extended background distorted the map aspect")
		return
	# Verify camera framing + zero uncovered strips + pan across ALL device profiles (including iPad & tall/wide screens)
	var bg_h := bg_sprite.texture.get_size().y * bg_sprite.scale.y
	var profiles_doc: Dictionary = load("res://scenes/runtime/DisplayPolicy.gd").load_device_profiles()
	for prof in profiles_doc.get("profiles", []):
		if not (prof is Dictionary):
			continue
		var pid_prof := str(prof.get("id", ""))
		for pp_mode in [false, true]:
			arena.pixel_perfect_enabled = pp_mode
			var prof_layout: Dictionary = arena.apply_device_profile(pid_prof)
			var vis_arr: Array = prof_layout.get("visible_logic_size", [1920.0, 1080.0])
			var eff_vis := Vector2(float(vis_arr[0]), float(vis_arr[1])) / camera.zoom
			if absf(camera.zoom.x - camera.zoom.y) > 0.0001:
				fail("Camera zoom must remain uniform on %s (pp=%s): %s" % [pid_prof, str(pp_mode), str(camera.zoom)])
				return
			for test_px in [-120.0, 2160.0, 4440.0]:
				arena.player_node.position = Vector2(test_px, arena._ground_y_at(test_px))
				arena._update_follow_camera()
				var c_left := camera.position.x - eff_vis.x * 0.5
				var c_right := camera.position.x + eff_vis.x * 0.5
				var c_top := camera.position.y - eff_vis.y * 0.5
				var c_bot := camera.position.y + eff_vis.y * 0.5
				if bg_sprite.position.x > c_left + 0.5 or bg_sprite.position.x + bg_w < c_right - 0.5 or bg_sprite.position.y > c_top + 0.5 or bg_sprite.position.y + bg_h < c_bot - 0.5:
					fail("Device %s (pp=%s) uncovered area at px=%s: cam=[%s..%s, %s..%s] bg=[%s..%s, %s..%s]" % [pid_prof, str(pp_mode), str(test_px), str(c_left), str(c_right), str(c_top), str(c_bot), str(bg_sprite.position.x), str(bg_sprite.position.x + bg_w), str(bg_sprite.position.y), str(bg_sprite.position.y + bg_h)])
					return
	# Also test giant/tall hypothetical viewport (e.g. 2732x2048 iPad Pro & 3840x2160 4K)
	for extra_sz in [Vector2i(2732, 2048), Vector2i(3840, 2160), Vector2i(3440, 1440)]:
		var ex_layout: Dictionary = arena.set_pixel_perfect_enabled(false, extra_sz)
		var ex_vis := Vector2(float(ex_layout["visible_logic_size"][0]), float(ex_layout["visible_logic_size"][1])) / camera.zoom
		arena.player_node.position = Vector2(3300.0, arena._ground_y_at(3300.0))
		arena._update_follow_camera()
		var ex_top := camera.position.y - ex_vis.y * 0.5
		var ex_bot := camera.position.y + ex_vis.y * 0.5
		if bg_sprite.position.y > ex_top + 0.5 or bg_sprite.position.y + bg_h < ex_bot - 0.5:
			fail("Large viewport %s left uncovered vertical area: top=%s bot=%s" % [str(extra_sz), str(ex_top), str(ex_bot)])
			return
	arena.pixel_perfect_enabled = false
	arena.apply_device_profile("ipad_10th")
	if arena._ground_tilemap.get_cell_source_id(Vector2i(0, 11)) != 0:
		fail("iPad ground tiles do not reach the bottom of the expanded view")
		return
	var k70e_int: Dictionary = arena.set_pixel_perfect_enabled(true, Vector2i(2712, 1220), Rect2i(96, 0, 2568, 1184))
	if not bool(k70e_int.get("pixel_perfect_applied", false)) or absf(float(k70e_int.get("effective_scale", 0.0)) - 1.0) > 0.001:
		fail("Redmi K70E Pixel Perfect toggle must clamp scale to 1.0: " + str(k70e_int))
		return
	var hd720_guard: Dictionary = arena.set_pixel_perfect_enabled(true, Vector2i(1600, 720), Rect2i(52, 0, 1516, 696))
	if bool(hd720_guard.get("pixel_perfect_applied", true)) or not bool(hd720_guard.get("below_1080p_guard", false)):
		fail("720p (<1080px height) must guard against integer clipping and retain fractional: " + str(hd720_guard))
		return
	arena.set_pixel_perfect_enabled(false, Vector2i(1920, 1080))

	var stage_metrics_check: Dictionary = arena.get_stage_metrics()
	if str(stage_metrics_check.get("stretch_aspect", "")) != "expand" or str(stage_metrics_check.get("renderer", "")) != "gl_compatibility":
		fail("get_stage_metrics() missing D1/D3 display telemetry: " + str(stage_metrics_check))
		return

	if arena.roster_characters.size() != 11:
		fail("Expected 11 finalized characters including Floating Camera, got " + str(arena.roster_characters.size()))
		return

	for entry in arena.roster_characters:
		var cid := str(entry.get("character_id", ""))
		if not arena.select_character(cid):
			fail("ArenaSandbox failed to instantiate character: " + cid)
			return
		await process_frame
		if arena.player_node == null or arena.dummy_node == null:
			fail("Missing spawned player/dummy for " + cid)
			return
		var loc: Dictionary = entry.get("render_contract", {}).get("locomotion", {})
		var loc_kind := str(loc.get("kind", "ground"))
		var expected_scale := float(loc.get("default_scale", 2.0))
		var expected_y := float(loc.get("flight_default_y", 250.0)) if loc_kind == "flight" else 840.0
		if arena.player_node.position != Vector2(560.0, expected_y) or arena.dummy_node.position != Vector2(1360.0, expected_y):
			fail("Wrong spawn coordinates for %s: player=%s dummy=%s (expected y=%s)" % [cid, str(arena.player_node.position), str(arena.dummy_node.position), str(expected_y)])
			return
		if loc_kind == "flight":
			arena.step_flight_vertical(-1.0, 10.0)
			if arena.player_node.position.y != arena.fly_min_y:
				fail("Flight ceiling clamp failed for %s: got %s" % [cid, str(arena.player_node.position.y)])
				return
			arena.step_flight_vertical(1.0, 10.0)
			if arena.player_node.position.y != arena.ground_y:
				fail("Flight ground clamp failed for %s: got %s" % [cid, str(arena.player_node.position.y)])
				return
		if arena.player_node.scale != Vector2(expected_scale, expected_scale) or arena.dummy_node.scale != Vector2(-expected_scale, expected_scale):
			fail("Wrong calibrated Nearest scale %s for %s: player=%s dummy=%s" % [str(expected_scale), cid, str(arena.player_node.scale), str(arena.dummy_node.scale)])
			return
		var spr := arena.player_node.get_node_or_null("Sprite") as AnimatedSprite2D
		if spr == null or spr.texture_filter != CanvasItem.TEXTURE_FILTER_NEAREST or spr.centered:
			fail("Character Sprite filter/centered contract failed for " + cid)
			return
		var anchor_arr: Array = entry.get("map_sync_metrics", {}).get("foot_anchor_px", [])
		if anchor_arr.size() == 2:
			var expected_off := Vector2(-float(anchor_arr[0]), -float(anchor_arr[1]))
			if spr.offset != expected_off:
				fail("Offset mismatch for %s: %s != %s" % [cid, str(spr.offset), str(expected_off)])
				return

	# Idle-only stationary character uses the live 60Hz engine clock without AI movement.
	if not arena.select_character("bat_chiroptera"):
		fail("Bat must spawn for reverse-direction action test")
		return
	var bat_sprite := arena.player_node.get_node("Sprite") as AnimatedSprite2D
	if not arena._request_player_action("attack_light") or not arena._is_player_action_playing():
		fail("Player skill must remain active while the movement loop runs")
		return
	bat_sprite.play(&"idle")
	if not arena.player_node.set_facing_left(true):
		fail("Bat right-to-left turn failed")
		return
	if not arena._request_player_action("power_up") or str(arena.player_node.get_meta(&"_arena_queued_action", "")) != "power_up":
		fail("Skill pressed during reverse turn must queue")
		return
	arena.player_node._on_skill_finished(&"turn")
	if not arena.player_node.scale.x < 0.0:
		fail("Bat reverse turn did not commit left facing")
		return
	var queued := str(arena.player_node.get_meta(&"_arena_queued_action", ""))
	arena.player_node.remove_meta(&"_arena_queued_action")
	if not arena._request_player_action(queued) or str(bat_sprite.animation) != "power_up":
		fail("Queued skill failed after reverse turn")
		return
	if not arena.player_node.set_facing_left(false):
		fail("Bat left-to-right turn failed")
		return
	arena.player_node._on_skill_finished(&"turn")
	if arena.player_node.scale.x < 0.0:
		fail("Bat turn did not commit right facing")
		return
	if not arena.select_character("chilopoda"):
		fail("Chilopoda must spawn for no-jump test")
		return
	var before_jump_y: float = arena.player_node.position.y
	arena._on_touch_action("jump")
	if arena.player_vy != 0.0 or arena.player_node.position.y != before_jump_y:
		fail("Monster without jump clip must not jump")
		return
	if not arena.select_character("tasmanian_king_crab") or not arena._request_player_action("attack_light"):
		fail("Crab light button must resolve its authored attack_nomal clip")
		return
	var crab_sprite := arena.player_node.get_node("Sprite") as AnimatedSprite2D
	if crab_sprite.animation != &"attack_nomal":
		fail("Crab light button played wrong clip")
		return

	# Idle-only stationary character uses the live 60Hz engine clock without AI movement.
	arena.select_character("shenron")
	await process_frame
	var shenron_sprite := arena.player_node.get_node("Sprite") as AnimatedSprite2D
	var stationary_pos: Vector2 = arena.dummy_node.position
	arena.set_utility_ai_enabled(true)
	for tick in range(100):
		var decision: Dictionary = arena.step_utility_ai(1.0 / 60.0)
		if decision.get("intent", "") != "idle" or arena.dummy_node.position != stationary_pos:
			fail("Shenron stationary AI moved or attacked")
			return
	var seen_idle_frames := {}
	for tick in range(105):
		seen_idle_frames[shenron_sprite.frame] = true
		await physics_frame
	if seen_idle_frames.size() != 8 or shenron_sprite.animation != &"idle":
		fail("Shenron must play all eight idle poses on the Godot clock")
		return
	arena.set_utility_ai_enabled(false)

	# Verify runtime scale switching (including fractional 1.5x Nearest) preserves anchor & filter
	arena.select_character("t_rex")
	await process_frame
	arena.set_character_scale(1.5)
	if arena.player_node.scale != Vector2(1.5, 1.5) or arena.dummy_node.scale != Vector2(-1.5, 1.5):
		fail("Fractional scale 1.5x toggle failed")
		return
	arena.set_character_scale(3.0)
	if arena.player_node.scale != Vector2(3.0, 3.0) or arena.dummy_node.scale != Vector2(-3.0, 3.0):
		fail("Scale 3x toggle failed")
		return
	arena.set_character_scale(1.0)
	if arena.player_node.scale != Vector2(1.0, 1.0) or arena.dummy_node.scale != Vector2(-1.0, 1.0):
		fail("Scale 1x toggle failed")
		return
	arena.set_character_scale(2.0)

	# --- Utility AI Contract Verification (Shared 1:1 with arena-stage.json & Web) ---
	# 1) Pure body-edge distance verification
	var r_a: Rect2 = UtilityAIScript.compute_body_rect(1000.0, 840.0, 100.0, 100.0, 1.0)
	var r_b: Rect2 = UtilityAIScript.compute_body_rect(1140.0, 840.0, 100.0, 100.0, 1.0)
	if absf(UtilityAIScript.compute_edge_distance(r_a, r_b) - 40.0) > 0.01:
		fail("Expected body edge gap 40.0, got " + str(UtilityAIScript.compute_edge_distance(r_a, r_b)))
		return

	# 2) T-Rex heavy combo: Patrol -> Chase [50,200) -> Light1 -> 1s -> Light2 -> 1s -> Heavy (<200) -> Far >=200 PowerUp
	arena.select_character("t_rex")
	await process_frame
	arena.set_utility_ai_enabled(true)
	if arena.ai_controller.zone_max_x - arena.ai_controller.zone_min_x > 500.0:
		fail("Utility AI zone exceeds 500px")
		return
	var d_out: Dictionary = arena.step_utility_ai(0.016)
	if d_out.get("intent", "") != "patrol":
		fail("Expected patrol outside zone, got " + str(d_out))
		return
	# Move player inside zone at mid-range (~130px gap)
	arena.dummy_node.position.x = 1360.0
	arena.player_node.position = Vector2(1010.0, 840.0) # out of zone still (<1120) -> put inside zone
	arena.player_node.position = Vector2(1130.0, 840.0) # 1360 - 1130 = 230px center; t_rex bw=186*2=372? Let's place dummy at 1560 and player at 1130 or exact rects
	arena.ai_controller.reset_zone(1360.0, arena.walkable_min_x, arena.walkable_max_x)
	arena.dummy_node.position.x = 1520.0
	arena.player_node.position.x = 1130.0 # within [1120, 1600]; edge gap = 390 - 372 = 18px? Use direct controller + sandbox check
	# Wait: T-Rex body width at 2x is 186*2=372px! To test exact [50,200) and >=200 inside zone cleanly, temporarily use 1x scale!
	arena.set_character_scale(1.0)
	arena.dummy_node.position = Vector2(1500.0, 840.0)
	arena.player_node.position = Vector2(1200.0, 840.0) # edge gap = 300 - 186 = 114px in [50, 200)
	var d_chase: Dictionary = arena.step_utility_ai(0.016)
	if d_chase.get("intent", "") != "chase":
		fail("Expected chase at 114px edge gap, got " + str(d_chase))
		return

	# Close range (< 50px edge gap): Light 1 -> Cool -> Light 2 -> Cool -> Heavy (< 200px)
	arena.player_node.position = Vector2(1285.0, 840.0) # center gap 215 - 186 = 29px < 50
	var d_l1: Dictionary = arena.step_utility_ai(0.016)
	if d_l1.get("attack_clip", "") != "attack_light" or arena.ai_controller.light_chain_count != 1:
		fail("Expected Light 1, got " + str(d_l1))
		return
	# Advance past animation + 1s cooldown
	for _i in range(70):
		arena.step_utility_ai(1.0 / 60.0)
	# Ensure next trigger after cooldown fires Light 2 (or already fired inside loop -> chain == 2 or heavy cycled!)
	# Reset deterministically so each beat is asserted right on transition:
	arena.set_utility_ai_enabled(true)
	arena.dummy_node.position = Vector2(1500.0, 840.0)
	arena.player_node.position = Vector2(1285.0, 840.0)
	var b1: Dictionary = arena.step_utility_ai(0.016)
	if b1.get("attack_clip", "") != "attack_light":
		fail("Combo step 1 expected attack_light, got " + str(b1))
		return
	var b_cool: Dictionary = arena.step_utility_ai(0.016)
	if b_cool.get("intent", "") != "busy":
		fail("Combo step 1 immediate next frame must be busy, got " + str(b_cool))
		return
	arena._ai_action_clip = ""
	arena._ai_action_timer_s = 0.0
	arena.ai_controller.cooldown_remaining = 0.0
	var b2: Dictionary = arena.step_utility_ai(0.016)
	if b2.get("attack_clip", "") != "attack_light" or arena.ai_controller.light_chain_count != 2:
		fail("Combo step 2 expected attack_light chain=2, got " + str(b2))
		return
	arena._ai_action_clip = ""
	arena._ai_action_timer_s = 0.0
	arena.ai_controller.cooldown_remaining = 0.0
	arena.player_node.position = Vector2(1210.0, 840.0) # within zone [1120,1600], 290 - 186 = 104px (<200px, heavy follow-up valid!)
	var b3: Dictionary = arena.step_utility_ai(0.016)
	if b3.get("attack_clip", "") != "attack_heavy" or arena.ai_controller.light_chain_count != 0:
		fail("Combo step 3 (<200px after 2 lights) expected attack_heavy & reset, got " + str(b3))
		return

	# After 2 lights, target runs >= 200px inside zone -> PowerUp & resets light_chain_count!
	arena.set_utility_ai_enabled(true)
	arena.dummy_node.position = Vector2(1550.0, 840.0)
	arena.player_node.position = Vector2(1335.0, 840.0)
	arena.step_utility_ai(0.016)
	arena._ai_action_clip = ""; arena._ai_action_timer_s = 0.0; arena.ai_controller.cooldown_remaining = 0.0
	arena.step_utility_ai(0.016) # chain == 2
	arena._ai_action_clip = ""; arena._ai_action_timer_s = 0.0; arena.ai_controller.cooldown_remaining = 0.0
	arena.player_node.position = Vector2(1140.0, 840.0) # gap = 410 - 186 = 224px >= 200px inside zone [1120, 1600]
	var b_far: Dictionary = arena.step_utility_ai(0.016)
	if b_far.get("attack_clip", "") != "power_up" or arena.ai_controller.light_chain_count != 0:
		fail("Expected power_up and chain reset when target runs >=200px, got " + str(b_far))
		return

	# 3) Dilophosaurus has no attack_heavy -> stays on attack_light after 2 lights
	arena.select_character("dilophosaurus")
	await process_frame
	arena.set_character_scale(1.0)
	arena.set_utility_ai_enabled(true)
	arena.dummy_node.position = Vector2(1500.0, 840.0)
	arena.player_node.position = Vector2(1330.0, 840.0)
	arena.ai_controller.light_chain_count = 2
	var d_noheavy: Dictionary = arena.step_utility_ai(0.016)
	if d_noheavy.get("attack_clip", "") != "attack_light":
		fail("Non-heavy monster must fire attack_light instead of heavy, got " + str(d_noheavy))
		return

	# 4) Flying mob (bat_chiroptera): hover y=340, no chase at >=50px (fires power_up), close melee <50px fires attack_light
	arena.select_character("bat_chiroptera")
	await process_frame
	arena.set_character_scale(1.0)
	arena.set_utility_ai_enabled(true)
	if absf(arena.dummy_node.position.y - 250.0) > 0.5:
		fail("Flying enemy must spawn at fly_default_y=250, got " + str(arena.dummy_node.position.y))
		return
	arena.player_node.position = Vector2(1160.0, 840.0) # in zone horizontally, far in air-to-ground height -> ranged power_up
	var f_far: Dictionary = arena.step_utility_ai(0.016)
	if f_far.get("attack_clip", "") != "power_up" or int(f_far.get("move_dir", 9)) != 0:
		fail("Flying enemy at >=50px must not chase and must use power_up, got " + str(f_far))
		return
	arena._ai_action_clip = ""; arena._ai_action_timer_s = 0.0; arena.ai_controller.cooldown_remaining = 0.0
	arena.player_node.position = Vector2(1340.0, 250.0) # close in air (<50px) -> attack_light
	var f_close: Dictionary = arena.step_utility_ai(0.016)
	if f_close.get("attack_clip", "") != "attack_light":
		fail("Flying enemy at <50px must use attack_light, got " + str(f_close))
		return

	# 5) Chilopoda special rule: <50px -> power_up (laser), >=50px -> attack_light (burrow)
	arena.select_character("chilopoda")
	await process_frame
	arena.set_character_scale(1.0)
	arena.set_utility_ai_enabled(true)
	arena.dummy_node.position = Vector2(1500.0, 840.0)
	arena.player_node.position = Vector2(1330.0, 840.0) # close (<50px gap since bw=160 -> 170-160=10px)
	var c_close: Dictionary = arena.step_utility_ai(0.016)
	if c_close.get("attack_clip", "") != "power_up":
		fail("Chilopoda close (<50px) must fire power_up laser, got " + str(c_close))
		return
	arena._ai_action_clip = ""; arena._ai_action_timer_s = 0.0; arena.ai_controller.cooldown_remaining = 0.0
	arena.player_node.position = Vector2(1200.0, 840.0) # far (300-160=140px >= 50px)
	var c_far: Dictionary = arena.step_utility_ai(0.016)
	if c_far.get("attack_clip", "") != "attack_light":
		fail("Chilopoda >=50px must fire attack_light burrow, got " + str(c_far))
		return

	# 6) Tasmanian King Crab unlocked horizontal flip (no turn clip): faces enemy behind it before power_up
	arena.select_character("tasmanian_king_crab")
	await process_frame
	arena.set_character_scale(2.0)
	arena.set_utility_ai_enabled(true)
	if arena.dummy_node.scale.x >= 0.0:
		fail("Crab enemy should spawn facing left (-X) toward player, got scale.x=" + str(arena.dummy_node.scale.x))
		return
	# Player moves behind Crab inside zone [1120..1600] on +X side (edge gap 204px >= 200) -> Crab flips right (+X) and casts power_up
	arena.dummy_node.position = Vector2(1125.0, 840.0)
	arena.player_node.position = Vector2(1595.0, 840.0)
	var crab_behind_r: Dictionary = arena.step_utility_ai(0.016)
	if crab_behind_r.get("intent", "") != "attack" or crab_behind_r.get("attack_clip", "") != "power_up" or arena.dummy_node.scale.x <= 0.0:
		fail("Crab must flip right (+X) toward behind enemy before power_up, got res=%s scale.x=%s" % [str(crab_behind_r), str(arena.dummy_node.scale.x)])
		return
	# Now move Player behind Crab again inside zone on -X side (edge gap 202px >= 200) -> Crab flips left (-X) before attacking
	arena._ai_action_clip = ""; arena._ai_action_timer_s = 0.0; arena.ai_controller.cooldown_remaining = 0.0
	arena.dummy_node.position = Vector2(1590.0, 840.0)
	arena.player_node.position = Vector2(1122.0, 840.0)
	var crab_behind_l: Dictionary = arena.step_utility_ai(0.016)
	if crab_behind_l.get("intent", "") != "attack" or crab_behind_l.get("attack_clip", "") != "power_up" or arena.dummy_node.scale.x >= 0.0:
		fail("Crab must flip left (-X) toward behind enemy before power_up, got res=%s scale.x=%s" % [str(crab_behind_l), str(arena.dummy_node.scale.x)])
		return

	# Calibrated walk speeds, non-turn instant flip burst, and smooth walk->turn->walk mid-stride resume
	var expected_screen_speeds := {
		"chilopoda": 140.0,
		"bat_chiroptera": 115.0,
		"spinosaurus": 170.0,
		"t_rex": 120.0,
		"pteranodon": 140.0,
		"tasmanian_king_crab": 115.0,
		"sarcosuchus": 135.0,
		"dilophosaurus": 155.0,
		"drum": 140.0,
	}
	for cid in expected_screen_speeds.keys():
		arena.select_character(cid)
		var entry: Dictionary = arena._find_character_entry(cid)
		var spd: float = arena._get_walk_speed_px_per_s(entry)
		if absf(spd - float(expected_screen_speeds[cid])) > 0.2:
			fail("Calibrated screen speed mismatch for %s: got %f, expected %f (char_scale=%f)" % [cid, spd, float(expected_screen_speeds[cid]), arena.char_scale])
			return
	var ptero_entry: Dictionary = arena._find_character_entry("pteranodon")
	var crab_entry: Dictionary = arena._find_character_entry("tasmanian_king_crab")
	if absf(arena._get_turn_speed_multiplier(ptero_entry) - 1.2) > 0.001 or absf(arena._get_turn_speed_multiplier(crab_entry) - 1.3) > 0.001:
		fail("Instant-turn burst multiplier mismatch for pteranodon/crab")
		return
	if arena._turn_momentum_factor(0.02, 0.25, 1, -1) <= 0.0 or arena._turn_momentum_factor(0.22, 0.25, 1, -1) >= 0.0:
		fail("Turnaround momentum curve did not transition smoothly from +dir to -dir")
		return
	arena.select_character("bat_chiroptera")
	arena.player_node.play_clip(&"walk")
	arena.player_node.set_meta("_arena_turn_resume_clip", "walk")
	if not arena.player_node.move_in_direction(-1, &"walk") or not arena.player_node.is_turning():
		fail("Bat walk->turn did not trigger cleanly")
		return
	arena.player_node._on_skill_finished(&"turn")
	if arena.player_node.sprite.animation != &"walk" or arena.player_node.sprite.frame < 1:
		fail("Bat turn->walk stalled instead of resuming mid-stride: clip=%s frame=%d" % [str(arena.player_node.sprite.animation), arena.player_node.sprite.frame])
		return

	# 7) Drum AI: idle outside zone / >=400px; teleport (~50px) 50..200px; continuous attack_light every 0.2s <=50px;
	# power_up (11-frame Row 3 prep + Row 4-5 orb at frame 10) in 200..400px; walk clip present; no attack_heavy.
	arena.select_character("drum")
	await process_frame
	if absf(arena.char_scale - 2.5) > 0.001 or absf(arena.enemy_scale - 2.5) > 0.001:
		fail("Drum finalized default_scale must be 2.5, got char=%s enemy=%s" % [str(arena.char_scale), str(arena.enemy_scale)])
		return
	arena.set_utility_ai_enabled(true)
	if not arena.dummy_node.call(&"has_clip", "walk") or arena.dummy_node.call(&"has_clip", "attack_heavy"):
		fail("Drum must include bipedal walk clip and must NOT have separate attack_heavy")
		return
	arena.dummy_node.position = Vector2(1360.0, 840.0)
	arena.player_node.position = Vector2(560.0, 840.0)
	var drum_out: Dictionary = arena.step_utility_ai(1.0 / 60.0)
	if drum_out.get("intent", "") != "idle" or int(drum_out.get("move_dir", 9)) != 0:
		fail("Drum outside zone must remain stationary idle (never patrol), got " + str(drum_out))
		return
	# Enter zone [1120..1600] in 50..200px band -> triggers teleport (~50px) -> attack_light
	arena.player_node.position = Vector2(1150.0, 840.0)
	var drum_tp: Dictionary = arena.step_utility_ai(1.0 / 60.0)
	if drum_tp.get("intent", "") != "attack" or drum_tp.get("attack_clip", "") != "teleport":
		fail("Drum on 50..200px entry must trigger teleport, got " + str(drum_tp))
		return
	for _i in range(15):
		arena.step_utility_ai(1.0 / 60.0)
	var tp_edge_dist: float = absf(arena.dummy_node.position.x - arena.player_node.position.x) - ((56.0 * 2.5 + 56.0 * 2.5) * 0.5)
	if absf(tp_edge_dist - 50.0) > 6.0:
		fail("Drum teleport must land ~50px edge gap from target, got gap=" + str(tp_edge_dist))
		return
	var saw_light := false
	for _i in range(10):
		var d_step: Dictionary = arena.step_utility_ai(1.0 / 60.0)
		if d_step.get("attack_clip", "") == "attack_light":
			saw_light = true
			break
	if not saw_light:
		fail("Drum after teleport must immediately unleash attack_light (Row 2)")
		return
	# Complete first attack_light (~24 ticks = 0.4s), verify 0.2s cooldown before second continuous attack_light <= 50px
	for _i in range(26):
		arena.step_utility_ai(1.0 / 60.0)
	var light_cd_wait: Dictionary = arena.step_utility_ai(1.0 / 60.0)
	if light_cd_wait.get("attack_clip", "") == "attack_light":
		fail("Drum must wait 0.2s cooldown between continuous attack_light strikes")
		return
	var saw_second_light := false
	for _i in range(16):
		var d2: Dictionary = arena.step_utility_ai(1.0 / 60.0)
		if d2.get("attack_clip", "") == "attack_light":
			saw_second_light = true
			break
	if not saw_second_light:
		fail("Drum <=50px must strike attack_light continuously every 0.2s")
		return
	# Target retreats beyond melee into 200 < edge_dist < 400 -> power_up (11-frame Row 3+4+5 -> orb at frame 10)
	arena._ai_action_clip = ""; arena._ai_action_timer_s = 0.0; arena.ai_controller.cooldown_remaining = 0.0
	arena._enemy_orb_active = false; arena._enemy_orb_spawned_for_cast = false
	arena.dummy_node.position = Vector2(1360.0, 840.0)
	arena.player_node.position = Vector2(960.0, 840.0) # center gap=400, half-widths=112 -> edge_dist=288 in (200, 400)
	var pu_d: Dictionary = arena.step_utility_ai(1.0 / 60.0)
	if pu_d.get("intent", "") != "attack" or pu_d.get("attack_clip", "") != "power_up":
		fail("Drum at 200<edge_dist<400 must cast power_up, got " + str(pu_d))
		return
	var saw_drum_orb := false
	for _i in range(55):
		arena.step_utility_ai(1.0 / 60.0)
		if arena._enemy_orb_active:
			saw_drum_orb = true
			break
	if not saw_drum_orb:
		fail("Drum power_up release frame 10 must spawn independent electric_orb_fx projectile")
		return
	# Retreat >= 400px -> returns to stationary idle
	arena._ai_action_clip = ""; arena._ai_action_timer_s = 0.0; arena.ai_controller.cooldown_remaining = 0.0
	arena.player_node.position = Vector2(800.0, 840.0) # edge_dist = 448 >= 400
	var drum_far_idle: Dictionary = arena.step_utility_ai(1.0 / 60.0)
	if drum_far_idle.get("intent", "") != "idle" or int(drum_far_idle.get("move_dir", 9)) != 0:
		fail("Drum >=400px must return to stationary idle, got " + str(drum_far_idle))
		return

	# Verify Rocky Plateau Original JPG Backdrop + 1 Horizontal 32x32 TileMapLayer + Contact Shadow + Ground Dust FX (0 floating platforms)
	var metrics_ter: Dictionary = arena.get_stage_metrics()
	if not bool(metrics_ter.get("terrain_loaded", false)) or int(metrics_ter.get("platforms_count", -1)) != 0:
		fail("Terrain config & 0 floating platforms must load in ArenaSandbox: " + str(metrics_ter))
		return
	if arena.get_node_or_null("TerrainLayer/GroundTileMap") == null:
		fail("Missing TerrainLayer/GroundTileMap TileMapLayer node")
		return
	var bg_layer_node := arena.get_node_or_null("BackgroundLayer") as CanvasItem
	if bg_layer_node == null or not bg_layer_node.visible:
		fail("Original JPG BackgroundLayer must remain visible behind 1 horizontal ground tile ledge")
		return
	arena.select_character("t_rex")
	arena.player_node.position = Vector2(512.0, 840.0)
	arena.player_vy = 0.0
	var jump_res: Dictionary = arena.step_player_vertical_physics(1.0 / 60.0, true, false)
	if not bool(jump_res.get("jumped", false)) or arena._active_dust_fx.size() < 1:
		fail("Jump from ground must spawn pixel ground dust FX")
		return
	var peak_y := 840.0
	var landed_ground := false
	for _t in range(90):
		var st: Dictionary = arena.step_player_vertical_physics(1.0 / 60.0, false, false)
		peak_y = minf(peak_y, float(st.get("y", 840.0)))
		if _t > 5 and bool(st.get("on_ground", false)) and absf(float(st.get("y", 0.0)) - 840.0) < 0.5:
			landed_ground = true
			break
	if peak_y >= 760.0 or not landed_ground:
		fail("Player must arc above ground and land back on horizontal floor ground_y=840, peak=" + str(peak_y) + " y=" + str(arena.player_node.position.y))
		return
	var sh_on_ground: Dictionary = arena.compute_contact_shadow_params(512.0, 840.0, 56.0, true)
	var sh_in_air: Dictionary = arena.compute_contact_shadow_params(512.0, 700.0, 56.0, true)
	if float(sh_in_air["half_w"]) >= float(sh_on_ground["half_w"]):
		fail("Contact shadow must shrink with height above horizontal ground floor")
		return

	# Verify T-rex power_up spawns ProjectileFX (fireball_fx) synchronized with engine-export.json (origin [304,138] - anchor [176,224])
	arena.select_character("t_rex")
	await process_frame
	var trex_node: Node2D = arena.player_node
	var trex_pfx := trex_node.get_node_or_null("ProjectileFX") as AnimatedSprite2D
	if trex_pfx == null:
		fail("T-rex prefab must expose ProjectileFX for power_up fireball_fx")
		return
	if trex_pfx.visible or trex_pfx.position != Vector2(128.0, -86.0) or trex_pfx.offset != Vector2(-176.0, -128.0):
		fail("T-rex ProjectileFX geometry mismatch: vis=%s pos=%s offset=%s" % [str(trex_pfx.visible), str(trex_pfx.position), str(trex_pfx.offset)])
		return
	if not arena._request_player_action("power_up"):
		fail("T-rex player power_up request must succeed")
		return
	var trex_saw_fireball := false
	var trex_fireball_hid := false
	for _t in range(60):
		await physics_frame
		arena.step_player_movement(1.0 / 60.0, 0)
		if trex_pfx.visible and trex_pfx.animation == &"fireball_fx":
			trex_saw_fireball = true
		elif trex_saw_fireball and not trex_pfx.visible:
			trex_fireball_hid = true
			break
	if not trex_saw_fireball or not trex_fireball_hid:
		fail("T-rex power_up must emit fireball_fx on hit event and hide after finishing: saw=%s hid=%s" % [str(trex_saw_fireball), str(trex_fireball_hid)])
		return

	# Verify Drum Player can walk, turn cleanly without bool(null) crash, attack_light, power_up orb, and teleport
	arena.select_character("drum")
	await process_frame
	var drum_player: Node2D = arena.player_node
	if arena._is_fighter_turning(drum_player):
		fail("Drum player must report _is_fighter_turning == false")
		return
	var drum_x0 := drum_player.position.x
	for _t in range(10):
		arena.step_player_movement(1.0 / 60.0, 1)
	if drum_player.position.x <= drum_x0 + 10.0:
		fail("Drum player must walk right cleanly: x0=%s x1=%s" % [str(drum_x0), str(drum_player.position.x)])
		return
	var drum_peak_x := drum_player.position.x
	for _t in range(10):
		arena.step_player_movement(1.0 / 60.0, -1)
	if drum_player.position.x >= drum_peak_x - 10.0 or not arena.player_facing_left:
		fail("Drum player must walk left and flip cleanly: peak=%s x2=%s left=%s" % [str(drum_peak_x), str(drum_player.position.x), str(arena.player_facing_left)])
		return
	for _t in range(2):
		arena.step_player_movement(1.0 / 60.0, 0)
	if not arena._request_player_action("attack_light"):
		fail("Drum player attack_light must succeed")
		return
	var drum_spr := drum_player.get_node("Sprite") as AnimatedSprite2D
	if drum_spr.animation != &"attack_light":
		fail("Drum player Sprite must play attack_light, got " + str(drum_spr.animation))
		return
	for _t in range(45):
		await physics_frame
		arena.step_player_movement(1.0 / 60.0, 0)
		if not arena._is_player_action_playing():
			break
	if not arena._request_player_action("power_up"):
		fail("Drum player power_up must succeed")
		return
	var drum_cfx := drum_player.get_node_or_null("ChargeFX") as AnimatedSprite2D
	var drum_pfx := drum_player.get_node_or_null("ProjectileFX") as AnimatedSprite2D
	if drum_cfx == null or not drum_cfx.visible:
		fail("Drum player power_up must activate ChargeFX")
		return
	var drum_saw_orb := false
	var drum_orb_moved := false
	var orb_start_x := 0.0
	for _t in range(70):
		await physics_frame
		arena.step_player_movement(1.0 / 60.0, 0)
		if drum_pfx != null and drum_pfx.visible:
			if not drum_saw_orb:
				drum_saw_orb = true
				orb_start_x = drum_pfx.position.x
			elif absf(drum_pfx.position.x - orb_start_x) > 20.0:
				drum_orb_moved = true
				break
	if not drum_saw_orb or not drum_orb_moved:
		fail("Drum player power_up must release moving electric_orb_fx: saw=%s moved=%s" % [str(drum_saw_orb), str(drum_orb_moved)])
		return
	for _t in range(30):
		await physics_frame
		arena.step_player_movement(1.0 / 60.0, 0)
		if not arena._is_player_action_playing():
			break
	# Test Drum player teleport dash
	arena.step_player_movement(1.0 / 60.0, 1)
	drum_player.position.x = 500.0
	if not arena._request_player_action("teleport"):
		fail("Drum player teleport must succeed")
		return
	var tp_start_x := drum_player.position.x
	for _t in range(35):
		await physics_frame
		arena.step_player_movement(1.0 / 60.0, 0)
	if drum_player.position.x <= tp_start_x + 150.0:
		fail("Drum player teleport must relocate +120*char_scale forward: start=%s end=%s" % [str(tp_start_x), str(drum_player.position.x)])
		return
	# Verify Drum on K70E can walk all the way near visible edges [-240..+2160] without stopping at 140..1780
	var k70e_drum_layout: Dictionary = arena.apply_device_profile("redmi_k70e")
	var k70e_drum_vis_w := float(k70e_drum_layout.get("visible_logic_size", [2400.7869, 1080.0])[0])
	var drum_half_w := 56.0 * 2.5 * 0.5
	var exp_drum_min := -240.0 + drum_half_w
	var exp_drum_max := 6360.0 - drum_half_w
	if absf(arena.walkable_min_x - exp_drum_min) > 1.0 or absf(arena.walkable_max_x - exp_drum_max) > 1.0:
		fail("K70E Drum walkable bounds mismatch: got=[%s,%s] exp=[%s,%s]" % [str(arena.walkable_min_x), str(arena.walkable_max_x), str(exp_drum_min), str(exp_drum_max)])
		return
	drum_player.position.x = 50.0
	for _t in range(180):
		arena.step_player_movement(1.0 / 60.0, -1)
	if drum_player.position.x >= -150.0 or absf(drum_player.position.x - arena.walkable_min_x) > 1.0:
		fail("K70E Drum must walk past old 140px wall right up to body-edge visible left bound: x=%s min=%s" % [str(drum_player.position.x), str(arena.walkable_min_x)])
		return
	drum_player.position.x = 1850.0
	for _t in range(180):
		arena.step_player_movement(1.0 / 60.0, 1)
	if drum_player.position.x <= 2050.0:
		fail("K70E Drum must walk past original screen right edge: x=%s" % str(drum_player.position.x))
		return
	arena.set_pixel_perfect_enabled(false, Vector2i(1920, 1080))

	# Verify Floating Camera 70x74 seamless idle<->walk phase continuity + ranged AI attack_light + projectile
	if not arena.select_character("floating_camera"):
		fail("Floating Camera must select in ArenaSandbox")
		return
	await process_frame
	var fc_dims: Vector2i = arena._get_body_dims(arena._find_character_entry_ro("floating_camera"))
	if fc_dims != Vector2i(70, 74):
		fail("Floating Camera body_only_bbox_px must be 70x74, got " + str(fc_dims))
		return
	var fc_spr := arena.player_node.get_node_or_null("Sprite") as AnimatedSprite2D
	arena.step_player_movement(1.0 / 60.0, 1)
	if fc_spr.animation != &"walk":
		fail("Floating Camera must enter walk when moving, got " + str(fc_spr.animation))
		return
	fc_spr.set_frame_and_progress(4, 0.35)
	arena.step_player_movement(1.0 / 60.0, 0)
	if fc_spr.animation != &"idle" or fc_spr.frame != 4:
		fail("Floating Camera stopping walk->idle must preserve phase frame=4 seamlessly, got anim=%s frame=%d" % [str(fc_spr.animation), fc_spr.frame])
		return
	arena.step_player_movement(1.0 / 60.0, 1)
	if fc_spr.animation != &"walk" or fc_spr.frame != 4:
		fail("Floating Camera resuming idle->walk must preserve phase frame=4 seamlessly, got anim=%s frame=%d" % [str(fc_spr.animation), fc_spr.frame])
		return
	arena.select_enemy_character("floating_camera", true)
	arena.set_utility_ai_enabled(true)
	arena.dummy_node.position = Vector2(1500.0, 300.0)
	arena.player_node.position = Vector2(1200.0, 300.0)
	var fc_ai_res: Dictionary = arena.step_utility_ai(1.0 / 60.0)
	if fc_ai_res.get("attack_clip", "") != "attack_light" or arena._ai_action_clip != "attack_light":
		fail("Floating Camera flying AI at >=50px without power_up must fire attack_light, got " + str(fc_ai_res))
		return
	arena.set_utility_ai_enabled(false)

	# Verify step-edge immediate drop, uphill blocking, AI step handling, and flight floor across ALL ground/flying archetypes
	for step_cid in ["drum", "t_rex", "spinosaurus", "chilopoda", "tasmanian_king_crab", "sarcosuchus", "dilophosaurus"]:
		arena.select_character(step_cid)
		await process_frame
		# 1. Walk off Step 1 (2850, 840 -> 890): must start falling on the VERY FIRST frame past edge!
		arena.player_node.position = Vector2(2848.0, 840.0)
		arena.player_vy = 0.0
		var fell_immediately := false
		for _t in range(12):
			arena.step_player_movement(1.0 / 60.0, 1)
			if arena.player_node.position.x >= 2850.0:
				if arena.player_node.position.y > 840.0:
					fell_immediately = true
				else:
					fail("%s hovered at step 1 edge x=%s y=%s" % [step_cid, str(arena.player_node.position.x), str(arena.player_node.position.y)])
					return
				break
		if not fell_immediately:
			fail("%s failed to step off and begin falling at step 1" % step_cid)
			return
		# Continue falling to Step 2 floor (890), then walk off Step 2 (3695 -> 945)
		for _t in range(40):
			arena.step_player_movement(1.0 / 60.0, 0)
		if absf(arena.player_node.position.y - 890.0) > 1.0:
			fail("%s did not land on Step 2 floor y=890, got y=%s" % [step_cid, str(arena.player_node.position.y)])
			return
		# Walking back left uphill into Step 1 wall must be blocked
		arena.player_node.position = Vector2(2880.0, 890.0)
		for _t in range(25):
			arena.step_player_movement(1.0 / 60.0, -1)
		if arena.player_node.position.x < 2850.0:
			fail("%s walked uphill through Step 1 wall to x=%s" % [step_cid, str(arena.player_node.position.x)])
			return
		# Walk off Step 2 (3695) -> must start falling immediately and land on y=945 (including after turning right)
		arena.player_node.position = Vector2(3693.0, 890.0)
		arena.player_vy = 0.0
		var fell_step2 := false
		for _t in range(120):
			await physics_frame
			arena.step_player_movement(1.0 / 60.0, 1)
			if arena.player_node.position.x >= 3695.0:
				if arena.player_node.position.y > 890.0:
					fell_step2 = true
				else:
					fail("%s hovered at step 2 edge x=%s y=%s" % [step_cid, str(arena.player_node.position.x), str(arena.player_node.position.y)])
					return
				break
		if not fell_step2:
			fail("%s failed to begin falling at step 2 (x=%s y=%s turning=%s)" % [step_cid, str(arena.player_node.position.x), str(arena.player_node.position.y), str(arena._is_fighter_turning(arena.player_node))])
			return
		for _t in range(45):
			arena.step_player_movement(1.0 / 60.0, 0)
		if absf(arena.player_node.position.y - 945.0) > 1.0:
			fail("%s did not land on Step 3 floor y=945, got y=%s" % [step_cid, str(arena.player_node.position.y)])
			return
	# Verify Drum teleport cannot tunnel uphill through Step 1 wall and falls if teleporting off Step 1
	arena.select_character("drum")
	await process_frame
	arena.step_player_movement(1.0 / 60.0, -1)
	arena.player_node.position = Vector2(2900.0, 890.0)
	arena._request_player_action("teleport")
	for _t in range(30):
		await physics_frame
		arena.step_player_movement(1.0 / 60.0, 0)
	if arena.player_node.position.x < 2850.0:
		fail("Drum teleport must be blocked by Step 1 cliff wall, got x=%s" % str(arena.player_node.position.x))
		return
	# Verify AI (Utility AI) across step edges: chasing downhill drops to y=890; chasing uphill stops at Step 1 wall
	arena.select_character("t_rex")
	await process_frame
	arena.select_enemy_character("spinosaurus", true)
	await process_frame
	arena.set_utility_ai_enabled(true)
	arena.ai_controller.reset_zone(3050.0, 2600.0, 3400.0)
	arena.dummy_node.position = Vector2(2842.0, 840.0)
	arena.enemy_vy = 0.0
	arena.player_node.position = Vector2(3270.0, 890.0)
	for _t in range(45):
		await physics_frame
		arena.step_utility_ai(1.0 / 60.0)
	if arena.dummy_node.position.x < 2850.0 or absf(arena.dummy_node.position.y - 890.0) > 1.0:
		fail("AI chasing downhill off Step 1 must drop cleanly to y=890, got " + str(arena.dummy_node.position))
		return
	arena.player_node.position = Vector2(2700.0, 840.0)
	for _t in range(30):
		await physics_frame
		arena.step_utility_ai(1.0 / 60.0)
	if arena.dummy_node.position.x < 2850.0:
		fail("AI chasing uphill from Step 2 must be blocked by Step 1 cliff wall, got " + str(arena.dummy_node.position))
		return
	arena.set_utility_ai_enabled(false)

	# Verify flying characters descend to lower step floor y=945 cleanly
	arena.select_character("floating_camera")
	await process_frame
	arena.player_node.position = Vector2(4100.0, 840.0)
	arena.step_flight_vertical(1.0, 5.0)
	if absf(arena.player_node.position.y - 945.0) > 0.5:
		fail("Flying character over Step 3 must descend to local floor y=945, got " + str(arena.player_node.position.y))
		return

	# Verify PixelRulerModal 1:1 world PX measurements across devices (FHD, K70E, iPad)
	if arena.ruler_button == null or arena.ruler_modal == null or arena.ruler_modal_visible:
		fail("Ruler button and hidden PixelRulerModal must initialize cleanly")
		return
	arena.select_character("drum")
	await process_frame
	arena.set_ruler_modal_visible(true)
	if not arena.ruler_modal_visible or not arena.ruler_modal.visible:
		fail("set_ruler_modal_visible(true) must open PixelRulerModal")
		return
	arena.player_node.position = Vector2(360.0, 840.0)
	arena.dummy_node.position = Vector2(1360.0, 840.0)
	var rm_k70e: Dictionary = {}
	arena.apply_device_profile("redmi_k70e")
	rm_k70e = arena.measure_player_enemy_distance()
	if absf(float(rm_k70e.get("dx_world_px", 0.0)) - 1000.0) > 0.5 or absf(float(rm_k70e.get("player_enemy_edge_gap", 0.0)) - 860.0) > 0.5:
		fail("Ruler K70E Drum 360<->1360 measurement mismatch: " + str(rm_k70e))
		return
	arena.apply_device_profile("ipad_10th")
	var rm_ipad: Dictionary = arena.measure_player_enemy_distance()
	if absf(float(rm_ipad.get("dx_world_px", 0.0)) - 1000.0) > 0.5 or absf(float(rm_ipad.get("player_enemy_edge_gap", 0.0)) - 860.0) > 0.5:
		fail("Ruler iPad Drum 360<->1360 must stay 1:1 world PX invariant: " + str(rm_ipad))
		return
	arena.set_ruler_modal_visible(false)
	arena.set_pixel_perfect_enabled(false, Vector2i(1920, 1080))

	# Smoke test Player movement + power_up across every character in roster without script errors
	for ch_entry in arena.roster_characters:
		if not (ch_entry is Dictionary):
			continue
		var cid_smoke := str(ch_entry.get("character_id", ""))
		if cid_smoke.is_empty():
			continue
		arena.select_character(cid_smoke)
		await process_frame
		arena.step_player_movement(1.0 / 60.0, 1)
		if arena._has_clip_name(arena.player_node, &"power_up"):
			if not arena._request_player_action("power_up"):
				fail("Roster player power_up failed for " + cid_smoke)
				return

	# Field Mode verification: 7 ground + 7 flying monsters, Stamina/3s Mini-Stun, Drum Hero, Homing Orbs, 7s Respawns, Dragon Ball drops, Pointer & Pad Bindings
	arena.enable_field_mode(true, false)
	await process_frame
	var fm = arena.field_manager
	if fm == null or not fm.active or fm.slots.size() != 14:
		fail("Field mode must spawn 14 monster slots (7 ground + 7 flying)")
		return
	if arena.player_node != null or fm.player_spawned:
		fail("Hero Drum must start hidden when entering field mode")
		return
	var exp_ids := ["chilopoda", "spinosaurus", "tasmanian_king_crab", "t_rex", "sarcosuchus", "dilophosaurus", "spinosaurus", "bat_chiroptera", "pteranodon", "floating_camera", "bat_chiroptera", "pteranodon", "floating_camera", "bat_chiroptera"]
	var exp_hps := [1300.0, 1500.0, 1300.0, 1800.0, 1500.0, 1300.0, 1500.0, 900.0, 1000.0, 800.0, 900.0, 1000.0, 800.0, 900.0]
	for si in range(14):
		var s: Dictionary = fm.slots[si]
		if str(s["character_id"]) != exp_ids[si] or absf(float(s["max_hp"]) - exp_hps[si]) > 0.1:
			fail("Slot %d mismatch: got %s HP=%s, expected %s HP=%s" % [si, str(s["character_id"]), str(s["max_hp"]), exp_ids[si], str(exp_hps[si])])
			return

	# Spawn Drum at far left of map
	arena.set_field_hero_visible(true)
	await process_frame
	if arena.player_node == null or not fm.player_spawned or absf(arena.player_node.position.x - (arena.walkable_min_x + 24.0)) > 2.0:
		fail("Drum must spawn at far left end of map")
		return
	if absf(fm.player_hp - 1500.0) > 0.1 or absf(fm.player_mana) > 0.1:
		fail("Drum must start at 1500 HP and 0 Mana")
		return

	# Drum melee deals 200 dmg, adds +20 Mana, reduces monster Stamina by 20 without HIT while Stamina > 0; breaks at 0 for 3s mini-stun
	var slot0: Dictionary = fm.slots[0]
	var m0 := slot0["node"] as Node2D
	arena.player_node.position = Vector2(m0.position.x - 40.0, m0.position.y)
	arena.player_facing_left = false
	arena.player_node.scale = Vector2(arena.char_scale, arena.char_scale)
	fm.pointer_kind = "enemy"
	fm.pointer_slot_id = str(slot0["id"])
	fm.apply_damage_to_slot(slot0, 200.0, 20.0)
	if absf(float(slot0["hp"]) - 1100.0) > 0.1 or absf(float(slot0["stamina"]) - 80.0) > 0.1 or float(slot0["stun_timer_s"]) > 0.0:
		fail("First hit must reduce HP 1300->1100 and Stamina 100->80 without mini-stun")
		return
	var m0_spr := m0.get_node_or_null("Sprite") as AnimatedSprite2D
	if m0_spr != null and m0_spr.animation == &"hit":
		fail("Monster must NOT play hit while Stamina > 0")
		return
	# 4 more stamina breaks -> 0 Stamina -> 3.0s attack-lock + 1 HIT clip per hit!
	for _k in range(4):
		fm.apply_damage_to_slot(slot0, 50.0, 20.0)
	if float(slot0["stamina"]) > 0.1 or absf(float(slot0["stun_timer_s"]) - 3.0) > 0.15 or float(slot0.get("hit_anim_timer_s", 0.0)) <= 0.0:
		fail("5th stamina hit must break poise to 0, start 3.0s stun lock, and trigger 1 HIT clip")
		return
	if m0_spr != null and m0_spr.animation != &"hit":
		fail("Monster must immediately play HIT animation when receiving damage with broken stamina, anim=%s" % str(m0_spr.animation))
		return
	# Wait past 1 hit clip (~0.8s = 50 frames) without attacking -> monster must resume normal movement (NOT stuck in hit), while still attack-locked!
	for _s1 in range(54):
		await physics_frame
		fm.step(1.0 / 60.0)
	if float(slot0.get("hit_anim_timer_s", 0.0)) > 0.0 or float(slot0["stun_timer_s"]) <= 0.5:
		fail("Single HIT clip must finish before 3.0s stun lock expires (hit_t=%s stun_t=%s)" % [str(slot0.get("hit_anim_timer_s", 0.0)), str(slot0["stun_timer_s"])])
		return
	if m0_spr != null and m0_spr.animation == &"hit":
		fail("When unattacked after single HIT clip ends, monster must move/idle normally instead of looping hit")
		return
	if not str(slot0.get("action_clip", "")).is_empty():
		fail("Broken-stamina monster must remain locked from attacking back during 3s window")
		return
	# Hitting once more while stamina broken triggers 1 more HIT clip and resets 3s lock (1 hit = 1 hit anim)
	fm.apply_damage_to_slot(slot0, 50.0, 20.0)
	if float(slot0.get("hit_anim_timer_s", 0.0)) <= 0.0 or (m0_spr != null and m0_spr.animation != &"hit"):
		fail("Follow-up hit during broken stamina must trigger 1 HIT clip")
		return
	# Step remaining 3.1s without hitting -> stun expires and Stamina refills to 100
	for _s2 in range(190):
		await physics_frame
		fm.step(1.0 / 60.0)
	if float(slot0["stun_timer_s"]) > 0.0 or absf(float(slot0["stamina"]) - 100.0) > 0.1:
		fail("Monster Stamina must refill to 100 after 3s attack-lock ends without hits")
		return

	# Check 100 Mana requirement for PowerUp orb (+50% speed = 1170 px/s) + homing 400 dmg + default powerup explosion (-20% scale = 0.68)
	fm.player_mana = 80.0
	if fm.request_player_power_up():
		fail("Drum power_up must fail when Mana < 100")
		return
	fm.player_mana = 100.0
	if not fm.request_player_power_up() or absf(fm.player_mana) > 0.1:
		fail("Drum power_up must succeed and consume 100 Mana")
		return
	fm._explosion_nodes.clear()
	fm.call("_spawn_homing_projectile", arena.player_node, "drum", "electric_orb_fx", arena.player_node.position, 2.5, slot0, true, 400.0, 20.0)
	if fm.homing_projectiles.is_empty() or absf(float(fm.homing_projectiles[fm.homing_projectiles.size() - 1]["speed"]) - 1170.0) > 1.0:
		fail("Drum skill projectile speed must be +50%% (1170 px/s)")
		return
	var pre_m0_hp: float = float(slot0["hp"])
	for _dp in range(180):
		fm.step(1.0 / 60.0)
		if float(slot0["hp"]) < pre_m0_hp - 0.1:
			break
	if float(slot0["hp"]) >= pre_m0_hp - 0.1 or fm._explosion_nodes.is_empty():
		fail("Drum power_up projectile must hit target and spawn default powerup explosion (exp=%d)" % fm._explosion_nodes.size())
		return
	var drum_exp := fm._explosion_nodes[0] as AnimatedSprite2D
	if drum_exp == null or absf(drum_exp.scale.x - 0.68) > 0.03:
		fail("Default explosion scale must be 0.68 (-20%% from 0.85), got %s" % (str(drum_exp.scale.x) if drum_exp != null else "null"))
		return
	fm.homing_projectiles.clear()
	fm._explosion_nodes.clear()
	# Test enemy projectile hitting Drum: subtracts HP, flashes Drum, and spawns small powerup explosion FX!
	var fcam_slot: Dictionary = fm.slots[9] # floating_camera (800 HP, 80 dmg)
	var pre_hp: float = float(fm.player_hp)
	fm._explosion_nodes.clear()
	fm.call("_spawn_homing_projectile", fcam_slot["node"], "floating_camera", "projectile_fx", Vector2(2000.0, 260.0), 1.8, {}, false, 80.0, 0.0)
	arena.player_node.position = Vector2(2620.0, 840.0)
	for _p in range(240):
		fm.step(1.0 / 60.0)
		if float(fm.player_hp) < pre_hp - 0.1:
			break
	if absf(fm.player_hp - (pre_hp - 80.0)) > 0.1 or float(fm.player_hit_flash_s) <= 0.0 or fm._explosion_nodes.is_empty():
		fail("Enemy projectile must hit Drum for 80 dmg (hp=%s->%s), trigger player hit flash (flash=%s), and spawn powerup explosion FX (exp=%d, proj=%d)" % [str(pre_hp), str(fm.player_hp), str(fm.player_hit_flash_s), fm._explosion_nodes.size(), fm.homing_projectiles.size()])
		return
	var d_spr := arena.player_node.get_node_or_null("Sprite") as AnimatedSprite2D
	if d_spr != null and d_spr.animation == &"hit":
		fail("Hero Drum must NEVER play HIT stagger animation")
		return

	# Hero Immortal & Monster Attack Range overlay toggles
	arena.set_show_monster_ranges(true)
	if not arena.show_monster_ranges_enabled or not bool(fm.show_monster_ranges):
		fail("set_show_monster_ranges(true) must enable monster range overlay")
		return
	arena.set_show_monster_ranges(false)

	var hp_before_imm: float = float(fm.player_hp)
	arena.set_hero_immortal(true)
	fm.apply_damage_to_player(5000.0)
	if fm.player_dead or absf(float(fm.player_hp) - hp_before_imm) > 0.1:
		fail("Immortal mode must prevent player HP loss and KO")
		return
	arena.set_hero_immortal(false)

	# Player 0 HP KO + 3s respawn at far left with 1500 HP
	fm.apply_damage_to_player(2000.0)
	if not fm.player_dead or fm.player_hp > 0.0:
		fail("Drum at 0 HP must enter KO state")
		return
	for _r in range(190):
		fm.step(1.0 / 60.0)
	if fm.player_dead or absf(fm.player_hp - 1500.0) > 0.1 or absf(arena.player_node.position.x - (arena.walkable_min_x + 24.0)) > 2.0:
		fail("Drum must respawn at far left with 1500 HP after 3s KO")
		return

	# 30%-gated Weighted Dragon Ball drops (gate < 30% -> roll star across 30/20/10/5/2/0.5/0.1) & Top Layer z_index == 50 + 1s unlock + pointer cycle
	var drop_cases := [
		[0.0, 0.0, 7],
		[15.0, 35.0, 6],
		[29.9, 55.0, 5],
		[10.0, 62.0, 4],
		[5.0, 66.0, 3],
		[1.0, 67.2, 2],
		[20.0, 67.55, 1],
		[30.0, 0.0, 0],
		[45.0, 10.0, 0],
		[80.0, 5.0, 0],
	]
	for dc in drop_cases:
		var rolled := int(fm.roll_dragon_ball_number(float(dc[0]), float(dc[1])))
		if rolled != int(dc[2]):
			fail("Dragon Ball roll mismatch at gate=%s star=%s: got %d expected %d" % [str(dc[0]), str(dc[1]), rolled, int(dc[2])])
			return
	var spawned_ball: Node2D = fm.roll_and_spawn_dragon_ball(Vector2(arena.player_node.position.x + 20.0, arena.player_node.position.y), 10.0, 0.0)
	if spawned_ball == null or arena._item_drop_layer.z_index <= arena.fighters_layer.z_index:
		fail("Dropped Dragon Ball layer z_index must exceed FightersLayer z_index")
		return
	if fm.call("_can_pickup_item", spawned_ball):
		fail("Dropped item must not be pickable before 1.0s drop completion")
		return
	for _b in range(66):
		arena.step_dropped_items(1.0 / 60.0)
		fm.step(1.0 / 60.0)
	if not fm.call("_can_pickup_item", spawned_ball):
		fail("Dropped item must become pickable after 1.0s")
		return
	var cyc: Dictionary = fm.cycle_target_pointer()
	if str(cyc.get("kind", "")) == "":
		fail("Target pointer cycle must select a valid candidate")
		return

	# Ground slot death -> 12s respawn with dilophosaurus alternation; flying slot -> bat/pteranodon/camera rotation
	var g_slot: Dictionary = fm.slots[1]
	fm.apply_damage_to_slot(g_slot, 2000.0, 20.0)
	if bool(g_slot["alive"]):
		fail("Ground slot 1 must die cleanly")
		return
	for _rg_early in range(430):
		fm.step(1.0 / 60.0)
	if bool(g_slot["alive"]):
		fail("Ground slot 1 must stay dead at 7.16s now that monster respawn is 12s")
		return
	for _rg in range(300):
		fm.step(1.0 / 60.0)
	if not bool(g_slot["alive"]) or str(g_slot["character_id"]) != "dilophosaurus" or absf(float(g_slot["max_hp"]) - 1300.0) > 0.1:
		fail("First ground respawn must alternate dilophosaurus HP=1300 after 12s, got %s" % str(g_slot.get("character_id", "")))
		return

	# MobileActionPad slot assignment check (no hard lock on 2..7, 1 & 8 locked)
	var pad_test = preload("res://scenes/runtime/MobileActionPad.gd").new()
	arena.add_child(pad_test)
	pad_test.configure_for_character("drum", PackedStringArray(["idle", "walk", "jump", "teleport", "attack_light", "power_up"]), false)
	if pad_test.get_slot_binding(1) != "attack_light" or pad_test.get_slot_binding(4) != "power_up" or pad_test.get_slot_binding(8) != "cycle_target":
		fail("MobileActionPad Drum default slots mismatch")
		return
	pad_test.set_slot_binding(5, "power_up")
	if pad_test.get_slot_binding(5) != "power_up":
		fail("MobileActionPad flexible slot 5 assignment failed")
		return
	if pad_test.safe_root == null or pad_test.find_child("WorldPositionMap", true, false) != null or pad_test.has_method("set_map_progress"):
		fail("WorldPositionMap mini-map must be removed per Owner request")
		return
	var btn1 := pad_test._slot_buttons.get(1) as Button
	var btn8 := pad_test._slot_buttons.get(8) as Button
	if btn1 == null or btn1.get_node_or_null("Visual") == null or btn8 == null or btn8.get_node_or_null("Visual") == null:
		fail("MobileActionPad buttons must attach custom vector visual overlays")
		return
	pad_test.queue_free()

	# Flying monster stability (no rapid left/right flipping in place), elliptical orbit, single 360-deg curved FX, and 360 flight vector
	var bat_slot: Dictionary = fm.slots[7] # bat_chiroptera
	var fcam_s: Dictionary = fm.slots[9] # floating_camera
	var bat_node := bat_slot["node"] as Node2D
	var fcam_node := fcam_s["node"] as Node2D
	var bat_pfx := bat_node.get_node_or_null("ProjectileFX") as Node2D
	if bat_pfx != null and (bat_pfx.scale.length() > 0.01 or bat_pfx.modulate.a > 0.01):
		fail("Field bat must hide legacy prefab ProjectileFX so only 1 FX fires, scale=%s mod=%s" % [str(bat_pfx.scale), str(bat_pfx.modulate)])
		return
	if not bool(fcam_node.get("external_projectile_managed")):
		fail("Field floating_camera must have external_projectile_managed=true")
		return

	bat_slot["cooldown_s"] = 2.0
	bat_slot["action_clip"] = ""
	bat_slot["turn_lock_s"] = 0.0
	bat_slot["orbit_phase"] = 0.8
	bat_node.position = Vector2(float(bat_slot["x_home"]), float(bat_slot["y_home"]))
	fcam_s["cooldown_s"] = 2.0
	fcam_s["action_clip"] = ""
	fcam_s["turn_lock_s"] = 0.0
	arena.player_node.position = Vector2(bat_node.position.x + 140.0, 840.0)
	for _warm in range(30):
		await physics_frame
		fm.step(1.0 / 60.0)
	var bat_flips := 0
	var prev_bat_left := bat_node.scale.x < 0.0
	var bat_min_y := bat_node.position.y
	var bat_max_y := bat_node.position.y
	var bat_min_x := bat_node.position.x
	var bat_max_x := bat_node.position.x
	for _fo in range(55):
		await physics_frame
		fm.step(1.0 / 60.0)
		var now_left := bat_node.scale.x < 0.0
		if now_left != prev_bat_left:
			bat_flips += 1
			prev_bat_left = now_left
		bat_min_y = minf(bat_min_y, bat_node.position.y)
		bat_max_y = maxf(bat_max_y, bat_node.position.y)
		bat_min_x = minf(bat_min_x, bat_node.position.x)
		bat_max_x = maxf(bat_max_x, bat_node.position.x)
	if bat_flips > 1:
		fail("Bat must NOT oscillate/turn repeatedly in place during cooldown aggro, flips=%d" % bat_flips)
		return
	if (bat_max_x - bat_min_x) < 10.0 or (bat_max_y - bat_min_y) < 3.0:
		fail("Flying monster must cruise smoothly along circular/elliptical 2D orbit (dx=%s, dy=%s)" % [str(bat_max_x - bat_min_x), str(bat_max_y - bat_min_y)])
		return

	# Check 360-degree projectile rotation: pointed sonic_screech_fx rotates smoothly toward target; spherical electric_orb_fx stays unrotated
	arena.set_hero_immortal(true)
	fm.homing_projectiles.clear()
	fm.call("_spawn_homing_projectile", bat_node, "bat_chiroptera", "sonic_screech_fx", bat_node.position, 2.0, {}, false, 100.0, 0.0)
	fm.step(1.0 / 60.0)
	if fm.homing_projectiles.is_empty():
		fail("Bat homing sonic_screech_fx must spawn")
		return
	var sonic_fx: AnimatedSprite2D = fm.homing_projectiles[0]["sprite"] as AnimatedSprite2D
	if absf(sonic_fx.rotation) < 0.1:
		fail("Pointed sonic_screech_fx firing downward at Drum must rotate toward 360-deg trajectory, rot=%s" % str(sonic_fx.rotation))
		return
	fm.homing_projectiles.clear()
	fm.call("_spawn_homing_projectile", arena.player_node, "drum", "electric_orb_fx", arena.player_node.position, 2.0, bat_slot, true, 400.0, 20.0)
	fm.step(1.0 / 60.0)
	if fm.homing_projectiles.is_empty():
		fail("Drum homing electric_orb_fx must spawn")
		return
	var orb_fx: AnimatedSprite2D = fm.homing_projectiles[0]["sprite"] as AnimatedSprite2D
	if absf(orb_fx.rotation) > 0.001:
		fail("Spherical electric_orb_fx must remain unrotated (rotation=0)")
		return
	arena.set_hero_immortal(false)

	# Verify exact non-box body silhouette & tâm thân (both Hero and Monsters),
	# calligraphic red "X" target animation, double-tap auto-attack, and Hero > Monster Z-layering!
	var trex_slot2: Dictionary = fm.slots[3] # t_rex (ground)
	var trex_node2 := trex_slot2["node"] as Node2D
	var trex_rect: Rect2 = arena.get_fighter_body_rect(trex_node2, "t_rex", float(trex_slot2["scale_val"]))
	var trex_core: Vector2 = arena.get_fighter_core_world_pos(trex_node2, "t_rex", float(trex_slot2["scale_val"]))
	var drum_core: Vector2 = arena.get_fighter_core_world_pos(arena.player_node, "drum", arena.char_scale)
	if not arena.silhouette_contains_point(trex_node2, "t_rex", float(trex_slot2["scale_val"]), trex_core, 0.0):
		fail("T-rex body silhouette must contain its tâm thân core")
		return
	if not arena.silhouette_contains_point(arena.player_node, "drum", arena.char_scale, drum_core, 0.0):
		fail("Drum body silhouette must contain its tâm thân core")
		return
	# Empty top-left corner of T-rex bounding box (above tail) must NOT count as solid body!
	var empty_corner := Vector2(trex_rect.position.x + 2.0, trex_rect.position.y + 2.0)
	if arena.silhouette_contains_point(trex_node2, "t_rex", float(trex_slot2["scale_val"]), empty_corner, 0.0):
		fail("Empty bounding-box corner above T-rex tail must NOT register as solid body hit")
		return

	# Layer priority: Monster (10) < Hero (20) < Boss (30) and overlapping layers allowed
	if trex_node2.z_index != arena.Z_LAYER_MONSTER or arena.player_node.z_index != arena.Z_LAYER_HERO or arena.player_node.z_index <= trex_node2.z_index:
		fail("Layer priority must place Hero (%d) above Monster (%d)" % [arena.player_node.z_index, trex_node2.z_index])
		return

	# Single tap -> selects T-rex & starts transient calligraphic red "X" animation (0.0 -> 0.28s) that later fades out
	if float(fm.pointer_x_visible_s) > 0.001:
		fail("Calligraphic red X must NOT stay visible before touch interaction")
		return
	var tap_res: Dictionary = fm.select_target_at_world_pos(trex_core)
	if not bool(tap_res.get("selected", false)) or fm.pointer_slot_id != str(trex_slot2["id"]) or float(fm.pointer_x_anim_s) > 0.001 or float(fm.pointer_x_visible_s) <= 0.5:
		fail("Single tap must target T-rex and show transient calligraphic red X, got %s" % str(tap_res))
		return
	# Wait 0.90s without further interaction -> calligraphic X must disappear automatically!
	for _xv in range(54):
		fm.step(1.0 / 60.0)
	if float(fm.pointer_x_visible_s) > 0.001:
		fail("Calligraphic red X must disappear after interaction ends, remaining=%s" % str(fm.pointer_x_visible_s))
		return
	# Re-tap then double-tap 260px away -> shows X again & triggers auto-approach attack!
	fm.select_target_at_world_pos(trex_core)
	for _dt_step in range(8):
		fm.step(1.0 / 60.0)
	var pre_trex_hp: float = float(trex_slot2["hp"])
	arena.player_node.position = Vector2(trex_rect.position.x - 260.0, trex_node2.position.y)
	arena.player_vy = 0.0
	fm.hit_impacts.clear()
	fm.floating_texts.clear()
	var dbl_res: Dictionary = fm.select_target_at_world_pos(trex_core)
	if not bool(dbl_res.get("double_tap_attack", false)) or not bool(fm.auto_approach_active) or float(fm.pointer_x_visible_s) <= 0.5:
		fail("Double-tap on target must show X and start auto-approach attack, got %s" % str(dbl_res))
		return
	for _aa in range(180):
		await physics_frame
		fm.step(1.0 / 60.0)
		if float(trex_slot2["hp"]) < pre_trex_hp:
			break
	if float(trex_slot2["hp"]) >= pre_trex_hp:
		fail("Double-tap auto-approach must walk close to target core and deal melee damage")
		return
	if fm.hit_impacts.is_empty() or fm.floating_texts.is_empty() or float(trex_slot2.get("hit_flash_s", 0.0)) <= 0.0:
		fail("Hit feedback FX (impact burst + damage popup + flash) must trigger on hit")
		return
	# Check -40% hit-flash & blink contrast reduction on monster & hero sprites (60% contrast from Color.WHITE)
	var m_flash_spr := trex_node2.get_node_or_null("Sprite") as AnimatedSprite2D
	if m_flash_spr != null:
		fm.call("_apply_hit_flash_modulate", m_flash_spr, true, true, false)
		var m_on: Color = m_flash_spr.modulate
		fm.call("_apply_hit_flash_modulate", m_flash_spr, true, false, false)
		var m_off: Color = m_flash_spr.modulate
		if m_on.g < 0.45 or absf(m_off.g - m_on.g) > 0.28 or m_on.r > 0.82:
			fail("Monster hit-flash & blink contrast must be reduced by 40%%, on=%s off=%s" % [str(m_on), str(m_off)])
			return
	fm.apply_damage_to_player(10.0)
	fm.step(1.0 / 60.0)
	var h_flash_spr := arena.player_node.get_node_or_null("Sprite") as AnimatedSprite2D
	if h_flash_spr != null:
		fm.call("_apply_hit_flash_modulate", h_flash_spr, true, true, true)
		var h_on: Color = h_flash_spr.modulate
		fm.call("_apply_hit_flash_modulate", h_flash_spr, true, false, true)
		var h_off: Color = h_flash_spr.modulate
		if h_on.g < 0.45 or absf(h_off.g - h_on.g) > 0.30 or h_on.r > 0.82:
			fail("Hero hit-flash & blink contrast must be reduced by 40%%, on=%s off=%s" % [str(h_on), str(h_off)])
			return
	# Verify normal ("melee") and heavy ("heavy") collision impact FX metadata + clear duration separation
	fm.hit_impacts.clear()
	fm.call("_spawn_hit_impact_fx", Vector2(3100.0, 820.0), "melee", "-50", Color.YELLOW, Vector2(1.0, 0.0))
	fm.call("_spawn_hit_impact_fx", Vector2(3140.0, 820.0), "heavy", "-70", Color.ORANGE, Vector2(-1.0, 0.0))
	if fm.hit_impacts.size() != 2 or str(fm.hit_impacts[0]["kind"]) != "melee" or str(fm.hit_impacts[1]["kind"]) != "heavy" or float(fm.hit_impacts[1]["duration_s"]) <= float(fm.hit_impacts[0]["duration_s"]):
		fail("Normal & heavy collision FX must register distinct impact kinds and timings: %s" % str(fm.hit_impacts))
		return
	if int(OverheadBarsDrawScript.FLOATING_DAMAGE_FONT_SIZE) != 24 or int(OverheadBarsDrawScript.FLOATING_DAMAGE_OUTLINE_SIZE) != 5:
		fail("Floating damage popup font must stay +20%% larger (24px, outline 5)")
		return

	# Normal attack 0.2s cooldown & anti-mash (no input queueing): finish clip, reject spam during 0.2s, allow after 0.2s
	for _wait_clip in range(60):
		await physics_frame
		arena.step_player_movement(1.0 / 60.0, 0)
		fm.step(1.0 / 60.0)
		if not arena._is_player_action_playing() and float(arena.player_light_cooldown_s) <= 0.0:
			break
	if not fm.request_player_primary_action():
		fail("First normal attack from ready state must succeed (playing=%s cd=%s dead=%s)" % [str(arena._is_player_action_playing()), str(arena.player_light_cooldown_s), str(fm.player_dead)])
		return
	if fm.request_player_primary_action() or arena.player_node.has_meta(&"_arena_queued_action"):
		fail("Mashing normal attack during active clip must be rejected without queueing")
		return
	for _finish_clip in range(60):
		await physics_frame
		arena.step_player_movement(1.0 / 60.0, 0)
		fm.step(1.0 / 60.0)
		if not arena._is_player_action_playing():
			break
	# One extra movement step transitions _player_light_clip_active -> 0.2s cooldown right when clip ends
	arena.step_player_movement(1.0 / 60.0, 0)
	if float(arena.player_light_cooldown_s) <= 0.14 or fm.request_player_primary_action():
		fail("Normal attack must enforce 0.2s recovery cooldown after finishing clip, cd=%s" % str(arena.player_light_cooldown_s))
		return
	for _cd_step in range(15):
		await physics_frame
		arena.step_player_movement(1.0 / 60.0, 0)
		fm.step(1.0 / 60.0)
	if float(arena.player_light_cooldown_s) > 0.001 or not fm.request_player_primary_action():
		fail("Normal attack must become ready again once 0.2s cooldown expires, cd=%s" % str(arena.player_light_cooldown_s))
		return

	# Skill-vs-Skill clash: player power_up orb cuts enemy projectile with clash FX + explosion
	fm.homing_projectiles.clear()
	fm.hit_impacts.clear()
	fm._explosion_nodes.clear()
	fm.call("_spawn_homing_projectile", arena.player_node, "drum", "electric_orb_fx", Vector2(3000.0, 760.0), 2.5, trex_slot2, true, 400.0, 20.0)
	fm.call("_spawn_homing_projectile", trex_node2, "t_rex", "fireball_fx", Vector2(3015.0, 760.0), 1.75, {}, false, 100.0, 0.0)
	fm.step(1.0 / 60.0)
	var saw_clash := false
	for imp in fm.hit_impacts:
		if str(imp.get("kind", "")) == "clash":
			saw_clash = true
			break
	if not saw_clash or fm._explosion_nodes.is_empty():
		fail("Colliding player & enemy skill projectiles must trigger a 'clash' impact + explosion FX")
		return

	# === BOSS MAP DRUM EVENT TESTS ===
	# 1) 5' initial timer must pause/reset while no Hero exists in map, then spawn after 300s with Hero present.
	arena.set_field_hero_visible(false)
	fm.start_field(false)
	for _nb in range(32):
		fm.step(10.0)
	if not fm.boss_slot.is_empty() or absf(fm.boss_spawn_timer_s - 300.0) > 0.1:
		fail("Boss Drum must NOT spawn or count down 5' timer when no Hero exists in map (timer=%.1f)" % fm.boss_spawn_timer_s)
		return
	arena.set_field_hero_visible(true)
	fm.set_player_immortal(false)
	for _hb in range(29):
		fm.step(10.0)
	fm.step(9.0)
	if not fm.boss_slot.is_empty() and bool(fm.boss_slot.get("alive", false)):
		fail("Boss Drum must not spawn before Hero reaches 300s (5') in map (timer=%.2f)" % fm.boss_spawn_timer_s)
		return
	fm.step(1.5)
	if fm.slots.size() != 14 or fm.boss_slot.is_empty() or not bool(fm.boss_slot.get("alive", false)):
		fail("Boss Drum must spawn after 5' with Hero while preserving 14 normal slots")
		return
	var bnode0 := fm.boss_slot.get("node") as Node2D
	if bnode0 == null or bnode0.name != "FieldBoss_drum" or bnode0.z_index != arena.Z_LAYER_BOSS or absf(bnode0.scale.y - 2.5) > 0.01:
		fail("Boss Drum visual identity/scale/z_index mismatch: name=%s z=%d scale=%s" % [str(bnode0.name if bnode0 else ""), int(bnode0.z_index if bnode0 else -1), str(bnode0.scale if bnode0 else Vector2.ZERO)])
		return
	if absf(float(fm.boss_slot["max_hp"]) - 5000.0) > 0.1 or absf(float(fm.boss_slot["max_stamina"]) - 200.0) > 0.1:
		fail("Boss Drum stats mismatch: hp=%.1f stam=%.1f" % [float(fm.boss_slot["max_hp"]), float(fm.boss_slot["max_stamina"])])
		return

	# 2) Entry Teleport from far random spawn (~5900px) -> right beside Hero + shoulder attack_light (120 dmg)
	fm.start_field(false)
	arena.set_field_hero_visible(true)
	fm.set_player_immortal(false)
	arena.player_node.position = Vector2(400.0, float(arena.call("_ground_y_at", 400.0)))
	var hp_before_boss: float = fm.player_hp
	var bs: Dictionary = fm.spawn_boss_drum(5900.0)
	if bs.is_empty() or str(bs.get("action_clip", "")) != "teleport":
		fail("Boss Drum spawn must immediately initiate entry 'teleport' clip toward Hero")
		return
	var bnode := bs["node"] as Node2D
	for _tp_f in range(36):
		fm.step(1.0 / 60.0)
	if absf(bnode.position.x - arena.player_node.position.x) > 360.0:
		fail("Boss Drum entry teleport must relocate from 5900px beside Hero (~400px), got x=%.1f" % bnode.position.x)
		return
	for _melee_f in range(36):
		fm.step(1.0 / 60.0)
	if absf(fm.player_hp - (hp_before_boss - 120.0)) > 0.1 and fm.player_hp > hp_before_boss - 119.0:
		fail("Boss Drum post-teleport light attack must deal 120 damage, hp before=%.1f after=%.1f" % [hp_before_boss, fm.player_hp])
		return

	# 3) UtilityAI ranged power_up (220 dmg) at 200..400px & global pursuit >400px
	fm.homing_projectiles.clear()
	var b_ai: UtilityAIController = bs["ai"] as UtilityAIController
	b_ai.cooldown_remaining = 0.0
	b_ai.set_meta(&"drum_phase", "engaged")
	bs["action_clip"] = ""
	bs["action_timer_s"] = 0.0
	arena.player_node.position = Vector2(bnode.position.x + 360.0, float(arena.call("_ground_y_at", bnode.position.x + 360.0)))
	fm.step(1.0 / 60.0)
	if str(bs.get("action_clip", "")) != "power_up":
		fail("Boss Drum UtilityAI at ~360px center distance must cast 'power_up', got '%s'" % str(bs.get("action_clip", "")))
		return
	var saw_boss_orb := false
	for _pw_f in range(60):
		fm.step(1.0 / 60.0)
		for pr in fm.homing_projectiles:
			if not bool(pr.get("is_player", true)) and absf(float(pr.get("damage", 0.0)) - 220.0) < 0.1:
				saw_boss_orb = true
	if not saw_boss_orb:
		fail("Boss Drum power_up must launch homing electric_orb_fx dealing 220 damage")
		return

	arena.player_node.position = Vector2(3300.0, float(arena.call("_ground_y_at", 3300.0)))
	bs["action_clip"] = ""
	bs["action_timer_s"] = 0.0
	fm._boss_teleport_chase_cd_s = 0.0
	for _ch_f in range(40):
		fm.step(1.0 / 60.0)
	if absf(bnode.position.x - arena.player_node.position.x) > 400.0:
		fail("Boss Drum must globally pursue & teleport to Hero at x=3300 (>400px away), got x=%.1f" % bnode.position.x)
		return

	# 4) Manual HUD summon button & Boss KO -> 100% Dragon Ball drop + 30' (1800s) respawn cooldown
	if DisplayServer.get_name() != "headless" and (arena.boss_spawn_button == null or arena.boss_spawn_button.text != "⚡ Gọi Boss Drum"):
		fail("ArenaSandbox must expose '⚡ Gọi Boss Drum' manual test button")
		return
	arena.enable_field_mode(true, true)
	var b_manual: Dictionary = arena.spawn_boss_drum_now()
	if b_manual.is_empty() or not bool(b_manual.get("alive", false)):
		fail("spawn_boss_drum_now() button helper must spawn alive Boss Drum")
		return
	await process_frame
	if "Boss Drum:" not in arena.hud_label.text:
		fail("HUD must show alive Boss Drum HP status, got '%s'" % arena.hud_label.text)
		return

	var drops_before: int = arena._dropped_item_nodes.size()
	fm.apply_damage_to_slot(fm.boss_slot, 5000.0, 20.0)
	if bool(fm.boss_slot.get("alive", true)) or absf(fm.boss_respawn_timer_s - 1800.0) > 0.1:
		fail("Defeated Boss Drum must set alive=false and 1800s (30') respawn timer (got %.1f)" % fm.boss_respawn_timer_s)
		return
	if arena._dropped_item_nodes.size() <= drops_before:
		fail("Defeated Boss Drum must drop Dragon Ball at 100%% rate")
		return
	for _cd30 in range(179):
		fm.step(10.0)
	if bool(fm.boss_slot.get("alive", false)):
		fail("Boss Drum must NOT respawn before 1800s (30') elapsed (rem=%.1f)" % fm.boss_respawn_timer_s)
		return
	fm.step(12.0)
	if not bool(fm.boss_slot.get("alive", false)):
		fail("Boss Drum must respawn once 1800s (30') elapsed with Hero in map")
		return

	arena.enable_field_mode(false, false)
	await process_frame

	# Verify 360-degree continuous analog vector flight on flying character (Pteranodon) without affecting Drum
	arena.select_character("pteranodon")
	await process_frame
	var fly_start: Vector2 = arena.player_node.position
	var ang_vec := Vector2(cos(0.65), sin(0.65))
	for _fv in range(20):
		arena.step_player_movement(1.0 / 60.0, 1, 0, false, false, false, ang_vec)
	var fly_delta: Vector2 = arena.player_node.position - fly_start
	if fly_delta.x <= 15.0 or fly_delta.y <= 10.0:
		fail("Flying fighter must support smooth 360-degree multi-axis analog flight, delta=%s" % str(fly_delta))
		return

	var verified_roster_count: int = arena.roster_characters.size()
	arena.queue_free()
	await process_frame
	print("[OK] Godot 4 ArenaSandbox 1920x1080 1:1 parity + Utility AI + %d characters PASSED!" % verified_roster_count)
	quit(0)
