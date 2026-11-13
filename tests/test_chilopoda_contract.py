"""Chilopoda's approved master and new action contracts; not a visual naturalness score."""
from pathlib import Path
import json,hashlib,unittest
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text())
class ChilopodaContract(unittest.TestCase):
    def data(self):return read('assets/chilopoda/clips/animation-clips.json'),read('assets/chilopoda/godot_bundle/engine-export.json')
    def test_master_scope_and_timing(self):
        m,e=self.data();body=e['render_contract']['body_clips'];self.assertEqual(set(body),{'idle','walk','turn','attack_light','power_up','hit','ko'})
        for n in ['run','jump','attack_heavy','guard','win','aura_loop']:self.assertNotIn(n,m['clips'])
        base=R/'assets/chilopoda/clips';idle=Image.open(base/m['frames'][m['clips']['idle']['frames'][0]]['file']).convert('RGBA');roster=read('assets/roster.json');ch=next(c for c in roster['characters'] if c['character_id']=='chilopoda');master=Image.open(R/ch['canonical_identity']['path']).convert('RGBA');self.assertEqual(idle.tobytes(),master.tobytes());self.assertEqual(e['anchor_px'],[176,224]);self.assertEqual(e['frame_size'],[384,256])
        for n in body:
            for idx in m['clips'][n]['frames']:
                a=np.array(Image.open(base/m['frames'][idx]['file']));self.assertTrue(np.isin(a[:,:,3],[0,255]).all(),(n,idx))
        for n,c in e['clips'].items():self.assertEqual(c['godot']['relative_durations'],c['ticks'],n)
        self.assertEqual(len(e['atlas']['pages']),1)
    def test_burrow_hidden_interval_and_paired_laser_origin(self):
        m,e=self.data();c=e['render_contract']['chilopoda'];b=c['burrow'];self.assertEqual(b['emerge_start_tick']-b['hidden_start_tick'],30);self.assertEqual(b['after_bite'],'remain_at_target_then_idle');self.assertEqual(sum(m['clips']['attack_light']['ticks'][:6]),b['hidden_start_tick']);self.assertEqual(sum(m['clips']['attack_light']['ticks'][:7]),b['emerge_start_tick']);self.assertEqual(sum(m['clips']['attack_light']['ticks'][:11]),b['bite_tick'])
        self.assertEqual(b['frame_ticks'],m['clips']['attack_light']['ticks'])
        self.assertEqual(b['top_y_by_frame'],[Image.open(R/'assets/chilopoda/clips'/m['frames'][i]['file']).getbbox()[1] for i in m['clips']['attack_light']['frames']])
        l=c['laser'];self.assertTrue(l['two_independent_origins']);self.assertEqual(l['on_hit'],'hide_projectile');self.assertEqual(sum(m['clips']['power_up']['ticks'][:l['release_frame']]),l['release_tick'])
        for i,tips in enumerate(l['tip_anchors_by_frame']):
            self.assertEqual(len(tips),2);self.assertNotEqual(tips[0],tips[1]);im=Image.open(R/'assets/chilopoda/clips'/m['frames'][m['clips']['power_up']['frames'][i]]['file']).convert('RGBA')
            for x,y in tips:self.assertGreater(im.getpixel((x,y))[3],0,(i,x,y))
    def test_turn_seams_and_unchanged_approved_peers(self):
        m,e=self.data();base=R/'assets/chilopoda/clips';images=lambda n:[Image.open(base/m['frames'][i]['file']).convert('RGBA') for i in m['clips'][n]['frames']]
        walk=images('walk');turn=images('turn');self.assertEqual(turn[0].tobytes(),walk[0].tobytes());self.assertEqual(turn[-1].tobytes(),walk[0].tobytes());self.assertEqual(sum(m['clips']['turn']['ticks']),36);self.assertEqual(len(turn),11);b=e['render_contract']['chilopoda']['burrow_turn'];self.assertEqual(b['hidden_start_tick'],16);self.assertEqual(b['emerge_start_tick'],22);self.assertFalse(b['relocate']);self.assertTrue(e['render_contract']['locomotion']['patrol']['enabled']);self.assertEqual(len({im.tobytes() for im in walk}),12)
        peers=read('work/characters/chilopoda/atlas-v1/protected-peers.json')
        for path,sha in peers.items():
            if path!='assets/roster.json':self.assertEqual(hashlib.sha256((R/path).read_bytes()).hexdigest(),sha,path)

    def test_burrow_turn_motion_gate_requires_explicit_owner_contract_and_review(self):
        import copy
        from tools.preview.motion_quality import assess_motion_quality, REQUIRED_CHECKS
        _,e=self.data();contract=e['render_contract']
        review={'status':'reviewed_pending_owner','method':'imagegen_complete_body_keyframes','atlas_sha256':'sample','checks':{k:True for k in REQUIRED_CHECKS}}
        review['checks']['perspective_turns']=False
        self.assertFalse(assess_motion_quality(review,'sample',contract)['ok_for_human_test'])
        review['checks']['burrow_turn_bidirectional']=True
        result=assess_motion_quality(review,'sample',contract)
        self.assertTrue(result['ok_for_human_test']);self.assertFalse(result['release_approved'])
        missing_owner=copy.deepcopy(contract);missing_owner['turning'].pop('owner_instruction')
        self.assertFalse(assess_motion_quality(review,'sample',missing_owner)['ok_for_human_test'])
        review['checks']['body_connections']=False
        self.assertFalse(assess_motion_quality(review,'sample',contract)['ok_for_human_test'])

    def test_owner_selected_power1_identity_is_canonical_across_ready_poses(self):
        m,e=self.data();base=R/'assets/chilopoda/clips';w=R/'work/characters/chilopoda/identity-v2';previous=read('work/characters/chilopoda/identity-v2/before-runtime/clips/animation-clips.json')
        oldbase=w/'before-runtime/clips';source=Image.open(oldbase/previous['frames'][previous['clips']['power_up']['frames'][1]]['file']).convert('RGBA')
        canonical=Image.open(w/'canonical/master.png').convert('RGBA');self.assertEqual(canonical.tobytes(),source.tobytes())
        for name,indices in [('idle',[0]),('attack_light',[0,15]),('power_up',[0,10]),('hit',[0,5]),('ko',[0])]:
            for j in indices:self.assertEqual(Image.open(base/m['frames'][m['clips'][name]['frames'][j]]['file']).convert('RGBA').tobytes(),canonical.tobytes(),(name,j))
        for j in range(10):self.assertEqual(Image.open(base/m['frames'][m['clips']['power_up']['frames'][j]]['file']).convert('RGBA').tobytes(),Image.open(oldbase/previous['frames'][previous['clips']['power_up']['frames'][j+1]]['file']).convert('RGBA').tobytes())
        self.assertEqual(sum(m['clips']['power_up']['ticks']),42);self.assertEqual(e['render_contract']['chilopoda']['laser']['release_tick'],16)
        for name in e['render_contract']['effect_clips']:
            self.assertEqual(m['clips'][name]['ticks'],previous['clips'][name]['ticks'])
            for new_i,old_i in zip(m['clips'][name]['frames'],previous['clips'][name]['frames']):self.assertEqual(Image.open(base/m['frames'][new_i]['file']).convert('RGBA').tobytes(),Image.open(oldbase/previous['frames'][old_i]['file']).convert('RGBA').tobytes())

    def test_owner_approved_runtime_is_frozen(self):
        receipt=read('assets/chilopoda/owner_approval.json')
        self.assertEqual(receipt['status'],'owner_approved')
        self.assertEqual(receipt['approved_revision'],'identity-v2 / v0.11.1')
        for path,expected in receipt['approved_runtime_files_sha256'].items():
            self.assertEqual(hashlib.sha256((R/path).read_bytes()).hexdigest(),expected,path)
        frozen=read('work/characters/chilopoda/approved-final-frames/animation-clips.json')
        live,_=self.data();self.assertEqual(frozen,live)
