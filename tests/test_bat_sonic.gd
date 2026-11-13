extends SceneTree

func _init() -> void:
	call_deferred("run_test")

func run_test() -> void:
	var fighter = load("res://scenes/BatChiroptera.tscn").instantiate()
	root.add_child(fighter)
	await process_frame
	var body = fighter.get_node("Sprite") as AnimatedSprite2D
	var fx = fighter.get_node("ProjectileFX") as AnimatedSprite2D
	if not fighter.play_clip(&"power_up"):
		printerr("[FAIL] Bat sonic action unavailable")
		quit(1)
		return
	body.pause()
	if fx.visible:
		printerr("[FAIL] Sonic wave started before release")
		quit(1)
		return
	body.frame = 1
	if fx.visible:
		printerr("[FAIL] Sonic wave started in anticipation frame1")
		quit(1)
		return
	body.frame = 2
	fx.pause()
	if not fx.visible or fx.animation != &"sonic_screech_fx" or fx.frame != 0:
		printerr("[FAIL] Sonic wave did not release at bodyframe2/tick10")
		quit(1)
		return
	if fx.offset != Vector2(-127, -176):
		printerr("[FAIL] Sonic origin and pivot do not match contract")
		quit(1)
		return
	var duration := 0.0
	for i in range(7):
		duration += fx.sprite_frames.get_frame_duration(&"sonic_screech_fx", i)
	if duration != 14.0 or fx.sprite_frames.get_animation_speed(&"sonic_screech_fx") != 60.0:
		printerr("[FAIL] Sonic seven phases do not total14ticks/60Hz")
		quit(1)
		return
	fighter._on_projectile_finished()
	if fx.visible:
		printerr("[FAIL] Sonic wave remains visible after completion")
		quit(1)
		return
	print("[OK] Bat sonic: anticipation hidden, release bodyframe2/tick10, 7x2ticks at60Hz, contract mouth offset, completion hidden")
	fighter.free()
	quit(0)
