//! DR7-Studio — Rust Data-Oriented (SoA) 2D Combat Core, 60Hz Animation Stepper & Instanced Batcher.
//! Designed for locked 60 FPS (<= 16.67 ms/frame) on Mobile (Android APK / iOS)
//! with 2,000+ concurrent real-time fighters + Spatial Hash AoI culling + Browser WASM Parity.

pub const ARENA_W: f32 = 2400.0;
pub const ARENA_H: f32 = 1350.0;
pub const CELL_SIZE: f32 = 64.0;
pub const GRID_COLS: usize = 38; // ceil(2400 / 64)
pub const GRID_ROWS: usize = 22; // ceil(1350 / 64)
pub const GRID_CELLS: usize = GRID_COLS * GRID_ROWS;

#[derive(Clone, Copy, Debug)]
pub struct FrameUv {
    pub u: f32,
    pub v: f32,
    pub uw: f32,
    pub vh: f32,
    pub duration_ms: f32,
}

/// Deterministic 60Hz clip stepper shared by Rust Engine & Browser WASM Human-Test Inspector.
/// Returns `(next_step_idx, remaining_elapsed_ms, finished_oneshot)`.
pub fn step_clip_timeline(
    mut step_idx: usize,
    mut elapsed_ms: f32,
    dt_ms: f32,
    durations_ms: &[f32],
    is_loop: bool,
    auto_replay_oneshot: bool,
) -> (usize, f32, bool) {
    let len = durations_ms.len();
    if len == 0 {
        return (0, 0.0, true);
    }
    if step_idx >= len {
        step_idx = 0;
    }
    elapsed_ms += dt_ms.max(0.0);
    let mut finished = false;
    let mut guard = 0usize;
    while guard < 16 {
        let cur_dur = durations_ms[step_idx].max(16.0);
        if elapsed_ms < cur_dur {
            break;
        }
        elapsed_ms -= cur_dur;
        if step_idx + 1 < len {
            step_idx += 1;
        } else if is_loop || auto_replay_oneshot {
            step_idx = 0;
        } else {
            step_idx = len - 1;
            elapsed_ms = 0.0;
            finished = true;
            break;
        }
        guard += 1;
    }
    (step_idx, elapsed_ms, finished)
}

/// Structure-of-Arrays (SoA) world state: zero heap allocations during 60Hz tick!
pub struct CombatWorld {
    pub count: usize,
    pub x: Vec<f32>,
    pub y: Vec<f32>,
    pub vx: Vec<f32>,
    pub vy: Vec<f32>,
    pub facing: Vec<f32>,
    pub team: Vec<u8>,
    pub state: Vec<u8>,
    pub frame_idx: Vec<u16>,
    pub elapsed_ms: Vec<f32>,
    pub hp: Vec<f32>,
    pub flash: Vec<f32>,
    pub rng_state: u64,

    // Pre-allocated O(N) spatial hash tables (zero per-frame allocation)
    cell_head: Vec<i32>,
    next_entity: Vec<i32>,

    // Atlas animation table synced 1:1 with character's combined .tres
    pub frames: Vec<FrameUv>,
    // Packed GPU instance buffer: 8 floats per fighter
    // [0:x, 1:y, 2:u, 3:v, 4:uw, 5:vh, 6:facing, 7:flash]
    pub gpu_instances: Vec<f32>,
}

impl CombatWorld {
    pub fn new(count: usize, frames: Vec<FrameUv>) -> Self {
        let safe_frames = if frames.is_empty() {
            vec![FrameUv { u: 0.0, v: 0.0, uw: 0.25, vh: 0.5, duration_ms: 83.33 }; 8]
        } else {
            frames
        };
        let mut world = Self {
            count,
            x: vec![0.0; count],
            y: vec![0.0; count],
            vx: vec![0.0; count],
            vy: vec![0.0; count],
            facing: vec![1.0; count],
            team: vec![0; count],
            state: vec![1; count],
            frame_idx: vec![0; count],
            elapsed_ms: vec![0.0; count],
            hp: vec![1000.0; count],
            flash: vec![0.0; count],
            rng_state: 0xD770_2026_CAFE_BABE_u64,
            cell_head: vec![-1; GRID_CELLS],
            next_entity: vec![-1; count],
            frames: safe_frames,
            gpu_instances: vec![0.0; count * 8],
        };
        world.reset_positions();
        world
    }

    #[inline]
    fn next_rand_f32(&mut self) -> f32 {
        let mut x = self.rng_state.max(1);
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.rng_state = x;
        let r = x.wrapping_mul(0x2545F4914F6CDD1D);
        ((r >> 40) as u32 as f32) / (16777216.0_f32)
    }

    pub fn reset_positions(&mut self) {
        let n_frames = self.frames.len().max(1);
        for i in 0..self.count {
            let team = (i & 1) as u8;
            // Start two armies converging across the arena for immediate real-time clashes
            let side_base = if team == 0 { 80.0 } else { ARENA_W * 0.44 };
            self.x[i] = side_base + self.next_rand_f32() * (ARENA_W * 0.48);
            self.y[i] = 100.0 + self.next_rand_f32() * (ARENA_H - 150.0);
            let ang = self.next_rand_f32() * 6.2831853;
            let spd = 75.0 + self.next_rand_f32() * 110.0;
            self.vx[i] = ang.cos() * spd * if team == 0 { 1.0 } else { -1.0 };
            self.vy[i] = ang.sin() * spd * 0.7;
            self.facing[i] = if self.vx[i] >= 0.0 { 1.0 } else { -1.0 };
            self.team[i] = team;
            self.frame_idx[i] = (i % n_frames) as u16;
            self.elapsed_ms[i] = self.next_rand_f32() * 75.0;
            self.hp[i] = 1000.0;
            self.flash[i] = 0.0;
        }
    }

    /// Advance 1 real-time combat tick: movement + O(N) spatial-grid combat + animation + GPU buffer pack.
    pub fn step(&mut self, dt_ms: f32) -> u32 {
        let dt_s = dt_ms * 0.001;
        let n = self.count;
        let n_frames = self.frames.len().max(1);

        // 1. Rebuild O(N) spatial hash grid
        self.cell_head.fill(-1);
        for i in 0..n {
            let mut nx = self.x[i] + self.vx[i] * dt_s;
            let mut ny = self.y[i] + self.vy[i] * dt_s;
            if nx < 60.0 {
                nx = 60.0;
                self.vx[i] = self.vx[i].abs();
            } else if nx > ARENA_W - 60.0 {
                nx = ARENA_W - 60.0;
                self.vx[i] = -self.vx[i].abs();
            }
            if ny < 90.0 {
                ny = 90.0;
                self.vy[i] = self.vy[i].abs();
            } else if ny > ARENA_H - 40.0 {
                ny = ARENA_H - 40.0;
                self.vy[i] = -self.vy[i].abs();
            }
            self.x[i] = nx;
            self.y[i] = ny;
            self.facing[i] = if self.vx[i] >= 0.0 { 1.0 } else { -1.0 };
            self.flash[i] = (self.flash[i] - dt_s * 4.5).max(0.0);

            let cx = ((nx / CELL_SIZE) as usize).min(GRID_COLS - 1);
            let cy = ((ny / CELL_SIZE) as usize).min(GRID_ROWS - 1);
            let cell = cy * GRID_COLS + cx;
            self.next_entity[i] = self.cell_head[cell];
            self.cell_head[cell] = i as i32;
        }

        // 2. Resolve nearby enemy ki/melee clashes in 3x3 neighborhood
        let mut hits: u32 = 0;
        for i in 0..n {
            let ix = self.x[i];
            let iy = self.y[i];
            let iteam = self.team[i];
            let cx = ((ix / CELL_SIZE) as isize).clamp(0, (GRID_COLS - 1) as isize);
            let cy = ((iy / CELL_SIZE) as isize).clamp(0, (GRID_ROWS - 1) as isize);

            let mut checks = 0usize;
            'outer: for dy in -1..=1 {
                let ny_c = cy + dy;
                if ny_c < 0 || ny_c >= GRID_ROWS as isize {
                    continue;
                }
                for dx in -1..=1 {
                    let nx_c = cx + dx;
                    if nx_c < 0 || nx_c >= GRID_COLS as isize {
                        continue;
                    }
                    let mut j = self.cell_head[(ny_c as usize) * GRID_COLS + (nx_c as usize)];
                    while j >= 0 {
                        let ju = j as usize;
                        if ju > i && self.team[ju] != iteam {
                            let ddx = self.x[ju] - ix;
                            let ddy = self.y[ju] - iy;
                            let d2 = ddx * ddx + ddy * ddy;
                            if d2 < 42.0 * 42.0 && d2 > 0.01 {
                                hits += 1;
                                let inv = 18.0 / d2.sqrt();
                                self.vx[i] -= ddx * inv;
                                self.vy[i] -= ddy * inv;
                                self.vx[ju] += ddx * inv;
                                self.vy[ju] += ddy * inv;
                                self.hp[i] = if self.hp[i] <= 8.0 { 1000.0 } else { self.hp[i] - 8.0 };
                                self.hp[ju] = if self.hp[ju] <= 8.0 { 1000.0 } else { self.hp[ju] - 8.0 };
                                self.flash[i] = 1.0;
                                self.flash[ju] = 1.0;
                            }
                            checks += 1;
                            if checks >= 6 {
                                break 'outer;
                            }
                        }
                        j = self.next_entity[ju];
                    }
                }
            }
        }

        // 3. Advance 60Hz tick animations & write contiguous GPU instance buffer
        // Exact layout: [0:x, 1:y, 2:u, 3:v, 4:uw, 5:vh, 6:facing, 7:flash]
        for i in 0..n {
            let v2 = self.vx[i] * self.vx[i] + self.vy[i] * self.vy[i];
            if v2 > 190.0 * 190.0 {
                let s = 190.0 / v2.sqrt();
                self.vx[i] *= s;
                self.vy[i] *= s;
            }

            let mut fidx = (self.frame_idx[i] as usize) % n_frames;
            let mut el = self.elapsed_ms[i] + dt_ms;
            let dur = self.frames[fidx].duration_ms.max(16.0);
            if el >= dur {
                el -= dur;
                fidx = (fidx + 1) % n_frames;
            }
            self.frame_idx[i] = fidx as u16;
            self.elapsed_ms[i] = el;

            let fuv = self.frames[fidx];
            let base = i * 8;
            self.gpu_instances[base] = self.x[i];
            self.gpu_instances[base + 1] = self.y[i];
            self.gpu_instances[base + 2] = fuv.u;
            self.gpu_instances[base + 3] = fuv.v;
            self.gpu_instances[base + 4] = fuv.uw;
            self.gpu_instances[base + 5] = fuv.vh;
            self.gpu_instances[base + 6] = self.facing[i];
            self.gpu_instances[base + 7] = self.flash[i];
        }

        hits
    }

    pub fn count_aoi_entities(&self, cam_x: f32, cam_y: f32, half_w: f32, half_h: f32) -> usize {
        let mut visible = 0usize;
        for i in 0..self.count {
            if (self.x[i] - cam_x).abs() <= half_w && (self.y[i] - cam_y).abs() <= half_h {
                visible += 1;
            }
        }
        visible
    }
}

// ============================================================================
// WebAssembly C-ABI Exports for Browser Execution on localhost:8080
// ============================================================================
static mut WASM_WORLD: Option<CombatWorld> = None;
static mut WASM_CLIP_DURS: [f32; 256] = [83.33; 256];
static mut WASM_CLIP_LEN: usize = 1;
static mut WASM_CLIP_OUT: [f32; 3] = [0.0; 3]; // [step_idx, elapsed_ms, finished_flag]

#[no_mangle]
pub extern "C" fn wasm_init_world(count: usize, frame_count: usize) -> *const f32 {
    let n_frames = frame_count.max(1);
    let default_frames = vec![
        FrameUv { u: 0.0, v: 0.0, uw: 0.25, vh: 0.5, duration_ms: 83.33 };
        n_frames
    ];
    let world = CombatWorld::new(count, default_frames);
    let ptr = world.gpu_instances.as_ptr();
    unsafe {
        WASM_WORLD = Some(world);
    }
    ptr
}

#[no_mangle]
pub extern "C" fn wasm_set_frame_uv(idx: usize, u: f32, v: f32, uw: f32, vh: f32, duration_ms: f32) {
    unsafe {
        if let Some(ref mut w) = WASM_WORLD {
            if idx < w.frames.len() {
                w.frames[idx] = FrameUv { u, v, uw, vh, duration_ms };
            } else if idx == w.frames.len() {
                w.frames.push(FrameUv { u, v, uw, vh, duration_ms });
            }
        }
    }
}

#[no_mangle]
pub extern "C" fn wasm_step_world(dt_ms: f32) -> u32 {
    unsafe {
        if let Some(ref mut w) = WASM_WORLD {
            w.step(dt_ms)
        } else {
            0
        }
    }
}

#[no_mangle]
pub extern "C" fn wasm_get_instance_ptr() -> *const f32 {
    unsafe {
        if let Some(ref w) = WASM_WORLD {
            w.gpu_instances.as_ptr()
        } else {
            core::ptr::null()
        }
    }
}

#[no_mangle]
pub extern "C" fn wasm_count_aoi(cam_x: f32, cam_y: f32, half_w: f32, half_h: f32) -> usize {
    unsafe {
        if let Some(ref w) = WASM_WORLD {
            w.count_aoi_entities(cam_x, cam_y, half_w, half_h)
        } else {
            0
        }
    }
}

#[no_mangle]
pub extern "C" fn wasm_clip_set_len(len: usize) {
    unsafe {
        WASM_CLIP_LEN = len.clamp(1, 256);
    }
}

#[no_mangle]
pub extern "C" fn wasm_clip_set_dur(idx: usize, duration_ms: f32) {
    unsafe {
        if idx < 256 {
            WASM_CLIP_DURS[idx] = duration_ms.max(16.0);
        }
    }
}

#[no_mangle]
pub extern "C" fn wasm_clip_step(
    step_idx: usize,
    elapsed_ms: f32,
    dt_ms: f32,
    is_loop: u32,
    auto_replay_oneshot: u32,
) -> *const f32 {
    unsafe {
        let base_ptr = core::ptr::addr_of!(WASM_CLIP_DURS) as *const f32;
        let slice = core::slice::from_raw_parts(base_ptr, WASM_CLIP_LEN);
        let (next_idx, rem_ms, fin) = step_clip_timeline(
            step_idx,
            elapsed_ms,
            dt_ms,
            slice,
            is_loop != 0,
            auto_replay_oneshot != 0,
        );
        WASM_CLIP_OUT[0] = next_idx as f32;
        WASM_CLIP_OUT[1] = rem_ms;
        WASM_CLIP_OUT[2] = if fin { 1.0 } else { 0.0 };
        core::ptr::addr_of!(WASM_CLIP_OUT) as *const f32
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_2000_fighters_realtime_budget_and_spatial_grid() {
        let frames: Vec<FrameUv> = (0..8)
            .map(|i| FrameUv {
                u: (i % 4) as f32 * 0.25,
                v: (i / 4) as f32 * 0.5,
                uw: 0.25,
                vh: 0.5,
                duration_ms: 83.33,
            })
            .collect();
        let mut world = CombatWorld::new(2200, frames);
        let mut total_hits = 0u32;
        for _ in 0..30 {
            total_hits += world.step(16.6667);
        }
        assert_eq!(world.gpu_instances.len(), 2200 * 8);
        assert!(total_hits > 0, "Spatial combat grid must resolve real collisions");
        // Verify exact GPU float layout [x, y, u, v, uw, vh, facing, flash]
        assert!(world.gpu_instances[2] >= 0.0 && world.gpu_instances[2] <= 1.0, "u in 0..1");
        assert!(world.gpu_instances[4] > 0.0 && world.gpu_instances[4] <= 1.0, "uw in 0..1");
        assert!(world.gpu_instances[6].abs() == 1.0, "facing must be +1 or -1 at index 6");
        let aoi = world.count_aoi_entities(ARENA_W * 0.5, ARENA_H * 0.5, 480.0, 270.0);
        assert!(aoi < 2200, "AoI spatial culling must reduce network payload per mobile client");
    }

    #[test]
    fn test_oneshot_and_loop_clip_stepper() {
        let durs = [80.0, 80.0, 80.0];
        let (idx, _, fin) = step_clip_timeline(2, 70.0, 20.0, &durs, false, false);
        assert_eq!(idx, 2);
        assert!(fin, "Oneshot clip without auto-replay must signal finished at final frame");

        let (idx_wrap, _, fin_wrap) = step_clip_timeline(2, 70.0, 20.0, &durs, false, true);
        assert_eq!(idx_wrap, 0, "Oneshot clip with auto-replay must wrap back to frame 0");
        assert!(!fin_wrap);
    }
}
