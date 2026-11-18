extends SceneTree
const Ritual := preload("res://scenes/ShenronSummon2D.gd")
func fail(message: String) -> void:
	printerr("[FAIL] " + message)
	quit(1)
func _init() -> void:
	call_deferred("run_test")
func run_test() -> void:
	var ritual := Ritual.new()
	ritual.manual_clock = true
	root.add_child(ritual)
	await process_frame
	if not ritual.start_from(Vector2(560, 650)):
		fail("Ritual start failed")
		return
	if ritual.start_from(Vector2.ZERO):
		fail("Duplicate call must not restart an active ritual")
		return
	for index in range(7):
		var before := ritual.sample_state(float(index * 18) - 1.0)
		var launched := ritual.sample_state(float(index * 18))
		if before["balls"][index]["visible"] or not launched["balls"][index]["visible"]:
			fail("Wrong numeric launch order at item " + str(index + 1))
			return
	var gathered := ritual.sample_state(162.0)
	for item in ritual.config["items"]:
		var index := int(item["number"]) - 1
		var off: Array = item["formation_offset_px"]
		var expected := Vector2(960.0 + float(off[0]), 540.0 + float(off[1]))
		if gathered["balls"][index]["position"].distance_to(expected) > 0.01:
			fail("Gather layout drift")
			return
	if ritual.sample_state(227.0)["ground_alpha"] != 0.0 or ritual.sample_state(246.0)["dragon_alpha"] != 0.0 or ritual.sample_state(246.0)["ground_alpha"] != 0.0:
		fail("Ground/dragon must remain hidden before Flash #2 starts")
		return
	var flash1 := ritual.sample_state(230.0)
	if flash1["flash_alpha"] != 1.0 or flash1["ground_alpha"] != 0.0 or flash1["dragon_alpha"] != 0.0:
		fail("Flash #1 must be white without leaking ground/dragon")
		return
	if ritual.sample_state(240.0)["flash_alpha"] != 0.0 or ritual.sample_state(240.0)["ground_alpha"] != 0.0 or ritual.sample_state(240.0)["dragon_alpha"] != 0.0:
		fail("Two flashes need a clean dark interval before Flash #2")
		return
	var flash2_peak := ritual.sample_state(250.0)
	if flash2_peak["flash_alpha"] != 1.0 or flash2_peak["ground_alpha"] != 1.0 or flash2_peak["dragon_alpha"] <= 0.5:
		fail("Ground cluster (1.0) and Shenron dissolve must be past 50% at Flash #2 peak")
		return
	var flash2_fade := ritual.sample_state(254.0)
	if absf(float(flash2_fade["flash_alpha"]) - 0.5) > 0.001 or flash2_fade["ground_alpha"] != 1.0 or flash2_fade["dragon_alpha"] <= 0.85:
		fail("Flash #2 clearing must immediately expose ground=1.0 and nearly complete dissolve dragon")
		return
	var flash2_done := ritual.sample_state(256.0)
	if flash2_done["flash_alpha"] != 0.0 or flash2_done["ground_alpha"] != 1.0 or flash2_done["dragon_alpha"] < 0.97:
		fail("Flash #2 ending must immediately reveal >=97% of Shenron with zero post-flash wait")
		return
	if ritual.sample_state(258.0)["flash_alpha"] != 0.0 or ritual.sample_state(258.0)["ground_alpha"] != 1.0 or ritual.sample_state(258.0)["dragon_alpha"] != 1.0:
		fail("Shenron dissolve and ground cluster must both be 100% locked by tick 258")
		return
	for at_tick in range(250, 600):
		if ritual.sample_state(float(at_tick))["glow_alpha"] < 0.78:
			fail("Ground aura must remain luminous while ground cluster & dragon are present")
			return
	ritual.seek_tick(252.0)
	if absf(float(ritual.dissolve_material.get_shader_parameter("progress")) - 0.75) > 0.0001 or ritual.dragon.modulate.a != 1.0:
		fail("Reveal must use pixel threshold ease_out_quad at full body alpha, not global fade")
		return
	if ritual.dissolve_material.get_shader_parameter("canvas_anchor") != Vector2(192.0, 240.0) or ritual.dissolve_material.get_shader_parameter("mask_size") != Vector2(96.0, 68.0) or ritual.dissolve_material.get_shader_parameter("cell_size") != 4.0:
		fail("Dissolve shader anchor/mask/cell contract parameters mismatch")
		return
	var partial_position := ritual.dragon.position
	ritual.seek_tick(258.0)
	if ritual.dissolve_material.get_shader_parameter("progress") != 1.0 or partial_position != ritual.dragon.position:
		fail("Dissolve must fill in place and finish fully visible")
		return
	var ready := ritual.sample_state(258.0)
	var ground: Rect2 = ready["ground_rect"]
	if ground.size.x != 144.0 or absf(ground.end.y - 840.0) > 0.01 or ritual.dragon.position.x != 960.0 or not ritual.dragon.visible:
		fail("Ground/dragon placement mismatch")
		return
	if ritual.dragon.scale != Vector2(2.76, 2.76) or ritual.dragon_sprite.texture_filter != CanvasItem.TEXTURE_FILTER_NEAREST:
		fail("Dragon scale/filter drift")
		return
	ritual.seek_tick(10000.0)
	if not ritual.active or not ritual.dragon.visible:
		fail("Summon must persist until dismissed")
		return
	ritual.dismiss()
	if ritual.active or ritual.dragon.visible or not ritual.start_from(Vector2(800, 600)):
		fail("Dismiss/replay failed")
		return
	var trace: Array = []
	ritual.origin = Vector2(560, 650)
	for at_tick in [0,18,27,54,108,162,210,219,228,230,240,246,247,248,250,252,254,256,257,258,266,284,330,10000]:
		var sample := ritual.sample_state(float(at_tick))
		var trace_balls: Array = []
		for ball in sample["balls"]:
			var pos: Vector2 = ball["position"]
			trace_balls.append({"number":ball["number"],"visible":ball["visible"],"alpha":ball["alpha"],"position":[pos.x,pos.y]})
		var rect: Rect2 = sample["ground_rect"]
		var dragon_pos: Vector2 = sample["dragon_position"]
		trace.append({"reveal_top":sample["reveal_top"],"flash_alpha":sample["flash_alpha"],"tick":at_tick,"phase":sample["phase"],"balls":trace_balls,"ground_rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y],"ground_alpha":sample["ground_alpha"],"glow_alpha":sample["glow_alpha"],"dragon_position":[dragon_pos.x,dragon_pos.y],"dragon_alpha":sample["dragon_alpha"],"dragon_frame":sample["dragon_frame"]})
	var dismiss_trace: Array = []
	for d_tick in [0, 2, 6, 10, 14, 18, 19, 20, 22, 24, 26, 28]:
		var ds := ritual.sample_dismiss_state(float(d_tick), 258.0)
		var dp: Vector2 = ds["dragon_position"]
		dismiss_trace.append({"tick":d_tick,"flash_alpha":ds["flash_alpha"],"phase":ds["phase"],"ground_alpha":ds["ground_alpha"],"glow_alpha":ds["glow_alpha"],"dragon_position":[dp.x,dp.y],"dragon_alpha":ds["dragon_alpha"],"dragon_frame":ds["dragon_frame"],"elements_visible":ds["elements_visible"],"finished":ds["finished"]})
	if ritual.sample_dismiss_state(2.0, 258.0)["flash_alpha"] != 1.0 or not ritual.sample_dismiss_state(14.0, 258.0)["elements_visible"]:
		fail("Dismiss Flash #1 and dark interval must keep Shenron & ground visible")
		return
	if ritual.sample_dismiss_state(20.0, 258.0)["flash_alpha"] != 1.0 or ritual.sample_dismiss_state(20.0, 258.0)["elements_visible"] or ritual.sample_dismiss_state(24.0, 258.0)["dragon_alpha"] != 0.0:
		fail("Dismiss Flash #2 peak must hide Shenron & ground cleanly")
		return
	if ritual.sample_dismiss_state(28.0, 258.0)["flash_alpha"] != 0.0 or not ritual.sample_dismiss_state(28.0, 258.0)["finished"]:
		fail("Dismiss Flash #2 must clear completely at tick 28")
		return
	ritual.seek_tick(258.0)
	if not ritual.is_ready_for_wish() or ritual.select_wish("heal_full").is_empty() or not ritual.dismissing:
		fail("Selecting wish after summon ready must auto-start 2-flash dismiss")
		return
	for _step in range(30):
		ritual.seek_dismiss_tick(ritual.dismiss_tick + 1.0)
		if ritual.dismiss_tick >= 28.0:
			ritual.dismiss()
			break
	if ritual.active or ritual.dragon.visible:
		fail("2-flash dismiss sequence must finish inactive with hidden dragon")
		return
	print("SHENRON_SUMMON_TRACE=" + JSON.stringify(trace))
	print("SHENRON_DISMISS_TRACE=" + JSON.stringify(dismiss_trace))
	ritual.free()
	print("[OK] Summon: numeric1..7 flights, source layout, ground144px@840, Shenron2.76@center, wish-menu, 2-flash dismiss, replay")
	quit(0)
