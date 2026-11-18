import hashlib
import json
from pathlib import Path
import unittest
import numpy as np
from PIL import Image, ImageFilter
from tools.preview import server
ROOT=Path(__file__).resolve().parents[1]
class ShenronSummonAssets(unittest.TestCase):
    def test_seven_numbered_native_crops_and_shared_atlas(self):
        c=server.load_rituals()['shenron_summon']
        self.assertEqual([i['number'] for i in c['items']], list(range(1,8)))
        self.assertEqual(c['qa']['star_counts'],list(range(1,8)))
        atlas=Image.open(ROOT/c['atlas']).convert('RGBA')
        evidence=json.loads((ROOT/'docs/contracts/shenron_summon/extraction.json').read_text())
        source=Image.open(ROOT/c['source_images'][0]['file']).convert('RGB')
        for item in c['items']:
            im=Image.open(ROOT/item['file']).convert('RGBA')
            x,y,w,h=item['region']
            self.assertEqual(im.tobytes(),atlas.crop((x,y,x+w,y+h)).tobytes())
            self.assertEqual(im.getpixel((0,0))[3],0)
            record=evidence['items']['ball_'+str(item['number'])]
            original=np.array(source.crop(record['source_box_xyxy']))
            mask=np.array(im.getchannel('A').filter(ImageFilter.MinFilter(5)))==255
            self.assertTrue(np.array_equal(np.array(im)[:,:,:3][mask],original[mask]),'Opaque source interior changed')
            self.assertEqual(record['star_count'],item['number'])
            self.assertEqual(len(record['star_component_areas']),item['number'])
        self.assertEqual(hashlib.sha256((ROOT/c['atlas']).read_bytes()).hexdigest(),c['atlas_sha256'])

    def test_shared_six_second_contract_and_ground_source(self):
        c=server.load_rituals()['shenron_summon'];t=c['timeline'];l=c['layout']
        self.assertEqual(c['tick_hz'],60)
        self.assertEqual(t['ready_tick'],258)
        self.assertEqual(6*t['launch_stride_ticks']+t['flight_ticks'],t['last_arrival_tick'])
        self.assertLess(t['last_arrival_tick'],t['vanish_start_tick'])
        self.assertLess(t['vanish_start_tick'],t['ground_start_tick'])
        flash2_start=t['flash_start_ticks'][1]
        flash2_peak=flash2_start+t['flash_rise_ticks']
        flash2_end=flash2_peak+t['flash_hold_ticks']+t['flash_fall_ticks']
        self.assertEqual(t['ground_start_tick'],flash2_start)
        self.assertEqual(t['dragon_start_tick'],flash2_start)
        self.assertLessEqual(t['ground_start_tick']+t['ground_fade_ticks'],flash2_peak)
        self.assertLessEqual(t['ready_tick'],flash2_end+2)
        self.assertEqual(t['dragon_reveal_curve'],'ease_out_quad')
        self.assertEqual(l['map_center_px'],[960,540]);self.assertEqual(l['ground_y'],840)
        self.assertEqual(l['ground_display_width_px'],144);self.assertEqual(l['dragon_scale'],2.76)
        self.assertEqual(c['behavior']['trigger'],'button_only')
        self.assertTrue(c['behavior']['persist_until_dismissed'])
        self.assertTrue(c['behavior']['requires_seven_balls_in_gameplay'])
        self.assertTrue(c['behavior']['test_mode_bypass_ball_requirement'])
        self.assertTrue(c['behavior']['auto_dismiss_after_wish'])
        dt=c['dismiss_timeline']
        self.assertEqual(dt['flash_start_ticks'],[0,18])
        self.assertEqual(dt['vanish_tick'],dt['flash_start_ticks'][1]+dt['flash_rise_ticks'])
        self.assertEqual(dt['end_tick'],dt['flash_start_ticks'][1]+dt['flash_rise_ticks']+dt['flash_hold_ticks']+dt['flash_fall_ticks'])
        self.assertEqual(len(c['wishes']),3)
        self.assertTrue(all(w.get('id') and w.get('label') and w.get('notice') for w in c['wishes']))
        for source in c['source_images']:
            self.assertEqual(hashlib.sha256((ROOT/source['file']).read_bytes()).hexdigest(),source['sha256'])
        with __import__('zipfile').ZipFile(__import__('io').BytesIO(server.build_godot_zip_bytes())) as archive:
            names = set(archive.namelist())
            self.assertIn('assets/rituals/shenron_summon/sequence.json', names)
            self.assertIn('assets/rituals/shenron_summon/dissolve-threshold.png', names)
            self.assertIn('scenes/ShenronSummon2D.gd', names)
            self.assertIn('scenes/ShenronPixelDissolve.gdshader', names)

    def test_ground_native_pixel_finish_and_flight_preservation(self):
        c=server.load_rituals()['shenron_summon']
        im=Image.open(ROOT/'assets/rituals/shenron_summon/ground-cluster.png').convert('RGBA')
        self.assertEqual(im.size,(144,136))
        self.assertEqual(sum(im.getchannel('A').histogram()[1:255]),0)
        previous=json.loads((ROOT/'docs/contracts/shenron_summon/v2-sequence.json').read_text())
        v2_hashes=json.loads((ROOT/'docs/contracts/shenron_summon/v2-item-hashes.json').read_text())
        for key in ['launch_stride_ticks','flight_ticks','last_arrival_tick','vanish_start_tick']:
            self.assertEqual(c['timeline'][key],previous['timeline'][key])
        for a,b in zip(c['items'],previous['items']):
            self.assertEqual(a['formation_offset_px'],b['formation_offset_px'])
            self.assertEqual(hashlib.sha256((ROOT/a['file']).read_bytes()).hexdigest(),v2_hashes[Path(a['file']).name])

    def test_pixel_dissolve_mask_and_unchanged_approved_combo(self):
        c=server.load_rituals()['shenron_summon'];r=c['reveal']
        self.assertEqual(r['method'],'pixel_dissolve')
        self.assertEqual(r['cell_size_canvas_px'],4)
        im=Image.open(ROOT/r['mask']).convert('RGBA')
        self.assertEqual(im.size,(96,68))
        self.assertEqual(hashlib.sha256((ROOT/r['mask']).read_bytes()).hexdigest(),r['mask_sha256'])
        values=np.array(im)[:,:,0]
        self.assertEqual(len(np.unique(values)),256)
        counts=[int(((values+0.5)/256<=p).sum()) for p in [0,.25,.5,.75,1]]
        self.assertEqual(counts[0],0);self.assertEqual(counts[-1],96*68)
        self.assertTrue(all(a<b for a,b in zip(counts,counts[1:])))
        old=json.loads((ROOT/'docs/contracts/shenron_summon/v4-sequence.json').read_text())
        for key in ['layout','items','regions','atlas_sha256']:
            self.assertEqual(c[key],old[key])
        for tkey in ['launch_stride_ticks','flight_ticks','last_arrival_tick','gather_hold_ticks','vanish_start_tick','flash_start_ticks','flash_rise_ticks','flash_hold_ticks','flash_fall_ticks','glow_period_ticks']:
            self.assertEqual(c['timeline'][tkey],old['timeline'][tkey])
