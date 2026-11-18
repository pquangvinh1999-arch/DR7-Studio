extends SceneTree

func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed: PackedScene = load("res://scenes/FloatingCamera.tscn")
	if packed == null:
		printerr("FLOATING_CAMERA_PREFAB_FAIL")
		quit(1)
		return
	var camera := packed.instantiate() as CharacterFighter2D
	root.add_child(camera)
	await process_frame
	var body := camera.get_node("Sprite") as AnimatedSprite2D
	var projectile := camera.get_node("ProjectileFX") as AnimatedSprite2D
	if body == null or projectile == null or body.offset != Vector2(-96, -112) or body.texture_filter != CanvasItem.TEXTURE_FILTER_NEAREST:
		printerr("FLOATING_CAMERA_BODY_FAIL")
		quit(1)
		return
	var frames := body.sprite_frames
	if frames.get_frame_count(&"idle") != 8 or frames.get_frame_count(&"walk") != 8:
		printerr("FLOATING_CAMERA_IDLE_COUNT_FAIL")
		quit(1)
		return
	for i in range(8):
		if frames.get_frame_texture(&"idle", i) != frames.get_frame_texture(&"walk", i) or frames.get_frame_duration(&"idle", i) != frames.get_frame_duration(&"walk", i):
			printerr("FLOATING_CAMERA_IDLE_PARITY_FAIL frame=", i)
			quit(1)
			return
	camera.position = Vector2(500, 300)
	camera.play_clip(&"idle")
	await create_timer(0.14).timeout
	if camera.position != Vector2(500, 300) or body.frame == 0:
		printerr("FLOATING_CAMERA_IDLE_HOVER_FAIL frame=", body.frame, " pos=", camera.position)
		quit(1)
		return
	if not camera.play_clip(&"attack_light"):
		printerr("FLOATING_CAMERA_ATTACK_FAIL")
		quit(1)
		return
	await create_timer(0.24).timeout
	if not projectile.visible or projectile.global_position.x <= 521.0:
		printerr("FLOATING_CAMERA_PROJECTILE_FAIL visible=", projectile.visible, " x=", projectile.global_position.x)
		quit(1)
		return
	# Returning to idle after attack_light must keep active projectile flying forward until lifetime expires.
	var proj_x_before_idle := projectile.global_position.x
	camera.play_clip(&"idle")
	if not camera.set_facing_left(true) or camera.scale.x >= 0.0:
		printerr("FLOATING_CAMERA_FACING_FAIL")
		quit(1)
		return
	await create_timer(0.08).timeout
	if not projectile.visible or projectile.global_position.x <= proj_x_before_idle:
		printerr("FLOATING_CAMERA_PROJECTILE_PERSIST_FAIL visible=", projectile.visible, " x=", projectile.global_position.x)
		quit(1)
		return
	camera.play_clip(&"hit")
	await create_timer(0.18).timeout
	if body.animation != &"ko":
		printerr("FLOATING_CAMERA_EXPLOSION_FAIL clip=", body.animation)
		quit(1)
		return
	await create_timer(0.50).timeout
	if body.visible:
		printerr("FLOATING_CAMERA_KO_HIDE_FAIL")
		quit(1)
		return
	camera.play_clip(&"idle")
	if not body.visible:
		printerr("FLOATING_CAMERA_RESET_VISIBLE_FAIL")
		quit(1)
		return
	print("FLOATING_CAMERA_ACTIONS_OK body=70x74 idle=walk_poses_without_translation source_forward=+X projectile=+X persist_after_idle hit->ko")
	camera.queue_free()
	quit(0)
