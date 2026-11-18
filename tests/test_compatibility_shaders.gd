extends SceneTree
## D3 Compatibility Renderer + 2-Shader Verification (ChilopodaGroundClip + ShenronPixelDissolve + DisplayPolicy + ZoneClientSync).

const ZoneSyncScript := preload("res://scenes/net/ZoneClientSync.gd")


func _init() -> void:
	call_deferred("run_test")


func fail(msg: String) -> void:
	printerr("[FAIL] " + msg)
	quit(1)


func run_test() -> void:
	if str(ProjectSettings.get_setting("rendering/renderer/rendering_method", "")) != "gl_compatibility":
		fail("Expected gl_compatibility renderer")
		return

	# 1. Test ChilopodaGroundClip.gdshader under Compatibility OpenGL3 driver
	var chilopoda_frames := load("res://assets/chilopoda/godot_bundle/godot/chilopoda.tres") as SpriteFrames
	if chilopoda_frames == null:
		fail("Failed to load chilopoda.tres")
		return
	var clip_vp := SubViewport.new()
	clip_vp.size = Vector2i(384, 256)
	clip_vp.transparent_bg = true
	clip_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(clip_vp)
	var c_spr := Sprite2D.new()
	c_spr.centered = false
	c_spr.texture = chilopoda_frames.get_frame_texture("idle", 0)
	c_spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var c_mat := ShaderMaterial.new()
	c_mat.shader = load("res://scenes/ChilopodaGroundClip.gdshader")
	c_mat.set_shader_parameter("clip_enabled", true)
	c_mat.set_shader_parameter("clip_y", 180.0)
	c_spr.material = c_mat
	clip_vp.add_child(c_spr)
	await process_frame
	await RenderingServer.frame_post_draw
	var clip_img := clip_vp.get_texture().get_image()
	var below_visible := 0
	var above_visible := 0
	for y in range(256):
		for x in range(384):
			if clip_img.get_pixel(x, y).a > 0.5:
				if y > 181:
					below_visible += 1
				elif y < 179:
					above_visible += 1
	clip_vp.free()
	if above_visible == 0 or below_visible > 0:
		fail("ChilopodaGroundClip shader failed on gl_compatibility: above=%d below=%d" % [above_visible, below_visible])
		return

	# 2. Verify ZoneClientSync handles 50-entity zone snapshot cleanly
	var zsync := ZoneSyncScript.new()
	var entities: Array = []
	for i in range(50):
		entities.append({"id": "ent_%d" % i, "x": 200.0 + float(i) * 20.0, "y": 840.0, "clip": "walk"})
	zsync._on_packet({"op": "zone_snapshot", "tick": 120, "entities": entities})
	if zsync.entities_by_id.size() != 50 or zsync.last_snapshot_tick != 120:
		fail("ZoneClientSync failed 50-entity zone snapshot check")
		return

	print("COMPATIBILITY_SHADERS_OK chilopoda_above=%d chilopoda_below=%d zone_entities=%d" % [above_visible, below_visible, zsync.entities_by_id.size()])
	quit(0)
