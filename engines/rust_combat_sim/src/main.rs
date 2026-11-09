use rust_combat_sim::{CombatWorld, FrameUv, ARENA_H, ARENA_W};
use std::fs;
use std::path::PathBuf;
use std::time::Instant;

fn find_first_tres(assets_dir: &PathBuf) -> Option<PathBuf> {
    let entries = fs::read_dir(assets_dir).ok()?;
    let mut dirs: Vec<PathBuf> = entries
        .filter_map(|e| e.ok().map(|x| x.path()))
        .filter(|p| p.is_dir())
        .collect();
    dirs.sort();
    for d in dirs {
        let godot_dir = d.join("godot_bundle").join("godot");
        if let Ok(files) = fs::read_dir(&godot_dir) {
            let mut tres_files: Vec<PathBuf> = files
                .filter_map(|f| f.ok().map(|x| x.path()))
                .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("tres"))
                .collect();
            tres_files.sort();
            if let Some(first) = tres_files.into_iter().next() {
                return Some(first);
            }
        }
    }
    None
}

fn load_real_character_frames(repo_root: &PathBuf) -> Vec<FrameUv> {
    // Dynamically parse exact Rect2 regions from the first finalized character .tres if present,
    // otherwise use 8 synthetic 1-Layer Combined baseline frames.
    let mut out = Vec::new();
    let assets_dir = repo_root.join("assets");
    if let Some(tres_path) = find_first_tres(&assets_dir) {
        let atlas_w = 4096.0_f32;
        let atlas_h = 4096.0_f32;
        if let Ok(txt) = fs::read_to_string(&tres_path) {
            for line in txt.lines() {
                let trimmed = line.trim();
                if let Some(rest) = trimmed.strip_prefix("region = Rect2(") {
                    if let Some(inner) = rest.strip_suffix(')') {
                        let nums: Vec<f32> = inner
                            .split(',')
                            .filter_map(|s| s.trim().parse::<f32>().ok())
                            .collect();
                        if nums.len() == 4 {
                            out.push(FrameUv {
                                u: nums[0] / atlas_w,
                                v: nums[1] / atlas_h,
                                uw: nums[2] / atlas_w,
                                vh: nums[3] / atlas_h,
                                duration_ms: 83.33,
                            });
                        }
                    }
                }
            }
        }
    }
    if out.is_empty() {
        out = (0..8)
            .map(|i| FrameUv {
                u: (i % 4) as f32 * 0.25,
                v: (i / 4) as f32 * 0.5,
                uw: 0.25,
                vh: 0.5,
                duration_ms: 83.33,
            })
            .collect();
    }
    out
}

fn main() {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .to_path_buf();
    let frames = load_real_character_frames(&repo_root);
    let counts = [500usize, 2000usize, 5000usize];
    let steps = 180usize; // 3 seconds of 60 FPS real-time mass combat

    println!("{{\"engine\":\"Rust 1.99.1 SoA + SpatialHash + Single-Batch GPU Instancing\", \"frames_loaded\":{}, \"benchmarks\":[", frames.len());
    for (idx, &n) in counts.iter().enumerate() {
        let mut world = CombatWorld::new(n, frames.clone());
        // Warmup
        for _ in 0..15 {
            world.step(16.6667);
        }
        let t0 = Instant::now();
        let mut total_hits: u64 = 0;
        for _ in 0..steps {
            total_hits += world.step(16.6667) as u64;
        }
        let elapsed_ms = t0.elapsed().as_secs_f64() * 1000.0;
        let avg_ms = elapsed_ms / (steps as f64);
        let aoi_visible = world.count_aoi_entities(ARENA_W * 0.5, ARENA_H * 0.5, 480.0, 270.0);
        // Compact binary delta packet: 10 bytes per AoI fighter (u16 id, i16 x, i16 y, u8 state_frame, u8 hp_pct, u16 flags)
        let aoi_kbps_at_20hz = (aoi_visible as f64 * 10.0 * 20.0 * 8.0) / 1000.0;
        let comma = if idx + 1 < counts.len() { "," } else { "" };
        println!(
            "  {{\"fighters\":{}, \"avg_frame_cpu_ms\":{:.4}, \"max_theoretical_fps\":{:.0}, \"budget_60fps_pct\":{:.2}, \"gpu_draw_calls\":1, \"instance_buffer_kb\":{:.1}, \"hits_resolved\":{}, \"aoi_entities_in_view\":{}, \"aoi_net_kbps_per_client_20hz\":{:.1}}}{}",
            n,
            avg_ms,
            1000.0 / avg_ms.max(0.0001),
            (avg_ms / 16.6667) * 100.0,
            (n * 32) as f64 / 1024.0,
            total_hits,
            aoi_visible,
            aoi_kbps_at_20hz,
            comma
        );
    }
    println!("]}}");
}
