extends SceneTree
var hits: Array = []

func _init() -> void:
	call_deferred("run_test")

func fail(message: String) -> void:
	printerr("[FAIL] Chilopoda: ", message)
	quit(1)

func run_test() -> void:
	var fighter = load("res://scenes/Chilopoda.tscn").instantiate()
	root.add_child(fighter)
	await process_frame
	fighter.set_process(false)
	fighter.set_physics_process(false)
	fighter.combat_hit.connect(func(kind: String, amount: int, target: Vector2): hits.append([kind, amount, target]))
	var body = fighter.get_node("Sprite") as AnimatedSprite2D
	for sign_value in [1.0, -1.0]:
		fighter.global_position = Vector2(100, 0)
		fighter.scale.x = sign_value
		fighter.set_combat_target_global(Vector2(100+sign_value*128, 0))
		fighter.play_clip(&"attack_light")
		body.pause()
		hits.clear()
		var hidden := 0
		for tick in range(90):
			fighter.render_action_tick("attack_light", float(tick))
			if tick >= 24 and tick < 54:
				hidden += 1
				if body.visible:
					fail("body visible during hidden30ticks")
					return
			elif not body.visible:
				fail("body unexpectedly hidden")
				return
			if tick >= 54 and absf(fighter.global_position.x-(100+sign_value*80)) > 0.001:
				fail("emergence target depends on wrong facing")
				return
			if tick < 69 and not hits.is_empty():
				fail("bite damage emitted before impact")
				return
		if hidden != 30 or hits.size() != 1 or hits[0][0] != "burrow_bite":
			fail("hidden interval/bite one-shot mismatch")
			return
		fighter._on_skill_finished(&"attack_light")
		if body.animation != &"idle" or absf(fighter.global_position.x-(100+sign_value*80)) > 0.001:
			fail("did not stay at target and recover idle")
			return
		fighter.global_position = Vector2(100, 0)
		fighter.set_combat_target_global(Vector2(100+sign_value*128, 0))
		fighter.play_clip(&"power_up")
		body.pause()
		hits.clear()
		fighter.render_action_tick("power_up", 15.0)
		if fighter.lasers[0].visible or fighter.lasers[1].visible or not fighter.glows[0].visible or not fighter.glows[1].visible:
			fail("dual antenna charge phase invalid")
			return
		fighter.render_action_tick("power_up", 16.0)
		if not fighter.lasers[0].visible or not fighter.lasers[1].visible or fighter.lasers[0].position == fighter.lasers[1].position:
			fail("two bolts did not release from distinct antenna tips")
			return
		fighter.render_action_tick("power_up", 41.0)
		fighter.render_action_tick("power_up", 41.5)
		if fighter.lasers[0].visible or fighter.lasers[1].visible or hits.size() != 2:
			fail("bolts did not disappear/emit exactlytwo hits")
			return
	# Burrow turn commits facing only during the fully hidden interval, at both endpoints.
	fighter.scale.x = 1.0
	fighter.global_position = Vector2(7, 0)
	fighter.start_patrol(0, 8)
	fighter.advance_patrol(1.0)
	if not fighter._turn_pending or fighter.scale.x < 0:
		fail("right endpoint flipped before turn")
		return
	for tick in range(36):
		fighter.render_action_tick("turn", float(tick))
		if body.visible == (tick >= 16 and tick < 22):
			fail("turn hidden window invalid")
			return
		if (fighter.scale.x < 0) != (tick >= 16):
			fail("right-to-left facing must commit only while hidden")
			return
		if absf(fighter.global_position.x-8.0) > 0.001:
			fail("turn relocated at right endpoint")
			return
	fighter._on_skill_finished(&"turn")
	if fighter.scale.x >= 0 or body.animation != &"walk":
		fail("right endpoint did not reverse after turn")
		return
	fighter.advance_patrol(1.0)
	if not fighter._turn_pending or fighter.scale.x > 0:
		fail("left endpoint did not start reverse burrow turn")
		return
	for tick in range(36):
		fighter.render_action_tick("turn", float(tick))
		if body.visible == (tick >= 16 and tick < 22):
			fail("reverse turn hidden window invalid")
			return
		if (fighter.scale.x > 0) != (tick >= 16):
			fail("left-to-right facing must commit only while hidden")
			return
		if absf(fighter.global_position.x) > 0.001:
			fail("turn relocated at left endpoint")
			return
	fighter._on_skill_finished(&"turn")
	if fighter.scale.x <= 0 or body.animation != &"walk":
		fail("left endpoint did not resume rightwalk")
		return
	print("[OK] Chilopoda:90tickburrow/30hidden/staytarget,42tickdualredlasers/disappear,mirroredtargets,bothendpointturnandreversal verified")
	fighter.free()
	quit(0)
