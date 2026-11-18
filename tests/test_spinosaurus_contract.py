"""Whole-pose provenance and independent motion acceptance regressions."""
import hashlib
import json
from pathlib import Path
import unittest
import numpy as np
from PIL import Image
from tools.preview.motion_quality import assess_motion_quality, REQUIRED_CHECKS
ROOT=Path(__file__).resolve().parents[1]
SRC_DIR=ROOT/'assets/spinosaurus/source'
CONTRACTS=ROOT/'docs/contracts/spinosaurus'
class SpinosaurusContract(unittest.TestCase):
 def setUp(self):
  self.qa=json.loads((ROOT/'docs/characters/spinosaurus-final-qa.json').read_text());self.base=ROOT/'assets/spinosaurus/clips';self.data=json.loads((self.base/'animation-clips.json').read_text())
 def test_scope_scale_and_master_identity(self):
  self.assertEqual(hashlib.sha256((SRC_DIR/'approved-original.png').read_bytes()).hexdigest(),self.qa['source_sha256'])
  self.assertEqual(len(self.data['frames']),71);self.assertEqual(len(self.data['clips']),9);self.assertLessEqual(self.qa['body_only_bbox_px']['w'],158);self.assertEqual(self.data['anchor_px'],[176,224]);self.assertEqual(len(self.qa['atlas']['pages']),1)
 def test_each_body_frame_has_generated_whole_cell_provenance(self):
  import re
  for sources in self.qa['source_poses'].values():
   for src in sources:
    self.assertTrue(src['complete_body_generated']);self.assertRegex(src['sheet_sha256'],r'^[0-9a-f]{64}$');self.assertGreaterEqual(src['largest_component_fraction'],.99);self.assertEqual(len(src['cell_rect_px']),4)
  self.assertEqual(self.qa['motion_method'],'existing_complete_source_frames')
  self.assertIn('legacy cut-part/warp builder rejected',(CONTRACTS/'retired-cut-part-note.py').read_text())
 def test_pixel_frames_and_bite_vfx(self):
  partial=[]
  for f in self.data['frames']:
   a=np.array(Image.open(self.base/f['file']).convert('RGBA'));self.assertEqual(a.shape,(256,384,4));self.assertFalse(a[[0,-1],:,3].any());self.assertFalse(a[:,[0,-1],3].any());soft=(a[:,:,3]>0)&(a[:,:,3]<255)
   if soft.any() and not f['name'].startswith('attack_heavy'):
    partial.append(f['name']);self.assertLessEqual(int(a[:,:,3][soft].max()),145);self.assertLess(int(soft.sum()),40);colors=a[soft,:3];self.assertTrue((colors[:,0]>colors[:,1]).all());self.assertTrue((colors[:,1]>colors[:,2]).all())
  self.assertEqual(partial,['attack_light_03','attack_light_04','attack_light_05'])
 def test_real_turn_poses_and_accelerated_tail_timing(self):
  ticks=self.qa['clips']['attack_heavy']['ticks'];self.assertEqual(sum(ticks),35);self.assertLess(sum(ticks),46);self.assertLess(sum(ticks[3:8]),sum(ticks[:3]));self.assertEqual(self.qa['clips']['turn']['ticks'],[6,4,4,6])
  frames={f['name']:np.array(Image.open(self.base/f['file'])) for f in self.data['frames']};self.assertFalse(np.array_equal(frames['turn_02'],frames['turn_00']));self.assertFalse(np.array_equal(frames['turn_02'],frames['turn_00'][:,::-1]))
  for i,j in enumerate([0,3,4]):self.assertTrue(np.array_equal(frames[f'turn_{i:02d}'],frames[f'attack_heavy_{j:02d}']))
 def test_fireball_source_unchanged(self):
  for i in range(4):
   f=next(f for f in self.data['frames'] if f['name']==f'fireball_fx_{i:02d}');self.assertTrue(np.array_equal(np.array(Image.open(self.base/f['file'])),np.array(Image.open(SRC_DIR/f'fireball-reference/fireball_fx_{i:02d}.png'))))
 def test_walk_only_and_run_fully_removed(self):
  manifest=json.loads((self.base/'source-manifest.json').read_text())
  self.assertEqual(set(manifest['clips']),{'idle','walk','attack_light','attack_heavy','power_up','hit','ko','turn','fireball_fx'})
  self.assertNotIn('running',manifest['states'])
  self.assertFalse(any(f['name'].startswith('run_') for f in self.data['frames']))
  self.assertEqual(manifest['clips']['walk']['ticks'],[7,8]*4)
  meta=json.loads((ROOT/'assets/spinosaurus/godot_bundle/engine-export.json').read_text())
  self.assertNotIn('run',meta['render_contract']['body_clips'])
  self.assertEqual(meta['render_contract']['locomotion'],{'kind':'ground','clip':'walk','walk_cycle_order':list(range(8)),'default_scale':2.0,'screen_speed_px_per_second':170,'speed_px_per_second':85.0})
  self.assertEqual(meta['clips']['turn']['ticks'],[2,6,5,3])
  self.assertEqual(meta['render_contract']['turning']['duration_ticks'],16)
 def test_gait_scope_preserves_other_clips_and_walk_middle(self):
  before=json.loads((CONTRACTS/'before-final-no-run.json').read_text())
  edge_hashes=json.loads((CONTRACTS/'walk-edge-uniform-frame-hashes.json').read_text())
  walk_snap_map=json.loads((CONTRACTS/'walk-snap-hashes.json').read_text())
  walk_torso_x=[]
  for f in self.data['frames']:
   name=f['name'];actual=hashlib.sha256((self.base/f['file']).read_bytes()).hexdigest()
   if name.startswith('walk_'):
    im=np.array(Image.open(self.base/f['file']).convert('RGBA'))
    ys,xs=np.where(im[:195,:,3]>0)
    walk_torso_x.append(float(xs.mean()))
    bb=Image.fromarray(im).getbbox()
    area=int((im[:,:,3]>0).sum())
    eye=int(((im[:,:,0]>=180)&(im[:,:,1]>=80)&(im[:,:,1]<=190)&(im[:,:,2]<=60)&(im[:,:,3]>0)).sum())
    self.assertIsNotNone(bb);self.assertTrue(72<=bb[3]-bb[1]<=76,(name,bb));self.assertEqual(bb[3],224,(name,bb))
    self.assertTrue(4450<=area<=4700,(name,area));self.assertGreaterEqual(eye,1,(name,eye))
    self.assertEqual(actual,edge_hashes['frames'][name],name)
    if name not in ('walk_00','walk_07'):self.assertEqual(actual,walk_snap_map[name],name)
    continue
   if not name.startswith('run_'):self.assertEqual(actual,before['frames'][name],name)
  self.assertLessEqual(max(walk_torso_x)-min(walk_torso_x),2.0,walk_torso_x)
  meta=json.loads((ROOT/'assets/spinosaurus/godot_bundle/engine-export.json').read_text())
  for name,c in meta['clips'].items():
   if name in ('run','turn'):continue
   self.assertEqual(c['godot'],before['clips'][name]['godot'])
   self.assertEqual(c['events_ms'],before['clips'][name]['events_ms'])
 def test_owner_approval_is_bound_to_final_no_run_atlas(self):
  prev_receipt=json.loads((ROOT/'docs/releases/spinosaurus-v0.6.0-approval.json').read_text())
  self.assertEqual(prev_receipt['status'],'owner_approved')
  self.assertEqual(prev_receipt['workflow_id'],'PIPE-003')
  receipt=json.loads((ROOT/'assets/spinosaurus/owner_approval.json').read_text())
  self.assertEqual(prev_receipt['atlas_sha256'],receipt['previous_atlas_sha256'])
  self.assertEqual(receipt['status'],'owner_approved')
  self.assertEqual(receipt['workflow_id'],'PIPE-011')
  self.assertEqual(receipt['approved_revision'],'walk-edge-uniform-v1 / v0.12.0')
  self.assertIn('run',receipt['excluded_clips'])
  self.assertNotIn('run',receipt['present_clips'])
  self.assertEqual(receipt['atlas_sha256'],hashlib.sha256((ROOT/receipt['atlas_path']).read_bytes()).hexdigest())
  for rel,exp in receipt['approved_runtime_files_sha256'].items():
   self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),exp,rel)
  frozen=ROOT/receipt['frozen_source']
  self.assertEqual(frozen.read_bytes(),(ROOT/receipt['clips_manifest_path']).read_bytes())
  roster=json.loads((ROOT/'assets/roster.json').read_text())
  entry=next(ch for ch in roster['characters'] if ch['character_id']=='spinosaurus')
  self.assertEqual(entry['status'],'finalized_owner_approved')
  self.assertEqual(entry['atlas_stage'],'finalized_owner_approved')
  self.assertEqual(entry['motion_quality']['status'],'owner_approved')
  self.assertTrue(entry['motion_quality']['owner_approved'])
  self.assertEqual(entry['owner_animation_approval']['workflow_id'],'PIPE-011')
  self.assertEqual(entry['motion_quality']['atlas_sha256'],receipt['atlas_sha256'])
  self.assertEqual(entry['motion_quality']['previous_revision_atlas_sha256'],prev_receipt['atlas_sha256'])
 def test_heavy_body_preserved_and_contact_effect_starts_at_five(self):
  tail=self.qa['tail_impact'];self.assertEqual(tail['contact_frame'],5);self.assertTrue(tail['body_pixels_preserved'])
  self.assertEqual([r['frame'] for r in tail['phases']],[5,6,7]);self.assertTrue(all(r['effect_pixels']>0 for r in tail['phases']))
  before=json.loads((CONTRACTS/'revision-v3-frame-hashes.json').read_text())
  for f in self.data['frames']:
   if f['name'].startswith('attack_heavy') and int(f['name'][-2:]) not in [5,6,7]:self.assertEqual(hashlib.sha256((self.base/f['file']).read_bytes()).hexdigest(),before[f['name']])
class MotionQualityGate(unittest.TestCase):
 def setUp(self):self.review={'status':'reviewed_pending_owner','method':'imagegen_complete_body_keyframes','atlas_sha256':'hash','checks':{k:True for k in REQUIRED_CHECKS},'unresolved_structural_failures':[]}
 def test_technical_success_cannot_override_structural_failure(self):
  self.review.update(status='failed',technical_checks={'exit_code':0},unresolved_structural_failures=['hip torn']);self.assertFalse(assess_motion_quality(self.review,'hash')['ok_for_human_test'])
 def test_review_binds_to_actual_atlas_and_visual_checks(self):
  self.assertFalse(assess_motion_quality(self.review,'different')['ok_for_human_test']);self.review['checks']['body_connections']=False;self.assertFalse(assess_motion_quality(self.review,'hash')['ok_for_human_test'])
 def test_self_review_is_not_owner_approval(self):
  result=assess_motion_quality(self.review,'hash');self.assertTrue(result['ok_for_human_test']);self.assertFalse(result['release_approved']);self.review['method']='cut_part_warp_and_patch';self.assertFalse(assess_motion_quality(self.review,'hash')['ok_for_human_test'])
 def test_identity_failure_blocks_technically_valid_motion(self):
  self.review.update(technical_checks={'exit_code':0})
  self.review['checks']['character_identity']=False
  result=assess_motion_quality(self.review,'hash')
  self.assertFalse(result['ok_for_human_test']);self.assertFalse(result['release_approved'])
  self.assertTrue(any('identity FAIL' in error for error in result['errors']))
