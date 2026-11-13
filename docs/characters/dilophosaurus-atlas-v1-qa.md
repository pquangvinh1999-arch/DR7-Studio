# Dilophosaurus atlas demo — v0.9.0

Owner approved master frill-v2; new atlas movement remains pending Human Test.

- Body:idle4,walk8,attack_light8,hit6,ko8,turn4,power_up24=62wholeposes. No run/jump/heavy/aura/guard/win. Body comes from new imagegen wholeposes of approved157×96master; no limb cut/warp orSpino artwork reuse.
- Power:8tickpreparation,60tick(1second)active,20tickrecovery;88ticktotal≈1.467seconds. Mouthopenswide,slightlowering/forwardreach,pairedneckfrillsphysicallycompress/expand8cycles; no externalFXfromfrills.
- Owner crescent83×95,keyRGB(6,7,13),1sourcepose; pocket-firstkey/edgeunmix,wholeFX26×48Nearest beforebakedrotations. Sourcepose isnotAIredrawn. Alpha reveal/erase vertically top→bottom orbottom→top. Three targetslashes at12/31/50tick,each6ticks,angles−40°/+35°/−70°,sametargetCanvas(320,168). No projectiletravel. Target suppliedindependently:Godot set_slash_target_global/canvas;JS targetCanvasPx. Bothglobalpositionandfacingoverrides tested.
- Oneatlas3494×2342,76cells/80PNGrefs/10clips,canvas384×256,anchor176,224,Nearest,exact60Hzticks(exportauto). Idle0matchesapprovedmasterRGBA;bodyalpha100%;FXkey/pocket/spillmeasured0. Fullgameplayenvelope(54,111,291,113);body2.453×1.5m at64PPU.
- Earlywalkfailedsupport(frame7bottom218vsground224)andrepeatedsupportrole;wholecycle regenerated, finalsupportbottom223/224,0..7→0forward. Idle4quietposesreplaceproportion-drifting12posecandidate,keeping2speriod. Dark-onlytorsoanchorfollowedlegshadows; fixedhipROIsilhouettecentroidrestoresstableX. Turnwhitefringe121/488brightboundarypixels→1/560aftergeneratedmattecleanup;claws/teethhighlightsretained. Actualvisualreviewsupplementspixelcounts.
- Technical:loop.sh testexit0,39Python/E2E,6Godotbundle,3customticktests,2Rust;WASMrelease0. Chromiumall7actions×3backgrounds,0pageerrors,88tickFXcontractcheck. GodotZIPfreshimport/bundles/targetslashtestexit0;HTTPatlas/TRES/meta/WASMbytesmatch.909approvedpeerfilesunchanged.
- Motion:all10filmstrips+powercompositeonlight/dark/checkerandbrowserstillsopened. Timingtracesverifyplayback/frameorder,notnaturalness. ReferenceclipWARNsforOwnerexclusionsandOwnerapprovalpendingremainreportedverbatiminJSON/logs. ExistingT-rexlegacytickissueunchanged/outofscope.

[Open demo](http://localhost:8080/?character=dilophosaurus&clip=power_up&frame=0&paused=1). [Detailed evidence](dilophosaurus-atlas-v1-qa.json). No PIPE006/atlasapprovalreceipt yet.
