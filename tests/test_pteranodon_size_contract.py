"""Protect the approved gameplay size, authored timing and independent FX anchor."""
import json,re,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text())
class PteranodonSizeContract(unittest.TestCase):
 def test_runtime_matches_owner_approved_size_sample(self):
  live=Image.open(ROOT/'assets/pteranodon/clips/frames/frame-00.png').convert('RGBA')
  sample=Image.open(ROOT/'work/reviews/character-size-v1/pteranodon-sample.png').convert('RGBA')
  self.assertEqual(live.size,(384,256));self.assertEqual(live.tobytes(),sample.tobytes())
  b=live.getchannel('A').getbbox();self.assertEqual((b[2]-b[0],b[3]-b[1]),(157,107))
  self.assertEqual(set(live.getchannel('A').getextrema()),{0,255})
 def test_size_change_preserves_all_authored_action_timing(self):
  old=load('work/characters/pteranodon/size-sync-v10/source/animation-clips.json')
  new=load('assets/pteranodon/clips/animation-clips.json')
  self.assertEqual(len(new['frames']),61);self.assertEqual(set(new['clips']),set(old['clips']));self.assertEqual(new['states'],old['states'])
  for name,c in new['clips'].items():
   for key in ['frames','ticks','duration_ms','loop','loop_policy','events_ms','keys','hitstop_ticks']:
    self.assertEqual(c.get(key),old['clips'][name].get(key),(name,key))
 def test_both_godot_fx_prefabs_follow_the_shared_contract(self):
  meta=load('assets/pteranodon/godot_bundle/engine-export.json');rc=meta['render_contract'];origin=rc['projectile']['origin_canvas_px'];pivot=rc['fx_pivot_px'];anchor=meta['anchor_px']
  self.assertEqual(rc['projectile']['release_frame'],2);self.assertEqual(rc['projectile']['lifetime_ticks'],14)
  text=(ROOT/'scenes/Pteranodon.tscn').read_text().split('[node name="ProjectileFX"',1)[1]
  text=text.split('[node name=',1)[0];values=re.search(r'offset = Vector2\(([^,]+), ([^)]+)\)',text)
  self.assertEqual([float(v) for v in values.groups()],[origin[i]-pivot[i]-anchor[i] for i in range(2)])
  fx=(ROOT/'scenes/PteranodonSonicWaveFX.tscn').read_text();values=re.search(r'offset = Vector2\(([^,]+), ([^)]+)\)',fx)
  self.assertEqual([float(v) for v in values.groups()],[-v for v in pivot])
