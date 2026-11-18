extends SceneTree
## Headless Godot 4 verification for 1x (32x32) Dragon Ball items:
## - Diagonal full-body shine sweep @ 60Hz, hidden in bag mode
## - Map hide/show toggle button
## - Monster death drop (+10px jump -> fall -> +10px roll -> sheen starts)
## - Collector pickup flight shrinking to player center


func fail(msg: String) -> void:
	printerr("[FAIL] " + msg)
	quit(1)


func _init() -> void:
	call_deferred("run_test")


func run_test() -> void:
	var sf: SpriteFrames = load("res://assets/items/dragon_balls/godot/dragon_balls.tres")
	if sf == null:
		fail("Unable to load dragon_balls.tres")
		return

	for n in range(1, 8):
		var cname := StringName("ball_%02d" % n)
		if not sf.has_animation(cname):
			fail("Missing ball animation: " + String(cname))
			return
		var btex: Texture2D = sf.get_frame_texture(cname, 0)
		if btex == null or btex.get_size() != Vector2(32.0, 32.0):
			fail("Dragon ball 1x size must be 32x32 for " + String(cname))
			return

	var expected_durs := [3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 4.0, 50.0]
	if sf.get_frame_count(&"sparkle_fx") != expected_durs.size():
		fail("Diagonal sheen sparkle_fx must contain 8 frames")
		return
	for j in range(expected_durs.size()):
		if not is_equal_approx(sf.get_frame_duration(&"sparkle_fx", j), expected_durs[j]):
			fail("sparkle_fx tick mismatch at frame %d" % j)
			return

	var item_packed: PackedScene = load("res://scenes/items/DragonBallItem2D.tscn")
	var item := item_packed.instantiate()
	root.add_child(item)
	await process_frame

	if item.texture_filter != CanvasItem.TEXTURE_FILTER_NEAREST:
		fail("DragonBallItem2D must enforce Nearest texture_filter")
		return
	item.call("set_display_mode", "map")
	item.call("set_ball_number", 7)
	var mm: Dictionary = item.call("get_item_metrics")
	if mm["body_clip"] != "ball_07" or mm["body_offset"] != [-16.0, -32.0] or not bool(mm["sparkle_visible"]):
		fail("Map resting item must show ball_07 + sheen FX: " + str(mm))
		return

	# Bag hides effect completely (icon only)
	item.call("set_display_mode", "bag")
	item.call("set_ball_number", 3)
	var bm: Dictionary = item.call("get_item_metrics")
	if bm["body_clip"] != "ball_03" or bm["body_offset"] != [-16.0, -16.0] or bool(bm["sparkle_visible"]):
		fail("Bag item must hide sparkle_fx completely: " + str(bm))
		return
	item.queue_free()

	var arena_packed: PackedScene = load("res://scenes/ArenaSandbox.tscn")
	var arena := arena_packed.instantiate()
	root.add_child(arena)
	await process_frame

	# 1. Verify Arena toggle hide/show button & API
	if not bool(arena.call("get_item_drop_metrics")["enabled"]):
		fail("Arena items should start visible for test")
		return
	var after_hide := bool(arena.call("toggle_dropped_items_visible"))
	if after_hide:
		fail("Toggle must hide items")
		return
	var after_show := bool(arena.call("toggle_dropped_items_visible"))
	if not after_show:
		fail("Second toggle must re-show items")
		return

	# Clear static preview, then test Monster Death Drop (+10px jump -> fall -> +10px roll -> sheen ON)
	arena.call("set_item_drop_preview", true, 1, 1.0)
	arena.call("_clear_dropped_items")
	var dropped: Node2D = arena.call("trigger_monster_death_drop", 5)
	var spawn_x := dropped.position.x
	var ground_y := float(arena.get("ground_y"))
	var min_y := dropped.position.y
	var land_x := spawn_x
	var saw_fall := false
	var saw_roll := false
	var sheen_during_drop := false
	var step_dt := 1.0 / 60.0

	for _tick in range(50):
		arena.call("step_dropped_items", step_dt)
		var st_m: Dictionary = dropped.call("get_item_metrics")
		min_y = minf(min_y, dropped.position.y)
		if st_m["lifecycle_state"] == "dropping":
			if bool(st_m["sparkle_visible"]):
				sheen_during_drop = true
			if st_m["drop_subphase"] == "fall":
				saw_fall = true
				land_x = dropped.position.x
			elif st_m["drop_subphase"] == "roll":
				saw_roll = true
		elif st_m["lifecycle_state"] == "resting":
			break

	if sheen_during_drop:
		fail("Sheen FX must NOT activate until after drop + 10px roll completes")
		return
	if absf((ground_y - min_y) - 10.0) > 0.35:
		fail("Drop must jump up ~10px, got rise=%.3f" % (ground_y - min_y))
		return
	if not saw_fall or not saw_roll:
		fail("Drop did not pass through both fall and roll phases")
		return
	var resting_m: Dictionary = dropped.call("get_item_metrics")
	if resting_m["lifecycle_state"] != "resting" or not bool(resting_m["sparkle_visible"]):
		fail("Item must rest and start sheen FX after rolling: " + str(resting_m))
		return
	var rolled_dist := absf(dropped.position.x - land_x)
	if rolled_dist < 8.0 or rolled_dist > 13.5:
		fail("Post-landing roll must move ~10px (got %.2f)" % rolled_dist)
		return

	# 2. Test Collector Pickup: flies to player torso & shrinks monotonically until absorbed
	var started := int(arena.call("pickup_dropped_items"))
	if started != 1:
		fail("Expected 1 dropped ball to begin pickup, got " + str(started))
		return
	var prev_scale := dropped.scale.x
	var shrunk_monotonically := true
	var still_collecting_at_24 := false
	for _t2 in range(36):
		arena.call("step_dropped_items", step_dt)
		var pm: Dictionary = dropped.call("get_item_metrics")
		if _t2 == 23 and pm["lifecycle_state"] == "collecting":
			still_collecting_at_24 = true
		if pm["lifecycle_state"] == "collecting":
			if bool(pm["sparkle_visible"]):
				fail("Sheen FX should disable during collect flight")
				return
			if dropped.scale.x > prev_scale + 0.0001:
				shrunk_monotonically = false
			prev_scale = dropped.scale.x
		elif pm["lifecycle_state"] == "collected":
			break
	if not still_collecting_at_24:
		fail("20% slower pickup (30 ticks) must still be collecting at tick 24")
		return
	if not shrunk_monotonically or dropped.scale.x >= 0.15:
		fail("Collecting ball must monotonically shrink toward collector, final scale=%.3f" % dropped.scale.x)
		return
	var final_m: Dictionary = arena.call("get_item_drop_metrics")
	if not final_m["collected_bag_balls"].has(5):
		fail("Collected ball #5 missing from ArenaSandbox collected_bag_balls: " + str(final_m))
		return

	arena.queue_free()
	print("[OK] DragonBallItem2D (diagonal sheen + bag hides FX + hide/show toggle + 10px drop/roll + shrink pickup) PASSED!")
	quit(0)
