extends SceneTree
## Benchmark thực tế trên Godot Engine 4.7.2 cho bài toán >2,000 user giao tranh 60 FPS:
## So sánh:
##   (A) Kiến trúc Node truyền thống: N × AnimatedSprite2D (1 lớp vs 3 lớp)
##   (B) Kiến trúc tối ưu Data-Oriented GDScript + MultiMeshInstance2D (1 Draw Call + Spatial Grid)

const ARENA_W := 2400.0
const ARENA_H := 1350.0
const CELL_SIZE := 64.0
const GRID_COLS := 38
const GRID_ROWS := 22
const GRID_CELLS := GRID_COLS * GRID_ROWS

func _run_node_tree_bench(count: int, steps: int) -> Dictionary:
	var sf_comb: SpriteFrames = load("res://assets/trunks_rage/godot_bundle/godot/trunks_rage.tres")
	var container := Node2D.new()
	root.add_child(container)
	var sprites: Array[AnimatedSprite2D] = []
	var pos_x := PackedFloat32Array(); pos_x.resize(count)
	var pos_y := PackedFloat32Array(); pos_y.resize(count)
	var vel_x := PackedFloat32Array(); vel_x.resize(count)
	var vel_y := PackedFloat32Array(); vel_y.resize(count)
	var team := PackedByteArray(); team.resize(count)

	var cell_head := PackedInt32Array(); cell_head.resize(GRID_CELLS)
	var next_ent := PackedInt32Array(); next_ent.resize(count)

	for i in range(count):
		pos_x[i] = fmod(float(i * 97), ARENA_W - 120.0) + 60.0
		pos_y[i] = fmod(float(i * 53), ARENA_H - 130.0) + 90.0
		vel_x[i] = 95.0 if (i % 2 == 0) else -95.0
		vel_y[i] = 55.0 if (i % 3 == 0) else -55.0
		team[i] = i & 1
		var root_sp := AnimatedSprite2D.new()
		root_sp.sprite_frames = sf_comb
		root_sp.play(&"aura_loop")
		root_sp.position = Vector2(pos_x[i], pos_y[i])
		container.add_child(root_sp)
		sprites.append(root_sp)

	var t0 := Time.get_ticks_usec()
	var total_hits := 0
	for _s in range(steps):
		cell_head.fill(-1)
		for i in range(count):
			var nx := pos_x[i] + vel_x[i] * 0.0166667
			var ny := pos_y[i] + vel_y[i] * 0.0166667
			if nx < 60.0 or nx > ARENA_W - 60.0: vel_x[i] = -vel_x[i]
			if ny < 90.0 or ny > ARENA_H - 40.0: vel_y[i] = -vel_y[i]
			pos_x[i] = nx
			pos_y[i] = ny
			sprites[i].position = Vector2(nx, ny)
			var cx := clampi(int(nx / CELL_SIZE), 0, GRID_COLS - 1)
			var cy := clampi(int(ny / CELL_SIZE), 0, GRID_ROWS - 1)
			var c := cy * GRID_COLS + cx
			next_ent[i] = cell_head[c]
			cell_head[c] = i

		for i in range(count):
			var ix := pos_x[i]
			var iy := pos_y[i]
			var it := team[i]
			var cx := clampi(int(ix / CELL_SIZE), 0, GRID_COLS - 1)
			var cy := clampi(int(iy / CELL_SIZE), 0, GRID_ROWS - 1)
			var j := cell_head[cy * GRID_COLS + cx]
			var checks := 0
			while j >= 0 and checks < 4:
				if j > i and team[j] != it:
					var ddx := pos_x[j] - ix
					var ddy := pos_y[j] - iy
					if ddx * ddx + ddy * ddy < 1764.0:
						total_hits += 1
					checks += 1
				j = next_ent[j]

	var elapsed_ms := float(Time.get_ticks_usec() - t0) / 1000.0
	container.free()
	var avg_ms := elapsed_ms / float(steps)
	return {
		"mode": "Godot 4 Node2D/AnimatedSprite2D (1-Layer Combined)",
		"fighters": count,
		"total_nodes": count,
		"avg_frame_cpu_ms": snappedf(avg_ms, 0.001),
		"budget_60fps_pct": snappedf((avg_ms / 16.6667) * 100.0, 0.1),
		"gpu_draw_calls_est": count,
		"hits_resolved": total_hits,
	}

func _run_multimesh_bench(count: int, steps: int) -> Dictionary:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_2D
	mm.use_custom_data = true
	mm.instance_count = count
	var mmi := MultiMeshInstance2D.new()
	mmi.multimesh = mm
	root.add_child(mmi)

	var pos_x := PackedFloat32Array(); pos_x.resize(count)
	var pos_y := PackedFloat32Array(); pos_y.resize(count)
	var vel_x := PackedFloat32Array(); vel_x.resize(count)
	var vel_y := PackedFloat32Array(); vel_y.resize(count)
	var team := PackedByteArray(); team.resize(count)
	var cell_head := PackedInt32Array(); cell_head.resize(GRID_CELLS)
	var next_ent := PackedInt32Array(); next_ent.resize(count)

	for i in range(count):
		pos_x[i] = fmod(float(i * 97), ARENA_W - 120.0) + 60.0
		pos_y[i] = fmod(float(i * 53), ARENA_H - 130.0) + 90.0
		vel_x[i] = 95.0 if (i % 2 == 0) else -95.0
		vel_y[i] = 55.0 if (i % 3 == 0) else -55.0
		team[i] = i & 1

	var t0 := Time.get_ticks_usec()
	var total_hits := 0
	for s in range(steps):
		cell_head.fill(-1)
		var uv_x := float((4 + (s % 4)) % 4) * 0.25
		for i in range(count):
			var nx := pos_x[i] + vel_x[i] * 0.0166667
			var ny := pos_y[i] + vel_y[i] * 0.0166667
			if nx < 60.0 or nx > ARENA_W - 60.0: vel_x[i] = -vel_x[i]
			if ny < 90.0 or ny > ARENA_H - 40.0: vel_y[i] = -vel_y[i]
			pos_x[i] = nx
			pos_y[i] = ny
			mm.set_instance_transform_2d(i, Transform2D(0.0, Vector2(nx, ny)))
			mm.set_instance_custom_data(i, Color(uv_x, 0.5, 0.25, 0.5))
			var cx := clampi(int(nx / CELL_SIZE), 0, GRID_COLS - 1)
			var cy := clampi(int(ny / CELL_SIZE), 0, GRID_ROWS - 1)
			var c := cy * GRID_COLS + cx
			next_ent[i] = cell_head[c]
			cell_head[c] = i

		for i in range(count):
			var ix := pos_x[i]
			var iy := pos_y[i]
			var it := team[i]
			var cx := clampi(int(ix / CELL_SIZE), 0, GRID_COLS - 1)
			var cy := clampi(int(iy / CELL_SIZE), 0, GRID_ROWS - 1)
			var j := cell_head[cy * GRID_COLS + cx]
			var checks := 0
			while j >= 0 and checks < 4:
				if j > i and team[j] != it:
					var ddx := pos_x[j] - ix
					var ddy := pos_y[j] - iy
					if ddx * ddx + ddy * ddy < 1764.0:
						total_hits += 1
					checks += 1
				j = next_ent[j]

	var elapsed_ms := float(Time.get_ticks_usec() - t0) / 1000.0
	mmi.free()
	var avg_ms := elapsed_ms / float(steps)
	return {
		"mode": "Godot 4 MultiMeshInstance2D (1-Layer Combined Atlas)",
		"fighters": count,
		"total_nodes": 1,
		"avg_frame_cpu_ms": snappedf(avg_ms, 0.001),
		"budget_60fps_pct": snappedf((avg_ms / 16.6667) * 100.0, 0.1),
		"gpu_draw_calls_est": 1,
		"hits_resolved": total_hits,
	}

func _init() -> void:
	var results := [
		_run_node_tree_bench(500, 60),
		_run_node_tree_bench(2000, 60),
		_run_node_tree_bench(5000, 60),
		_run_multimesh_bench(500, 60),
		_run_multimesh_bench(2000, 60),
		_run_multimesh_bench(5000, 60),
	]
	print("GODOT_BENCH_JSON=" + JSON.stringify({"engine": "Godot 4.7.2 GDScript (1-Layer Combined Atlas)", "benchmarks": results}))
	quit(0)
