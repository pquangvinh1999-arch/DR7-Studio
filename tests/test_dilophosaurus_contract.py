"""Owner action scope, one-second burst, same-target slashes and source preservation."""
from pathlib import Path
import unittest,json,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text())
class DilophosaurusContract(unittest.TestCase):
 def data(self):return read('assets/dilophosaurus/clips/animation-clips.json'),read('assets/dilophosaurus/godot_bundle/engine-export.json')
 def test_owner_approved_revision_is_frozen(self):
  receipt=read('assets/dilophosaurus/owner_approval.json');self.assertEqual(receipt['status'],'owner_approved');self.assertEqual(receipt['workflow_id'],'PIPE-006')
  for path,digest in receipt['approved_runtime_files_sha256'].items():
   self.assertEqual(hashlib.sha256((R/path).read_bytes()).hexdigest(),digest,path)
  frozen=R/receipt['frozen_source'];live=R/receipt['clips_manifest_path'];self.assertEqual(frozen.read_bytes(),live.read_bytes())
  manifest=json.loads(frozen.read_text())
  for f in manifest['frames']:
   self.assertEqual((frozen.parent/f['file']).read_bytes(),(live.parent/f['file']).read_bytes(),f['file'])
 def test_owner_scope_and_master_identity(self):
  m,e=self.data();body=['idle','walk','attack_light','hit','ko','turn','power_up'];self.assertEqual(set(e['render_contract']['body_clips']),set(body));self.assertEqual(set(m['clips']),set(body+e['render_contract']['effect_clips']))
  for n in ['attack_heavy','run','jump','aura_loop','guard','win']:self.assertNotIn(n,m['clips'])
  root=R/'assets/dilophosaurus/clips';live=Image.open(root/m['frames'][m['clips']['idle']['frames'][0]]['file']).convert('RGBA');master=Image.open(R/'work/characters/dilophosaurus/master-review/frill-v2/master-gameplay-v2.png').convert('RGBA');self.assertEqual(live.tobytes(),master.tobytes());self.assertEqual(e['anchor_px'],[176,224]);self.assertEqual(e['frame_size'],[384,256])
  for n in body:
   for idx in m['clips'][n]['frames']:
    im=Image.open(root/m['frames'][idx]['file']);self.assertEqual(sum(im.getchannel('A').histogram()[1:255]),0,(n,idx))
 def test_one_second_pulses_three_hits_same_target_no_emission(self):
  m,e=self.data();p=e['render_contract']['target_slashes'];self.assertIsNone(e['render_contract']['projectile']);self.assertEqual(p['active_window_ticks'],[8,68]);recover=m['clips']['power_up']['keys']['recover'];self.assertEqual(sum(m['clips']['power_up']['ticks'][2:recover]),60);self.assertEqual(sum(m['clips']['power_up']['ticks']),88);self.assertEqual(len(p['strikes']),3)
  self.assertEqual([x['at_tick'] for x in p['strikes']],[12,31,50]);self.assertEqual(len({x['angle_deg'] for x in p['strikes']}),3);self.assertEqual(p['default_target_canvas_px'],[320,168])
  for x in p['strikes']:self.assertEqual(m['clips'][x['clip']]['ticks'],[1]*6);self.assertEqual(m['clips'][x['clip']]['role'],'fx');self.assertFalse(m['clips'][x['clip']]['loop'])
  for name,c in e['clips'].items():self.assertEqual(c['godot']['relative_durations'],c['ticks'],name)
 def test_idle_cadence_and_frozen_turn_other_actions_and_fx(self):
  m,e=self.data();base=read('work/characters/dilophosaurus/motion-v2/baseline.json')
  idle=m['clips']['idle'];self.assertEqual(sum(idle['ticks']),120);self.assertLess(max(idle['ticks']),30)
  self.assertGreater(len(idle['frames']),len(base['manifest']['clips']['idle']['frames']))
  self.assertEqual(e['render_contract'],base['meta']['render_contract'])
  for n,c in base['manifest']['clips'].items():
   if n in ['idle','power_up']:continue
   self.assertEqual(m['clips'][n]['ticks'],c['ticks'],n)
   self.assertEqual(m['clips'][n].get('events_ms'),c.get('events_ms'),n)
   actual=[hashlib.sha256((R/'assets/dilophosaurus/clips'/m['frames'][i]['file']).read_bytes()).hexdigest() for i in m['clips'][n]['frames']]
   self.assertEqual(actual,base['frame_sha256_by_clip'][n],n)
 def test_source_fx_and_forward_walk_ground_contacts(self):
  m,e=self.data();source=R/'work/characters/dilophosaurus/atlas-v1/source/air-slash-owner.png';self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),'f09380c8b17329c1a7bcb2253305543470a55badf1fbe61ba6a5ecbf9cb5730d')
  proof=read('work/characters/dilophosaurus/atlas-v1/fx-source-evidence.json');self.assertEqual(proof['source_pose_count'],1);self.assertEqual(len(proof['timeline_transforms']),18);self.assertTrue(all(not x['new_AI_art'] and not x['body_emission'] for x in proof['timeline_transforms']))
  walk=m['clips']['walk'];self.assertEqual(walk['loop_policy'],'cycle');self.assertEqual(len(walk['frames']),8);self.assertEqual(e['render_contract']['locomotion']['walk_cycle_order'],list(range(8)));self.assertEqual(len({m['frames'][i]['source']['file_sha256'] for i in walk['frames']}),8)
  for i in walk['frames']:
   im=Image.open(R/'assets/dilophosaurus/clips'/m['frames'][i]['file']);b=im.getbbox();self.assertIn(b[3],[223,224],f'Walk support foot is above shared ground: frame{i} bbox{b}')
