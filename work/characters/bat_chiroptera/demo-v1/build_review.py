"""Register the complete generated still; no anatomical cuts or pose changes."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tools.art.measure_pixel_sharpness import measure

OUT = Path(__file__).resolve().parent
SOURCE = Path('/home/codespace/.codex/generated_images/01a1d375-ef4d-7900-8359-5538635411a2/exec-2ec59404-793f-41cf-a1fa-346b9a4627f0.png')
if not (OUT / 'generated-cleanup.png').exists():
    shutil.copy2(SOURCE, OUT / 'generated-cleanup.png')
raw = Image.open(OUT / 'generated-cleanup.png').convert('RGBA')
rgba = np.array(raw)
# Hard-alpha pixel-art finishing after imagegen extraction, applied to whole still.
rgba[:, :, 3] = np.where(rgba[:, :, 3] >= 128, 255, 0)
rgba[rgba[:, :, 3] == 0] = 0
whole = Image.fromarray(rgba)
source_box = whole.getbbox()
whole = whole.crop(source_box)
width = 126
height = round(whole.height * width / whole.width)
whole = whole.resize((width, height), Image.Resampling.NEAREST)
box = whole.getbbox()
assert box[2] - box[0] == 126, box
master = Image.new('RGBA', (384, 256))
master.alpha_composite(whole, (176 - width // 2, 200 - height))
master.save(OUT / 'master.png')
reference = Image.open(ROOT / 'assets/pteranodon/clips/frames/frame-00.png').convert('RGBA')
assert reference.getbbox() == (98, 96, 255, 203)
for name, color in [('light', (237, 236, 227)), ('dark', (28, 31, 39)), ('checker', (170, 170, 170))]:
    board = Image.new('RGBA', (768, 604), color + (255,))
    if name == 'checker':
        draw = ImageDraw.Draw(board)
        for y in range(0, 604, 16):
            for x in range(0, 768, 16):
                if (x // 16 + y // 16) % 2:
                    draw.rectangle((x, y, x + 15, y + 15), fill=(205, 205, 205, 255))
    draw = ImageDraw.Draw(board)
    ink = (245, 245, 245) if name == 'dark' else (24, 24, 24)
    draw.text((18, 12), 'Pteranodon | 157px | 1x', fill=ink)
    draw.text((402, 12), 'Bat - Chiroptera | 126px | 1x', fill=ink)
    board.alpha_composite(reference, (0, 22))
    board.alpha_composite(master, (384, 22))
    draw.text((18, 295), 'Pteranodon | 2x Nearest', fill=ink)
    draw.text((402, 295), 'Bat | 2x Nearest', fill=ink)
    for sprite, x in [(reference, 192), (master, 576)]:
        crop = sprite.crop(sprite.getbbox())
        zoom = crop.resize((crop.width * 2, crop.height * 2), Image.Resampling.NEAREST)
        board.alpha_composite(zoom, (x - zoom.width // 2, 565 - zoom.height))
    board.convert('RGB').save(OUT / f'comparison-{name}.png')
metrics = measure(OUT / 'master.png')
metrics.update(reference_width_px=157, requested_ratio=0.8, actual_ratio=126/157,
               source_alpha_threshold=128, source_whole_bbox=list(source_box),
               registration='Whole sprite uniform Nearest scale, bbox center x176 and bottom y200; static candidate only.',
               art_source='host_image', route='image_gen', owner_approved=False,
               motion_quality='not_applicable_static_demo', technical_checks='static_measurements_only')
(OUT / 'measurements.json').write_text(json.dumps(metrics, indent=2) + '\n')
protected = json.loads((OUT / 'protected-peers.json').read_text())
changed = [f for f, sha in protected.items() if hashlib.sha256((ROOT / f).read_bytes()).hexdigest() != sha]
assert not changed, changed
print(json.dumps({'measurements': metrics, 'protected_runtime_files_unchanged': len(protected)}, indent=2))
