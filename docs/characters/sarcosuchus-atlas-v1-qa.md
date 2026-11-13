# Sarcosuchus atlas demo v0.8.0

Master approved separately; atlas motion remains pending Owner Human Test.

- Body: idle12, walk8, attack_nomal8, power_up9, hit6, ko8, turn4 (55 poses). No run/jump/heavy/aura/guard/win.
- Whole-body imagegen poses from the approved master; no limb cut/warp/patch. Original idle0/turn0 retained exactly. Four perspective turn poses are used for A/D facing changes,20ticks.
- Power source: immutable `image copy.png`,690×159, six poses left-to-right. Pocket-first green key and contamination unmix; no FX redraw. One scaled source-sphere variant supplies the small charging sphere.
- Release from mouth at bodyframe2/tick10; sixFX×3ticks once; hidden at tick28. Charge anchors Canvas(237,202)/(239,190), release(244,194); projectile velocity(4,0)px/tick.
- One atlas3106×2082,61cells,62sourcePNG,63clipreferences; Nearest60Hz exact integer ticks. Canvas384×256,anchor176,224; idle body157×34,2.453×0.531m at64PPU. Measured idle Sobel254.471, hard body alpha100%; no scalar forcing.
- Technical: loop.sh test exit0,35Python/E2E,5Godotbundles,both charge tests,2Rusttests; WASMrelease exit0. Browser traversed21action/background sequences with0pageerrors; HTTP byte/hash parity and extracted GodotZIP tests exit0.716approved peer files unchanged.
- Motion: filmstrips/composite on light,dark,checker and runtime stills opened directly. Playback traces verify frame traversal and loop seams; naturalness requires Owner review. Technical results do not certify natural gait or bite feel.
- WARN: Owner-excluded reference clips remain reported; normal bite is named attack_nomal. Existing T-rex legacy tick issue is unchanged and outside this task.

Preview: http://localhost:8080/?character=sarcosuchus&clip=power_up&frame=0&paused=1

Detailed measured data and evidence: [QA JSON](sarcosuchus-atlas-v1-qa.json). No atlas approval receipt, PIPE005 or push has been created.
