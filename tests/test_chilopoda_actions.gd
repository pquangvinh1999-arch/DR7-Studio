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
		var dust_saw_scaled := false
		for tick in range(90):
			fighter.render_action_tick("attack_light", float(tick))
			if fighter.dust_sprite.visible:
				if not fighter.dust_sprite.scale.is_equal_approx(Vector2(2.65, 2.65)):
					fail("burrow dust FX scale expected 2.65x, got %s" % [str(fighter.dust_sprite.scale)])
					return
				dust_saw_scaled = true
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
		if hidden != 30 or not dust_saw_scaled or hits.size() != 1 or hits[0][0] != "burrow_bite":
			fail("hidden interval/dust scale/bite one-shot mismatch")
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
		fighter.render_action_tick("power_up", 0.0)
		var charge_area: int = fighter.fireball_sprite.sprite_frames.get_frame_texture(&"fireball_fx", fighter.fireball_sprite.frame).get_image().get_used_rect().get_area()
		fighter.render_action_tick("power_up", 15.0)
		var fb_mid_charge: int = fighter.fireball_sprite.frame
		if not fighter.fireball_sprite.visible or fb_mid_charge > 2:
			fail("mouth fireball charge phase invalid: visible=%s frame=%d" % [str(fighter.fireball_sprite.visible), fb_mid_charge])
			return
		fighter.render_action_tick("power_up", 16.0)
		var release_pos: Vector2 = fighter.fireball_sprite.position
		fighter.render_action_tick("power_up", 24.0)
		var flight_area: int = fighter.fireball_sprite.sprite_frames.get_frame_texture(&"fireball_fx", fighter.fireball_sprite.frame).get_image().get_used_rect().get_area()
		if not fighter.fireball_sprite.visible or fighter.fireball_sprite.frame < 3 or fighter.fireball_sprite.position.x <= release_pos.x or flight_area <= charge_area:
			fail("mouth fireball did not launch/grow: vis=%s frame=%d release=%s pos=%s area0=%d area24=%d" % [
				str(fighter.fireball_sprite.visible), fighter.fireball_sprite.frame, str(release_pos), str(fighter.fireball_sprite.position),
				charge_area, flight_area
			])
			return
		fighter.render_action_tick("power_up", 41.0)
		fighter.render_action_tick("power_up", 41.5)
		if fighter.fireball_sprite.visible or hits.size() != 1 or str(hits[0][0]) != "fireball" or int(hits[0][1]) != 250:
			fail("fireball did not disappear/emit single 250 hit: visible=%s hits=%s" % [str(fighter.fireball_sprite.visible), str(hits)])
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
	print("[OK] Chilopoda:90tickburrow/30hidden/staytarget,42tickmouthfireball/250hit/disappear,mirroredtargets,bothendpointturnandreversal verified")
	fighter.free()
	quit(0)
