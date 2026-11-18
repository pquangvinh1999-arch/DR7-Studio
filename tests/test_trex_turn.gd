extends SceneTree

func fail(msg: String) -> void:
	printerr("[FAIL] " + msg)
	quit(1)

func _init() -> void:
	call_deferred("run_test")

func run_test() -> void:
	var scene := load("res://scenes/TRex.tscn") as PackedScene
	if scene == null:
		fail("Unable to load res://scenes/TRex.tscn")
		return
	var node := scene.instantiate()
	root.add_child(node)
	await process_frame

	var sprite := node.get_node("Sprite") as AnimatedSprite2D
	if sprite == null or sprite.sprite_frames == null:
		fail("Missing Sprite or SpriteFrames")
		return
	if sprite.offset != Vector2(-176.0, -224.0):
		fail("Wrong Sprite offset: " + str(sprite.offset))
		return
	if sprite.texture_filter != CanvasItem.TEXTURE_FILTER_NEAREST:
		fail("Wrong texture filter: " + str(sprite.texture_filter))
		return
	if not sprite.sprite_frames.has_animation(&"turn"):
		fail("Missing turn clip on TRex SpriteFrames")
		return
	if sprite.sprite_frames.get_frame_count(&"turn") != 5:
		fail("Expected 5 turn frames, got " + str(sprite.sprite_frames.get_frame_count(&"turn")))
		return
	if sprite.sprite_frames.get_animation_loop(&"turn"):
		fail("turn clip must not loop")
		return
	var expected_ticks := [6.0, 3.0, 3.0, 3.0, 6.0]
	for i in range(5):
		var dur := sprite.sprite_frames.get_frame_duration(&"turn", i)
		if dur != expected_ticks[i]:
			fail("Unexpected turn tick duration at frame %d: %s" % [i, str(dur)])
			return

	# Verify existing legacy actions still load cleanly
	for legacy_clip in [&"idle", &"walk", &"run", &"attack_light", &"attack_heavy", &"power_up", &"hit", &"ko", &"fireball_fx"]:
		if not sprite.sprite_frames.has_animation(legacy_clip):
			fail("Missing legacy clip: " + String(legacy_clip))
			return

	# Right -> Left endpoint turn check (walk -> turn -> walk)
	if not node.start_patrol(80.0, 880.0, 55.0, &"walk"):
		fail("start_patrol failed for walk")
		return
	node.position.x = 876.0
	node.step_patrol(0.1)
	if node.position.x != 880.0 or not node.is_turning() or sprite.animation != &"turn":
		fail("Right endpoint did not trigger clamped turn: x=%s turning=%s anim=%s" % [str(node.position.x), str(node.is_turning()), str(sprite.animation)])
		return
	if node.is_facing_left():
		fail("Facing flipped prematurely before turn finished (R->L)")
		return
	if node.play_clip(&"idle") or node.set_facing_left(false):
		fail("Allowed illegal interruption during pending turn")
		return
	sprite.animation_finished.emit()
	if not node.is_facing_left() or node.is_turning() or sprite.animation != &"walk":
		fail("R->L turn did not commit left facing + resume walk: left=%s turning=%s anim=%s" % [str(node.is_facing_left()), str(node.is_turning()), str(sprite.animation)])
		return

	# Left -> Right endpoint turn check (walk -> turn -> walk)
	node.position.x = 83.0
	node.step_patrol(0.1)
	if node.position.x != 80.0 or not node.is_turning() or sprite.animation != &"turn":
		fail("Left endpoint did not trigger clamped turn: x=%s turning=%s anim=%s" % [str(node.position.x), str(node.is_turning()), str(sprite.animation)])
		return
	if not node.is_facing_left():
		fail("Facing flipped prematurely before turn finished (L->R)")
		return
	sprite.animation_finished.emit()
	if node.is_facing_left() or node.is_turning() or sprite.animation != &"walk":
		fail("L->R turn did not commit right facing + resume walk: left=%s turning=%s anim=%s" % [str(node.is_facing_left()), str(node.is_turning()), str(sprite.animation)])
		return

	# Run patrol endpoint check + manual bidirectional reversal check (run -> turn -> run)
	if not node.start_patrol(80.0, 880.0, 108.0, &"run"):
		fail("start_patrol failed for run")
		return
	node.position.x = 876.0
	node.step_patrol(0.1)
	if not node.is_turning() or sprite.animation != &"turn" or node.is_facing_left():
		fail("Run patrol right endpoint failed to hold facing during turn")
		return
	sprite.animation_finished.emit()
	if not node.is_facing_left() or sprite.animation != &"run":
		fail("Run patrol R->L turn did not resume run facing left")
		return
	node.position.x = 84.0
	node.step_patrol(0.1)
	if not node.is_turning() or sprite.animation != &"turn" or not node.is_facing_left():
		fail("Run patrol left endpoint failed to hold -X facing during L->R turn")
		return
	sprite.animation_finished.emit()
	if node.is_facing_left() or sprite.animation != &"run":
		fail("Run patrol L->R turn did not resume run facing right")
		return

	node.stop_patrol()
	if not node.move_in_direction(-1, &"walk") or not node.is_turning():
		fail("Manual bidirectional move_in_direction (-1) reversal failed")
		return
	sprite.animation_finished.emit()
	if not node.is_facing_left() or sprite.animation != &"walk":
		fail("Manual reversal did not finish facing left in walk")
		return
	if not node.move_in_direction(1, &"run") or not node.is_turning():
		fail("Manual bidirectional move_in_direction (+1, run) reversal failed")
		return
	sprite.animation_finished.emit()
	if node.is_facing_left() or sprite.animation != &"run":
		fail("Manual reversal did not finish facing right in run")
		return

	print("[OK] TRex turn: 5 perspective frames [6,3,3,3,6], lock during spin, R->L & L->R two-endpoint walk/run transitions verified")
	quit(0)
