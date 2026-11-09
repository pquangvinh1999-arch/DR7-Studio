extends SceneTree
## Vòng lặp kiểm thử tự động Engine (Godot 4.7.2 Headless) cho TOÀN BỘ nhân vật trong assets/roster.json:
## - Đọc động 100% từ roster.json (không gán cứng ID nhân vật).
## - Chỉ kiểm định kiến trúc chuẩn duy nhất: Gộp Chung 1 Lớp Nguyên Bản (Combined 1-Layer).
## - Xác minh nạp SpriteFrames .tres, Texture2D Atlas, lọc mẫu Nearest (filter=1), tâm chân offset == -anchor_px và Prefab .tscn.

func _init() -> void:
	var roster_path := "res://assets/roster.json"
	var rf := FileAccess.open(roster_path, FileAccess.READ)
	if rf == null:
		printerr("[FAIL] Không mở được ", roster_path)
		quit(1)
		return

	var roster = JSON.parse_string(rf.get_as_text())
	if typeof(roster) != TYPE_DICTIONARY or not roster.has("characters"):
		printerr("[FAIL] roster.json sai cấu trúc")
		quit(1)
		return

	var chars: Array = roster["characters"]
	if chars.is_empty():
		var fighter_script: GDScript = load("res://scenes/CharacterFighter2D.gd")
		var anim_script: GDScript = load("res://tests/SkillAnimator2D.gd")
		if fighter_script == null or anim_script == null:
			printerr("[FAIL] Không nạp được CharacterFighter2D.gd hoặc SkillAnimator2D.gd")
			quit(1)
			return
		var fighter_inst = fighter_script.new()
		if fighter_inst == null or not fighter_inst.has_method("play_clip"):
			printerr("[FAIL] CharacterFighter2D.gd thiếu API play_clip")
			quit(1)
			return
		fighter_inst.free()
		var assets_dir := DirAccess.open("res://assets")
		if assets_dir != null:
			assets_dir.list_dir_begin()
			var entry := assets_dir.get_next()
			while entry != "":
				if assets_dir.current_is_dir() and not entry.begins_with("."):
					printerr("[FAIL] Phát hiện thư mục nhân vật dư thừa trong assets/ khi roster rỗng: ", entry)
					assets_dir.list_dir_end()
					quit(1)
					return
				entry = assets_dir.get_next()
			assets_dir.list_dir_end()
		print("[OK] Roster rỗng (0 nhân vật) — Đã kiểm chứng CharacterFighter2D.gd & SkillAnimator2D.gd sẵn sàng nhận Atlas mới.")
		quit(0)
		return

	var failures := 0
	for ch in chars:
		var cid: String = ch.get("character_id", "")
		var modes: Dictionary = ch.get("modes", {})
		if modes.has("layered_3d_depth"):
			printerr("[FAIL] Nhân vật %s vẫn còn cấu hình layered_3d_depth đã bị loại bỏ theo Hiến pháp!" % cid)
			failures += 1
			continue

		var c1: Dictionary = modes.get("combined_1layer", {})
		var bid: String = c1.get("bundle_id", "")
		var prefab_path: String = c1.get("godot_prefab", "")
		var base_dir := "res://assets/%s/godot_bundle" % bid
		var tres_path := "%s/godot/%s.tres" % [base_dir, bid]
		var tscn_path := "%s/godot/%s.tscn" % [base_dir, bid]
		var export_path := "%s/engine-export.json" % base_dir

		var ef := FileAccess.open(export_path, FileAccess.READ)
		if ef == null:
			printerr("[FAIL] Thiếu engine-export.json: ", export_path)
			failures += 1
			continue
		var export_meta: Dictionary = JSON.parse_string(ef.get_as_text())
		var anchor: Array = export_meta.get("anchor_px", [0.0, 0.0])
		var exp_off := Vector2(-float(anchor[0]), -float(anchor[1]))

		var sf: SpriteFrames = load(tres_path)
		if sf == null:
			printerr("[FAIL] Không nạp được SpriteFrames: ", tres_path)
			failures += 1
			continue

		var anim_names := sf.get_animation_names()
		for req_clip in export_meta.get("clips", {}).keys():
			if not anim_names.has(req_clip):
				printerr("[FAIL] %s thiếu clip đã khai báo trong roster.json: %s" % [cid, req_clip])
				failures += 1
				continue
			var fcnt := sf.get_frame_count(req_clip)
			if fcnt <= 0:
				printerr("[FAIL] %s clip %s có 0 frame" % [cid, req_clip])
				failures += 1
				continue
			var tex := sf.get_frame_texture(req_clip, 0)
			if tex == null or tex.get_width() <= 0 or tex.get_height() <= 0:
				printerr("[FAIL] %s clip %s lỗi nạp Texture2D" % [cid, req_clip])
				failures += 1
				continue
			var clip_meta: Dictionary = export_meta.get("clips", {}).get(req_clip, {})
			var expected_durations: Array = clip_meta.get("godot", {}).get("relative_durations", [])
			var frame_size: Array = export_meta.get("frame_size", [0, 0])
			if not is_equal_approx(sf.get_animation_speed(req_clip), 60.0) or expected_durations.size() != fcnt:
				printerr("[FAIL] %s:%s timing metadata không khớp 60Hz" % [cid, req_clip])
				failures += 1
			for frame_idx in range(fcnt):
				var frame_tex: Texture2D = sf.get_frame_texture(req_clip, frame_idx)
				if frame_tex == null or frame_tex.get_size() != Vector2(frame_size[0], frame_size[1]):
					printerr("[FAIL] %s:%s frame %d sai texture/canvas" % [cid, req_clip, frame_idx])
					failures += 1
				if frame_idx < expected_durations.size() and not is_equal_approx(sf.get_frame_duration(req_clip, frame_idx), float(expected_durations[frame_idx])):
					printerr("[FAIL] %s:%s frame %d sai duration tick" % [cid, req_clip, frame_idx])
					failures += 1
			print("[OK] %s -> %s frames=%d loop=%s speed=%.1f" % [
				bid, req_clip, fcnt, str(sf.get_animation_loop(req_clip)), sf.get_animation_speed(req_clip)
			])

		var raw_packed: PackedScene = load(tscn_path)
		if raw_packed == null:
			printerr("[FAIL] Không nạp được raw scene: ", tscn_path)
			failures += 1
			continue
		var raw_inst := raw_packed.instantiate() as AnimatedSprite2D
		if raw_inst == null:
			printerr("[FAIL] %s không phải AnimatedSprite2D" % tscn_path)
			failures += 1
			continue
		if raw_inst.centered:
			printerr("[FAIL] %s centered phải bằng false để dùng offset tâm chân chính xác" % tscn_path)
			failures += 1
		if raw_inst.offset.distance_to(exp_off) > 0.05:
			printerr("[FAIL] %s lệch offset %s so với -anchor_px %s" % [tscn_path, str(raw_inst.offset), str(exp_off)])
			failures += 1
		if raw_inst.texture_filter != CanvasItem.TEXTURE_FILTER_NEAREST:
			printerr("[FAIL] %s chưa bật TEXTURE_FILTER_NEAREST (1)" % tscn_path)
			failures += 1
		print("[OK] %s AnimatedSprite2D centered=%s offset=%s filter=%d" % [
			bid, str(raw_inst.centered), str(raw_inst.offset), raw_inst.texture_filter
		])
		raw_inst.free()

		var prefab_packed: PackedScene = load(prefab_path)
		if prefab_packed == null:
			printerr("[FAIL] Không nạp được Prefab chính thức: ", prefab_path)
			failures += 1
			continue
		var prefab_inst := prefab_packed.instantiate()
		root.add_child(prefab_inst)
		if not prefab_inst.has_method("play_clip") or not prefab_inst.play_clip(&"idle"):
			printerr("[FAIL] Prefab %s không chạy được play_clip('idle')" % prefab_path)
			failures += 1
		print("[OK] Combined 1-Layer Prefab verified: %s (%d clips)" % [prefab_path, anim_names.size()])
		prefab_inst.free()

	if failures > 0:
		printerr("[FAIL] Tổng số lỗi kiểm định Godot 4: ", failures)
		quit(1)
		return

	quit(0)
