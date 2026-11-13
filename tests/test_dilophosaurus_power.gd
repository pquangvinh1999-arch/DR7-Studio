extends SceneTree

func _init() -> void:
	call_deferred("run_test")

func run_test() -> void:
	var packed = load("res://scenes/Dilophosaurus.tscn") as PackedScene
	if packed == null:
		printerr("[FAIL] Cannot load Dilophosaurus prefab")
		quit(1)
		return
	var fighter = packed.instantiate()
	root.add_child(fighter)
	await process_frame
	var body = fighter.get_node("Sprite") as AnimatedSprite2D
	body.stop()
	body.animation = &"power_up"
	var fx = fighter.get_node("SlashFX") as AnimatedSprite2D
	var hits := [12, 31, 50]
	var names := [&"air_slash_a_fx", &"air_slash_b_fx", &"air_slash_c_fx"]
	var visible_ticks := 0
	for tick in range(88):
		fighter.render_power_tick(float(tick))
		var expected := -1
		for i in range(3):
			if tick >= hits[i] and tick < hits[i] + 6:
				expected = i
		if expected < 0:
			if fx.visible:
				printerr("[FAIL] Unexpected slash at tick%d" % tick)
				quit(1)
				return
		else:
			visible_ticks += 1
			if not fx.visible or fx.animation != names[expected] or fx.frame != tick - hits[expected] or fx.position != Vector2(144, -56):
				printerr("[FAIL] Slash phase/position at tick%d" % tick)
				quit(1)
				return
	fighter.set_slash_target_canvas(Vector2(280, 150))
	fighter.render_power_tick(31.0)
	if fx.position != Vector2(104, -74):
		printerr("[FAIL] Target canvas override ignored")
		quit(1)
		return
	fighter.position = Vector2(50, 10)
	fighter.scale.x = -1.0
	fighter.set_slash_target_global(Vector2(100, 30))
	fighter.render_power_tick(50.0)
	if fx.global_position.distance_to(Vector2(100, 30)) > 0.001:
		printerr("[FAIL] Global enemy target changes with facing")
		quit(1)
		return
	print("[OK] Dilophosaurus88ticks,3slashes x6ticks at12/31/50,same target; canvas/global target override including facing verified; visible_ticks=%d" % visible_ticks)
	fighter.queue_free()
	quit(0)
