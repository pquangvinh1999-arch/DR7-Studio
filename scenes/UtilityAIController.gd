class_name UtilityAIController
extends RefCounted
## Pure Utility AI state machine shared across DR7-Studio monsters/bosses on Godot 4.
## Mirrors `gameplay.utility_ai` in `res://assets/maps/rocky_plateau/arena-stage.json`
## and the exact 1:1 JS evaluation rules in `tools/preview/index.html`.

var close_edge_px: float = 50.0
var mid_max_edge_px: float = 200.0
var heavy_max_edge_px: float = 200.0
var attack_cooldown_s: float = 1.0
var light_hits_before_heavy: int = 2
var zone_width_max_px: float = 500.0
var zone_width_px: float = 480.0

var home_x: float = 1360.0
var zone_min_x: float = 1120.0
var zone_max_x: float = 1600.0
var patrol_dir: int = -1
var cooldown_remaining: float = 0.0
var light_chain_count: int = 0
var last_intent: String = "idle"
var last_reason: String = "init"


func configure_from_stage(stage_config: Dictionary) -> void:
	var gp: Dictionary = stage_config.get("gameplay", {})
	var u: Variant = gp.get("utility_ai", {})
	if not (u is Dictionary):
		return
	var uc := u as Dictionary
	close_edge_px = float(uc.get("close_edge_px", 50.0))
	mid_max_edge_px = float(uc.get("mid_max_edge_px", 200.0))
	heavy_max_edge_px = float(uc.get("heavy_max_edge_px", 200.0))
	attack_cooldown_s = float(uc.get("attack_cooldown_s", 1.0))
	light_hits_before_heavy = int(uc.get("light_hits_before_heavy", 2))
	zone_width_max_px = float(uc.get("zone_width_max_px", 500.0))
	zone_width_px = minf(zone_width_max_px, float(uc.get("zone_width_default_px", 480.0)))


func reset_zone(center_x: float, walkable_min_x: float, walkable_max_x: float) -> void:
	var half := minf(zone_width_px, zone_width_max_px) * 0.5
	var min_allowed := walkable_min_x
	var max_allowed := walkable_max_x
	var span := maxf(40.0, minf(zone_width_max_px, half * 2.0))
	home_x = clampf(center_x, min_allowed + span * 0.5, max_allowed - span * 0.5)
	zone_min_x = clampf(home_x - span * 0.5, min_allowed, max_allowed)
	zone_max_x = clampf(home_x + span * 0.5, zone_min_x + 40.0, max_allowed)
	cooldown_remaining = 0.0
	light_chain_count = 0
	patrol_dir = -1
	reset_drum_state()
	last_intent = "patrol"
	last_reason = "zone_init"


static func compute_body_rect(pos_x: float, foot_y: float, body_w: float, body_h: float, scale: float) -> Rect2:
	var bw := maxf(16.0, body_w * scale)
	var bh := maxf(16.0, body_h * scale)
	return Rect2(pos_x - bw * 0.5, foot_y - bh, bw, bh)


static func compute_edge_distance(self_rect: Rect2, target_rect: Rect2) -> float:
	var dx := maxf(0.0, maxf(self_rect.position.x - (target_rect.position.x + target_rect.size.x),
		target_rect.position.x - (self_rect.position.x + self_rect.size.x)))
	var dy := maxf(0.0, maxf(self_rect.position.y - (target_rect.position.y + target_rect.size.y),
		target_rect.position.y - (self_rect.position.y + self_rect.size.y)))
	return sqrt(dx * dx + dy * dy)


func tick_cooldown(dt: float) -> void:
	if cooldown_remaining > 0.0:
		cooldown_remaining = maxf(0.0, cooldown_remaining - maxf(0.0, dt))


func notify_attack_started() -> void:
	cooldown_remaining = attack_cooldown_s


func _is_target_in_zone(target_x: float) -> bool:
	return target_x >= zone_min_x and target_x <= zone_max_x


func _patrol_step(self_x: float) -> Dictionary:
	if self_x <= zone_min_x + 4.0:
		patrol_dir = 1
	elif self_x >= zone_max_x - 4.0:
		patrol_dir = -1
	last_intent = "patrol"
	last_reason = "target_outside_zone"
	return {
		"intent": "patrol",
		"move_dir": patrol_dir,
		"attack_clip": "",
		"desired_face_left": patrol_dir < 0,
		"edge_dist": -1.0,
		"reason": last_reason,
	}


func evaluate(params: Dictionary) -> Dictionary:
	if bool(params.get("is_stationary", false)):
		last_intent = "idle"
		last_reason = "stationary"
		return {"intent": "idle", "move_dir": 0, "attack_clip": "", "desired_face_left": bool(params.get("facing_left", false)), "edge_dist": -1.0, "reason": last_reason}
	var cid: String = str(params.get("character_id", ""))
	var is_flying: bool = bool(params.get("is_flying", false))
	var has_heavy: bool = bool(params.get("has_heavy", false))
	var has_power_up: bool = bool(params.get("has_power_up", true))
	var light_clip: String = str(params.get("light_clip", "attack_light"))
	var self_rect: Rect2 = params.get("self_rect", Rect2())
	var target_rect: Rect2 = params.get("target_rect", Rect2())
	var self_x: float = float(params.get("self_x", home_x))
	var target_x: float = float(params.get("target_x", 0.0))
	var is_busy: bool = bool(params.get("is_busy", false))
	var zone_active: bool = _is_target_in_zone(target_x)
	var edge_dist := compute_edge_distance(self_rect, target_rect)
	var face_left := target_x < self_x

	# Drum custom monster AI handles engagement hysteresis (<400px), teleport (50..200px),
	# 0.2s continuous attack_light (<=50px), and ranged power_up (200..400px) with no patrol walk.
	if cid == "drum":
		return _evaluate_drum(
			self_x,
			target_x,
			zone_min_x,
			zone_max_x,
			face_left,
			edge_dist,
			is_busy,
			bool(params.get("facing_left", false)),
			zone_active
		)

	if not zone_active:
		if light_chain_count > 0:
			light_chain_count = 0
		if is_busy:
			return {"intent": "busy", "move_dir": 0, "attack_clip": "", "desired_face_left": target_x < self_x, "edge_dist": -1.0, "reason": "busy"}
		return _patrol_step(self_x)

	if is_busy:
		last_intent = "busy"
		last_reason = "executing_action"
		return {"intent": "busy", "move_dir": 0, "attack_clip": "", "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}

	# Special Case 1: Chilopoda reverses range roles (close -> dual laser power_up, >=50px -> burrow attack_light)
	if cid == "chilopoda":
		light_chain_count = 0
		if cooldown_remaining > 0.0:
			last_intent = "wait_cooldown"
			last_reason = "chilopoda_cooldown"
			return {"intent": "wait_cooldown", "move_dir": 0, "attack_clip": "", "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}
		var chosen := "power_up" if edge_dist < close_edge_px else light_clip
		last_intent = "attack"
		last_reason = "chilopoda_close_laser" if edge_dist < close_edge_px else "chilopoda_far_burrow"
		cooldown_remaining = attack_cooldown_s
		return {"intent": "attack", "move_dir": 0, "attack_clip": chosen, "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}

	# Special Case 2: Flying mobs hover/patrol at air lane, never chase ground/far targets; use power_up (or light_clip if none) at >=50px, light when <50px.
	if is_flying:
		if edge_dist >= close_edge_px:
			light_chain_count = 0
			if cooldown_remaining > 0.0:
				var pat := _patrol_step(self_x)
				pat["edge_dist"] = edge_dist
				pat["reason"] = "flying_hover_cooldown"
				last_reason = pat["reason"]
				return pat
			var ranged_clip := "power_up" if has_power_up else light_clip
			last_intent = "attack"
			last_reason = "flying_ranged_far"
			cooldown_remaining = attack_cooldown_s
			return {"intent": "attack", "move_dir": 0, "attack_clip": ranged_clip, "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}
		if cooldown_remaining > 0.0:
			last_intent = "wait_cooldown"
			last_reason = "flying_melee_cooldown"
			return {"intent": "wait_cooldown", "move_dir": 0, "attack_clip": "", "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}
		last_intent = "attack"
		last_reason = "flying_melee_close"
		cooldown_remaining = attack_cooldown_s
		return {"intent": "attack", "move_dir": 0, "attack_clip": light_clip, "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}

	# Standard Ground Utility AI:
	# 1) Far (>= 200px): reset light combo chain and fire ranged power_up.
	if edge_dist >= mid_max_edge_px:
		light_chain_count = 0
		if cooldown_remaining > 0.0:
			last_intent = "wait_cooldown"
			last_reason = "far_power_up_cooldown"
			return {"intent": "wait_cooldown", "move_dir": 0, "attack_clip": "", "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}
		last_intent = "attack"
		last_reason = "far_power_up"
		cooldown_remaining = attack_cooldown_s
		return {"intent": "attack", "move_dir": 0, "attack_clip": "power_up", "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}

	# 2) Heavy follow-up: if 2 lights already landed AND target remains < 200px (heavy reach), unleash attack_heavy!
	if has_heavy and light_chain_count >= light_hits_before_heavy and edge_dist < heavy_max_edge_px:
		if cooldown_remaining > 0.0:
			last_intent = "wait_cooldown"
			last_reason = "heavy_ready_cooldown"
			return {"intent": "wait_cooldown", "move_dir": 0, "attack_clip": "", "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}
		light_chain_count = 0
		last_intent = "attack"
		last_reason = "combo_heavy_followup"
		cooldown_remaining = attack_cooldown_s
		return {"intent": "attack", "move_dir": 0, "attack_clip": "attack_heavy", "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}

	# 3) Close (< 50px): launch light attack and advance chain counter.
	if edge_dist < close_edge_px:
		if cooldown_remaining > 0.0:
			last_intent = "wait_cooldown"
			last_reason = "close_light_cooldown"
			return {"intent": "wait_cooldown", "move_dir": 0, "attack_clip": "", "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}
		light_chain_count += 1
		last_intent = "attack"
		last_reason = "close_light_%d" % light_chain_count
		cooldown_remaining = attack_cooldown_s
		return {"intent": "attack", "move_dir": 0, "attack_clip": light_clip, "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}

	# 4) Mid-range [50px, 200px): chase inside zone towards target!
	var chase_dir := 0
	if target_x > self_x + 2.0 and self_x < zone_max_x:
		chase_dir = 1
	elif target_x < self_x - 2.0 and self_x > zone_min_x:
		chase_dir = -1
	last_intent = "chase"
	last_reason = "mid_range_chase"
	return {"intent": "chase", "move_dir": chase_dir, "attack_clip": "", "desired_face_left": face_left, "edge_dist": edge_dist, "reason": last_reason}


func reset_drum_state() -> void:
	set_meta(&"drum_phase", "idle_ready")
	set_meta(&"drum_engaged", false)


func _evaluate_drum(
	_self_x: float,
	_target_x: float,
	_zone_min_x: float,
	_zone_max_x: float,
	face_left: bool,
	edge_dist: float,
	is_busy: bool = false,
	current_face_left: bool = false,
	in_zone: bool = true
) -> Dictionary:
	var engaged := bool(get_meta(&"drum_engaged", false))
	var phase := str(get_meta(&"drum_phase", "idle_ready"))

	if edge_dist >= 400.0 or (not in_zone and not engaged):
		set_meta(&"drum_engaged", false)
		set_meta(&"drum_phase", "idle_ready")
		if is_busy:
			last_intent = "busy"
			last_reason = "executing_action"
			return {
				"intent": "busy",
				"move_dir": 0,
				"attack_clip": "",
				"desired_face_left": face_left,
				"edge_dist": edge_dist if in_zone else -1.0,
				"reason": last_reason,
			}
		last_intent = "idle"
		last_reason = "outside_range_400_idle" if (engaged or in_zone) else "outside_zone_idle"
		return {
			"intent": "idle",
			"move_dir": 0,
			"attack_clip": "",
			"desired_face_left": face_left if in_zone else current_face_left,
			"edge_dist": edge_dist if in_zone else -1.0,
			"reason": last_reason,
		}

	set_meta(&"drum_engaged", true)

	if is_busy:
		last_intent = "busy"
		last_reason = "executing_action"
		return {
			"intent": "busy",
			"move_dir": 0,
			"attack_clip": "",
			"desired_face_left": face_left,
			"edge_dist": edge_dist,
			"reason": last_reason,
		}

	if cooldown_remaining > 0.0:
		last_intent = "wait_cooldown"
		last_reason = "drum_light_cooldown" if edge_dist <= close_edge_px else "drum_combo_cooldown"
		return {
			"intent": "wait_cooldown",
			"move_dir": 0,
			"attack_clip": "",
			"desired_face_left": face_left,
			"edge_dist": edge_dist,
			"reason": last_reason,
		}

	# Immediate follow-up strike right after teleport (~50px ambush) unless target fled past 200px
	if phase == "post_teleport_light" and edge_dist <= mid_max_edge_px:
		set_meta(&"drum_phase", "engaged")
		cooldown_remaining = 0.2
		last_intent = "attack"
		last_reason = "drum_shoulder_light"
		return {
			"intent": "attack",
			"move_dir": 0,
			"attack_clip": "attack_light",
			"desired_face_left": face_left,
			"edge_dist": edge_dist,
			"reason": last_reason,
		}

	# Close melee <= 50px: continuous attack_light every 0.2s
	if edge_dist <= close_edge_px:
		set_meta(&"drum_phase", "engaged")
		cooldown_remaining = 0.2
		last_intent = "attack"
		last_reason = "drum_light_continuous"
		return {
			"intent": "attack",
			"move_dir": 0,
			"attack_clip": "attack_light",
			"desired_face_left": face_left,
			"edge_dist": edge_dist,
			"reason": last_reason,
		}

	# Beyond melee allowance (200 < edge_dist < 400): Row 3 prep + Row 4-5 power_up electric orb
	if edge_dist > mid_max_edge_px:
		set_meta(&"drum_phase", "engaged")
		cooldown_remaining = attack_cooldown_s
		last_intent = "attack"
		last_reason = "drum_powerup_ranged"
		return {
			"intent": "attack",
			"move_dir": 0,
			"attack_clip": "power_up",
			"desired_face_left": face_left,
			"edge_dist": edge_dist,
			"reason": last_reason,
		}

	# Mid approach inside 50 < edge_dist <= 200px: speed-vanish teleport to ~50px then attack_light
	set_meta(&"drum_phase", "post_teleport_light")
	cooldown_remaining = 0.0
	last_intent = "attack"
	last_reason = "drum_teleport_ambush"
	return {
		"intent": "attack",
		"move_dir": 0,
		"attack_clip": "teleport",
		"desired_face_left": face_left,
		"edge_dist": edge_dist,
		"reason": last_reason,
	}
