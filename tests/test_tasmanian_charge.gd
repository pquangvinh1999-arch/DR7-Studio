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
	# Unlocked bidirectional horizontal flip WITHOUT needing a separate perspective turn clip
	if fighter.is_facing_locked() or fighter.default_spawn_facing() != "right" or fighter.get_facing_name() != "right" or fighter.scale.x <= 0.0:
		printerr("[FAIL] Crab must spawn unlocked with default right (+X) facing")
		quit(1)
		return
	if not fighter.move_in_direction(-1, &"walk") or fighter.scale.x >= 0.0 or body.animation != &"walk" or fighter.get_facing_name() != "left":
		printerr("[FAIL] Crab failed horizontal flip + walk when moving left without turn clip")
		quit(1)
		return
	if not fighter.move_in_direction(1, &"walk") or fighter.scale.x <= 0.0 or body.animation != &"walk" or fighter.get_facing_name() != "right":
		printerr("[FAIL] Crab failed horizontal flip + walk when moving right without turn clip")
		quit(1)
		return
	if not fighter.set_facing_left(true) or fighter.scale.x >= 0.0 or bool(fighter.get("_turn_pending")):
		printerr("[FAIL] Crab must flip left via set_facing_left without waiting on missing turn clip")
		quit(1)
		return
	fighter.render_power_tick(24.0)
	if charge.visible or not projectile.visible or projectile.position != Vector2(267 - 176, 157 - 224) or fighter.scale.x >= 0.0:
		printerr("[FAIL] Crab flipped left must still launch ProjectileFX in mirrored -X direction")
		quit(1)
		return
	fighter.respawn(Vector2(520.0, 0.0), "left")
	if fighter.get_facing_name() != "left" or fighter.scale.x >= 0.0 or body.animation != &"idle":
		printerr("[FAIL] Crab did not apply explicit left facing on respawn")
		quit(1)
		return
	if not fighter.move_in_direction(1, &"walk") or fighter.scale.x <= 0.0 or fighter.get_facing_name() != "right":
		printerr("[FAIL] Left-respawned crab failed horizontal flip right when moving right")
		quit(1)
		return
	fighter.start_patrol(80.0, 880.0, 200.0, &"walk")
	fighter.position.x = 875.0
	fighter.step_patrol(0.1)
	if fighter.position.x < 879.999 or fighter.scale.x >= 0.0 or body.animation != &"walk":
		printerr("[FAIL] Crab patrol failed max_x bounce flip left")
		quit(1)
		return
	fighter.position.x = 85.0
	fighter.step_patrol(0.1)
	if fighter.position.x > 80.001 or fighter.scale.x <= 0.0 or body.animation != &"walk":
		printerr("[FAIL] Crab patrol failed min_x bounce flip right")
		quit(1)
		return
	fighter.stop_patrol()
	fighter.respawn(Vector2(280.0, 0.0))
	if fighter.get_facing_name() != "right" or fighter.scale.x <= 0.0:
		printerr("[FAIL] Default respawn did not restore default right (+X) facing")
		quit(1)
		return
	var sarco_packed = load("res://scenes/Sarcosuchus.tscn") as PackedScene
	if sarco_packed == null:
		printerr("[FAIL] Cannot load Sarcosuchus prefab to verify shared script compatibility")
		quit(1)
		return
	var sarco = sarco_packed.instantiate()
	root.add_child(sarco)
	await process_frame
	if sarco.is_facing_locked() or not sarco.set_facing_left(true):
		printerr("[FAIL] Shared TasmanianFighter2D script broke Sarcosuchus set_facing_left()")
		quit(1)
		return
	sarco._on_skill_finished(&"turn")
	if sarco.scale.x >= 0.0:
		printerr("[FAIL] Shared TasmanianFighter2D script broke Sarcosuchus turn commit scale.x")
		quit(1)
		return
	sarco.queue_free()
	print("[OK] Tasmanian unlocked horizontal flip (no turn clip), left-flipped power_up launch, patrol endpoints, and Sarcosuchus compatibility verified")
	fighter.queue_free()
	quit(0)
