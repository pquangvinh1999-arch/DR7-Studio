"""Bat - Chiroptera contract: preserves v0.10.0 non-turn clips/FX & snapshot while validating turn-v1."""
import hashlib
import json
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

R=Path(__file__).resolve().parents[1]
def read(path):return json.loads((R/path).read_text())
class BatContract(unittest.TestCase):
    def test_owner_approved_revision_is_frozen(self):
        prev_cal_receipt=read('docs/releases/bat_chiroptera-v0.11.2-approval.json')
        self.assertEqual(prev_cal_receipt['status'],'owner_approved')
        self.assertEqual(prev_cal_receipt['workflow_id'],'PIPE-009')
        receipt=read('assets/bat_chiroptera/owner_approval.json')
        self.assertEqual(receipt['status'],'owner_approved')
        self.assertEqual(receipt['workflow_id'],'PIPE-016')
        self.assertEqual(receipt['approved_revision'],'calibration-v1 / v0.12.0')
        self.assertEqual(hashlib.sha256((R/receipt['atlas_path']).read_bytes()).hexdigest(),receipt['atlas_sha256'])
        self.assertEqual(hashlib.sha256((R/receipt['engine_export_path']).read_bytes()).hexdigest(),receipt['engine_export_sha256'])
        for path,expected in receipt['approved_runtime_files_sha256'].items():
            self.assertEqual(hashlib.sha256((R/path).read_bytes()).hexdigest(),expected,path)
        export=read('assets/bat_chiroptera/godot_bundle/engine-export.json')
        loc=export['render_contract']['locomotion']
        self.assertAlmostEqual(loc['default_scale'],1.1,places=4)
        self.assertEqual(loc['screen_speed_px_per_second'],115)
        self.assertAlmostEqual(loc['speed_px_per_second'],104.545455,places=6)
        self.assertEqual(loc['flight_default_y'],250)
        prev_receipt=read('docs/releases/bat_chiroptera-v0.10.0-approval.json')
        self.assertEqual(prev_receipt['workflow_id'],'PIPE-007')
        self.assertEqual(prev_receipt['status'],'owner_approved')
        baseline=read('docs/contracts/bat_chiroptera/turn-v1-baseline-manifest.json')
        for bf in baseline['bat_frames']:
            idx=bf['index']
            live_frame=R/f'assets/bat_chiroptera/clips/frames/frame-{idx:02d}.png'
            self.assertEqual(hashlib.sha256(live_frame.read_bytes()).hexdigest(),bf['file_sha256'],bf['file'])
        frozen=R/receipt['frozen_source']
        for i,frame in enumerate(json.loads(frozen.read_text())['frames']):
            self.assertEqual((frozen.parent/frame['file']).read_bytes(),(R/f'assets/bat_chiroptera/clips/frames/frame-{i:02d}.png').read_bytes(),frame['file'])

    def test_reference_actions_timing_and_events_are_preserved(self):
        bat=read('assets/bat_chiroptera/clips/animation-clips.json')
        ref=read('assets/pteranodon/clips/animation-clips.json')
        self.assertEqual(set(bat['clips']),set(ref['clips'])|{'turn'})
        self.assertEqual(bat['states'],{**ref['states'],'turn':'turn'})
        self.assertEqual(len(bat['frames']),66)
        for name,c in ref['clips'].items():
            for key in ['ticks','duration_ms','loop','loop_policy','events_ms','keys','hitstop_ticks']:
                self.assertEqual(bat['clips'][name].get(key),c.get(key),(name,key))
            self.assertEqual(bat['clips'][name]['frames'],c['frames'],(name,'frames'))
        t=bat['clips']['turn']
        self.assertFalse(t['loop']);self.assertEqual(t['loop_policy'],'oneshot')
        self.assertEqual(t['ticks'],[2,3,4,3,3]);self.assertEqual(len(set(t['ticks']))>1,True)
        self.assertEqual(t['total_duration_ms'],250)
        self.assertEqual(len(t['frames']),5)
        turn_hashes=set()
        for idx in t['frames']:
            a=np.array(Image.open(R/'assets/bat_chiroptera/clips'/bat['frames'][idx]['file']).convert('RGBA'))
            self.assertTrue(np.isin(a[:,:,3],[0,255]).all(),idx)
            turn_hashes.add(hashlib.sha256(a.tobytes()).hexdigest())
        self.assertEqual(len(turn_hashes),5)

    def test_turn_contract_and_bidirectional_runtime(self):
        meta=read('assets/bat_chiroptera/godot_bundle/engine-export.json')
        rc=meta['render_contract']
        self.assertEqual(rc['turning']['clip'],'turn')
        self.assertEqual(rc['turning']['method'],'complete_perspective_poses')
        self.assertTrue(rc['turning']['mirror_sequence_for_reverse'])
        self.assertTrue(rc['locomotion']['patrol']['enabled'])
        self.assertIn('res://scenes/BatChiropteraFighter2D.gd',(R/'scenes/BatChiroptera.tscn').read_text())
        roster=read('assets/roster.json')
        ch=next(c for c in roster['characters'] if c['character_id']=='bat_chiroptera')
        self.assertEqual(ch['status'],'finalized_owner_approved')
        self.assertTrue(ch['motion_quality']['owner_approved'])
        self.assertEqual(ch['motion_quality']['status'],'owner_approved')
        self.assertEqual(ch['owner_animation_approval']['workflow_id'],'PIPE-016')
        receipt=read('assets/bat_chiroptera/owner_approval.json')
        self.assertEqual(ch['motion_quality']['atlas_sha256'],receipt['atlas_sha256'])
        self.assertEqual(ch['motion_quality']['previous_revision_atlas_sha256'],receipt['previous_atlas_sha256'])

    def test_master_size_identity_and_independent_fast_flight(self):
        m=read('assets/bat_chiroptera/clips/animation-clips.json');base=R/'assets/bat_chiroptera/clips'
        im=Image.open(base/m['frames'][m['clips']['idle']['frames'][0]]['file']).convert('RGBA')
        canonical=Image.open(R/'assets/bat_chiroptera/source/master.png').convert('RGBA')
        self.assertEqual(im.tobytes(),canonical.tobytes())
        b=im.getbbox();self.assertEqual((b[2]-b[0],b[3]-b[1]),(126,81))
        walk={hashlib.sha256((base/m['frames'][i]['file']).read_bytes()).hexdigest() for i in m['clips']['walk']['frames']}
        run={hashlib.sha256((base/m['frames'][i]['file']).read_bytes()).hexdigest() for i in m['clips']['run']['frames']}
        self.assertEqual(len(walk),8);self.assertEqual(len(run),8);self.assertFalse(walk&run)

    def test_purple_fx_preserves_reference_phase_silhouettes(self):
        bat=read('assets/bat_chiroptera/clips/animation-clips.json');ref=read('assets/pteranodon/clips/animation-clips.json')
        for bi,ri in zip(bat['clips']['sonic_screech_fx']['frames'],ref['clips']['sonic_screech_fx']['frames']):
            im=Image.open(R/'assets/bat_chiroptera/clips'/bat['frames'][bi]['file']).convert('RGBA')
            original=Image.open(R/'assets/pteranodon/clips'/ref['frames'][ri]['file']).convert('RGBA')
            expected=original.transform((384,256),Image.Transform.AFFINE,(1.25,0,-44,0,1.25,-35.25),resample=Image.Resampling.NEAREST)
            a=np.array(im);self.assertTrue(np.array_equal(a[:,:,3],np.array(expected)[:,:,3]))
            rgb=a[:,:,:3].astype(int);colored=(a[:,:,3]>0)&(rgb.max(2)-rgb.min(2)>30)
            self.assertTrue(colored.any());self.assertTrue(np.all(rgb[:,:,2][colored]>=rgb[:,:,0][colored]))
        meta=read('assets/bat_chiroptera/godot_bundle/engine-export.json');rc=meta['render_contract']
        self.assertEqual(rc['projectile']['release_frame'],2);self.assertEqual(rc['projectile']['lifetime_ticks'],14)
        self.assertEqual(rc['projectile']['palette'],'purple')
        self.assertEqual(len(meta['atlas']['pages']),1);self.assertEqual(meta['anchor_px'],[176,200])

if __name__=='__main__':unittest.main()
