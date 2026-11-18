class_name OverheadBarsDraw
extends RefCounted
## Draws crisp rounded pill HP / Mana / Stamina bars matching the Owner's reference sample,
## plus the animated Target Pointer chevron above the selected monster / item / NPC.

const FLOATING_DAMAGE_FONT_SIZE := 24
const FLOATING_DAMAGE_OUTLINE_SIZE := 5


static func draw_pill_bar(canvas: CanvasItem, rect: Rect2, ratio: float, fill_color: Color, track_color: Color) -> void:
	var r := clampf(ratio, 0.0, 1.0)
	var radius := rect.size.y * 0.5
	var sb_track := StyleBoxFlat.new()
	sb_track.bg_color = track_color
	sb_track.set_corner_radius_all(int(ceilf(radius)))
	canvas.draw_style_box(sb_track, rect)
	if r > 0.005:
		var fill_w := maxf(rect.size.y, rect.size.x * r)
		fill_w = minf(rect.size.x, fill_w)
		var sb_fill := StyleBoxFlat.new()
		sb_fill.bg_color = fill_color
		sb_fill.set_corner_radius_all(int(ceilf(radius)))
		canvas.draw_style_box(sb_fill, Rect2(rect.position, Vector2(fill_w, rect.size.y)))


static func draw_player_bars(canvas: CanvasItem, center_x: float, top_y: float, hp: float, max_hp: float, mana: float, max_mana: float) -> void:
	var bar_w := 124.0
	var hp_h := 16.0
	var mana_h := 9.0
	var gap := 4.0
	var x0 := center_x - bar_w * 0.5
	var hp_rect := Rect2(x0, top_y - hp_h - mana_h - gap, bar_w, hp_h)
	var mana_rect := Rect2(x0, top_y - mana_h, bar_w, mana_h)
	var white_track := Color(0.98, 0.99, 1.0, 0.96)
	draw_pill_bar(canvas, hp_rect, hp / maxf(1.0, max_hp), Color(0.0, 0.93, 0.04, 1.0), white_track)
	draw_pill_bar(canvas, mana_rect, mana / maxf(1.0, max_mana), Color(0.0, 0.68, 0.96, 1.0), white_track)
	var font := ThemeDB.fallback_font
	if font != null:
		var txt := "%d/%d" % [int(ceilf(maxf(0.0, hp))), int(round(max_hp))]
		canvas.draw_string(font, Vector2(x0, hp_rect.position.y - 4.0), txt, HORIZONTAL_ALIGNMENT_CENTER, bar_w, 15, Color(0.98, 1.0, 0.98, 0.98))


static func draw_enemy_bars(canvas: CanvasItem, center_x: float, top_y: float, hp: float, max_hp: float, stamina: float, max_stamina: float, stunned: bool = false, label_txt: String = "", is_boss: bool = false) -> void:
	var bar_w := 152.0 if is_boss else 116.0
	var hp_h := 17.0 if is_boss else 14.0
	var stam_h := 9.0 if is_boss else 8.0
	var gap := 3.0
	var x0 := center_x - bar_w * 0.5
	var hp_rect := Rect2(x0, top_y - hp_h - stam_h - gap, bar_w, hp_h)
	var stam_rect := Rect2(x0, top_y - stam_h, bar_w, stam_h)
	var hp_col := Color(0.95, 0.08, 0.08, 1.0) if is_boss else Color(0.92, 0.15, 0.15, 1.0)
	draw_pill_bar(canvas, hp_rect, hp / maxf(1.0, max_hp), hp_col, Color(0.98, 0.99, 1.0, 0.95))
	var stam_fill := Color(0.98, 0.72, 0.18, 1.0) if stunned else Color(0.93, 0.94, 0.97, 0.96)
	var stam_track := Color(0.18, 0.22, 0.30, 0.85)
	draw_pill_bar(canvas, stam_rect, stamina / maxf(1.0, max_stamina), stam_fill, stam_track)
	var font := ThemeDB.fallback_font
	if font != null:
		if is_boss:
			var boss_name := label_txt if not label_txt.is_empty() else "Drum"
			if stunned:
				boss_name += " [STUN]"
			var name_pos := Vector2(x0 - 24.0, hp_rect.position.y - 6.0)
			canvas.draw_string_outline(font, name_pos, boss_name, HORIZONTAL_ALIGNMENT_CENTER, bar_w + 48.0, 18, 4, Color(0.05, 0.02, 0.03, 0.96))
			canvas.draw_string(font, name_pos, boss_name, HORIZONTAL_ALIGNMENT_CENTER, bar_w + 48.0, 18, Color(1.0, 0.14, 0.14, 1.0))
		else:
			var top_str := "%s %d" % [label_txt, int(ceilf(maxf(0.0, hp)))] if not label_txt.is_empty() else "%d/%d" % [int(ceilf(maxf(0.0, hp))), int(round(max_hp))]
			if stunned:
				top_str += " [STUN]"
			canvas.draw_string(font, Vector2(x0 - 24.0, hp_rect.position.y - 4.0), top_str, HORIZONTAL_ALIGNMENT_CENTER, bar_w + 48.0, 14, Color(1.0, 0.94, 0.82, 0.98))


static func _draw_brush_stroke(canvas: CanvasItem, p0: Vector2, p1: Vector2, prog: float, base_w: float, col: Color, outline_col: Color) -> void:
	var t := clampf(prog, 0.0, 1.0)
	if t <= 0.01:
		return
	var steps := 10
	var dir := p1 - p0
	var len_px := dir.length()
	if len_px <= 0.5:
		return
	var perp := Vector2(-dir.y, dir.x) / len_px
	var cur_steps := maxi(1, int(ceilf(float(steps) * t)))
	for i in range(cur_steps):
		var s0 := float(i) / float(steps)
		var s1 := minf(t, float(i + 1) / float(steps))
		if s1 <= s0:
			continue
		var a := p0.lerp(p1, s0) + perp * (sin(s0 * PI) * 1.4)
		var b := p0.lerp(p1, s1) + perp * (sin(s1 * PI) * 1.4)
		# Calligraphic taper: thicker at head/belly, sharp brush tip at tail
		var w := base_w * (1.18 - 0.52 * s0)
		canvas.draw_line(a, b, outline_col, w + 3.2, true)
	for i in range(cur_steps):
		var s0 := float(i) / float(steps)
		var s1 := minf(t, float(i + 1) / float(steps))
		if s1 <= s0:
			continue
		var a := p0.lerp(p1, s0) + perp * (sin(s0 * PI) * 1.4)
		var b := p0.lerp(p1, s1) + perp * (sin(s1 * PI) * 1.4)
		var w := base_w * (1.18 - 0.52 * s0)
		canvas.draw_line(a, b, col, w, true)


static func draw_calligraphic_red_x(canvas: CanvasItem, center_pos: Vector2, anim_progress: float, bob_phase_s: float, scale_boost: float = 1.0, alpha_mul: float = 1.0) -> void:
	var amul := clampf(alpha_mul, 0.0, 1.0)
	if amul <= 0.01:
		return
	var p := clampf(anim_progress, 0.0, 1.0)
	var bob := sin(bob_phase_s * 6.0) * 3.0 if p >= 0.95 else 0.0
	var c := center_pos + Vector2(0.0, bob)
	var r := 16.0 * scale_boost
	var stroke1_prog := clampf(p / 0.48, 0.0, 1.0)
	var stroke2_prog := clampf((p - 0.48) / 0.48, 0.0, 1.0)
	var ink_col := Color(0.96, 0.10, 0.12, 0.98 * amul)
	var outline_col := Color(0.14, 0.02, 0.03, 0.95 * amul)
	_draw_brush_stroke(canvas, c + Vector2(-r, -r), c + Vector2(r, r), stroke1_prog, 5.2 * scale_boost, ink_col, outline_col)
	_draw_brush_stroke(canvas, c + Vector2(r, -r), c + Vector2(-r, r), stroke2_prog, 5.2 * scale_boost, ink_col, outline_col)


static func draw_target_pointer(canvas: CanvasItem, target_pos: Vector2, bob_phase_s: float, kind: String = "enemy") -> void:
	var bob := sin(bob_phase_s * 6.0) * 4.0
	var tip := target_pos + Vector2(0.0, bob)
	var col := Color(1.0, 0.26, 0.26, 0.98)
	if kind == "item":
		col = Color(1.0, 0.84, 0.18, 0.98)
	elif kind == "npc":
		col = Color(0.24, 0.92, 0.98, 0.98)
	var pts := PackedVector2Array([
		tip,
		tip + Vector2(-12.0, -16.0),
		tip + Vector2(12.0, -16.0),
	])
	canvas.draw_colored_polygon(pts, col)
	canvas.draw_polyline(PackedVector2Array([pts[0], pts[1], pts[2], pts[0]]), Color(0.04, 0.06, 0.10, 0.95), 2.0)


static func draw_selection_ring(canvas: CanvasItem, body_rect: Rect2, progress: float, kind: String = "enemy") -> void:
	var p := clampf(progress, 0.0, 1.0)
	var col := Color(1.0, 0.30, 0.30, p * 0.95)
	if kind == "item":
		col = Color(1.0, 0.86, 0.20, p * 0.95)
	elif kind == "npc":
		col = Color(0.28, 0.92, 1.0, p * 0.95)
	var grow_px := (1.0 - p) * 14.0
	var r := body_rect.grow(grow_px)
	canvas.draw_rect(r, col, false, 2.5)


static func draw_hit_impact(canvas: CanvasItem, pos: Vector2, progress: float, kind: String = "melee", impact_dir: Vector2 = Vector2.RIGHT) -> void:
	var p := clampf(progress, 0.0, 1.0)
	var inv := 1.0 - p
	var dir_n := impact_dir.normalized() if impact_dir.length_squared() > 0.001 else Vector2.RIGHT
	var base_ang := dir_n.angle()
	var dark_rim := Color(0.14, 0.06, 0.04, inv * 0.88)

	if kind == "melee":
		# Upgraded normal melee strike collision FX: crisp crescent punch arc + dark-outlined starburst + directional sparks
		var radius := lerpf(12.0, 48.0, p)
		var ring_col := Color(1.0, 0.76, 0.22, inv * 0.92)
		var slash_col := Color(1.0, 0.90, 0.42, inv * 0.95)
		var core_col := Color(1.0, 0.95, 0.78, inv * 0.62)
		# Open shockwave crescent in strike direction (no spoked crosshair wheel)
		canvas.draw_arc(pos, radius, base_ang - PI * 0.58, base_ang + PI * 0.58, 22, dark_rim, 6.0)
		canvas.draw_arc(pos, radius, base_ang - PI * 0.54, base_ang + PI * 0.54, 22, ring_col, 3.0)
		# Sweeping front kinetic cleave arc
		var arc_r := radius * 1.18
		canvas.draw_arc(pos, arc_r, base_ang - 1.02, base_ang + 1.02, 20, dark_rim, 7.5)
		canvas.draw_arc(pos, arc_r, base_ang - 0.96, base_ang + 0.96, 20, slash_col, 4.0)
		# Crisp 4-point contact diamond burst at impact center
		var sr_long := lerpf(15.0, 26.0, sin(p * PI)) * (1.0 - p * 0.35)
		var sr_short := lerpf(6.0, 10.0, sin(p * PI)) * (1.0 - p * 0.35)
		var star_pts := PackedVector2Array()
		for i in range(8):
			var a := base_ang + float(i) * (PI * 0.25)
			var r_v := sr_long if (i % 2 == 0) else sr_short
			star_pts.append(pos + Vector2(cos(a), sin(a)) * r_v)
		canvas.draw_colored_polygon(star_pts, slash_col)
		var star_rim := star_pts.duplicate()
		star_rim.append(star_pts[0])
		canvas.draw_polyline(star_rim, dark_rim, 2.2)
		# Inner controlled glint core
		var cs := maxf(4.0, (1.0 - p * 0.65) * 9.0)
		canvas.draw_colored_polygon(PackedVector2Array([
			pos + Vector2(0.0, -cs), pos + Vector2(cs, 0.0), pos + Vector2(0.0, cs), pos + Vector2(-cs, 0.0)
		]), core_col)
		# Directional flying pixel impact shards along strike vector
		for s_ang in [-0.72, -0.28, 0.28, 0.72, 2.55, -2.55]:
			var ua := base_ang + float(s_ang)
			var uvec := Vector2(cos(ua), sin(ua))
			var sp0 := pos + uvec * (radius * 0.48)
			var sp1 := pos + uvec * (radius * (1.38 if absf(float(s_ang)) < 1.0 else 0.95))
			canvas.draw_line(sp0, sp1, dark_rim, 4.8)
			canvas.draw_line(sp0, sp1, slash_col, 2.2)
		return

	if kind == "heavy":
		# Upgraded heavy melee smash collision FX: twin fiery shockwaves + X-cleave + 8 radial spikes + forward shock sparks
		var radius := lerpf(16.0, 76.0, p)
		var outer_col := Color(1.0, 0.32, 0.12, inv * 0.95)
		var mid_col := Color(1.0, 0.80, 0.24, inv * 0.92)
		var core_col := Color(1.0, 0.94, 0.78, inv * 0.66)
		# Broken twin shockwave arcs so they frame the starburst cleanly
		for ring_spec in [
			[radius, outer_col, 6.5, 3.0],
			[radius * 0.64, mid_col, 4.5, 2.0],
		]:
			var rr := float(ring_spec[0])
			var rcol := ring_spec[1] as Color
			var rw_rim := float(ring_spec[2])
			var rw_in := float(ring_spec[3])
			canvas.draw_arc(pos, rr, base_ang - 1.25, base_ang + 1.25, 24, dark_rim, rw_rim)
			canvas.draw_arc(pos, rr, base_ang - 1.20, base_ang + 1.20, 24, rcol, rw_in)
			canvas.draw_arc(pos, rr, base_ang + PI - 0.85, base_ang + PI + 0.85, 16, dark_rim, rw_rim)
			canvas.draw_arc(pos, rr, base_ang + PI - 0.80, base_ang + PI + 0.80, 16, rcol, rw_in)
		# Bold dark-outlined X-cleave slashes across impact center
		var slash_len := radius * 1.30
		for cleave_off in [-0.72, 0.72]:
			var cv := Vector2(cos(base_ang + float(cleave_off)), sin(base_ang + float(cleave_off)))
			canvas.draw_line(pos - cv * slash_len, pos + cv * slash_len, dark_rim, 7.0)
			canvas.draw_line(pos - cv * slash_len, pos + cv * slash_len, mid_col, 3.2)
		# 8 Tapered impact spikes bursting radially
		for i in range(8):
			var sa := base_ang + float(i) * (PI * 0.25)
			var u := Vector2(cos(sa), sin(sa))
			var perp := Vector2(-u.y, u.x)
			var tip_r := radius * (1.42 if (i % 2 == 0) else 1.08)
			var base_r := radius * 0.30
			var half_b := (1.0 - p * 0.45) * (8.5 if (i % 2 == 0) else 6.0)
			var poly := PackedVector2Array([pos + u * base_r + perp * half_b, pos + u * tip_r, pos + u * base_r - perp * half_b])
			canvas.draw_colored_polygon(poly, outer_col)
			var rim := poly.duplicate()
			rim.append(poly[0])
			canvas.draw_polyline(rim, dark_rim, 2.0)
		# 4 Forward heavy spark bolts shooting along blow direction
		for f_ang in [-0.55, -0.22, 0.22, 0.55]:
			var fa := base_ang + float(f_ang)
			var fv := Vector2(cos(fa), sin(fa))
			var fp0 := pos + fv * (radius * 0.82)
			var fp1 := pos + fv * (radius * 1.56)
			canvas.draw_line(fp0, fp1, dark_rim, 5.2)
			canvas.draw_line(fp0, fp1, mid_col, 2.4)
		var cs_h := maxf(5.0, (1.0 - p * 0.65) * 13.0)
		canvas.draw_colored_polygon(PackedVector2Array([
			pos + Vector2(0.0, -cs_h), pos + Vector2(cs_h, 0.0), pos + Vector2(0.0, cs_h), pos + Vector2(-cs_h, 0.0)
		]), core_col)
		return

	var outer_col := Color(1.0, 0.78, 0.20, inv * 0.95)
	var core_col := Color(1.0, 0.98, 0.86, inv)
	var max_r := 28.0
	if kind == "skill":
		outer_col = Color(0.28, 0.86, 1.0, inv * 0.95)
		max_r = 44.0
	elif kind == "stun":
		outer_col = Color(1.0, 0.62, 0.12, inv)
		max_r = 48.0
	elif kind == "clash":
		outer_col = Color(1.0, 0.90, 0.36, inv)
		max_r = 46.0
	elif kind == "player_hit":
		outer_col = Color(1.0, 0.24, 0.24, inv * 0.95)
		max_r = 32.0

	var radius := lerpf(8.0, max_r, p)
	# Reduce hit-impact glare contrast by an additional 40% (0.64 * 0.60 = 0.384 on flash overlay glare).
	var lum := 0.384
	outer_col = Color(outer_col.r * lum, outer_col.g * lum, outer_col.b * lum, outer_col.a * lum)
	core_col = Color(core_col.r * lum, core_col.g * lum, core_col.b * lum, core_col.a * lum)
	# Crisp pixel shockbox + diagonal star sparks (zero blur/ellipse)
	var box := Rect2(pos.x - radius, pos.y - radius, radius * 2.0, radius * 2.0)
	canvas.draw_rect(box, outer_col, false, 2.5)
	var core_sz := maxf(4.0, (1.0 - p * 0.7) * 14.0)
	canvas.draw_rect(Rect2(pos.x - core_sz * 0.5, pos.y - core_sz * 0.5, core_sz, core_sz), core_col, true)
	for dir_vec in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1), Vector2(0.75, 0.75), Vector2(-0.75, 0.75), Vector2(0.75, -0.75), Vector2(-0.75, -0.75)]:
		var p0 := pos + (dir_vec as Vector2) * (radius * 0.45)
		var p1 := pos + (dir_vec as Vector2) * (radius * 1.25)
		canvas.draw_line(p0, p1, outer_col, 2.5)


static func draw_floating_damage(canvas: CanvasItem, pos: Vector2, text_str: String, progress: float, color: Color) -> void:
	var font := ThemeDB.fallback_font
	if font == null or text_str.is_empty():
		return
	var alpha := clampf(1.0 - maxf(0.0, progress - 0.35) / 0.65, 0.0, 1.0)
	var col := Color(color.r, color.g, color.b, alpha)
	var outline := Color(0.03, 0.04, 0.08, alpha * 0.96)
	var draw_pos := Vector2(pos.x - 72.0, pos.y)
	canvas.draw_string_outline(font, draw_pos, text_str, HORIZONTAL_ALIGNMENT_CENTER, 144.0, FLOATING_DAMAGE_FONT_SIZE, FLOATING_DAMAGE_OUTLINE_SIZE, outline)
	canvas.draw_string(font, draw_pos, text_str, HORIZONTAL_ALIGNMENT_CENTER, 144.0, FLOATING_DAMAGE_FONT_SIZE, col)
