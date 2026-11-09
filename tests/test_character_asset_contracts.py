"""Check the admitted binary assets and the same timeline served to the browser."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/preview'))
import server

class CharacterAssetContracts(unittest.TestCase):
    def bundles(self):
        roster=json.loads((ROOT/'assets/roster.json').read_text())
        for ch in roster['characters']:
            bid=ch['modes']['combined_1layer']['bundle_id']
            root=ROOT/'assets'/bid/'godot_bundle'
            yield ch,root,json.loads((root/'engine-export.json').read_text())

    def test_binary_receipts_and_individual_frames(self):
        for ch,root,meta in self.bundles():
            for rec in meta['files']:
                self.assertEqual(hashlib.sha256((root/rec['path']).read_bytes()).hexdigest(),rec['sha256'])
            source=root/meta['source']['path']
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),meta['source']['sha256'])
            built=json.loads(source.read_text())
            for frame in built['frames']:
                path=source.parent/frame['file']
                data=path.read_bytes()
                self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
                self.assertEqual(list(struct.unpack('>II',data[16:24])),meta['frame_size'])
                self.assertEqual(hashlib.sha256(data).hexdigest(),frame['source']['file_sha256'])

    def test_60hz_browser_timeline_keeps_fractional_milliseconds(self):
        for ch,root,meta in self.bundles():
            tres=next((root/'godot').glob('*.tres'))
            api=server.parse_tres(tres)['animations']
            for name,clip in meta['clips'].items():
                timeline=api[name]['frames']
                self.assertEqual(len(timeline),len(clip['frames']))
                tick_total=0
                for index,(frame,ticks) in enumerate(zip(timeline,clip['godot']['relative_durations'])):
                    self.assertEqual(clip['godot']['speed'],60)
                    self.assertAlmostEqual(frame['duration_ms'],ticks*1000/60,places=10)
                    tick_total+=ticks
                self.assertAlmostEqual(sum(f['duration_ms'] for f in timeline)*1000,tick_total*1000/60*1000,places=6)

    def test_one_page_and_owner_exclusions(self):
        for ch,root,meta in self.bundles():
            pages=meta['atlas']['pages']
            self.assertEqual(len(pages),1)
            self.assertLessEqual(max(pages[0]['size']),4096)
            self.assertEqual(meta['anchor_px'],ch['map_sync_metrics']['foot_anchor_px'])
            self.assertEqual(meta['frame_size'],ch['map_sync_metrics']['canvas_size_px'])
            self.assertTrue(set(ch['present_clips']).isdisjoint(ch.get('not_applicable_clips',{})))
            self.assertEqual(set(ch['present_clips']) | set(ch.get('effect_clips', [])),set(meta['clips']))

    def test_independent_fx_contract(self):
        for ch,root,meta in self.bundles():
            contract=meta.get('render_contract')
            if not contract: continue
            self.assertEqual(contract,ch['render_contract'])
            self.assertTrue(set(contract['body_clips']).isdisjoint(contract['effect_clips']))
            self.assertTrue(contract['aura']['independent_clock'])
            self.assertTrue(set(contract['body_clips']).issubset(meta['clips']))
            self.assertTrue(set(contract['effect_clips']).issubset(meta['clips']))

if __name__=='__main__':unittest.main()
