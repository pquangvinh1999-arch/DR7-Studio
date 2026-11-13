"""Sarcosuchus Owner scope and orb continuity; pixel hashes do not certify natural gait."""
from pathlib import Path
import hashlib,json,unittest
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text())
class SarcosuchusContract(unittest.TestCase):
 def test_exact_owner_action_scope_and_size(self):
  m=read('assets/sarcosuchus/clips/animation-clips.json');meta=read('assets/sarcosuchus/godot_bundle/engine-export.json')
  self.assertEqual(meta['render_contract']['body_clips'],['idle','walk','attack_nomal','power_up','hit','ko','turn'])
  self.assertEqual(set(m['clips']),set(meta['render_contract']['body_clips']+meta['render_contract']['effect_clips']))
  for excluded in ['jump','run','attack_heavy','aura_loop','guard','win']:self.assertNotIn(excluded,m['clips'])
  live=Image.open(R/'assets/sarcosuchus/clips/frames/frame-00.png').convert('RGBA')
  master=Image.open(R/'work/characters/sarcosuchus/master-review/master-gameplay-v1.png').convert('RGBA');self.assertEqual(live.tobytes(),master.tobytes());self.assertEqual(live.size,(384,256))
  b=live.getchannel('A').getbbox();self.assertEqual((b[2]-b[0],b[3]-b[1]),(157,34))
 def test_source_six_in_order_once_and_mouth_release(self):
  m=read('assets/sarcosuchus/clips/animation-clips.json');meta=read('assets/sarcosuchus/godot_bundle/engine-export.json');proj=m['clips']['energy_blast_fx'];charge=m['clips']['energy_charge_fx']
  self.assertEqual(len(proj['frames']),6);self.assertFalse(proj['loop']);self.assertFalse(charge['loop']);self.assertEqual(proj['ticks'],[3]*6)
  self.assertEqual(sum(m['clips']['power_up']['ticks'][:2]),10);self.assertEqual(meta['render_contract']['projectile']['origin_canvas_px'],[244,194])
  evidence=read('work/characters/sarcosuchus/atlas-v1/fx-source-evidence.json');self.assertEqual([x['new_AI_pose'] for x in evidence],[False]*6)
  self.assertEqual([x['source_center_px'][0] for x in evidence],sorted(x['source_center_px'][0] for x in evidence))
  self.assertEqual(hashlib.sha256((R/'work/characters/sarcosuchus/atlas-v1/source/power-up-owner.png').read_bytes()).hexdigest(),'8c7f70a42344094cfce44ca961bc7ad2c72761cebe3061da985b3b74a1c8acde')
  for idx in proj['frames']:
   a=np.array(Image.open(R/'assets/sarcosuchus/clips'/m['frames'][idx]['file']));visible=a[:,:,3]>0
   self.assertFalse(np.any(visible&(a[:,:,1].astype(int)>np.maximum(a[:,:,0],a[:,:,2]).astype(int)+1)),'No green-key rim may survive on blue/white source FX')
  self.assertEqual(len(m['clips']['turn']['frames']),4);self.assertEqual(sum(m['clips']['turn']['ticks']),20)
  for name,c in meta['clips'].items():self.assertEqual(c['godot']['relative_durations'],c['ticks'],name)
 def test_walk_is_forward_unique_cycle_and_body_alpha_is_hard(self):
  m=read('assets/sarcosuchus/clips/animation-clips.json');walk=m['clips']['walk'];self.assertEqual(walk['loop_policy'],'cycle');self.assertEqual(len(walk['frames']),8)
  self.assertEqual(len({m['frames'][i]['source']['file_sha256'] for i in walk['frames']}),8)
  for name in ['idle','walk','attack_nomal','power_up','hit','ko','turn']:
   for i in m['clips'][name]['frames']:
    im=Image.open(R/'assets/sarcosuchus/clips'/m['frames'][i]['file']);h=im.getchannel('A').histogram();self.assertEqual(sum(h[1:255]),0,(name,i))

 def test_charge_fits_jaw_and_launch_keeps_its_size(self):
  m=read('assets/sarcosuchus/clips/animation-clips.json');meta=read('assets/sarcosuchus/godot_bundle/engine-export.json');c=meta['render_contract'];root=R/'assets/sarcosuchus/clips'
  def im(idx):return Image.open(root/m['frames'][idx]['file']).convert('RGBA')
  charge=[im(i) for i in m['clips']['energy_charge_fx']['frames']];launch=im(m['clips']['energy_blast_fx']['frames'][0])
  self.assertEqual(len(charge),10);self.assertEqual(m['clips']['energy_charge_fx']['ticks'],[1]*10)
  widths=[x.getbbox()[2]-x.getbbox()[0] for x in charge];self.assertEqual(widths,sorted(widths));self.assertEqual((widths[0],widths[-1]),(1,10))
  b=charge[-1].getbbox();self.assertEqual(b[3]-b[1],9);self.assertEqual(charge[-1].tobytes(),launch.tobytes())
  alpha=[np.array(x)[:,:,3].sum() for x in charge];self.assertEqual(alpha,sorted(alpha))
  for t,fx in enumerate(charge+[launch]):
   bi=t//5;body=np.array(im(m['clips']['power_up']['frames'][bi]));point=c['charge']['origin_canvas_px_by_frame'][bi] if t<10 else c['projectile']['origin_canvas_px'];layer=Image.new('RGBA',(384,256));layer.alpha_composite(fx,(point[0]-176,point[1]-128));a=np.array(layer)
   teeth=(body[:,:,0]>=130)&(body[:,:,1]>=120)&(body[:,:,2]>=85)&(body[:,:,3]>0);roi=np.zeros((256,384),bool);roi[182:210,228:253]=True
   self.assertFalse(np.any(teeth&roi&(a[:,:,3]>0)),f'Orb covers bright tooth pixels at tick{t}')
  baseline=read('work/characters/sarcosuchus/power-up-v2/baseline.json')
  for name in c['body_clips']:
   for pos,idx in enumerate(m['clips'][name]['frames']):
    self.assertEqual(hashlib.sha256((root/m['frames'][idx]['file']).read_bytes()).hexdigest(),baseline['body'][f'{name}:{pos}']['sha256'])
