class_name FieldCombatManager
extends Node
## Multi-monster Field Combat, Exact Body-Edge Interactions, Hit Feedback FX,
## Direct Touch Target Selection + Cycle Pointer, Auto-Approach Normal Attack,
## Stamina/Mini-Stun (3s), and 30%-Gated Weighted Dragon Ball Drops.

signal player_state_changed()
signal pointer_changed(kind: String)

const UtilityAIControllerScript := preload("res://scenes/UtilityAIController.gd")
const OverheadBarsDrawScript := preload("res://scenes/runtime/OverheadBarsDraw.gd")
const PowerupExplosionFrames := preload("res://assets/fx/powerup_explosion/powerup_explosion.tres")

const RESPAWN_MONSTER_DELAY_S := 12.0
const RESPAWN_PLAYER_DELAY_S := 3.0
const BOSS_DRUM_INITIAL_DELAY_S := 300.0 # 5 minutes after hero exists in map
const BOSS_DRUM_RESPAWN_DELAY_S := 1800.0 # 30 minutes cooldown after Boss Drum is defeated
const MINI_STUN_DURATION_S := 3.0
const STAMINA_PER_HIT := 20.0
const PLAYER_MAX_HP := 1500.0
const PLAYER_MAX_MANA := 100.0
const PLAYER_LIGHT_DMG := 200.0
const PLAYER_HEAVY_DMG := 320.0
const PLAYER_POWER_DMG := 400.0
const PLAYER_MANA_GAIN := 20.0
const ITEM_PICKUP_UNLOCK_S := 1.0
const ITEM_PICKUP_RANGE_PX := 140.0
const MELEE_STRIKE_EDGE_PX := 85.0
const DRAGON_BALL_TOTAL_DROP_PCT := 30.0
const DOUBLE_TAP_WINDOW_S := 0.42
const Z_LAYER_FX := 38
const DRUM_SKILL_SPEED_PX_S := 1170.0
const MONSTER_SKILL_SPEED_PX_S := 780.0
const DEFAULT_EXPLOSION_SCALE := 0.68
const CLASH_EXPLOSION_SCALE := 0.58
const HIT_FLASH_BRIGHTNESS_MUL := 0.64
const HIT_FLASH_ALPHA_MUL := 0.80
const HIT_FLASH_CONTRAST_MUL := 0.60
const HIT_SHAKE_SCALE_MUL := 0.80
const POINTER_X_SHOW_DURATION_S := 0.75

# Gate: 30% total drop chance; once passed, roll star across original weights (30 / 20 / 10 / 5 / 2 / 0.5 / 0.1)
const DRAGON_BALL_DROP_TABLE := [
	{"ball": 7, "weight": 30.0},
	{"ball": 6, "weight": 20.0},
	{"ball": 5, "weight": 10.0},
	{"ball": 4, "weight": 5.0},
	{"ball": 3, "weight": 2.0},
	{"ball": 2, "weight": 0.5},
	{"ball": 1, "weight": 0.1},
]

const BOSS_DRUM_STATS := {"hp": 5000.0, "stamina": 200.0, "light_dmg": 120.0, "heavy_dmg": 120.0, "power_dmg": 220.0, "flying": false}

const BOSS_DROP_TABLE := [
	{"ball": 1, "weight": 8.0},
	{"ball": 2, "weight": 12.0},
	{"ball": 3, "weight": 18.0},
	{"ball": 4, "weight": 22.0},
	{"ball": 5, "weight": 20.0},
	{"ball": 6, "weight": 12.0},
	{"ball": 7, "weight": 8.0},
]

const MONSTER_STATS := {
	"chilopoda": {"hp": 1300.0, "light_dmg": 50.0, "heavy_dmg": 70.0, "power_dmg": 100.0, "flying": false},
	"spinosaurus": {"hp": 1500.0, "light_dmg": 50.0, "heavy_dmg": 70.0, "power_dmg": 100.0, "flying": false},
	"tasmanian_king_crab": {"hp": 1300.0, "light_dmg": 50.0, "heavy_dmg": 70.0, "power_dmg": 100.0, "flying": false},
	"t_rex": {"hp": 1800.0, "light_dmg": 50.0, "heavy_dmg": 70.0, "power_dmg": 100.0, "flying": false},
	"sarcosuchus": {"hp": 1500.0, "light_dmg": 50.0, "heavy_dmg": 70.0, "power_dmg": 100.0, "flying": false},
	"dilophosaurus": {"hp": 1300.0, "light_dmg": 50.0, "heavy_dmg": 70.0, "power_dmg": 100.0, "flying": false},
	"bat_chiroptera": {"hp": 900.0, "light_dmg": 70.0, "heavy_dmg": 70.0, "power_dmg": 100.0, "flying": true},
	"pteranodon": {"hp": 1000.0, "light_dmg": 70.0, "heavy_dmg": 70.0, "power_dmg": 100.0, "flying": true},
	"floating_camera": {"hp": 800.0, "light_dmg": 80.0, "heavy_dmg": 80.0, "power_dmg": 80.0, "flying": true},
}

const FLYING_ROTATION := ["bat_chiroptera", "pteranodon", "floating_camera"]

var arena: Node2D = null
var active: bool = false
var player_spawned: bool = false
var player_hp: float = PLAYER_MAX_HP
var player_max_hp: float = PLAYER_MAX_HP
var player_mana: float = 0.0
var player_max_mana: float = PLAYER_MAX_MANA
var player_dead: bool = false
var player_immortal: bool = false
var show_monster_ranges: bool = false
var player_respawn_timer_s: float = 0.0
var _player_melee_pending: bool = false
var _player_power_pending: bool = false
var _player_power_target: Dictionary = {}

var slots: Array[Dictionary] = []
var boss_slot: Dictionary = {}
var boss_has_spawned_once: bool = false
var boss_spawn_timer_s: float = BOSS_DRUM_INITIAL_DELAY_S
var boss_respawn_timer_s: float = 0.0
var _boss_teleport_chase_cd_s: float = 0.0
var homing_projectiles: Array[Dictionary] = []
var _flying_rotation_idx: int = 0
var _sim_time_s: float = 0.0

var pointer_kind: String = "enemy"
var pointer_slot_id: String = ""
var pointer_item_node: Node2D = null
var pointer_pulse_s: float = 0.0
var pointer_x_anim_s: float = 0.28
var pointer_x_anim_dur_s: float = 0.28
var pointer_x_visible_s: float = 0.0
var pointer_x_double_tap_pulse_s: float = 0.0
var _last_tap_kind: String = ""
var _last_tap_slot_id: String = ""
var _last_tap_item: Node2D = null
var _last_tap_time_s: float = -99.0

var auto_approach_active: bool = false
var _auto_approach_kind: String = ""
var _auto_approach_slot_id: String = ""
var _auto_approach_item: Node2D = null
var _auto_approach_timeout_s: float = 0.0

var player_hit_flash_s: float = 0.0
var player_hit_shake_s: float = 0.0
var hit_impacts: Array[Dictionary] = []
var floating_texts: Array[Dictionary] = []
var _explosion_nodes: Array[AnimatedSprite2D] = []


func setup(owner_arena: Node2D) -> void:
	arena = owner_arena


func _get_combat_slots() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for s in slots:
		out.append(s)
	if not boss_slot.is_empty():
		out.append(boss_slot)
	return out


static func _get_slot_stats(slot: Dictionary) -> Dictionary:
	if bool(slot.get("is_boss", false)):
		return BOSS_DRUM_STATS
	return MONSTER_STATS.get(str(slot.get("character_id", "")), {})


func clear_all() -> void:
	active = false
	for s in _get_combat_slots():
		var n := s.get("node") as Node2D
		if n != null and is_instance_valid(n):
			n.queue_free()
	slots.clear()
	boss_slot = {}
	boss_has_spawned_once = false
	boss_spawn_timer_s = BOSS_DRUM_INITIAL_DELAY_S
	boss_respawn_timer_s = 0.0
	_boss_teleport_chase_cd_s = 0.0
	for pr in homing_projectiles:
		var sp := pr.get("sprite") as Node2D
		if sp != null and is_instance_valid(sp):
			sp.queue_free()
	homing_projectiles.clear()
	for ex in _explosion_nodes:
		if ex != null and is_instance_valid(ex):
			ex.queue_free()
	_explosion_nodes.clear()
	hit_impacts.clear()
	floating_texts.clear()
	player_hit_flash_s = 0.0
	player_hit_shake_s = 0.0
	pointer_pulse_s = 0.0
	pointer_x_anim_s = pointer_x_anim_dur_s
	pointer_x_visible_s = 0.0
	pointer_x_double_tap_pulse_s = 0.0
	_last_tap_kind = ""
	_last_tap_slot_id = ""
	_last_tap_item = null
	_last_tap_time_s = -99.0
	cancel_auto_approach()
	pointer_slot_id = ""
	pointer_item_node = null
	pointer_kind = "enemy"


func cancel_auto_approach() -> void:
	auto_approach_active = false
	_auto_approach_kind = ""
	_auto_approach_slot_id = ""
	_auto_approach_item = null
	_auto_approach_timeout_s = 0.0


func start_field(spawn_player_immediately: bool = false) -> void:
	clear_all()
	active = true
	player_spawned = spawn_player_immediately
	player_hp = PLAYER_MAX_HP
	player_max_hp = PLAYER_MAX_HP
	player_mana = 0.0
	player_max_mana = PLAYER_MAX_MANA
	player_dead = false
	player_respawn_timer_s = 0.0
	_flying_rotation_idx = 0

	# 3 main-plateau slots and 1 ground monster on each of the 4 lower plateaus.
	var ground_defs := [
		{"id": "g0", "cid": "chilopoda", "x": 330.0, "zmin": -103.0, "zmax": 766.0},
		{"id": "g1", "cid": "spinosaurus", "x": 1160.0, "zmin": 730.0, "zmax": 1590.0},
		{"id": "g2", "cid": "tasmanian_king_crab", "x": 1990.0, "zmin": 1560.0, "zmax": 2430.0},
		{"id": "g3", "cid": "t_rex", "x": 3270.0, "zmin": 2900.0, "zmax": 3640.0},
		{"id": "g4", "cid": "sarcosuchus", "x": 4125.0, "zmin": 3750.0, "zmax": 4490.0},
		{"id": "g5", "cid": "dilophosaurus", "x": 5180.0, "zmin": 4790.0, "zmax": 5500.0},
		{"id": "g6", "cid": "spinosaurus", "x": 5960.0, "zmin": 5610.0, "zmax": 6310.0},
	]
	for gd in ground_defs:
		_create_and_spawn_slot(gd, false)

	# One flying monster above each ground slot and lower plateau.
	var flying_defs := [
		{"id": "f0", "cid": "bat_chiroptera", "x": 330.0, "y": 240.0, "zmin": -190.0, "zmax": 855.0},
		{"id": "f1", "cid": "pteranodon", "x": 1160.0, "y": 240.0, "zmin": 635.0, "zmax": 1685.0},
		{"id": "f2", "cid": "floating_camera", "x": 1990.0, "y": 240.0, "zmin": 1465.0, "zmax": 2515.0},
		{"id": "f3", "cid": "bat_chiroptera", "x": 3270.0, "y": 260.0, "zmin": 2745.0, "zmax": 3795.0},
		{"id": "f4", "cid": "pteranodon", "x": 4125.0, "y": 280.0, "zmin": 3600.0, "zmax": 4540.0},
		{"id": "f5", "cid": "floating_camera", "x": 5180.0, "y": 300.0, "zmin": 4740.0, "zmax": 5560.0},
		{"id": "f6", "cid": "bat_chiroptera", "x": 5960.0, "y": 320.0, "zmin": 5560.0, "zmax": 6360.0},
	]
	for fd in flying_defs:
		_create_and_spawn_slot(fd, true)

	_flying_rotation_idx = 1 # Continue Bat/Ptera/Camera rotation after 7 initial flying slots.
	refresh_pointer_valid()

	player_state_changed.emit()


func _create_and_spawn_slot(spec: Dictionary, is_flying: bool) -> void:
	var cid := str(spec["cid"])
	var slot := {
		"id": str(spec["id"]),
		"native_cid": cid,
		"character_id": cid,
		"is_flying": is_flying,
		"x_home": float(spec["x"]),
		"y_home": float(spec.get("y", arena.call("_ground_y_at", float(spec["x"])))),
		"zone_min_x": float(spec["zmin"]),
		"zone_max_x": float(spec["zmax"]),
		"respawn_toggle": false,
		"node": null,
		"alive": false,
		"hp": 1000.0,
		"max_hp": 1000.0,
		"stamina": 100.0,
		"max_stamina": 100.0,
		"stun_timer_s": 0.0,
		"hit_anim_timer_s": 0.0,
		"respawn_timer_s": 0.0,
		"ko_hide_timer_s": 0.0,
		"cooldown_s": 0.0,
		"light_chain": 0,
		"action_clip": "",
		"action_timer_s": 0.0,
		"vy": 0.0,
		"scale_val": 1.75,
		"facing_left": true,
		"patrol_dir": 1 if (slots.size() % 2 == 0) else -1,
		"patrol_pause_s": 0.0,
		"power_released": false,
		"melee_hit_done": false,
		"has_heavy": false,
		"has_power_up": false,
		"light_clip": "attack_light",
		"locomotion_clip": "walk",
		"preserve_phase": false,
		"sideways_locked": false,
		"turn_boost_s": 0.0,
		"turn_elapsed_s": 0.0,
		"turn_duration_s": 0.0,
		"turn_prev_dir": 1,
		"turn_target_left": true,
		"turn_lock_s": 0.0,
		"has_turn_clip": false,
		"orbit_phase": float(slots.size()) * 1.35,
		"orbit_dir": 1.0 if (slots.size() % 2 == 0) else -1.0,
		"hit_flash_s": 0.0,
		"hit_shake_s": 0.0,
	}
	slots.append(slot)
	_spawn_slot_monster(slot, cid)


func _spawn_slot_monster(slot: Dictionary, cid: String) -> void:
	var old_n := slot.get("node") as Node2D
	if old_n != null and is_instance_valid(old_n):
		old_n.queue_free()
	var entry: Dictionary = arena.call("_find_character_entry_ro", cid)
	if entry.is_empty():
		return
	var prefab_path: String = str(arena.call("_resolve_prefab_path", entry))
	if prefab_path.is_empty() or not ResourceLoader.exists(prefab_path):
		return
	var packed := ResourceLoader.load(prefab_path) as PackedScene
	if packed == null:
		return
	var inst := packed.instantiate() as Node2D
	if inst == null:
		return
	var parent_layer: Node = arena.fighters_layer if arena.fighters_layer != null else arena
	parent_layer.add_child(inst)
	inst.name = "FieldMob_%s_%s" % [str(slot["id"]), cid]

	var is_boss := bool(slot.get("is_boss", false))
	var sc := float(slot.get("boss_scale", 2.5)) if is_boss else float(arena.call("_get_entry_default_scale", entry))
	var spawn_x := float(slot["x_home"])
	var spawn_y := float(slot["y_home"]) if bool(slot["is_flying"]) else float(arena.call("_ground_y_at", spawn_x))
	arena.call("_configure_fighter_instance", inst, spawn_x, spawn_y, true, sc)
	inst.z_index = int(arena.call("get_fighter_layer_z", cid, false))

	var caps: Dictionary = arena.call("_resolve_enemy_capabilities", entry, inst)
	slot["node"] = inst
	slot["character_id"] = cid
	var st: Dictionary = _get_slot_stats(slot)
	var max_hp := float(st.get("hp", 1300.0))
	var max_stam := float(st.get("stamina", 100.0))

	slot["alive"] = true
	slot["hp"] = max_hp
	slot["max_hp"] = max_hp
	slot["stamina"] = max_stam
	slot["max_stamina"] = max_stam
	slot["stun_timer_s"] = 0.0
	slot["hit_anim_timer_s"] = 0.0
	slot["respawn_timer_s"] = 0.0
	slot["ko_hide_timer_s"] = 0.0
	slot["cooldown_s"] = 0.25
	slot["light_chain"] = 0
	slot["action_clip"] = ""
	slot["action_timer_s"] = 0.0
	slot["vy"] = 0.0
	slot["scale_val"] = sc
	slot["facing_left"] = inst.scale.x < 0.0
	slot["power_released"] = false
	slot["melee_hit_done"] = false
	slot["teleport_relocated"] = false
	slot["has_heavy"] = bool(caps.get("has_heavy", false))
	slot["has_power_up"] = bool(caps.get("has_power_up", false))
	slot["light_clip"] = str(caps.get("light_clip", "attack_light"))
	slot["locomotion_clip"] = str(caps.get("locomotion_clip", "walk"))
	slot["preserve_phase"] = bool(caps.get("preserve_idle_walk_phase", false))
	slot["sideways_locked"] = bool(caps.get("sideways_locked", false))
	slot["has_turn_clip"] = bool(arena.call("_has_turn_clip", entry))
	slot["turn_lock_s"] = 0.0
	slot["hit_flash_s"] = 0.0
	slot["hit_shake_s"] = 0.0
	if is_boss:
		inst.name = "FieldBoss_drum"
		inst.z_index = int(arena.Z_LAYER_BOSS)

	# Disable legacy horizontal prefab ProjectileFX & Drum internal orb in Field Mode so only 1 clean 360-degree projectile fires
	if inst.get("external_projectile_managed") != null:
		inst.set("external_projectile_managed", true)
	if inst.get("external_orb_managed") != null:
		inst.set("external_orb_managed", true)
	var pfx := inst.get_node_or_null("ProjectileFX") as Node2D
	if pfx != null:
		pfx.visible = false
		pfx.modulate = Color(1.0, 1.0, 1.0, 0.0)
		pfx.scale = Vector2.ZERO


func step(delta: float) -> void:
	if not active or delta <= 0.0:
		return
	_sim_time_s += delta

	# 1. Player respawn, auto-approach, & pending attack/power release
	if player_spawned and player_dead:
		cancel_auto_approach()
		player_respawn_timer_s = maxf(0.0, player_respawn_timer_s - delta)
		if player_respawn_timer_s <= 0.0:
			respawn_player_at_left()
	elif player_spawned and arena.player_node != null:
		_step_auto_approach(delta)
		_step_player_combat_hooks()

	# 2. Step Boss Map schedule + all active monster slots + Boss Drum
	_step_boss_spawn_schedule(delta)
	for slot in slots:
		_step_slot(slot, delta)
	if not boss_slot.is_empty():
		_step_slot(boss_slot, delta)

	# 3. Step homing projectiles (silhouette collision + skill-vs-skill clash + terrain stop)
	_step_homing_projectiles(delta)

	# 4. Apply hit flashes, shakes, pointer fade & impact/text timers immediately after combat updates
	_step_hit_visuals(delta)

	# 5. Tick dropped item ages (for 1s pickup delay)
	for item_n in arena._dropped_item_nodes:
		if is_instance_valid(item_n):
			var age := float(item_n.get_meta(&"drop_age_s", 0.0)) + delta
			item_n.set_meta(&"drop_age_s", age)

	refresh_pointer_valid()


func _step_boss_spawn_schedule(delta: float) -> void:
	if arena == null or not active:
		return
	if not boss_slot.is_empty() and bool(boss_slot.get("alive", false)):
		boss_respawn_timer_s = 0.0
		return
	var hero_present := player_spawned and arena.player_node != null and is_instance_valid(arena.player_node)
	if not boss_has_spawned_once:
		if not hero_present:
			boss_spawn_timer_s = BOSS_DRUM_INITIAL_DELAY_S
			return
		if not player_dead:
			boss_spawn_timer_s = maxf(0.0, boss_spawn_timer_s - delta)
			if boss_spawn_timer_s <= 0.0:
				spawn_boss_drum()
		return
	if boss_respawn_timer_s > 0.0:
		boss_respawn_timer_s = maxf(0.0, boss_respawn_timer_s - delta)
	if boss_respawn_timer_s <= 0.0 and hero_present and not player_dead:
		spawn_boss_drum()


func _pick_random_boss_spawn_x(min_x: float, max_x: float) -> float:
	var lo := min_x + 40.0
	var hi := max_x - 40.0
	if hi <= lo:
		return (min_x + max_x) * 0.5
	return randf_range(lo, hi)


func spawn_boss_drum(forced_spawn_x: float = -999999.0) -> Dictionary:
	if arena == null:
		return {}
	if not boss_slot.is_empty() and bool(boss_slot.get("alive", false)) and is_instance_valid(boss_slot.get("node")):
		# Never double-spawn while alive; re-trigger entry teleport onto hero if desired for test.
		if player_spawned and not player_dead and arena.player_node != null:
			var existing_ai := boss_slot.get("ai") as UtilityAIController
			if existing_ai != null:
				existing_ai.set_meta(&"drum_engaged", true)
				existing_ai.set_meta(&"drum_phase", "post_teleport_light")
			_start_slot_attack(boss_slot, "teleport", 0.0)
		return boss_slot

	var drum_entry: Dictionary = arena.call("_find_character_entry_ro", "drum")
	if drum_entry.is_empty():
		return {}
	var boss_bounds: Vector2 = arena.call("_get_fighter_walk_bounds_x", drum_entry, 2.5)
	var spawn_x := forced_spawn_x
	if spawn_x < -900000.0:
		spawn_x = _pick_random_boss_spawn_x(boss_bounds.x, boss_bounds.y)
	else:
		spawn_x = clampf(spawn_x, boss_bounds.x, boss_bounds.y)

	var ai := UtilityAIControllerScript.new()
	if arena.stage_config is Dictionary:
		ai.configure_from_stage(arena.stage_config)
	ai.reset_zone((boss_bounds.x + boss_bounds.y) * 0.5, boss_bounds.x, boss_bounds.y)

	boss_slot = {
		"id": "boss_drum",
		"native_cid": "drum",
		"character_id": "drum",
		"is_flying": false,
		"is_boss": true,
		"boss_scale": 2.5,
		"ai": ai,
		"x_home": spawn_x,
		"y_home": float(arena.call("_ground_y_at", spawn_x)),
		"zone_min_x": boss_bounds.x,
		"zone_max_x": boss_bounds.y,
		"respawn_toggle": false,
		"node": null,
		"alive": false,
		"hp": float(BOSS_DRUM_STATS["hp"]),
		"max_hp": float(BOSS_DRUM_STATS["hp"]),
		"stamina": float(BOSS_DRUM_STATS["stamina"]),
		"max_stamina": float(BOSS_DRUM_STATS["stamina"]),
		"stun_timer_s": 0.0,
		"hit_anim_timer_s": 0.0,
		"respawn_timer_s": 0.0,
		"ko_hide_timer_s": 0.0,
		"cooldown_s": 0.0,
		"light_chain": 0,
		"action_clip": "",
		"action_timer_s": 0.0,
		"vy": 0.0,
		"scale_val": 2.5,
		"facing_left": true,
		"patrol_dir": -1,
		"patrol_pause_s": 0.0,
		"power_released": false,
		"melee_hit_done": false,
		"teleport_relocated": false,
		"has_heavy": false,
		"has_power_up": true,
		"light_clip": "attack_light",
		"locomotion_clip": "walk",
		"preserve_phase": false,
		"sideways_locked": false,
		"turn_boost_s": 0.0,
		"turn_elapsed_s": 0.0,
		"turn_duration_s": 0.0,
		"turn_prev_dir": 1,
		"turn_target_left": true,
		"turn_lock_s": 0.0,
		"has_turn_clip": false,
		"orbit_phase": 0.0,
		"orbit_dir": -1.0,
		"hit_flash_s": 0.0,
		"hit_shake_s": 0.0,
	}
	_spawn_slot_monster(boss_slot, "drum")
	boss_has_spawned_once = true
	boss_spawn_timer_s = 0.0
	boss_respawn_timer_s = 0.0
	_boss_teleport_chase_cd_s = 2.0

	if player_spawned and not player_dead and arena.player_node != null:
		var bnode := boss_slot.get("node") as Node2D
		if bnode != null:
			var want_left: bool = arena.player_node.position.x < bnode.position.x
			boss_slot["facing_left"] = want_left
			bnode.scale = Vector2(-2.5 if want_left else 2.5, 2.5)
		ai.set_meta(&"drum_engaged", true)
		ai.set_meta(&"drum_phase", "post_teleport_light")
		_start_slot_attack(boss_slot, "teleport", 0.0)
	refresh_pointer_valid()
	return boss_slot


func _execute_boss_teleport_relocation(slot: Dictionary) -> void:
	var mnode := slot.get("node") as Node2D
	if mnode == null or not is_instance_valid(mnode) or arena == null or arena.player_node == null:
		return
	var px: float = arena.player_node.position.x
	var hero_floor_y := float(arena.call("_ground_y_at", px))
	var p_rect := _get_player_body_rect()
	var b_rect := _get_slot_body_rect(slot)
	var pw := p_rect.size.x if p_rect.size.x > 0.0 else 44.0 * float(arena.char_scale)
	var bw := b_rect.size.x if b_rect.size.x > 0.0 else 56.0 * float(slot["scale_val"])
	var target_dist := (pw + bw) * 0.5 + 36.0
	var side := -1.0 if mnode.position.x <= px else 1.0
	var min_b := float(slot["zone_min_x"])
	var max_b := float(slot["zone_max_x"])
	var entry: Dictionary = arena.call("_find_character_entry_ro", str(slot["character_id"]))
	var dims: Vector2i = arena.call("_get_body_dims", entry)
	var half_w := (float(dims.x) * float(slot["scale_val"]) * 0.5) if dims.x > 0 else (56.0 * float(slot["scale_val"]))

	var primary_x := float(arena.call("_resolve_terrain_horizontal_move", px, px + side * target_dist, hero_floor_y, false, min_b, max_b, half_w))
	var chosen_x := primary_x
	if absf(primary_x - px) < maxf(24.0, target_dist * 0.45):
		var alt_x := float(arena.call("_resolve_terrain_horizontal_move", px, px - side * target_dist, hero_floor_y, false, min_b, max_b, half_w))
		if absf(alt_x - px) > absf(primary_x - px):
			chosen_x = alt_x
	mnode.position.x = chosen_x
	mnode.position.y = float(arena.call("_ground_y_at", chosen_x))
	slot["vy"] = 0.0
	var want_left := px < mnode.position.x
	var sc := float(slot["scale_val"])
	slot["facing_left"] = want_left
	mnode.scale = Vector2(-sc if want_left else sc, sc)


func _step_boss_drum_ai(slot: Dictionary, delta: float) -> void:
	var mnode := slot.get("node") as Node2D
	if mnode == null or not is_instance_valid(mnode):
		return
	_boss_teleport_chase_cd_s = maxf(0.0, _boss_teleport_chase_cd_s - delta)
	var ai := slot.get("ai") as UtilityAIController
	if ai != null:
		ai.tick_cooldown(delta)

	if not player_spawned or player_dead or arena.player_node == null or not is_instance_valid(arena.player_node):
		if ai != null and ai.has_method("reset_drum_state"):
			ai.reset_drum_state()
		_step_slot_patrol(slot, delta)
		return

	if float(slot["stun_timer_s"]) > 0.0:
		arena.call("_ensure_fighter_locomotion", mnode, "idle", bool(slot["preserve_phase"]))
		return

	var px: float = arena.player_node.position.x
	var py: float = arena.player_node.position.y
	var self_rect := _get_slot_body_rect(slot)
	var target_rect := _get_player_body_rect()
	var res: Dictionary = {}
	if ai != null:
		res = ai.evaluate({
			"character_id": "drum",
			"is_flying": false,
			"is_stationary": false,
			"has_heavy": false,
			"has_power_up": true,
			"light_clip": "attack_light",
			"self_rect": self_rect,
			"target_rect": target_rect,
			"self_x": mnode.position.x,
			"target_x": px,
			"facing_left": mnode.scale.x < 0.0,
			"is_busy": false,
		})

	var dx_p := px - mnode.position.x
	if absf(dx_p) > 12.0:
		var want_left: bool = bool(res.get("desired_face_left", dx_p < 0.0))
		if (mnode.scale.x < 0.0) != want_left:
			var sc := float(slot["scale_val"])
			slot["facing_left"] = want_left
			mnode.scale = Vector2(-sc if want_left else sc, sc)

	var intent := str(res.get("intent", "idle"))
	var dy := absf(py - mnode.position.y)
	var edge_dist := float(res.get("edge_dist", _compute_slot_edge_gap(slot)))

	if intent == "attack":
		var clip := str(res.get("attack_clip", "attack_light"))
		if clip == "attack_light" and dy > 110.0 and _boss_teleport_chase_cd_s <= 0.0:
			if ai != null:
				ai.set_meta(&"drum_engaged", true)
				ai.set_meta(&"drum_phase", "post_teleport_light")
			_boss_teleport_chase_cd_s = 2.0
			_start_slot_attack(slot, "teleport", 0.0)
			return
		_start_slot_attack(slot, clip, 0.0)
		return
	elif intent == "wait_cooldown":
		arena.call("_ensure_fighter_locomotion", mnode, "idle", bool(slot["preserve_phase"]))
		return

	# Hero moved past 400px UtilityAI engagement range or high vertical elevation: global map pursuit!
	if _boss_teleport_chase_cd_s <= 0.0 or (dy > 110.0 and edge_dist >= 200.0):
		if ai != null:
			ai.set_meta(&"drum_engaged", true)
			ai.set_meta(&"drum_phase", "post_teleport_light")
		_boss_teleport_chase_cd_s = 2.0
		_start_slot_attack(slot, "teleport", 0.0)
		return

	var move_dir := -1 if px < mnode.position.x else 1
	var entry: Dictionary = arena.call("_find_character_entry_ro", "drum")
	var spd := float(arena.call("_get_walk_speed_px_per_s", entry, float(slot["scale_val"])))
	var dims: Vector2i = arena.call("_get_body_dims", entry)
	var moved := float(arena.call("_move_node_horizontal", mnode, float(move_dir) * spd * delta, false, float(slot["zone_min_x"]), float(slot["zone_max_x"]), float(dims.x) * float(slot["scale_val"]) * 0.5))
	if absf(moved) < 0.5 and py < mnode.position.y - 24.0:
		var fl_y := float(arena.call("_ground_y_at", mnode.position.x))
		if mnode.position.y >= fl_y - 1.0:
			slot["vy"] = -740.0
	arena.call("_ensure_fighter_locomotion", mnode, "walk", bool(slot["preserve_phase"]))


func respawn_player_at_left() -> void:
	player_dead = false
	player_hp = player_max_hp
	player_mana = 0.0
	player_respawn_timer_s = 0.0
	player_hit_flash_s = 0.0
	player_hit_shake_s = 0.0
	_player_melee_pending = false
	_player_power_pending = false
	cancel_auto_approach()
	if arena.player_node != null:
		var left_x := float(arena.walkable_min_x) + 24.0
		arena.player_node.position = Vector2(left_x, float(arena.call("_ground_y_at", left_x)))
		arena.player_vy = 0.0
		arena.player_facing_left = false
		arena.player_node.scale = Vector2(arena.char_scale, arena.char_scale)
		var pspr := arena.player_node.get_node_or_null("Sprite") as AnimatedSprite2D
		if pspr != null:
			pspr.modulate = Color.WHITE
			pspr.position.x = 0.0
		arena.call("_play_fighter_clip", arena.player_node, "idle")
	player_state_changed.emit()


func _face_player_toward_x(target_x: float) -> void:
	var pnode := arena.player_node as Node2D
	if pnode == null:
		return
	var dx: float = target_x - pnode.position.x
	if absf(dx) <= 4.0:
		return
	var want_left: bool = dx < 0.0
	arena.player_facing_left = want_left
	var sc := float(arena.char_scale)
	pnode.scale = Vector2(-sc if want_left else sc, sc)


func _step_auto_approach(delta: float) -> void:
	if not auto_approach_active or not player_spawned or player_dead or arena.player_node == null:
		cancel_auto_approach()
		return
	var pnode := arena.player_node as Node2D
	_auto_approach_timeout_s -= delta
	if _auto_approach_timeout_s <= 0.0:
		cancel_auto_approach()
		return

	if _auto_approach_kind == "item":
		if _auto_approach_item == null or not is_instance_valid(_auto_approach_item) or not _auto_approach_item.visible:
			cancel_auto_approach()
			return
		var st := str(_auto_approach_item.get("lifecycle_state"))
		if st == "collecting" or st == "collected" or st == "bag":
			cancel_auto_approach()
			return
		var dist: float = pnode.position.distance_to(_auto_approach_item.position)
		if dist <= ITEM_PICKUP_RANGE_PX and _can_pickup_item(_auto_approach_item):
			var target_item := _auto_approach_item
			cancel_auto_approach()
			_collect_single_item(target_item)
			arena.call("step_player_movement", delta, 0, 0, false, false, false, Vector2.ZERO)
			return
		var idx: float = _auto_approach_item.position.x - pnode.position.x
		var move_dir := -1 if idx < -6.0 else (1 if idx > 6.0 else 0)
		var jump_req := false
		if move_dir != 0 and not bool(arena.call("_can_cross_terrain_step", pnode.position.x, pnode.position.x + float(move_dir) * 28.0, pnode.position.y, false)):
			jump_req = true
		arena.call("step_player_movement", delta, move_dir, 0, jump_req, false, false, Vector2.ZERO)
		return

	if _auto_approach_kind == "enemy":
		var tgt := _find_slot_by_id(_auto_approach_slot_id)
		if tgt.is_empty() or not bool(tgt.get("alive", false)) or not is_instance_valid(tgt.get("node")):
			cancel_auto_approach()
			return
		var p_node := arena.player_node as Node2D
		var m_node := tgt["node"] as Node2D
		var p_rect := _get_player_body_rect()
		var m_rect := _get_slot_body_rect(tgt)
		var m_core := _get_slot_core_pos(tgt)
		var p_core := _get_player_core_pos()
		var edge_gap := _compute_slot_edge_gap(tgt)
		var v_gap := maxf(0.0, maxf(p_rect.position.y - m_rect.end.y, m_rect.position.y - p_rect.end.y))
		if edge_gap <= MELEE_STRIKE_EDGE_PX * 0.72 and v_gap <= 85.0:
			_face_player_toward_x(m_core.x)
			arena.call("step_player_movement", delta, 0, 0, false, false, false, Vector2.ZERO)
			if bool(arena.call("can_player_light_attack")):
				cancel_auto_approach()
				if bool(arena.call("_request_player_action", "attack_light")):
					_player_melee_pending = true
			return

		var p_entry: Dictionary = arena.call("_find_character_entry_ro", arena.active_character_id)
		var is_flying := bool(arena.call("_is_flying_entry", p_entry))
		if is_flying:
			var to_vec := m_core - p_core
			var avec := to_vec.normalized() if to_vec.length() > 1.0 else Vector2.ZERO
			var f_dir := -1 if avec.x < -0.18 else (1 if avec.x > 0.18 else 0)
			arena.call("step_player_movement", delta, f_dir, 0, false, false, false, avec)
			return

		var dx: float = m_core.x - p_core.x
		var move_dir := -1 if dx < -8.0 else (1 if dx > 8.0 else 0)
		var jump_req := false
		if absf(dx) <= 36.0 and v_gap > 85.0:
			if v_gap <= 190.0:
				jump_req = true
			else:
				# High flying target out of ground melee jump reach: stop cleanly underneath
				cancel_auto_approach()
				arena.call("step_player_movement", delta, 0, 0, false, false, false, Vector2.ZERO)
				return
		elif move_dir != 0:
			if not bool(arena.call("_can_cross_terrain_step", p_node.position.x, p_node.position.x + float(move_dir) * 28.0, p_node.position.y, false)):
				jump_req = true
			elif m_rect.end.y < p_rect.end.y - 24.0 and absf(dx) < 160.0:
				jump_req = true
		arena.call("step_player_movement", delta, move_dir, 0, jump_req, false, false, Vector2.ZERO)


func _step_player_combat_hooks() -> void:
	var pspr := arena.player_node.get_node_or_null("Sprite") as AnimatedSprite2D
	if pspr == null:
		return
	if _player_melee_pending:
		var anim_str := String(pspr.animation)
		var is_melee_anim := (anim_str == "attack_light" or anim_str == "attack_heavy" or anim_str == "attack_nomal")
		if is_melee_anim and pspr.frame >= 2:
			_player_melee_pending = false
			_execute_player_melee_hit("heavy" if anim_str == "attack_heavy" else "melee")
		elif not is_melee_anim:
			_player_melee_pending = false
	if _player_power_pending:
		if String(pspr.animation) == "power_up" and pspr.frame >= 10:
			_player_power_pending = false
			_launch_player_homing_orb()
		elif String(pspr.animation) != "power_up":
			_player_power_pending = false


func request_player_primary_action() -> bool:
	if not player_spawned or player_dead or arena.player_node == null:
		return false
	refresh_pointer_valid()

	if pointer_kind == "item" and pointer_item_node != null and is_instance_valid(pointer_item_node):
		if _can_pickup_item(pointer_item_node) and arena.player_node.position.distance_to(pointer_item_node.position) <= ITEM_PICKUP_RANGE_PX:
			cancel_auto_approach()
			return _collect_single_item(pointer_item_node)
		auto_approach_active = true
		_auto_approach_kind = "item"
		_auto_approach_slot_id = ""
		_auto_approach_item = pointer_item_node
		_auto_approach_timeout_s = 6.0
		return true
	if pointer_kind == "npc" and arena.shenron_summon != null and arena.shenron_summon.active:
		cancel_auto_approach()
		if arena.wish_panel != null:
			arena.wish_panel.visible = true
		return true
	if pointer_kind == "enemy" and not pointer_slot_id.is_empty():
		var pointed_tgt := _find_slot_by_id(pointer_slot_id)
		if not pointed_tgt.is_empty() and bool(pointed_tgt.get("alive", false)) and is_instance_valid(pointed_tgt.get("node")):
			var p_rect := _get_player_body_rect()
			var m_rect := _get_slot_body_rect(pointed_tgt)
			var m_core := _get_slot_core_pos(pointed_tgt)
			var edge_gap := _compute_slot_edge_gap(pointed_tgt)
			var v_gap := maxf(0.0, maxf(p_rect.position.y - m_rect.end.y, m_rect.position.y - p_rect.end.y))
			if edge_gap > MELEE_STRIKE_EDGE_PX or v_gap > 90.0:
				# Must move closer to pointed target before normal melee attack!
				auto_approach_active = true
				_auto_approach_kind = "enemy"
				_auto_approach_slot_id = pointer_slot_id
				_auto_approach_item = null
				_auto_approach_timeout_s = 6.0
				return true
			cancel_auto_approach()
			_face_player_toward_x(m_core.x)
	# If there's a ready item close by and no alive enemy within melee range, pick it up
	var nearest_enemy := _find_nearest_alive_slot_in_melee()
	if nearest_enemy.is_empty():
		for item_n in arena._dropped_item_nodes:
			if is_instance_valid(item_n) and _can_pickup_item(item_n) and arena.player_node.position.distance_to(item_n.position) <= ITEM_PICKUP_RANGE_PX:
				cancel_auto_approach()
				return _collect_single_item(item_n)
	if bool(arena.call("_request_player_action", "attack_light")):
		_player_melee_pending = true
		return true
	return false


func request_player_power_up() -> bool:
	if not player_spawned or player_dead or arena.player_node == null:
		return false
	if player_mana < 100.0:
		return false
	cancel_auto_approach()
	var tgt := _resolve_player_attack_target(true)
	if tgt.is_empty():
		return false
	var mnode := tgt.get("node") as Node2D
	if mnode != null and is_instance_valid(mnode):
		_face_player_toward_x(mnode.position.x)
	if bool(arena.call("_request_player_action", "power_up")):
		player_mana = maxf(0.0, player_mana - 100.0)
		_player_power_pending = true
		_player_power_target = tgt
		player_state_changed.emit()
		return true
	return false


func _compute_contact_edge_point(rect_a: Rect2, rect_b: Rect2) -> Vector2:
	var cx_a := rect_a.position.x + rect_a.size.x * 0.5
	var cy_a := rect_a.position.y + rect_a.size.y * 0.45
	var hx := clampf(cx_a, rect_b.position.x, rect_b.end.x)
	var hy := clampf(cy_a, rect_b.position.y + 8.0, rect_b.end.y - 8.0)
	return Vector2(hx, hy)


func _execute_player_melee_hit(hit_kind: String = "melee") -> void:
	var tgt := _resolve_player_attack_target(false)
	if tgt.is_empty():
		return
	var p_rect := _get_player_body_rect()
	var m_rect := _get_slot_body_rect(tgt)
	var edge := _compute_slot_edge_gap(tgt)
	var v_gap := maxf(0.0, maxf(p_rect.position.y - m_rect.end.y, m_rect.position.y - p_rect.end.y))
	if edge > MELEE_STRIKE_EDGE_PX or v_gap > 90.0:
		return
	var p_core := _get_player_core_pos()
	var hit_pt: Vector2 = arena.call("compute_nearest_silhouette_point", tgt["node"], str(tgt["character_id"]), float(tgt["scale_val"]), p_core)
	var hit_dir := (hit_pt - p_core).normalized() if hit_pt.distance_to(p_core) > 1.0 else Vector2(-1.0 if arena.player_node.scale.x < 0.0 else 1.0, 0.0)
	var dmg := PLAYER_HEAVY_DMG if hit_kind == "heavy" else PLAYER_LIGHT_DMG
	apply_damage_to_slot(tgt, dmg, STAMINA_PER_HIT, hit_pt, hit_kind, false, hit_dir)
	player_mana = minf(player_max_mana, player_mana + PLAYER_MANA_GAIN)
	player_state_changed.emit()


func _launch_player_homing_orb() -> void:
	var tgt := _player_power_target
	if tgt.is_empty() or not bool(tgt.get("alive", false)):
		tgt = _resolve_player_attack_target(true)
	if tgt.is_empty():
		return
	var dir_x: float = -1.0 if arena.player_node.scale.x < 0.0 else 1.0
	var start_pos: Vector2 = arena.player_node.position + Vector2(42.0 * dir_x * float(arena.char_scale), -28.0 * float(arena.char_scale))
	_spawn_homing_projectile(arena.player_node, "drum", "electric_orb_fx", start_pos, float(arena.char_scale), tgt, true, PLAYER_POWER_DMG, STAMINA_PER_HIT)


func _spawn_powerup_explosion(world_pos: Vector2, scale_val: float = 0.85) -> void:
	if arena == null or PowerupExplosionFrames == null:
		return
	var ex := AnimatedSprite2D.new()
	ex.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	ex.sprite_frames = PowerupExplosionFrames
	ex.centered = false
	ex.offset = Vector2(-40.0, -40.0)
	ex.scale = Vector2(scale_val, scale_val)
	ex.position = world_pos
	ex.z_index = Z_LAYER_FX
	var parent_layer: Node = arena.fighters_layer if arena.fighters_layer != null else arena
	parent_layer.add_child(ex)
	ex.play(&"explode")
	_explosion_nodes.append(ex)
	ex.animation_finished.connect(func() -> void:
		_explosion_nodes.erase(ex)
		if is_instance_valid(ex):
			ex.queue_free()
	)


func _spawn_hit_impact_fx(world_pos: Vector2, kind: String, dmg_text: String, text_col: Color, impact_dir: Vector2 = Vector2.RIGHT) -> void:
	var dur := 0.30 if kind == "heavy" else (0.24 if (kind == "melee" or kind == "skill" or kind == "stun" or kind == "clash") else 0.18)
	var d_norm := impact_dir.normalized() if impact_dir.length_squared() > 0.001 else Vector2.RIGHT
	hit_impacts.append({"pos": world_pos, "kind": kind, "dir": d_norm, "elapsed_s": 0.0, "duration_s": dur})
	if not dmg_text.is_empty():
		floating_texts.append({
			"pos": world_pos + Vector2(0.0, -16.0),
			"text": dmg_text,
			"color": text_col,
			"elapsed_s": 0.0,
			"duration_s": 0.60,
		})


static func _apply_hit_flash_modulate(spr: AnimatedSprite2D, flash_active: bool, blink: bool, is_hero: bool) -> void:
	if spr == null:
		return
	if not flash_active:
		spr.modulate = Color.WHITE
		return
	var base := Color(1.0, 0.24, 0.24, 1.0) if blink else Color(1.0, 0.94, 0.94, 0.72)
	if not is_hero:
		base = Color(1.0, 0.35, 0.28, 1.0) if blink else Color(1.0, 0.96, 0.75, 0.75)
	var raw_flash := Color(
		base.r * HIT_FLASH_BRIGHTNESS_MUL,
		base.g * HIT_FLASH_BRIGHTNESS_MUL,
		base.b * HIT_FLASH_BRIGHTNESS_MUL,
		base.a * HIT_FLASH_ALPHA_MUL
	)
	# Reduce hit-flash and blink contrast by 40% (60% remaining contrast relative to Color.WHITE).
	spr.modulate = Color.WHITE.lerp(raw_flash, HIT_FLASH_CONTRAST_MUL)


func _step_hit_visuals(delta: float) -> void:
	if pointer_pulse_s > 0.0:
		pointer_pulse_s = maxf(0.0, pointer_pulse_s - delta)
	if pointer_x_anim_s < pointer_x_anim_dur_s:
		pointer_x_anim_s = minf(pointer_x_anim_dur_s, pointer_x_anim_s + delta)
	if pointer_x_visible_s > 0.0:
		pointer_x_visible_s = maxf(0.0, pointer_x_visible_s - delta)
	if pointer_x_double_tap_pulse_s > 0.0:
		pointer_x_double_tap_pulse_s = maxf(0.0, pointer_x_double_tap_pulse_s - delta)
	if player_hit_flash_s > 0.0 or player_hit_shake_s > 0.0:
		player_hit_flash_s = maxf(0.0, player_hit_flash_s - delta)
		player_hit_shake_s = maxf(0.0, player_hit_shake_s - delta)
		if arena.player_node != null and is_instance_valid(arena.player_node):
			var pspr := arena.player_node.get_node_or_null("Sprite") as AnimatedSprite2D
			if pspr != null:
				var pblink := int(floor(_sim_time_s * 30.0)) % 2 == 0
				_apply_hit_flash_modulate(pspr, player_hit_flash_s > 0.0, pblink, true)
				var shake_amp := (1.2 * HIT_SHAKE_SCALE_MUL) / maxf(1.0, float(arena.char_scale))
				pspr.position.x = sin(_sim_time_s * 75.0) * shake_amp if player_hit_shake_s > 0.0 else 0.0
	for s in _get_combat_slots():
		var hf := float(s.get("hit_flash_s", 0.0))
		var hs := float(s.get("hit_shake_s", 0.0))
		if hf > 0.0 or hs > 0.0:
			hf = maxf(0.0, hf - delta)
			hs = maxf(0.0, hs - delta)
			s["hit_flash_s"] = hf
			s["hit_shake_s"] = hs
			var mn := s.get("node") as Node2D
			if mn != null and is_instance_valid(mn):
				var mspr := mn.get_node_or_null("Sprite") as AnimatedSprite2D
				if mspr != null:
					var mblink := int(floor(_sim_time_s * 30.0)) % 2 == 0
					_apply_hit_flash_modulate(mspr, hf > 0.0, mblink, false)
					mspr.position.x = sin(_sim_time_s * 75.0) * (4.0 * HIT_SHAKE_SCALE_MUL) if hs > 0.0 else 0.0
	for i in range(hit_impacts.size() - 1, -1, -1):
		var imp: Dictionary = hit_impacts[i]
		imp["elapsed_s"] = float(imp["elapsed_s"]) + delta
		if float(imp["elapsed_s"]) >= float(imp["duration_s"]):
			hit_impacts.remove_at(i)
	for i in range(floating_texts.size() - 1, -1, -1):
		var ft: Dictionary = floating_texts[i]
		ft["elapsed_s"] = float(ft["elapsed_s"]) + delta
		ft["pos"] = (ft["pos"] as Vector2) + Vector2(0.0, -52.0 * delta)
		if float(ft["elapsed_s"]) >= float(ft["duration_s"]):
			floating_texts.remove_at(i)


func _trigger_slot_single_hit_anim(slot: Dictionary) -> void:
	slot["action_clip"] = ""
	slot["action_timer_s"] = 0.0
	var mnode := slot.get("node") as Node2D
	if mnode == null or not is_instance_valid(mnode):
		return
	var spr := mnode.get_node_or_null("Sprite") as AnimatedSprite2D
	if spr == null or spr.sprite_frames == null or not spr.sprite_frames.has_animation(&"hit"):
		return
	arena.call("_play_fighter_clip", mnode, "hit")
	spr.frame = 0
	spr.frame_progress = 0.0
	spr.play(&"hit")
	var hit_dur := float(arena.call("_get_clip_duration_s", mnode, "hit"))
	slot["hit_anim_timer_s"] = maxf(0.18, hit_dur)


func apply_damage_to_slot(slot: Dictionary, dmg: float, stamina_dmg: float = STAMINA_PER_HIT, hit_pos: Vector2 = Vector2(-99999.0, -99999.0), hit_kind: String = "melee", spawn_power_explosion: bool = false, impact_dir: Vector2 = Vector2.RIGHT) -> void:
	if slot.is_empty() or not bool(slot.get("alive", false)):
		return
	var fx_pos := hit_pos if hit_pos.x > -90000.0 else _get_slot_core_pos(slot)
	var dmg_lbl := "-%d%s" % [int(round(dmg)), "!" if hit_kind == "skill" else ""]
	var dmg_col := Color(0.40, 0.94, 1.0, 1.0) if hit_kind == "skill" else (Color(1.0, 0.56, 0.22, 1.0) if hit_kind == "heavy" else Color(1.0, 0.92, 0.28, 1.0))
	slot["hit_flash_s"] = 0.16
	slot["hit_shake_s"] = 0.14 * HIT_SHAKE_SCALE_MUL
	if spawn_power_explosion:
		_spawn_powerup_explosion(fx_pos, DEFAULT_EXPLOSION_SCALE)

	slot["hp"] = maxf(0.0, float(slot["hp"]) - dmg)
	if float(slot["hp"]) <= 0.0:
		_spawn_hit_impact_fx(fx_pos, hit_kind, dmg_lbl, dmg_col, impact_dir)
		_kill_slot_monster(slot)
		return
	var broke_stun := false
	if float(slot["stun_timer_s"]) <= 0.0 and float(slot["stamina"]) > 0.0:
		slot["stamina"] = maxf(0.0, float(slot["stamina"]) - stamina_dmg)
		if float(slot["stamina"]) <= 0.0:
			# Break white stamina -> 3s attack-lock window + exactly 1 HIT clip for this hit!
			broke_stun = true
			slot["stun_timer_s"] = MINI_STUN_DURATION_S
			_trigger_slot_single_hit_anim(slot)
	elif float(slot["stun_timer_s"]) > 0.0:
		# Broken stamina window active: 1 incoming hit = 1 HIT clip (0 hits when unattacked).
		_trigger_slot_single_hit_anim(slot)
	if broke_stun:
		_spawn_hit_impact_fx(fx_pos, "stun", "%s CHOÁNG!" % dmg_lbl, Color(1.0, 0.68, 0.15, 1.0), impact_dir)
	else:
		_spawn_hit_impact_fx(fx_pos, hit_kind, dmg_lbl, dmg_col, impact_dir)


func set_player_immortal(enabled: bool) -> void:
	player_immortal = enabled
	if player_immortal and player_spawned and player_dead:
		player_dead = false
		player_respawn_timer_s = 0.0
		player_hp = player_max_hp
		if arena != null and arena.player_node != null:
			arena.call("_play_fighter_clip", arena.player_node, "idle")
	elif player_immortal and player_spawned and player_hp <= 0.0:
		player_hp = player_max_hp
	player_state_changed.emit()


func apply_damage_to_player(dmg: float, hit_pos: Vector2 = Vector2(-99999.0, -99999.0), spawn_power_explosion: bool = false, hit_kind: String = "player_hit", impact_dir: Vector2 = Vector2.RIGHT) -> void:
	if not player_spawned or player_dead:
		return
	if player_immortal:
		return
	var fx_pos := hit_pos if hit_pos.x > -90000.0 else _get_player_core_pos()
	player_hit_flash_s = 0.19
	player_hit_shake_s = 0.09 * HIT_SHAKE_SCALE_MUL
	_spawn_hit_impact_fx(fx_pos, hit_kind, "-%d" % int(round(dmg)), Color(1.0, 0.28, 0.28, 1.0), impact_dir)
	if spawn_power_explosion:
		_spawn_powerup_explosion(fx_pos, DEFAULT_EXPLOSION_SCALE)
	player_hp = maxf(0.0, player_hp - dmg)
	# Owner rule: Player does NOT suffer HIT animation/interrupt
	if player_hp <= 0.0:
		player_dead = true
		player_respawn_timer_s = RESPAWN_PLAYER_DELAY_S
		_player_melee_pending = false
		_player_power_pending = false
		cancel_auto_approach()
		if arena.player_node != null:
			arena.call("_play_fighter_clip", arena.player_node, "ko")
	player_state_changed.emit()


func _kill_slot_monster(slot: Dictionary) -> void:
	var is_boss := bool(slot.get("is_boss", false))
	slot["alive"] = false
	slot["stun_timer_s"] = 0.0
	slot["action_clip"] = ""
	slot["action_timer_s"] = 0.0
	slot["respawn_timer_s"] = BOSS_DRUM_RESPAWN_DELAY_S if is_boss else RESPAWN_MONSTER_DELAY_S
	slot["ko_hide_timer_s"] = 0.75
	if is_boss:
		boss_respawn_timer_s = BOSS_DRUM_RESPAWN_DELAY_S
		boss_spawn_timer_s = 0.0
	if _auto_approach_slot_id == str(slot.get("id", "")):
		cancel_auto_approach()
	var mnode := slot.get("node") as Node2D
	var drop_pos := Vector2(float(slot["x_home"]), float(arena.call("_ground_y_at", float(slot["x_home"]))))
	if mnode != null and is_instance_valid(mnode):
		drop_pos = mnode.position
		arena.call("_play_fighter_clip", mnode, "ko")
	roll_and_spawn_dragon_ball(drop_pos, -1.0, -1.0, is_boss)
	refresh_pointer_valid()



func roll_dragon_ball_number(gate_roll_0_to_100: float = -1.0, star_roll_0_to_table: float = -1.0, is_boss: bool = false) -> int:
	if is_boss:
		var b_total := 0.0
		for row in BOSS_DROP_TABLE:
			b_total += float(row["weight"])
		var br := randf() * b_total if star_roll_0_to_table < 0.0 else star_roll_0_to_table
		var b_acc := 0.0
		for row in BOSS_DROP_TABLE:
			b_acc += float(row["weight"])
			if br < b_acc:
				return int(row["ball"])
		return int(BOSS_DROP_TABLE[BOSS_DROP_TABLE.size() - 1]["ball"])
	var gate := randf() * 100.0 if gate_roll_0_to_100 < 0.0 else gate_roll_0_to_100
	# First gate: 30% total chance to drop any Dragon Ball item
	if gate >= DRAGON_BALL_TOTAL_DROP_PCT:
		return 0
	# Passed 30% gate -> roll star using existing DRAGON_BALL_DROP_TABLE weights (sum = 67.6)
	var total_w := 0.0
	for row in DRAGON_BALL_DROP_TABLE:
		total_w += float(row["weight"])
	var r := randf() * total_w if star_roll_0_to_table < 0.0 else star_roll_0_to_table
	var acc := 0.0
	for row in DRAGON_BALL_DROP_TABLE:
		acc += float(row["weight"])
		if r < acc:
			return int(row["ball"])
	return int(DRAGON_BALL_DROP_TABLE[DRAGON_BALL_DROP_TABLE.size() - 1]["ball"])


func roll_and_spawn_dragon_ball(world_pos: Vector2, forced_gate_roll: float = -1.0, forced_star_roll: float = -1.0, is_boss: bool = false) -> Node2D:
	var ball_num := roll_dragon_ball_number(forced_gate_roll, forced_star_roll, is_boss)
	if ball_num <= 0:
		return null
	arena.item_drop_enabled = true
	var layer: Node2D = arena.call("_ensure_item_drop_layer")
	layer.z_index = 50 # Top layer: never occluded by player or monsters
	var floor_y := float(arena.call("_ground_y_at", world_pos.x))
	var px: float = arena.player_node.position.x if arena.player_node != null else world_pos.x - 40.0
	var roll_dir := -1.0 if px <= world_pos.x else 1.0
	var item := arena.DragonBallItemScene.instantiate() as Node2D
	item.set("ball_number", ball_num)
	item.z_index = 50
	item.set_meta(&"drop_age_s", 0.0)
	if item.has_signal("collected"):
		item.connect("collected", arena._on_dropped_item_collected)
	layer.add_child(item)
	item.call("start_drop_from", world_pos, floor_y, roll_dir, arena.item_drop_scale)
	arena._dropped_item_nodes.append(item)
	return item


func _can_pickup_item(item_n: Node2D) -> bool:
	if item_n == null or not is_instance_valid(item_n) or not item_n.visible:
		return false
	var st := str(item_n.get("lifecycle_state"))
	if st == "collecting" or st == "collected" or st == "bag":
		return false
	return float(item_n.get_meta(&"drop_age_s", 1.0)) >= ITEM_PICKUP_UNLOCK_S


func _collect_single_item(item_n: Node2D) -> bool:
	if arena.player_node == null or not _can_pickup_item(item_n):
		return false
	var p_entry: Dictionary = arena.call("_find_character_entry_ro", arena.active_character_id)
	var dims: Vector2i = arena.call("_get_body_dims", p_entry)
	var center_off_y := -maxf(28.0, float(dims.y) * arena.char_scale * 0.5)
	return bool(item_n.call("start_collect", arena.player_node, center_off_y, arena.player_node.position + Vector2(0.0, center_off_y)))


func _step_slot(slot: Dictionary, delta: float) -> void:
	var mnode := slot.get("node") as Node2D
	if not bool(slot["alive"]):
		if mnode != null and is_instance_valid(mnode):
			var hide_t := float(slot["ko_hide_timer_s"]) - delta
			slot["ko_hide_timer_s"] = hide_t
			if hide_t <= 0.0:
				mnode.visible = false
		if bool(slot.get("is_boss", false)):
			return
		slot["respawn_timer_s"] = float(slot["respawn_timer_s"]) - delta
		if float(slot["respawn_timer_s"]) <= 0.0:
			var next_cid := ""
			if bool(slot["is_flying"]):
				next_cid = FLYING_ROTATION[_flying_rotation_idx % FLYING_ROTATION.size()]
				_flying_rotation_idx += 1
			else:
				slot["respawn_toggle"] = not bool(slot["respawn_toggle"])
				next_cid = "dilophosaurus" if bool(slot["respawn_toggle"]) else str(slot["native_cid"])
			_spawn_slot_monster(slot, next_cid)
		return

	if mnode == null or not is_instance_valid(mnode):
		return

	# Broken-stamina attack-lock (3.0s) + single HIT clip per incoming damage (1 hit = 1 hit anim, normal movement when unattacked)
	if float(slot["stun_timer_s"]) > 0.0:
		slot["stun_timer_s"] = maxf(0.0, float(slot["stun_timer_s"]) - delta)
		if float(slot["stun_timer_s"]) <= 0.0:
			slot["stamina"] = float(slot["max_stamina"])

	if float(slot.get("hit_anim_timer_s", 0.0)) > 0.0:
		slot["hit_anim_timer_s"] = maxf(0.0, float(slot.get("hit_anim_timer_s", 0.0)) - delta)
		if float(slot["hit_anim_timer_s"]) > 0.0:
			_step_slot_vertical(slot, delta)
			return
		arena.call("_ensure_fighter_locomotion", mnode, "idle", bool(slot["preserve_phase"]))

	var can_counter_attack := float(slot["stun_timer_s"]) <= 0.0

	slot["cooldown_s"] = maxf(0.0, float(slot["cooldown_s"]) - delta)
	slot["turn_boost_s"] = maxf(0.0, float(slot["turn_boost_s"]) - delta)
	slot["turn_lock_s"] = maxf(0.0, float(slot["turn_lock_s"]) - delta)
	if float(slot["action_timer_s"]) > 0.0:
		slot["action_timer_s"] = maxf(0.0, float(slot["action_timer_s"]) - delta)
	var spr := mnode.get_node_or_null("Sprite") as AnimatedSprite2D
	var turn_pending := bool(arena.call("_is_fighter_turning", mnode))
	if not turn_pending and not str(slot["action_clip"]).is_empty():
		var finished_early := spr != null and (String(spr.animation) != str(slot["action_clip"]) or not spr.is_playing())
		var expired := float(slot["action_timer_s"]) <= 0.0 or finished_early
		_step_slot_action_effects(slot, spr, expired)
		if expired:
			slot["action_clip"] = ""
			slot["action_timer_s"] = 0.0

	if turn_pending or not str(slot["action_clip"]).is_empty():
		_step_slot_vertical(slot, delta)
		return

	if bool(slot.get("is_boss", false)):
		_step_boss_drum_ai(slot, delta)
		_step_slot_vertical(slot, delta)
		return

	var has_target := _is_player_in_slot_aggro(slot)
	if not has_target:
		if bool(slot["is_flying"]):
			_step_flying_orbit(slot, delta, false)
		else:
			_step_slot_patrol(slot, delta)
			_step_slot_vertical(slot, delta)
		return

	# Aggro behavior toward Player (Drum): deadband + turn_lock_s prevents rapid left/right flipping in place
	var px: float = arena.player_node.position.x
	var dx_to_player := px - mnode.position.x
	if absf(dx_to_player) > 26.0 and float(slot["turn_lock_s"]) <= 0.0:
		var desired_left: bool = dx_to_player < 0.0
		if not bool(slot["sideways_locked"]) and (mnode.scale.x < 0.0) != desired_left:
			_face_slot_toward(slot, desired_left)
			_step_slot_vertical(slot, delta)
			return

	var edge_gap := _compute_slot_edge_gap(slot)
	var cid := str(slot["character_id"])
	var is_fly := bool(slot["is_flying"])
	var st: Dictionary = MONSTER_STATS.get(cid, {})
	var dy_to_player := absf(arena.player_node.position.y - mnode.position.y)

	if edge_gap <= 50.0 and dy_to_player <= 110.0:
		if can_counter_attack and float(slot["cooldown_s"]) <= 0.0:
			var use_heavy := bool(slot["has_heavy"]) and int(slot["light_chain"]) >= 2
			var clip := "attack_heavy" if use_heavy else str(slot["light_clip"])
			slot["light_chain"] = 0 if use_heavy else (int(slot["light_chain"]) + 1)
			_start_slot_attack(slot, clip, 0.95)
		else:
			arena.call("_ensure_fighter_locomotion", mnode, "idle", bool(slot["preserve_phase"]))
	elif is_fly:
		# Flying monsters stay aloft, cruise in smooth circular/elliptical orbits (without flipping against player facing), and fire downward
		var fx_clip := "attack_light" if cid == "floating_camera" else ("power_up" if bool(slot["has_power_up"]) else str(slot["light_clip"]))
		if can_counter_attack and float(slot["cooldown_s"]) <= 0.0:
			_start_slot_attack(slot, fx_clip, 1.35)
		else:
			_step_flying_orbit(slot, delta, true)
		return
	else:
		# Ground monster: outer aggro >= 200px uses power_up (100 dmg); mid-range 50..200px chases player!
		if can_counter_attack and edge_gap >= 200.0 and bool(slot["has_power_up"]):
			if float(slot["cooldown_s"]) <= 0.0:
				_start_slot_attack(slot, "power_up", 1.45)
			else:
				arena.call("_ensure_fighter_locomotion", mnode, "idle", bool(slot["preserve_phase"]))
		elif edge_gap > 50.0:
			var move_dir := -1 if px < mnode.position.x else 1
			var entry: Dictionary = arena.call("_find_character_entry_ro", cid)
			var spd := float(arena.call("_get_walk_speed_px_per_s", entry, float(slot["scale_val"])))
			var dims: Vector2i = arena.call("_get_body_dims", entry)
			arena.call("_move_node_horizontal", mnode, float(move_dir) * spd * delta, false, float(slot["zone_min_x"]), float(slot["zone_max_x"]), float(dims.x) * float(slot["scale_val"]) * 0.5)
			arena.call("_ensure_fighter_locomotion", mnode, str(slot["locomotion_clip"]), bool(slot["preserve_phase"]))
		else:
			arena.call("_ensure_fighter_locomotion", mnode, "idle", bool(slot["preserve_phase"]))

	_step_slot_vertical(slot, delta)


func _step_slot_patrol(slot: Dictionary, delta: float) -> void:
	var mnode := slot["node"] as Node2D
	if float(slot["patrol_pause_s"]) > 0.0:
		slot["patrol_pause_s"] = maxf(0.0, float(slot["patrol_pause_s"]) - delta)
		arena.call("_ensure_fighter_locomotion", mnode, "idle", bool(slot["preserve_phase"]))
		return
	var pmin := maxf(float(slot["zone_min_x"]) + 60.0, float(slot["x_home"]) - 180.0)
	var pmax := minf(float(slot["zone_max_x"]) - 60.0, float(slot["x_home"]) + 180.0)
	if pmax <= pmin:
		arena.call("_ensure_fighter_locomotion", mnode, "idle", bool(slot["preserve_phase"]))
		return
	var pdir := int(slot["patrol_dir"])
	var cid := str(slot["character_id"])
	var entry: Dictionary = arena.call("_find_character_entry_ro", cid)
	var spd := float(arena.call("_get_walk_speed_px_per_s", entry, float(slot["scale_val"]))) * 0.72
	var dims: Vector2i = arena.call("_get_body_dims", entry)
	var want_left := pdir < 0
	if not bool(slot["sideways_locked"]) and (mnode.scale.x < 0.0) != want_left:
		_face_slot_toward(slot, want_left)
		return
	arena.call("_move_node_horizontal", mnode, float(pdir) * spd * delta, bool(slot["is_flying"]), pmin, pmax, float(dims.x) * float(slot["scale_val"]) * 0.5)
	arena.call("_ensure_fighter_locomotion", mnode, str(slot["locomotion_clip"]), bool(slot["preserve_phase"]))
	if pdir > 0 and mnode.position.x >= pmax - 2.0:
		slot["patrol_dir"] = -1
		slot["patrol_pause_s"] = 0.75
	elif pdir < 0 and mnode.position.x <= pmin + 2.0:
		slot["patrol_dir"] = 1
		slot["patrol_pause_s"] = 0.75


func _step_flying_orbit(slot: Dictionary, delta: float, lock_facing_to_target: bool) -> void:
	var mnode := slot["node"] as Node2D
	var cid := str(slot["character_id"])
	var entry: Dictionary = arena.call("_find_character_entry_ro", cid)
	var spd := float(arena.call("_get_walk_speed_px_per_s", entry, float(slot["scale_val"])))
	var dims: Vector2i = arena.call("_get_body_dims", entry)
	var half_w := float(dims.x) * float(slot["scale_val"]) * 0.5
	var zmin := float(slot["zone_min_x"]) + maxf(60.0, half_w)
	var zmax := float(slot["zone_max_x"]) - maxf(60.0, half_w)
	var rx := clampf((zmax - zmin) * 0.34, 90.0, 220.0)
	var ry := 52.0
	var cx := clampf(float(slot["x_home"]), zmin, zmax)
	var cy := float(slot["y_home"])

	var angular_spd := clampf(spd / maxf(110.0, rx), 0.7, 1.55) * float(slot.get("orbit_dir", 1.0))
	var phase := fmod(float(slot.get("orbit_phase", 0.0)) + angular_spd * delta, TAU)
	slot["orbit_phase"] = phase

	var desired_x := clampf(cx + cos(phase) * rx, zmin, zmax)
	var desired_y := clampf(cy + sin(phase) * ry, float(arena.fly_min_y) + 28.0, cy + 56.0)
	var step_vec := Vector2(desired_x - mnode.position.x, desired_y - mnode.position.y)
	var max_step := maxf(120.0, spd * 1.15) * delta
	if step_vec.length() > max_step:
		step_vec = step_vec.normalized() * max_step

	if not lock_facing_to_target and not bool(slot["sideways_locked"]) and float(slot["turn_lock_s"]) <= 0.0:
		var vel_x := -sin(phase) * angular_spd * rx
		if absf(vel_x) > 12.0:
			var want_left := vel_x < 0.0
			if (mnode.scale.x < 0.0) != want_left:
				_face_slot_toward(slot, want_left)
				return

	arena.call("_move_node_horizontal", mnode, step_vec.x, true, float(slot["zone_min_x"]), float(slot["zone_max_x"]), half_w)
	mnode.position.y = clampf(mnode.position.y + step_vec.y, float(arena.fly_min_y), cy + 60.0)
	slot["vy"] = 0.0
	arena.call("_ensure_fighter_locomotion", mnode, str(slot["locomotion_clip"]), bool(slot["preserve_phase"]))


func _face_slot_toward(slot: Dictionary, want_left: bool) -> void:
	var mnode := slot["node"] as Node2D
	if (mnode.scale.x < 0.0) == want_left:
		return
	var sc := float(slot["scale_val"])
	slot["turn_lock_s"] = 0.42
	if bool(slot.get("has_turn_clip", false)) and mnode.has_method(&"set_facing_left"):
		mnode.set_meta("_arena_turn_resume_clip", str(slot["locomotion_clip"]))
		if bool(mnode.call(&"set_facing_left", want_left)):
			slot["facing_left"] = want_left
			return
	slot["facing_left"] = want_left
	mnode.scale = Vector2(-sc if want_left else sc, sc)


func _start_slot_attack(slot: Dictionary, clip: String, cd_s: float) -> void:
	var mnode := slot["node"] as Node2D
	var cid := str(slot["character_id"])
	if cid == "chilopoda" and mnode.has_method(&"set_combat_target_global") and arena.player_node != null:
		mnode.call(&"set_combat_target_global", arena.player_node.position)
	elif cid == "dilophosaurus" and mnode.has_method(&"set_slash_target_global") and arena.player_node != null:
		mnode.call(&"set_slash_target_global", arena.player_node.position)
	if bool(arena.call("_play_fighter_clip", mnode, clip)):
		slot["action_clip"] = clip
		slot["action_timer_s"] = float(arena.call("_get_clip_duration_s", mnode, clip))
		slot["cooldown_s"] = cd_s
		slot["power_released"] = false
		slot["melee_hit_done"] = false
		slot["teleport_relocated"] = false


func _step_slot_action_effects(slot: Dictionary, spr: AnimatedSprite2D, force_resolve: bool = false) -> void:
	var mnode := slot["node"] as Node2D
	var cid := str(slot["character_id"])
	var clip := str(slot["action_clip"])
	var st: Dictionary = _get_slot_stats(slot)
	if clip == "teleport":
		if not bool(slot.get("teleport_relocated", false)):
			var mid_reached := force_resolve or float(slot["action_timer_s"]) <= 0.17 or (spr != null and String(spr.animation) == "teleport" and spr.frame >= 2)
			if mid_reached:
				_execute_boss_teleport_relocation(slot)
				slot["teleport_relocated"] = true
		return
	if cid == "dilophosaurus" and clip == "power_up" and mnode.has_method(&"set_slash_target_global") and arena.player_node != null:
		mnode.call(&"set_slash_target_global", _get_player_core_pos())
	elif cid == "chilopoda" and clip == "power_up" and mnode.has_method(&"set_combat_target_global") and arena.player_node != null:
		mnode.call(&"set_combat_target_global", arena.player_node.position)
	var is_ranged_power := (clip == "power_up") or (cid == "floating_camera" and clip == "attack_light")
	if is_ranged_power and not bool(slot["power_released"]):
		var rel_frame := 2
		if cid == "chilopoda" or cid == "dilophosaurus":
			rel_frame = 3
		elif cid == "floating_camera":
			rel_frame = 1
		elif cid == "drum":
			rel_frame = 10
		if force_resolve or (spr != null and spr.frame >= rel_frame):
			slot["power_released"] = true
			if cid == "dilophosaurus":
				var p_core := _get_player_core_pos()
				# Dilophosaurus keeps its dedicated 3-slash target FX without spawning the default explosion.
				apply_damage_to_player(float(st.get("power_dmg", 100.0)), p_core, false)
			else:
				_spawn_slot_homing_power(slot, float(st.get("power_dmg", 100.0)))
	elif clip in ["attack_light", "attack_heavy", "attack_nomal"] and not bool(slot["melee_hit_done"]):
		var melee_frame := 11 if cid == "chilopoda" else 2
		if force_resolve or (spr != null and spr.frame >= melee_frame):
			slot["melee_hit_done"] = true
			var p_rect := _get_player_body_rect()
			var m_rect := _get_slot_body_rect(slot)
			var edge := _compute_slot_edge_gap(slot)
			var v_gap := maxf(0.0, maxf(p_rect.position.y - m_rect.end.y, m_rect.position.y - p_rect.end.y))
			if edge <= 85.0 and arena.player_node != null and v_gap <= 95.0:
				var is_heavy := clip == "attack_heavy"
				var dmg := float(st.get("heavy_dmg", 70.0)) if is_heavy else float(st.get("light_dmg", 50.0))
				var m_core := _get_slot_core_pos(slot)
				var hit_pt: Vector2 = arena.call("compute_nearest_silhouette_point", arena.player_node, arena.active_character_id, arena.char_scale, m_core)
				var hit_dir := (hit_pt - m_core).normalized() if hit_pt.distance_to(m_core) > 1.0 else Vector2(-1.0 if mnode.scale.x < 0.0 else 1.0, 0.0)
				apply_damage_to_player(dmg, hit_pt, false, "heavy" if is_heavy else "melee", hit_dir)


func _spawn_slot_homing_power(slot: Dictionary, dmg: float) -> void:
	var mnode := slot["node"] as Node2D
	var cid := str(slot["character_id"])
	var sc := float(slot["scale_val"])
	var dir_x := -1.0 if mnode.scale.x < 0.0 else 1.0
	var fx_clip := _resolve_fx_clip_for_character(cid)
	if fx_clip.is_empty():
		apply_damage_to_player(dmg)
		return
	var start_pos := mnode.position + (Vector2(dir_x * 42.0 * sc, -28.0 * sc) if cid == "drum" else Vector2(dir_x * 46.0 * sc, -48.0 * sc))
	_spawn_homing_projectile(mnode, cid, fx_clip, start_pos, sc, {}, false, dmg, 0.0)


func _resolve_fx_clip_for_character(cid: String) -> String:
	match cid:
		"t_rex", "spinosaurus", "chilopoda":
			return "fireball_fx"
		"tasmanian_king_crab":
			return "power_orb_projectile"
		"sarcosuchus":
			return "energy_blast_fx"
		"bat_chiroptera", "pteranodon":
			return "sonic_screech_fx"
		"floating_camera":
			return "projectile_fx"
		"drum":
			return "electric_orb_fx"
	return ""


func _spawn_homing_projectile(owner_node: Node2D, cid: String, fx_clip: String, start_pos: Vector2, sc: float, target_slot: Dictionary, is_player_attack: bool, dmg: float, stamina_dmg: float) -> void:
	var spr := owner_node.get_node_or_null("Sprite") as AnimatedSprite2D
	if spr == null or spr.sprite_frames == null or not spr.sprite_frames.has_animation(StringName(fx_clip)):
		if is_player_attack:
			apply_damage_to_slot(target_slot, dmg, stamina_dmg)
		else:
			apply_damage_to_player(dmg)
		return
	var entry: Dictionary = arena.call("_find_character_entry_ro", cid)
	var pivot_arr: Variant = entry.get("render_contract", {}).get("fx_pivot_px", [176.0, 128.0])
	var pivot := Vector2(float(pivot_arr[0]), float(pivot_arr[1])) if (pivot_arr is Array and pivot_arr.size() >= 2) else Vector2(64.0, 48.0)

	var fx := AnimatedSprite2D.new()
	fx.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	fx.sprite_frames = spr.sprite_frames.duplicate() as SpriteFrames
	fx.sprite_frames.set_animation_loop(StringName(fx_clip), true)
	fx.centered = false
	fx.offset = -pivot
	fx.scale = Vector2(sc, sc)
	fx.position = start_pos
	fx.z_index = Z_LAYER_FX
	var parent_layer: Node = arena.fighters_layer if arena.fighters_layer != null else arena
	parent_layer.add_child(fx)
	fx.play(StringName(fx_clip))

	var rotate_sprite := fx_clip not in ["electric_orb_fx", "power_orb_projectile"]
	var speed := DRUM_SKILL_SPEED_PX_S if (is_player_attack or cid == "drum") else MONSTER_SKILL_SPEED_PX_S
	var init_dir := Vector2(1.0, 0.0)
	if is_player_attack and not target_slot.is_empty() and is_instance_valid(target_slot.get("node")):
		var tpos := _get_slot_core_pos(target_slot)
		if tpos.distance_to(start_pos) > 1.0:
			init_dir = (tpos - start_pos).normalized()
	elif not is_player_attack and arena.player_node != null:
		var tpos := _get_player_core_pos()
		if tpos.distance_to(start_pos) > 1.0:
			init_dir = (tpos - start_pos).normalized()
	else:
		init_dir = Vector2(-1.0 if owner_node.scale.x < 0.0 else 1.0, 0.0)

	if rotate_sprite:
		fx.rotation = init_dir.angle()
	else:
		fx.scale = Vector2(-sc if init_dir.x < 0.0 else sc, sc)

	homing_projectiles.append({
		"sprite": fx,
		"is_player": is_player_attack,
		"target_slot_id": str(target_slot.get("id", "")),
		"damage": dmg,
		"stamina_damage": stamina_dmg,
		"speed": speed,
		"vel": init_dir * speed,
		"rotate_sprite": rotate_sprite,
		"base_scale": sc,
	})


func _step_homing_projectiles(delta: float) -> void:
	# 1. Skill-vs-Skill Clash: Player power_up orb cuts through enemy projectiles with Ki clash spark
	var removed_enemy_indices: Array[int] = []
	for pi in range(homing_projectiles.size()):
		var ppr: Dictionary = homing_projectiles[pi]
		if not bool(ppr.get("is_player", false)):
			continue
		var pfx := ppr.get("sprite") as AnimatedSprite2D
		if pfx == null or not is_instance_valid(pfx):
			continue
		for ei in range(homing_projectiles.size()):
			if ei == pi or removed_enemy_indices.has(ei):
				continue
			var epr: Dictionary = homing_projectiles[ei]
			if bool(epr.get("is_player", false)):
				continue
			var efx := epr.get("sprite") as AnimatedSprite2D
			if efx == null or not is_instance_valid(efx):
				continue
			if pfx.position.distance_to(efx.position) <= 40.0:
				var mid := (pfx.position + efx.position) * 0.5
				_spawn_hit_impact_fx(mid, "clash", "VA CHẠM!", Color(1.0, 0.92, 0.35, 1.0))
				_spawn_powerup_explosion(mid, CLASH_EXPLOSION_SCALE)
				efx.queue_free()
				removed_enemy_indices.append(ei)
	removed_enemy_indices.sort()
	for ri in range(removed_enemy_indices.size() - 1, -1, -1):
		homing_projectiles.remove_at(removed_enemy_indices[ri])

	# 2. Step movement + exact non-box body silhouette impact + terrain wall stop
	for i in range(homing_projectiles.size() - 1, -1, -1):
		var pr: Dictionary = homing_projectiles[i]
		var fx := pr.get("sprite") as AnimatedSprite2D
		if fx == null or not is_instance_valid(fx):
			homing_projectiles.remove_at(i)
			continue
		var tgt_pos := fx.position
		var tgt_node: Node2D = null
		var tgt_cid := ""
		var tgt_sc := 1.0
		var valid_target := false
		var target_slot: Dictionary = {}
		if bool(pr["is_player"]):
			target_slot = _find_slot_by_id(str(pr["target_slot_id"]))
			if not target_slot.is_empty() and bool(target_slot["alive"]) and is_instance_valid(target_slot["node"]):
				tgt_node = target_slot["node"] as Node2D
				tgt_cid = str(target_slot["character_id"])
				tgt_sc = float(target_slot["scale_val"])
				tgt_pos = _get_slot_core_pos(target_slot)
				var fl_y := float(arena.call("_ground_y_at", tgt_pos.x))
				tgt_pos.y = minf(tgt_pos.y, fl_y - 24.0)
				valid_target = true
		else:
			if player_spawned and not player_dead and arena.player_node != null:
				tgt_node = arena.player_node as Node2D
				tgt_cid = str(arena.active_character_id)
				tgt_sc = float(arena.char_scale)
				tgt_pos = _get_player_core_pos()
				valid_target = true

		if not valid_target or tgt_node == null:
			fx.queue_free()
			homing_projectiles.remove_at(i)
			continue

		var to_vec := tgt_pos - fx.position
		var dist := to_vec.length()
		var speed := float(pr["speed"])
		var step_d := speed * delta
		var sc := float(pr["base_scale"])
		var proj_r := 14.0 * clampf(sc * 0.65, 0.7, 1.4)
		var proj_rect := Rect2(fx.position - Vector2(proj_r, proj_r), Vector2(proj_r * 2.0, proj_r * 2.0))
		var hits_sil := bool(arena.call("silhouette_intersects_rect", tgt_node, tgt_cid, tgt_sc, proj_rect))

		if hits_sil or dist <= maxf(16.0, step_d):
			var sil_hit: Vector2 = arena.call("compute_nearest_silhouette_point", tgt_node, tgt_cid, tgt_sc, fx.position)
			if bool(pr["is_player"]):
				apply_damage_to_slot(target_slot, float(pr["damage"]), float(pr["stamina_damage"]), sil_hit, "skill", true)
			else:
				apply_damage_to_player(float(pr["damage"]), sil_hit, true)
			fx.queue_free()
			homing_projectiles.remove_at(i)
			continue

		# Smooth 360-degree steering arc toward exact body core (tâm thân)
		var vel: Vector2 = pr.get("vel", to_vec.normalized() * speed)
		var cur_dir := vel.normalized() if vel.length_squared() > 0.001 else to_vec.normalized()
		var desired_dir := to_vec / dist
		var ang_diff := cur_dir.angle_to(desired_dir)
		var turn_rate := 18.0 if dist <= 180.0 else 7.2
		var new_dir := cur_dir.rotated(clampf(ang_diff, -turn_rate * delta, turn_rate * delta)).normalized()
		var prev_pos := fx.position
		var next_pos := prev_pos + new_dir * step_d
		var sweep_rect := Rect2(
			Vector2(minf(prev_pos.x, next_pos.x), minf(prev_pos.y, next_pos.y)),
			Vector2(absf(next_pos.x - prev_pos.x), absf(next_pos.y - prev_pos.y))
		).grow(proj_r)
		if bool(arena.call("silhouette_intersects_rect", tgt_node, tgt_cid, tgt_sc, sweep_rect)):
			var sil_hit2: Vector2 = arena.call("compute_nearest_silhouette_point", tgt_node, tgt_cid, tgt_sc, next_pos)
			if bool(pr["is_player"]):
				apply_damage_to_slot(target_slot, float(pr["damage"]), float(pr["stamina_damage"]), sil_hit2, "skill", true)
			else:
				apply_damage_to_player(float(pr["damage"]), sil_hit2, true)
			fx.queue_free()
			homing_projectiles.remove_at(i)
			continue

		if bool(arena.call("terrain_blocks_segment", prev_pos, next_pos)):
			_spawn_hit_impact_fx(prev_pos, "melee", "", Color.WHITE)
			_spawn_powerup_explosion(prev_pos, CLASH_EXPLOSION_SCALE)
			fx.queue_free()
			homing_projectiles.remove_at(i)
			continue

		pr["vel"] = new_dir * speed
		fx.position = next_pos
		if bool(pr.get("rotate_sprite", true)):
			fx.scale = Vector2(sc, sc)
			fx.rotation = new_dir.angle()
		else:
			fx.rotation = 0.0
			fx.scale = Vector2(-sc if new_dir.x < 0.0 else sc, sc)


func _step_slot_vertical(slot: Dictionary, delta: float) -> void:
	var mnode := slot.get("node") as Node2D
	if mnode == null or not is_instance_valid(mnode):
		return
	if bool(slot["is_flying"]):
		# Flying monsters stay restricted in the air (y_home ± 30), never dropping to ground
		mnode.position.y = clampf(mnode.position.y, float(arena.fly_min_y), float(slot["y_home"]) + 40.0)
		slot["vy"] = 0.0
		return
	var floor_y := float(arena.call("_ground_y_at", mnode.position.x))
	var vy := float(slot["vy"])
	if mnode.position.y < floor_y - 0.5 or vy < 0.0:
		vy = float(arena.gravity_px_per_s2) * delta if vy == 0.0 else (vy + float(arena.gravity_px_per_s2) * delta)
		var dy_step := maxf(2.0, vy * delta) if vy >= 0.0 else (vy * delta)
		mnode.position.y = minf(floor_y, mnode.position.y + dy_step)
		slot["vy"] = vy
	else:
		mnode.position.y = floor_y
		slot["vy"] = 0.0


func _is_player_in_slot_aggro(slot: Dictionary) -> bool:
	if not player_spawned or player_dead or arena.player_node == null:
		return false
	var px: float = arena.player_node.position.x
	var py: float = arena.player_node.position.y
	if px < float(slot["zone_min_x"]) or px > float(slot["zone_max_x"]):
		return false
	if bool(slot["is_flying"]):
		return py <= float(arena.call("_ground_y_at", px)) + 40.0
	var my := (slot["node"] as Node2D).position.y
	return absf(py - my) <= 220.0


func _get_player_body_rect() -> Rect2:
	if arena == null or arena.player_node == null or not is_instance_valid(arena.player_node):
		return Rect2()
	return arena.call("get_fighter_body_rect", arena.player_node, arena.active_character_id, arena.char_scale) as Rect2


func _get_slot_body_rect(slot: Dictionary) -> Rect2:
	if arena == null or slot.is_empty():
		return Rect2()
	var mnode := slot.get("node") as Node2D
	if mnode == null or not is_instance_valid(mnode):
		return Rect2()
	return arena.call("get_fighter_body_rect", mnode, str(slot["character_id"]), float(slot["scale_val"])) as Rect2


func _get_player_core_pos() -> Vector2:
	if arena == null or arena.player_node == null or not is_instance_valid(arena.player_node):
		return Vector2.ZERO
	return arena.call("get_fighter_core_world_pos", arena.player_node, arena.active_character_id, arena.char_scale) as Vector2


func _get_slot_core_pos(slot: Dictionary) -> Vector2:
	if arena == null or slot.is_empty():
		return Vector2.ZERO
	var mnode := slot.get("node") as Node2D
	if mnode == null or not is_instance_valid(mnode):
		return Vector2.ZERO
	return arena.call("get_fighter_core_world_pos", mnode, str(slot["character_id"]), float(slot["scale_val"])) as Vector2


func _compute_slot_edge_gap(slot: Dictionary) -> float:
	if arena.player_node == null or not bool(slot["alive"]) or slot["node"] == null:
		return 99999.0
	return float(arena.call("compute_silhouette_edge_gap", arena.player_node, arena.active_character_id, arena.char_scale, slot["node"], str(slot["character_id"]), float(slot["scale_val"])))


func _find_slot_by_id(sid: String) -> Dictionary:
	for s in _get_combat_slots():
		if str(s["id"]) == sid:
			return s
	return {}


func _find_nearest_alive_slot_in_melee() -> Dictionary:
	var best: Dictionary = {}
	var best_gap := MELEE_STRIKE_EDGE_PX
	for s in _get_combat_slots():
		if not bool(s["alive"]):
			continue
		var gap := _compute_slot_edge_gap(s)
		if gap <= best_gap:
			best_gap = gap
			best = s
	return best


func _resolve_player_attack_target(allow_far: bool) -> Dictionary:
	if pointer_kind == "enemy" and not pointer_slot_id.is_empty():
		var ps := _find_slot_by_id(pointer_slot_id)
		if not ps.is_empty() and bool(ps["alive"]):
			if allow_far or _compute_slot_edge_gap(ps) <= MELEE_STRIKE_EDGE_PX:
				return ps
	var best: Dictionary = {}
	var best_gap := 99999.0 if allow_far else MELEE_STRIKE_EDGE_PX
	for s in _get_combat_slots():
		if not bool(s["alive"]):
			continue
		var gap := _compute_slot_edge_gap(s)
		if gap <= best_gap:
			best_gap = gap
			best = s
	return best


func _gather_pointer_candidates() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var ref_x: float = arena.player_node.position.x if (player_spawned and arena.player_node != null) else (arena._arena_camera.position.x if arena._arena_camera != null else 960.0)
	for s in _get_combat_slots():
		if bool(s["alive"]) and is_instance_valid(s["node"]):
			var sn := s["node"] as Node2D
			out.append({"kind": "enemy", "id": str(s["id"]), "node": sn, "dist": absf(sn.position.x - ref_x)})
	for item_n in arena._dropped_item_nodes:
		if _can_pickup_item(item_n):
			out.append({"kind": "item", "id": "", "node": item_n, "dist": absf(item_n.position.x - ref_x)})
	if arena.shenron_summon != null and arena.shenron_summon.active:
		out.append({"kind": "npc", "id": "shenron", "node": arena.shenron_summon, "dist": 0.0})
	out.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["dist"]) < float(b["dist"]))
	return out


func refresh_pointer_valid() -> void:
	var cands := _gather_pointer_candidates()
	if cands.is_empty():
		pointer_kind = "enemy"
		pointer_slot_id = ""
		pointer_item_node = null
		pointer_changed.emit(pointer_kind)
		return
	for c in cands:
		if pointer_kind == "enemy" and str(c["kind"]) == "enemy" and str(c["id"]) == pointer_slot_id:
			return
		if pointer_kind == "item" and str(c["kind"]) == "item" and c["node"] == pointer_item_node:
			return
		if pointer_kind == "npc" and str(c["kind"]) == "npc":
			return
	var first := cands[0]
	pointer_kind = str(first["kind"])
	pointer_slot_id = str(first["id"])
	pointer_item_node = first["node"] as Node2D if pointer_kind == "item" else null
	pointer_changed.emit(pointer_kind)


func cycle_target_pointer() -> Dictionary:
	cancel_auto_approach()
	var cands := _gather_pointer_candidates()
	if cands.is_empty():
		pointer_kind = "enemy"
		pointer_slot_id = ""
		pointer_item_node = null
		pointer_changed.emit(pointer_kind)
		return {"kind": pointer_kind}
	var cur_idx := -1
	for i in range(cands.size()):
		var c := cands[i]
		if pointer_kind == str(c["kind"]):
			if pointer_kind == "enemy" and str(c["id"]) == pointer_slot_id:
				cur_idx = i
				break
			elif pointer_kind == "item" and c["node"] == pointer_item_node:
				cur_idx = i
				break
			elif pointer_kind == "npc":
				cur_idx = i
				break
	var next_c := cands[(cur_idx + 1) % cands.size()]
	pointer_kind = str(next_c["kind"])
	pointer_slot_id = str(next_c["id"])
	pointer_item_node = next_c["node"] as Node2D if pointer_kind == "item" else null
	pointer_pulse_s = 0.28
	pointer_x_anim_s = 0.0
	pointer_x_visible_s = POINTER_X_SHOW_DURATION_S if pointer_kind == "enemy" else 0.0
	pointer_changed.emit(pointer_kind)
	arena.queue_redraw()
	return {"kind": pointer_kind, "slot_id": pointer_slot_id}


func select_target_at_world_pos(world_pos: Vector2) -> Dictionary:
	var best_kind := ""
	var best_slot_id := ""
	var best_item: Node2D = null
	var best_dist := 999999.0

	for s in _get_combat_slots():
		if not bool(s["alive"]) or not is_instance_valid(s["node"]):
			continue
		var mnode := s["node"] as Node2D
		if bool(arena.call("silhouette_contains_point", mnode, str(s["character_id"]), float(s["scale_val"]), world_pos, 18.0)):
			var core := _get_slot_core_pos(s)
			var d := world_pos.distance_to(core)
			if d < best_dist:
				best_dist = d
				best_kind = "enemy"
				best_slot_id = str(s["id"])
				best_item = null

	for item_raw in arena._dropped_item_nodes:
		var item_n := item_raw as Node2D
		if item_n == null or not is_instance_valid(item_n) or not item_n.visible:
			continue
		var lst := str(item_n.get("lifecycle_state"))
		if lst == "collecting" or lst == "collected" or lst == "bag":
			continue
		var item_center: Vector2 = item_n.position + Vector2(0.0, -16.0 * maxf(1.0, item_n.scale.x))
		var idist: float = world_pos.distance_to(item_center)
		if idist <= 46.0 and idist < best_dist:
			best_dist = idist
			best_kind = "item"
			best_slot_id = ""
			best_item = item_n

	if best_kind.is_empty() and arena.shenron_summon != null and arena.shenron_summon.active:
		var sh_pos: Vector2 = arena.shenron_summon.position + Vector2(960.0, 420.0)
		if world_pos.distance_to(sh_pos) <= 180.0:
			best_kind = "npc"
			best_slot_id = "shenron"

	if best_kind.is_empty():
		return {"selected": false}

	var tap_dt: float = _sim_time_s - _last_tap_time_s
	var same_as_last_tap := (best_kind == _last_tap_kind) and (best_slot_id == _last_tap_slot_id) and (best_item == _last_tap_item) and (tap_dt >= 0.04 and tap_dt <= DOUBLE_TAP_WINDOW_S)
	var changed := (pointer_kind != best_kind) or (pointer_slot_id != best_slot_id) or (pointer_item_node != best_item)
	if changed:
		cancel_auto_approach()
	pointer_kind = best_kind
	pointer_slot_id = best_slot_id
	pointer_item_node = best_item
	pointer_pulse_s = 0.30
	pointer_x_anim_s = 0.0
	pointer_x_visible_s = POINTER_X_SHOW_DURATION_S if best_kind == "enemy" else 0.0
	_last_tap_kind = best_kind
	_last_tap_slot_id = best_slot_id
	_last_tap_item = best_item
	_last_tap_time_s = _sim_time_s

	var auto_attacked := false
	if same_as_last_tap and (best_kind == "enemy" or best_kind == "item"):
		if best_kind == "enemy":
			pointer_x_double_tap_pulse_s = 0.35
			pointer_x_visible_s = 0.80
		_last_tap_time_s = -99.0
		auto_attacked = request_player_primary_action()

	pointer_changed.emit(pointer_kind)
	arena.queue_redraw()
	return {"selected": true, "kind": pointer_kind, "slot_id": pointer_slot_id, "double_tap_attack": auto_attacked}


func draw_overlays(canvas: CanvasItem) -> void:
	if not active:
		return
	if show_monster_ranges:
		_draw_monster_range_overlays(canvas)
	# 1. Player overhead Green HP + Blue Mana bars
	if player_spawned and not player_dead and arena.player_node != null:
		var p_rect := _get_player_body_rect()
		var p_top: float = p_rect.position.y - 18.0
		var p_cx: float = _get_player_core_pos().x
		OverheadBarsDrawScript.draw_player_bars(canvas, p_cx, p_top, player_hp, player_max_hp, player_mana, player_max_mana)

	# 2. All alive monsters + Boss Drum: Red HP + Milky White Stamina bars
	for s in _get_combat_slots():
		if not bool(s["alive"]) or not is_instance_valid(s["node"]):
			continue
		var m_rect := _get_slot_body_rect(s)
		var e_top := m_rect.position.y - 14.0
		var e_cx := _get_slot_core_pos(s).x
		var stunned := float(s["stun_timer_s"]) > 0.0
		var is_boss := bool(s.get("is_boss", false))
		var lbl := "Drum" if is_boss else str(s["character_id"])
		OverheadBarsDrawScript.draw_enemy_bars(canvas, e_cx, e_top, float(s["hp"]), float(s["max_hp"]), float(s["stamina"]), float(s["max_stamina"]), stunned, lbl, is_boss)

	# 3. Target Pointer UI: transient Calligraphic Red "X" (only shown during touch/select interaction, then disappears)
	var x_prog := clampf(pointer_x_anim_s / maxf(0.01, pointer_x_anim_dur_s), 0.0, 1.0)
	var x_boost := 1.0 + (pointer_x_double_tap_pulse_s / 0.35) * 0.35
	if pointer_kind == "enemy" and not pointer_slot_id.is_empty():
		if pointer_x_visible_s > 0.0:
			var ps := _find_slot_by_id(pointer_slot_id)
			if not ps.is_empty() and bool(ps["alive"]) and is_instance_valid(ps["node"]):
				var s_core := _get_slot_core_pos(ps)
				var boost := x_boost * (1.15 if pointer_x_double_tap_pulse_s > 0.0 else 1.0)
				var x_fade := clampf(pointer_x_visible_s / 0.22, 0.0, 1.0)
				OverheadBarsDrawScript.draw_calligraphic_red_x(canvas, s_core, x_prog, _sim_time_s, boost, x_fade)
	elif pointer_kind == "item" and pointer_item_node != null and is_instance_valid(pointer_item_node):
		OverheadBarsDrawScript.draw_target_pointer(canvas, pointer_item_node.position + Vector2(0.0, -44.0), _sim_time_s, "item")
		if pointer_pulse_s > 0.0:
			var ir := Rect2(pointer_item_node.position - Vector2(20.0, 36.0), Vector2(40.0, 40.0))
			OverheadBarsDrawScript.draw_selection_ring(canvas, ir, pointer_pulse_s / 0.30, "item")
	elif pointer_kind == "npc" and arena.shenron_summon != null and arena.shenron_summon.active:
		OverheadBarsDrawScript.draw_target_pointer(canvas, arena.shenron_summon.position + Vector2(960.0, 260.0), _sim_time_s, "npc")

	# 4. Hit impact bursts & floating damage numbers
	for imp in hit_impacts:
		var prog := clampf(float(imp["elapsed_s"]) / maxf(0.01, float(imp["duration_s"])), 0.0, 1.0)
		OverheadBarsDrawScript.draw_hit_impact(canvas, imp["pos"] as Vector2, prog, str(imp["kind"]), imp.get("dir", Vector2.RIGHT) as Vector2)
	for ft in floating_texts:
		var fprog := clampf(float(ft["elapsed_s"]) / maxf(0.01, float(ft["duration_s"])), 0.0, 1.0)
		OverheadBarsDrawScript.draw_floating_damage(canvas, ft["pos"] as Vector2, str(ft["text"]), fprog, ft["color"] as Color)


func _draw_monster_range_overlays(canvas: CanvasItem) -> void:
	var font := ThemeDB.fallback_font
	if player_spawned and not player_dead and arena.player_node != null:
		var p_rects: Array = arena.call("get_fighter_silhouette_rects", arena.player_node, arena.active_character_id, arena.char_scale)
		for pr_r in p_rects:
			canvas.draw_rect(pr_r as Rect2, Color(0.20, 0.92, 1.0, 0.72), false, 1.5)
		var p_core := _get_player_core_pos()
		canvas.draw_line(p_core - Vector2(8.0, 0.0), p_core + Vector2(8.0, 0.0), Color(0.20, 1.0, 1.0, 0.98), 2.0)
		canvas.draw_line(p_core - Vector2(0.0, 8.0), p_core + Vector2(0.0, 8.0), Color(0.20, 1.0, 1.0, 0.98), 2.0)
	for s in _get_combat_slots():
		if not bool(s["alive"]) or not is_instance_valid(s["node"]):
			continue
		var mnode := s["node"] as Node2D
		var m_rect := _get_slot_body_rect(s)
		var cid := str(s["character_id"])
		var m_rects: Array = arena.call("get_fighter_silhouette_rects", mnode, cid, float(s["scale_val"]))
		for mr_r in m_rects:
			canvas.draw_rect(mr_r as Rect2, Color(1.0, 0.72, 0.25, 0.65), false, 1.5)
		var m_core := _get_slot_core_pos(s)
		canvas.draw_line(m_core - Vector2(8.0, 0.0), m_core + Vector2(8.0, 0.0), Color(1.0, 0.35, 0.25, 0.98), 2.0)
		canvas.draw_line(m_core - Vector2(0.0, 8.0), m_core + Vector2(0.0, 8.0), Color(1.0, 0.35, 0.25, 0.98), 2.0)
		var is_fly := bool(s["is_flying"])
		var zmin := float(s["zone_min_x"])
		var zmax := float(s["zone_max_x"])
		var floor_y := float(arena.call("_ground_y_at", mnode.position.x))
		if is_fly:
			var top_y := float(s["y_home"]) - 76.0
			var bot_y := float(arena.call("_ground_y_at", float(s["x_home"]))) + 40.0
			var air_rect := Rect2(zmin, top_y, zmax - zmin, maxf(120.0, bot_y - top_y))
			canvas.draw_rect(air_rect, Color(0.95, 0.22, 0.22, 0.08), true)
			canvas.draw_rect(air_rect, Color(1.0, 0.30, 0.30, 0.78), false, 2.5)
			canvas.draw_line(Vector2(zmin, top_y + 36.0), Vector2(zmax, top_y + 36.0), Color(1.0, 0.45, 0.45, 0.55), 1.5)
			if font != null:
				canvas.draw_string(font, Vector2(zmin + 10.0, top_y + 24.0), "[BAY] %s | Vùng [%d..%d] (%dpx)" % [cid, int(round(zmin)), int(round(zmax)), int(round(zmax - zmin))], HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color(1.0, 0.72, 0.72, 0.96))
		else:
			var g_top := floor_y - 220.0
			var g_rect := Rect2(zmin, g_top, zmax - zmin, 232.0)
			canvas.draw_rect(g_rect, Color(0.16, 0.88, 0.42, 0.09), true)
			canvas.draw_rect(g_rect, Color(0.24, 0.94, 0.48, 0.82), false, 2.5)
			# Melee <= 50px bracket around monster body edge
			var m_left := m_rect.position.x - 50.0
			var m_right := m_rect.end.x + 50.0
			var melee_rect := Rect2(m_left, floor_y - 120.0, m_right - m_left, 120.0)
			canvas.draw_rect(melee_rect, Color(1.0, 0.85, 0.20, 0.82), false, 2.0)
			# Outer PowerUp >= 200px markers
			var p_left := m_rect.position.x - 200.0
			var p_right := m_rect.end.x + 200.0
			canvas.draw_line(Vector2(p_left, floor_y - 150.0), Vector2(p_left, floor_y + 6.0), Color(0.22, 0.88, 1.0, 0.82), 2.0)
			canvas.draw_line(Vector2(p_right, floor_y - 150.0), Vector2(p_right, floor_y + 6.0), Color(0.22, 0.88, 1.0, 0.82), 2.0)
			if font != null:
				var info := "[ĐẤT] %s | [%d..%d] (%dpx) | Melee<=50 | Power>=200" % [cid, int(round(zmin)), int(round(zmax)), int(round(zmax - zmin))]
				if player_spawned and not player_dead and arena.player_node != null:
					info += " | edge=%dpx" % int(round(_compute_slot_edge_gap(s)))
				canvas.draw_string(font, Vector2(zmin + 10.0, floor_y + 28.0), info, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color(0.70, 1.0, 0.78, 0.96))
