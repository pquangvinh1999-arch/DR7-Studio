"""Install Owner-requested burrow turn without changing any other clip's pixels/ticks."""
from pathlib import Path
import json,hashlib,shutil
W=Path(__file__).resolve().parent;R=W.parents[3];S=W/'stage';A=R/'assets/chilopoda'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
plan=read(W/'plan.json');m=read(S/'clips/animation-clips.json');meta=read(S/'godot_bundle/engine-export.json')
baseline=read(W/'turn-burrow-before.json')
for name,row in baseline.items():
 c=m['clips'][name];assert c['ticks']==row['ticks'],name
 assert [sha(S/'clips'/m['frames'][i]['file']) for i in c['frames']]==row['hashes'],name
old=read(A/'godot_bundle/engine-export.json');meta['source']['path']='../clips/animation-clips.json';meta['render_contract']=plan['render_contract'];meta['provenance']=old['provenance'];meta['provenance']['turn_source']='Own complete walk0 and burrow attack poses, no bodypart editing; facing changes only while fully underground.'
write(S/'godot_bundle/engine-export.json',meta)
# Preserve the previous admission for review; replace only this character's exports.
archive=W/'live-surface-turn-baseline'
if not archive.exists():shutil.copytree(A,archive)
for folder in ['clips','godot_bundle']:
 shutil.rmtree(A/folder);shutil.copytree(S/folder,A/folder)
(A/'clips/.gdignore').touch()
digest=sha(A/'godot_bundle/godot/chilopoda-atlas-00.png')
roster=read(R/'assets/roster.json');ch=next(c for c in roster['characters'] if c['character_id']=='chilopoda')
ch['render_contract']=plan['render_contract'];ch['facing_contract']['left_facing_rule']='36tick burrow turn at either endpoint: hidden ticks16..21, commit facing16, emerge22, resume opposite walk36. Full own-character poses; no visible flip or root relocation.'
review=ch['motion_quality'];review.update(status='pending',atlas_sha256=digest,naturalness_verdict='pending_visual_review_and_owner',notes='Owner replaces surface turn with burrow/reorient/emerge. All nonturn clip pixels/ticks verified unchanged; new runtime visual evidence pending.')
review['checks']['perspective_turns']=False;review['checks']['burrow_turn_bidirectional']=False
ch['status']='demo_pending_verification';write(R/'assets/roster.json',roster);write(W/'review/keyframe-review.json',review)
qa=read(R/'docs/characters/chilopoda-atlas-v1-qa.json');qa.update(atlas_sha256=digest,atlas=meta['atlas'],frames=len(m['frames']),render_contract=plan['render_contract'],motion_quality=review,technical_checks='pending',status='burrow_turn_revision_pending_checks');write(R/'docs/characters/chilopoda-atlas-v1-qa.json',qa)
protected=read(W/'protected-peers.json');assert not [p for p,h in protected.items() if p!='assets/roster.json' and sha(R/p)!=h]
print(json.dumps({'atlas_sha256':digest,'frames':len(m['frames']),'clips':len(m['clips']),'unchanged_nonturn_clips':list(baseline),'protected_peer_files':len(protected)-1}))
