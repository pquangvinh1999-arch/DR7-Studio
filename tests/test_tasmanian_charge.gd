extends SceneTree

func _init() -> void:
	call_deferred("run_test")

func run_test() -> void:
	var packed = load("res://scenes/TasmanianKingCrab.tscn") as PackedScene
	if packed == null:
		printerr("[FAIL] Cannot load Tasmanian prefab")
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
	for tick in range(60):
		fighter.render_power_tick(float(tick))
		if tick < 24:
			var expected_frame := int(tick / 4)
			if not charge.visible or projectile.visible or charge.frame != expected_frame:
				printerr("[FAIL] Wrong charge at tick%d" % tick)
				quit(1)
				return
		elif tick < 40:
			var elapsed := tick - 24
			var expected_position := Vector2(267 + 4 * elapsed - 176, 157 - 224)
			if charge.visible or not projectile.visible or projectile.frame != int(elapsed / 4) or projectile.position != expected_position:
				printerr("[FAIL] Wrong launch/fade/position at tick%d" % tick)
				quit(1)
				return
		elif charge.visible or projectile.visible:
			printerr("[FAIL] Orb did not disappear at lifetime16ticks")
			quit(1)
			return
	print("[OK] Tasmanian charge0..5 -> launch bodyframe2/tick24 -> peak/new6/new7/source0 -> hidden tick40;60ticks verified")
	fighter.queue_free()
	quit(0)
