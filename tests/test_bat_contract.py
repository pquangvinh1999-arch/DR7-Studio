"""Owner's Bat scope: Pteranodon actions/timing, smaller identity, purple sonic wave."""
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
        receipt=read('assets/bat_chiroptera/owner_approval.json')
        self.assertEqual(receipt['status'],'owner_approved')
        self.assertEqual(receipt['workflow_id'],'PIPE-007')
        for path,digest in receipt['approved_runtime_files_sha256'].items():
            self.assertEqual(hashlib.sha256((R/path).read_bytes()).hexdigest(),digest,path)
        self.assertEqual(hashlib.sha256((R/receipt['engine_export_path']).read_bytes()).hexdigest(),receipt['engine_export_sha256'])
        frozen=R/receipt['frozen_source'];live=R/receipt['clips_manifest_path']
        self.assertEqual(frozen.read_bytes(),live.read_bytes())
        for frame in json.loads(frozen.read_text())['frames']:
            self.assertEqual((frozen.parent/frame['file']).read_bytes(),(live.parent/frame['file']).read_bytes())

    def test_reference_actions_timing_and_events_are_preserved(self):
        bat=read('assets/bat_chiroptera/clips/animation-clips.json')
        ref=read('assets/pteranodon/clips/animation-clips.json')
        self.assertEqual(set(bat['clips']),set(ref['clips']))
        self.assertEqual(bat['states'],ref['states'])
        self.assertEqual(len(bat['frames']),61)
        for name,c in ref['clips'].items():
            for key in ['ticks','duration_ms','loop','loop_policy','events_ms','keys','hitstop_ticks']:
                self.assertEqual(bat['clips'][name].get(key),c.get(key),(name,key))
            self.assertEqual(len(bat['clips'][name]['frames']),len(c['frames']))

    def test_master_size_identity_and_independent_fast_flight(self):
        m=read('assets/bat_chiroptera/clips/animation-clips.json');base=R/'assets/bat_chiroptera/clips'
        im=Image.open(base/m['frames'][m['clips']['idle']['frames'][0]]['file']).convert('RGBA')
        canonical=Image.open(R/'work/characters/bat_chiroptera/approved-master/master.png').convert('RGBA')
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
