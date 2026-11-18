extends SceneTree
## Run with xvfb-run / compatibility renderer: checks the real GPU shader on both Sprite2D and Shenron.tscn AnimatedSprite2D.
func _init() -> void:
	call_deferred("run_test")
func run_test() -> void:
	var contract: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/rituals/shenron_summon/sequence.json"))
	var mask_tex := load("res://" + str(contract["reveal"]["mask"])) as Texture2D
	var mask := mask_tex.get_image()
	var frames := load("res://assets/shenron/godot_bundle/godot/shenron.tres") as SpriteFrames
	var source := frames.get_frame_texture("idle", 0).get_image()

	var viewport := SubViewport.new()
	viewport.size = Vector2i(384, 272)
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var sprite := Sprite2D.new()
	sprite.texture = frames.get_frame_texture("idle", 0)
	sprite.centered = false
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var material := ShaderMaterial.new()
	material.shader = load("res://scenes/ShenronPixelDissolve.gdshader")
	material.set_shader_parameter("canvas_anchor", Vector2.ZERO)
	material.set_shader_parameter("mask_size", Vector2(float(contract["reveal"]["mask_size_px"][0]), float(contract["reveal"]["mask_size_px"][1])))
	material.set_shader_parameter("cell_size", float(contract["reveal"]["cell_size_canvas_px"]))
	material.set_shader_parameter("edge_width", float(contract["reveal"]["edge_width"]))
	var rgb: Array = contract["reveal"]["edge_color_rgb"]
	material.set_shader_parameter("edge_color", Color(float(rgb[0])/255.0, float(rgb[1])/255.0, float(rgb[2])/255.0))
	material.set_shader_parameter("threshold_mask", mask_tex)
	sprite.material = material
	viewport.add_child(sprite)

	var results: Array = []
	for progress in [0.0, 0.25, 0.5, 0.75, 1.0]:
		material.set_shader_parameter("progress", progress)
		await process_frame
		await RenderingServer.frame_post_draw
		var rendered := viewport.get_texture().get_image()
		var visible := 0
		var mismatches := 0
		for y in range(272):
			for x in range(384):
				var threshold := (roundf(mask.get_pixel(x / 4, y / 4).r * 255.0) + 0.5) / 256.0
				var expected := source.get_pixel(x, y).a > 0.0 and float(progress) >= threshold
				var actual := rendered.get_pixel(x, y).a > 0.5
				if actual: visible += 1
				if actual != expected: mismatches += 1
		results.append({"progress":progress,"visible_pixels":visible,"mask_mismatches":mismatches})
		DirAccess.make_dir_recursive_absolute(OS.get_user_data_dir() + "/dissolve_evidence")
		rendered.save_png("user://dissolve_evidence/native-" + str(progress) + ".png")
		if mismatches > 0:
			printerr("[FAIL] Real dissolve shader mask drift: " + JSON.stringify(results))
			quit(1)
			return
	viewport.free()

	# Also verify the real Shenron.tscn AnimatedSprite2D (centered=false, offset=(-192,-240)) under ShenronSummon2D shader setup.
	var dragon_vp := SubViewport.new()
	dragon_vp.size = Vector2i(384, 272)
	dragon_vp.transparent_bg = true
	dragon_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(dragon_vp)
	var dragon := (load("res://scenes/Shenron.tscn") as PackedScene).instantiate() as Node2D
	dragon.position = Vector2(192, 240)
	dragon_vp.add_child(dragon)
	var dragon_sprite := dragon.get_node("Sprite") as AnimatedSprite2D
	dragon_sprite.stop()
	dragon_sprite.animation = &"idle"
	dragon_sprite.frame = 0
	var prefab_mat := material.duplicate() as ShaderMaterial
	prefab_mat.set_shader_parameter("canvas_anchor", -dragon_sprite.offset)
	prefab_mat.set_shader_parameter("progress", 0.5)
	dragon_sprite.material = prefab_mat
	await process_frame
	await RenderingServer.frame_post_draw
	var prefab_img := dragon_vp.get_texture().get_image()
	var prefab_mismatches := 0
	var prefab_visible := 0
	for y in range(272):
		for x in range(384):
			var threshold := (roundf(mask.get_pixel(x / 4, y / 4).r * 255.0) + 0.5) / 256.0
			var expected := source.get_pixel(x, y).a > 0.0 and 0.5 >= threshold
			var actual := prefab_img.get_pixel(x, y).a > 0.5
			if actual: prefab_visible += 1
			if actual != expected: prefab_mismatches += 1
	dragon_vp.free()
	if prefab_mismatches > 0 or prefab_visible != 14936:
		printerr("[FAIL] Shenron.tscn AnimatedSprite2D dissolve drift: visible=%d mismatches=%d" % [prefab_visible, prefab_mismatches])
		quit(1)
		return

	print("DISSOLVE_RENDER_TRACE=" + JSON.stringify(results))
	print("PREFAB_DISSOLVE_HALF_OK visible=%d mismatches=%d" % [prefab_visible, prefab_mismatches])
	quit(0)
