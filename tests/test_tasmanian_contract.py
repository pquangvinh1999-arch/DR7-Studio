"""Tasmanian Owner scope and orb continuity; pixel hashes do not certify natural gait."""
from pathlib import Path
import hashlib,json,unittest
from PIL import Image
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text())
class TasmanianContract(unittest.TestCase):
 def test_exact_owner_action_scope_and_size(self):
  m=read('assets/tasmanian_king_crab/clips/animation-clips.json');meta=read('assets/tasmanian_king_crab/godot_bundle/engine-export.json')
  self.assertEqual(meta['render_contract']['body_clips'],['idle','walk','attack_nomal','power_up','hit','ko'])
  self.assertEqual(set(m['clips']),set(meta['render_contract']['body_clips']+meta['render_contract']['effect_clips']))
  for excluded in ['jump','run','attack_heavy','aura_loop','guard','win']:self.assertNotIn(excluded,m['clips'])
  live=Image.open(R/'assets/tasmanian_king_crab/clips/frames/frame-00.png').convert('RGBA')
  master=Image.open(R/'assets/tasmanian_king_crab/source/master.png').convert('RGBA');self.assertEqual(live.tobytes(),master.tobytes());self.assertEqual(live.size,(384,256))
  b=live.getchannel('A').getbbox();self.assertEqual((b[2]-b[0],b[3]-b[1]),(133,64))
 def test_source_six_plus_two_bridges_and_release_from_peak(self):
  m=read('assets/tasmanian_king_crab/clips/animation-clips.json');loop=m['clips']['power_orb_loop'];proj=m['clips']['power_orb_projectile']
  self.assertEqual(len(loop['frames']),8);self.assertTrue(loop['loop']);self.assertFalse(proj['loop']);self.assertEqual(proj['frames'],[loop['frames'][i] for i in [5,6,7,0]])
  self.assertEqual(sum(m['clips']['power_up']['ticks'][:2]),24)
  evidence=read('docs/contracts/tasmanian_king_crab/fx-source-evidence.json');self.assertEqual([x['newly_generated'] for x in evidence],[False]*6+[True]*2)
  self.assertEqual([x['source_center_px'][0] for x in evidence[:6]],sorted([x['source_center_px'][0] for x in evidence[:6]],reverse=True))
  hashes=[m['frames'][i]['source']['file_sha256'] for i in loop['frames']];self.assertEqual(len(set(hashes)),8)
 def test_walk_is_forward_unique_cycle_and_body_alpha_is_hard(self):
  m=read('assets/tasmanian_king_crab/clips/animation-clips.json');walk=m['clips']['walk'];self.assertEqual(walk['loop_policy'],'cycle');self.assertEqual(len(walk['frames']),8)
  self.assertEqual(len({m['frames'][i]['source']['file_sha256'] for i in walk['frames']}),8)
  for name in ['idle','walk','attack_nomal','power_up','hit','ko']:
   for i in m['clips'][name]['frames']:
    im=Image.open(R/'assets/tasmanian_king_crab/clips'/m['frames'][i]['file']);h=im.getchannel('A').histogram();self.assertEqual(sum(h[1:255]),0,(name,i))

 def test_horizontal_flip_without_turn_contract(self):
  import hashlib
  roster=read('assets/roster.json')
  crab=next(c for c in roster['characters'] if c['character_id']=='tasmanian_king_crab')
  meta=read('assets/tasmanian_king_crab/godot_bundle/engine-export.json')
  fc=crab['facing_contract']
  self.assertEqual(fc['default_spawn_facing'],'right')
  self.assertEqual(fc['supported_spawn_facings'],['right','left'])
  loc=meta['render_contract']['locomotion']
  self.assertEqual(loc,crab['render_contract']['locomotion'])
  self.assertFalse(loc['sideways_strafe'])
  self.assertFalse(loc['lock_spawn_facing'])
  self.assertEqual(loc['default_spawn_facing'],'right')
  self.assertTrue(loc['allow_turn_or_flip'])
  self.assertEqual(loc['reverse_playback_mode'],'forward_cycle')
  self.assertTrue(loc['patrol']['enabled'])
  self.assertEqual(loc['default_scale'],1.25)
  self.assertEqual(loc['screen_speed_px_per_second'],115)
  self.assertEqual(meta['render_contract']['turning']['clip'],None)
  self.assertEqual(meta['render_contract']['turning']['method'],'instant_flip')
  self.assertEqual(meta['render_contract']['turning']['turn_speed_multiplier'],1.3)
  self.assertNotIn('turn',meta['clips'])
  prev_approval=read('docs/releases/tasmanian_king_crab-v0.7.0-approval.json')
  self.assertEqual(prev_approval['status'],'owner_approved')
  self.assertEqual(prev_approval['workflow_id'],'PIPE-004')
  self.assertTrue(bool(prev_approval['atlas_sha256']) and bool(prev_approval['tres_sha256']))
  receipt=read('assets/tasmanian_king_crab/owner_approval.json')
  self.assertEqual(receipt['status'],'owner_approved')
  self.assertEqual(receipt['workflow_id'],'PIPE-012')
  self.assertEqual(receipt['approved_revision'],'uniform-color-v1 / v0.12.0')
  self.assertEqual(hashlib.sha256((R/receipt['atlas_path']).read_bytes()).hexdigest(),receipt['atlas_sha256'])
  for rel,exp in receipt['approved_runtime_files_sha256'].items():
   self.assertEqual(hashlib.sha256((R/rel).read_bytes()).hexdigest(),exp,rel)
  frozen=R/receipt['frozen_source']
  self.assertEqual(frozen.read_bytes(),(R/receipt['clips_manifest_path']).read_bytes())
  roster_entry=next(c for c in read('assets/roster.json')['characters'] if c['character_id']=='tasmanian_king_crab')
  self.assertEqual(roster_entry['status'],'finalized_owner_approved')
  self.assertEqual(roster_entry['atlas_stage'],'finalized_owner_approved')
  self.assertEqual(roster_entry['motion_quality']['status'],'owner_approved')
  self.assertTrue(roster_entry['motion_quality']['owner_approved'])
  self.assertEqual(roster_entry['owner_animation_approval']['workflow_id'],'PIPE-012')
  self.assertEqual(roster_entry['motion_quality']['atlas_sha256'],receipt['atlas_sha256'])
  self.assertEqual(roster_entry['motion_quality']['previous_revision_atlas_sha256'],prev_approval['atlas_sha256'])
  from PIL import Image
  clips_m=read('assets/tasmanian_king_crab/clips/animation-clips.json')
  idle_lums=[]
  for cname in ('idle','walk'):
   for fi in clips_m['clips'][cname]['frames']:
    im=Image.open(R/'assets/tasmanian_king_crab/clips'/clips_m['frames'][fi]['file']).convert('RGBA')
    bb=im.getbbox();self.assertIsNotNone(bb);self.assertEqual(bb[3],224,(cname,fi))
    if cname=='idle':
     px=[r*0.299+g*0.587+b*0.114 for (r,g,b,a) in im.get_flattened_data() if a>0]
     idle_lums.append(sum(px)/len(px))
  self.assertLessEqual(max(idle_lums)-min(idle_lums),2.5)
 def test_all_body_clips_match_canonical_walk_luminance_and_palette(self):
  import numpy as np
  clips_m=read('assets/tasmanian_king_crab/clips/animation-clips.json')
  w_luma=np.array([0.299,0.587,0.114],dtype=np.float64)
  def stats_for(cname):
   lums=[];p95s=[];hi180=[];rgbs=[]
   for fi in clips_m['clips'][cname]['frames']:
    arr=np.array(Image.open(R/'assets/tasmanian_king_crab/clips'/clips_m['frames'][fi]['file']).convert('RGBA'))
    px=arr[arr[:,:,3]>0,:3].astype(np.float64)
    l=px@w_luma
    lums.append(float(l.mean()))
    p95s.append(float(np.percentile(l,95)))
    hi180.append(float((l>180).mean()*100.0))
    rgbs.append(px.mean(axis=0))
   return float(np.mean(lums)),max(p95s),max(hi180),np.mean(rgbs,axis=0)
  walk_lum,walk_p95,walk_hi,walk_rgb=stats_for('walk')
  for cname in ('idle','attack_nomal','power_up','hit','ko'):
   lum,p95,hi,rgb=stats_for(cname)
   self.assertLessEqual(abs(lum-walk_lum),3.0,(cname,lum,walk_lum))
   self.assertLessEqual(p95,walk_p95+5.0,(cname,p95,walk_p95))
   self.assertLessEqual(hi,2.5,(cname,hi))
   self.assertLessEqual(float(np.max(np.abs(rgb-walk_rgb))),3.5,(cname,rgb,walk_rgb))
