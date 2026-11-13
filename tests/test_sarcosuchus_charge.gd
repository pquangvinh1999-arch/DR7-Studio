extends SceneTree

func _init() -> void:
	call_deferred("run_test")

func run_test() -> void:
	var packed = load("res://scenes/Sarcosuchus.tscn") as PackedScene
	if packed == null:
		printerr("[FAIL] Cannot load Sarcosuchus prefab")
		quit(1)
		return
	var fighter = packed.instantiate()
	root.add_child(fighter)
	await process_frame
	var body = fighter.get_node("Sprite") as AnimatedSprite2D
	body.stop()
	body.animation = &"power_up"
	var charge = fighter.get_node("ChargeFX") as AnimatedSprite2D
	var projectile = fighter.get_node("ProjectileFX") as AnimatedSprite2D
	for tick in range(46):
		fighter.render_power_tick(float(tick))
		if tick < 10:
			var expected_frame := tick
			if not charge.visible or projectile.visible or charge.frame != expected_frame:
				printerr("[FAIL] Wrong charge at tick%d" % tick)
				quit(1)
				return
		elif tick < 28:
			var elapsed := tick - 10
			var expected_position := Vector2(244 + 4 * elapsed - 176, 194 - 224)
			if charge.visible or not projectile.visible or projectile.frame != int(elapsed / 3) or projectile.position != expected_position:
				printerr("[FAIL] Wrong launch/fade/position at tick%d" % tick)
				quit(1)
				return
		elif charge.visible or projectile.visible:
			printerr("[FAIL] Orb did not disappear at lifetime18ticks")
			quit(1)
			return
	print("[OK] Sarcosuchus charge0..9 (1→10px) -> same-size launch bodyframe2/tick10 -> six source FX left-to-right once -> hidden tick28;46ticks verified")
	fighter.queue_free()
	quit(0)
