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
        fb=c['fireball'];self.assertTrue(fb['one_shot']);self.assertEqual(fb['body_clip'],'power_up');self.assertEqual(fb['projectile_clip'],'fireball_fx');self.assertEqual(fb['on_hit'],'hide_projectile');self.assertEqual(sum(m['clips']['power_up']['ticks'][:fb['release_frame']]),fb['release_tick']);self.assertEqual(fb['charge_frames'],[0,1,2]);self.assertEqual(fb['flight_frames'],[3,4,5,6,7,8,9]);self.assertEqual(c['burrow']['dust_scale'],2.65)
        self.assertEqual(len(fb['mouth_anchors_by_frame']),len(m['clips']['power_up']['frames']))
        for i,(mx,my) in enumerate(fb['mouth_anchors_by_frame']):
            im=Image.open(R/'assets/chilopoda/clips'/m['frames'][m['clips']['power_up']['frames'][i]]['file']).convert('RGBA')
            self.assertTrue(any(im.getpixel((mx+dx,my+dy))[3]>0 for dx in range(-6,7) for dy in range(-6,7)),(i,mx,my))
        loc=e['render_contract']['locomotion'];self.assertAlmostEqual(loc['default_scale'],1.35,places=4);self.assertEqual(loc['screen_speed_px_per_second'],140)
    def test_turn_seams_and_unchanged_approved_peers(self):
        m,e=self.data();base=R/'assets/chilopoda/clips';images=lambda n:[Image.open(base/m['frames'][i]['file']).convert('RGBA') for i in m['clips'][n]['frames']]
        walk=images('walk');turn=images('turn');self.assertEqual(turn[0].tobytes(),walk[0].tobytes());self.assertEqual(turn[-1].tobytes(),walk[0].tobytes());self.assertEqual(sum(m['clips']['turn']['ticks']),36);self.assertEqual(len(turn),11);b=e['render_contract']['chilopoda']['burrow_turn'];self.assertEqual(b['hidden_start_tick'],16);self.assertEqual(b['emerge_start_tick'],22);self.assertFalse(b['relocate']);self.assertTrue(e['render_contract']['locomotion']['patrol']['enabled']);self.assertEqual(len({im.tobytes() for im in walk}),12)
        peers=read('docs/contracts/chilopoda/protected-peers.json')
        turn_retrofit_paths={
            'scenes/BatChiroptera.tscn',
            'scenes/BatChiropteraFighter2D.gd',
            'scenes/CharacterFighter2D.gd',
            'scenes/ArenaSandbox.gd',
            'scenes/TRex.tscn',
            'scenes/TRexFighter2D.gd',
            'scenes/TasmanianFighter2D.gd',
            'assets/tasmanian_king_crab/godot_bundle/engine-export.json',
        }
        for path,sha in peers.items():
            if path=='assets/roster.json' or path.startswith(('assets/bat_chiroptera/','assets/t_rex/','assets/tasmanian_king_crab/','assets/sarcosuchus/','assets/dilophosaurus/','assets/spinosaurus/','assets/pteranodon/')) or path in turn_retrofit_paths:
                continue
            self.assertEqual(hashlib.sha256((R/path).read_bytes()).hexdigest(),sha,path)

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
        m,e=self.data();base=R/'assets/chilopoda/clips';previous=read('docs/contracts/chilopoda/before-runtime-animation-clips.json');before_hashes=read('docs/contracts/chilopoda/before-runtime-frame-hashes.json')
        source_sha=before_hashes[previous['frames'][previous['clips']['power_up']['frames'][1]]['file']]
        canonical=Image.open(R/'assets/chilopoda/source/master.png').convert('RGBA')
        for name,indices in [('idle',[0]),('attack_light',[0,15]),('power_up',[0,10]),('hit',[0,5]),('ko',[0])]:
            for j in indices:self.assertEqual(Image.open(base/m['frames'][m['clips'][name]['frames'][j]]['file']).convert('RGBA').tobytes(),canonical.tobytes(),(name,j))
        self.assertEqual(hashlib.sha256((base/m['frames'][m['clips']['idle']['frames'][0]]['file']).read_bytes()).hexdigest(),source_sha)
        for j in range(10):self.assertEqual(hashlib.sha256((base/m['frames'][m['clips']['power_up']['frames'][j]]['file']).read_bytes()).hexdigest(),before_hashes[previous['frames'][previous['clips']['power_up']['frames'][j+1]]['file']])
        self.assertEqual(sum(m['clips']['power_up']['ticks']),42);self.assertEqual(e['render_contract']['chilopoda']['fireball']['release_tick'],16)
        self.assertEqual(e['render_contract']['effect_clips'],['burrow_dust_fx','fireball_fx'])
        self.assertEqual(m['clips']['burrow_dust_fx']['ticks'],previous['clips']['burrow_dust_fx']['ticks'])
        for new_i,old_i in zip(m['clips']['burrow_dust_fx']['frames'],previous['clips']['burrow_dust_fx']['frames']):self.assertEqual(hashlib.sha256((base/m['frames'][new_i]['file']).read_bytes()).hexdigest(),before_hashes[previous['frames'][old_i]['file']])
        fb_clip=m['clips']['fireball_fx'];self.assertEqual(len(fb_clip['frames']),10);self.assertEqual(fb_clip['ticks'],[1]*10)
        areas=[]
        for idx in fb_clip['frames']:
            im=Image.open(base/m['frames'][idx]['file']).convert('RGBA');x0,y0,x1,y1=im.getbbox();areas.append((x1-x0)*(y1-y0))
            px=list(im.get_flattened_data() if hasattr(im,'get_flattened_data') else im.getdata())
            self.assertEqual(sum(1 for _,_,_,a in px if 0<a<255),0,idx)
            self.assertEqual(sum(1 for r,g,b,a in px if a>0 and r<40 and g>120 and b>120),0,idx)
        self.assertEqual(areas,sorted(areas))

    def test_owner_approved_runtime_is_frozen(self):
        prev_receipt=read('docs/releases/chilopoda-v0.11.1-approval.json')
        self.assertEqual(prev_receipt['status'],'owner_approved')
        self.assertEqual(prev_receipt['workflow_id'],'PIPE-008')
        receipt=read('assets/chilopoda/owner_approval.json')
        self.assertEqual(receipt['status'],'owner_approved')
        self.assertEqual(receipt['workflow_id'],'PIPE-015')
        self.assertEqual(receipt['approved_revision'],'fireball-v1 / v0.12.0')
        self.assertEqual(hashlib.sha256((R/receipt['atlas_path']).read_bytes()).hexdigest(),receipt['atlas_sha256'])
        self.assertEqual(hashlib.sha256((R/receipt['engine_export_path']).read_bytes()).hexdigest(),receipt['engine_export_sha256'])
        for path,expected in receipt['approved_runtime_files_sha256'].items():
            self.assertEqual(hashlib.sha256((R/path).read_bytes()).hexdigest(),expected,path)
        frozen=R/receipt['frozen_source'];live=R/receipt['clips_manifest_path']
        self.assertEqual(frozen.read_bytes(),live.read_bytes())
        for f in json.loads(frozen.read_text())['frames']:
            self.assertEqual((frozen.parent/f['file']).read_bytes(),(live.parent/f['file']).read_bytes(),f['file'])
        ch=next(c for c in read('assets/roster.json')['characters'] if c['character_id']=='chilopoda')
        self.assertEqual(ch['status'],'finalized_owner_approved')
        self.assertTrue(ch['motion_quality']['owner_approved'])
        self.assertEqual(ch['motion_quality']['status'],'owner_approved')
        self.assertEqual(ch['owner_animation_approval']['workflow_id'],'PIPE-015')
        self.assertEqual(ch['motion_quality']['atlas_sha256'],receipt['atlas_sha256'])
        self.assertEqual(ch['motion_quality']['previous_revision_atlas_sha256'],prev_receipt['atlas_sha256'])
