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
  master=Image.open(R/'work/characters/tasmanian_king_crab/size-master/master.png').convert('RGBA');self.assertEqual(live.tobytes(),master.tobytes());self.assertEqual(live.size,(384,256))
  b=live.getchannel('A').getbbox();self.assertEqual((b[2]-b[0],b[3]-b[1]),(133,64))
 def test_source_six_plus_two_bridges_and_release_from_peak(self):
  m=read('assets/tasmanian_king_crab/clips/animation-clips.json');loop=m['clips']['power_orb_loop'];proj=m['clips']['power_orb_projectile']
  self.assertEqual(len(loop['frames']),8);self.assertTrue(loop['loop']);self.assertFalse(proj['loop']);self.assertEqual(proj['frames'],[loop['frames'][i] for i in [5,6,7,0]])
  self.assertEqual(sum(m['clips']['power_up']['ticks'][:2]),24)
  evidence=read('work/characters/tasmanian_king_crab/atlas-v1/fx-source-evidence.json');self.assertEqual([x['newly_generated'] for x in evidence],[False]*6+[True]*2)
  self.assertEqual([x['source_center_px'][0] for x in evidence[:6]],sorted([x['source_center_px'][0] for x in evidence[:6]],reverse=True))
  hashes=[m['frames'][i]['source']['file_sha256'] for i in loop['frames']];self.assertEqual(len(set(hashes)),8)
 def test_walk_is_forward_unique_cycle_and_body_alpha_is_hard(self):
  m=read('assets/tasmanian_king_crab/clips/animation-clips.json');walk=m['clips']['walk'];self.assertEqual(walk['loop_policy'],'cycle');self.assertEqual(len(walk['frames']),8)
  self.assertEqual(len({m['frames'][i]['source']['file_sha256'] for i in walk['frames']}),8)
  for name in ['idle','walk','attack_nomal','power_up','hit','ko']:
   for i in m['clips'][name]['frames']:
    im=Image.open(R/'assets/tasmanian_king_crab/clips'/m['frames'][i]['file']);h=im.getchannel('A').histogram();self.assertEqual(sum(h[1:255]),0,(name,i))
