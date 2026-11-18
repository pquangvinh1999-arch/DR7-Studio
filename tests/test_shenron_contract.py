import copy
import hashlib
import json
from pathlib import Path
import unittest
from PIL import Image
from tools.preview.motion_quality import assess_motion_quality, REQUIRED_CHECKS

ROOT = Path(__file__).resolve().parents[1]

class ShenronContract(unittest.TestCase):
    def test_idle_master_timing_and_stationary_contract(self):
        roster = json.loads((ROOT / 'assets/roster.json').read_text())
        ch = next(c for c in roster['characters'] if c['character_id'] == 'shenron')
        base = ROOT / 'assets/shenron'
        clips = json.loads((base / 'clips/animation-clips.json').read_text())
        export = json.loads((base / 'godot_bundle/engine-export.json').read_text())
        self.assertEqual(list(clips['clips']), ['idle'])
        idle = clips['clips']['idle']
        self.assertEqual(idle['frames'], list(range(8)))
        self.assertEqual(idle['ticks'], [12] * 8)
        self.assertEqual(idle['loop_policy'], 'cycle')
        self.assertEqual(export['anchor_px'], [192, 240])
        self.assertEqual(len(export['atlas']['pages']), 1)
        self.assertEqual(export['render_contract'], ch['render_contract'])
        loc = ch['render_contract']['locomotion']
        self.assertEqual(loc['kind'], 'stationary')
        self.assertEqual(loc['default_scale'], 2.76)
        self.assertEqual(loc['speed_px_per_second'], 0)
        self.assertFalse(loc['allow_turn_or_flip'])
        frames = sorted((base / 'clips/frames').glob('*.png'))
        self.assertEqual(len(frames), 8)
        master = Image.open(ROOT / ch['canonical_identity']['path']).convert('RGBA')
        self.assertEqual(Image.open(frames[0]).convert('RGBA').crop((0, 0, 384, 256)).tobytes(), master.tobytes())
        self.assertIsNone(Image.open(frames[0]).crop((0, 256, 384, 272)).getbbox())
        self.assertEqual(len({hashlib.sha256(f.read_bytes()).hexdigest() for f in frames}), 8)
        for f in frames:
            im = Image.open(f).convert('RGBA')
            self.assertEqual(im.size, (384, 272))
            alpha = im.getchannel('A').histogram()
            self.assertGreater(alpha[0], 0); self.assertGreater(alpha[255], 0)
            self.assertEqual(sum(alpha[1:255]), 0)

    def test_tail_wave_reaches_both_screen_directions(self):
        frames = sorted((ROOT / 'assets/shenron/clips/frames').glob('*.png'))
        right_pose = Image.open(frames[0]).convert('RGBA')
        left_pose = Image.open(frames[4]).convert('RGBA')
        left_roi = (65, 212, 100, 242)
        right_roi = (210, 210, 250, 235)
        self.assertEqual(right_pose.crop(left_roi).getchannel('A').histogram()[255], 0)
        self.assertGreater(right_pose.crop(right_roi).getchannel('A').histogram()[255], 0)
        self.assertGreater(left_pose.crop(left_roi).getchannel('A').histogram()[255], 0)
        self.assertEqual(left_pose.crop(right_roi).getchannel('A').histogram()[255], 0)

    def test_stationary_front_exception_does_not_approve_turning_characters(self):
        ch = next(c for c in json.loads((ROOT / 'assets/roster.json').read_text())['characters'] if c['character_id'] == 'shenron')
        review = {'status': 'reviewed_pending_owner', 'method': 'imagegen_complete_body_keyframes', 'atlas_sha256': 'test', 'checks': {k: True for k in REQUIRED_CHECKS}, 'not_applicable_checks': {'perspective_turns': 'Owner selected stationary front idle'}}
        review['checks']['perspective_turns'] = False
        self.assertTrue(assess_motion_quality(review, 'test', ch['render_contract'])['ok_for_human_test'])
        for key, value in [('kind', 'ground'), ('allow_turn_or_flip', True)]:
            rc = copy.deepcopy(ch['render_contract']); rc['locomotion'][key] = value
            self.assertFalse(assess_motion_quality(review, 'test', rc)['ok_for_human_test'])
        review['checks']['body_connections'] = False
        self.assertFalse(assess_motion_quality(review, 'test', ch['render_contract'])['ok_for_human_test'])

    def test_hover_translates_whole_approved_wave_without_deforming_parts(self):
        offsets=[0,-1,-2,-1,0,1,2,1]
        for index,dy in enumerate(offsets):
            source=Image.open(ROOT/f'assets/shenron/source/idle-v3-wave/idle_{index:02d}.png').convert('RGBA')
            expected=Image.new('RGBA',source.size);expected.paste(source,(0,dy))
            current=Image.open(ROOT/f'assets/shenron/clips/frames/frame-{index:02d}.png').convert('RGBA')
            self.assertEqual(current.tobytes(),expected.tobytes())
            self.assertEqual(current.getchannel('A').histogram()[255],source.getchannel('A').histogram()[255])
