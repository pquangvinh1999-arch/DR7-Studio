# Bat - Chiroptera demo

Owner requested the same animation set and timing as the approved Pteranodon, with purple sonic waves. The Bat master shown in the preceding review is the identity reference. The inherited Pteranodon sheets are motion references only; all Bat body poses were generated as complete bodies with built-in imagegen.

- Rest silhouette:126×81px, canvas384×256, anchor[176,200]. Width126 is157×0.8 rounded to an integer. Bat anatomy retains its own aspect ratio.
- Body clips:`idle`8×7ticks, `walk`8×6ticks, `run`8×4ticks, `attack_light`8poses/38ticks, `power_up`8poses/40ticks, `hit`6poses/28ticks, `ko`8poses/52ticks. `run` has independent fast-flight poses.
- Independent `sonic_screech_fx`:7phases×2ticks, released at bodyframe2/tick10, hidden at tick24. Mouth origin[225,165], FXpivot[176,141]. Original Pteranodon phase silhouettes/alpha are preserved before a uniform0.8 scale; hue0.772222 is sampled from the imagegen purple variant. No body emission was baked into body frames.
- One3106×2082atlas,61frames,8clips,Nearest,60Hz. Body is `combined_1layer`; FX adds a quad. Godot and localhost read the same rectangles, PNG and contract.
- Inherit Pteranodon scope: no `jump`, `attack_heavy` or Ki `aura_loop`; `guard`/`win` are excluded project-wide. Reference completeness warnings remain visible.

Inputs, prompts, source sheets, whole-pose registration and review evidence are in `work/characters/bat_chiroptera/atlas-v1/`. Master/SHA is frozen separately in `work/characters/bat_chiroptera/approved-master/`. No limb cutting, skeleton warping, body patching or palette/sharpness forcing was used. Body-alpha finishing uses threshold128; FX palette conversion preserves the original alpha before scaling. Native-alpha sources have no chroma-key color.

`prepare.py` records the plan and creates motion-only guide sheets; it must not overwrite the identity master when revising animations. The8generation prompts are preserved under `prompts/`. `build_frames.py` consumes the generated sheets, then the project skill's `build_animation_clips.py` and `export_engine.py --godot-fps auto` package them. `install_demo.py` is an initial admission script, not an overwrite/revision command. It requires recorded visual review and preserves all1137existing runtime peer files, excluding roster.json, which receives the new entry.

Validation:44Python/E2Etests,7Godotbundles,4GodotFXtests,2Rusttests and releaseWASM build returned exit0. The downloadable Godot ZIP also imported and passed bundle/Batsonic tests. CI includes the new contract/FX tests; remote CI was not run in this task. Browser24clip/background sequences returned0pageerrors; all54bodyposes were observed. Five individual33ms FX pose observations were missed in recorded headless playback; all61poses were observed in the offline3background playback, and the live40tick contract exactly matches release/lifetime/placement. This is not a mobile60FPS claim.

All8filmstrips and the power composite were opened directly on light/dark/checker backgrounds. Browser screenshots and recording preserve actual playback evidence. Structural self-review is `reviewed_pending_owner`; final naturalness and matching the requested Pteranodon motion await Owner Human Test. No final acceptance receipt or `skills.md` workflow has been created.

Human test: <http://localhost:8080/?character=bat_chiroptera&clip=power_up>. QA JSON: `docs/characters/bat-chiroptera-atlas-v1-qa.json`.

Owner đã nghiệm thu toàn bộ Bat lúc 2026-11-13T06:34:45.229155+00:00; chốt PIPE-007 và receipt `assets/bat_chiroptera/owner_approval.json`. Nội dung chờ nghiệm thu phía trên là lịch sử trước thời điểm này. Ảnh/timing giữ nguyên; dùng `approved-final-frames/` làm nguồn tái xuất.
