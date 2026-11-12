extends SceneTree

func _init() -> void:
	var meta = JSON.parse_string(FileAccess.get_file_as_string("res://godot_bundle/engine-export.json"))
	var sf: SpriteFrames = load("res://godot_bundle/godot/spinosaurus.tres")
	assert(sf != null, "SpriteFrames must load")
	var total := 0
	for name in meta.clips:
		var clip = meta.clips[name]
		assert(sf.has_animation(name), name)
		assert(sf.get_animation_speed(name) == 60.0, name + " speed")
		assert(sf.get_frame_count(name) == clip.frames.size(), name + " count")
		for i in range(sf.get_frame_count(name)):
			var tex := sf.get_frame_texture(name, i) as AtlasTexture
			assert(tex != null and tex.atlas != null, name + " texture")
			assert(tex.region.size == Vector2(384, 256), name + " canvas")
			assert(sf.get_frame_duration(name, i) == float(clip.godot.relative_durations[i]), name + " tick")
			total += 1
		print("[OK] spinosaurus %s: %d frames @60Hz" % [name, sf.get_frame_count(name)])
	assert(total == 71, "71 source frames")
	assert(meta.atlas.pages.size() == 1, "one atlas page")
	for record in meta.files:
		assert(FileAccess.get_sha256("res://godot_bundle/" + record.path) == record.sha256, record.path + " hash")
	var scene: PackedScene = load("res://godot_bundle/godot/spinosaurus.tscn")
	var node := scene.instantiate() as AnimatedSprite2D
	assert(node != null and not node.centered, "raw scene")
	assert(node.offset == Vector2(-176, -224), "anchor")
	assert(node.texture_filter == CanvasItem.TEXTURE_FILTER_NEAREST, "Nearest")
	node.free()
	print("[OK] Spinosaurus standalone: 71 frames / 9 clips, 60Hz ticks, atlas rect/hash, Nearest, anchor.")
	quit(0)
