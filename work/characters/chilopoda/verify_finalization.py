"""Final approved metadata delivery; compare current ZIP/HTTP bytes to frozen live assets."""
from pathlib import Path
import json,hashlib,urllib.request,zipfile,io
W=Path(__file__).resolve().parent;R=W.parents[2];V=W/'identity-v2/verification'
sha=lambda b:hashlib.sha256(b).hexdigest()
payload=json.load(urllib.request.urlopen('http://localhost:8080/api/bundles'))
assert payload['parity']['ok'];assert payload['motion_quality']['release_approved'];assert len(payload['motion_quality']['characters'])==8
for cid,result in payload['motion_quality']['characters'].items():assert result['release_approved'],(cid,result)
hashes={}
for rel,url in [('assets/chilopoda/godot_bundle/godot/chilopoda-atlas-00.png','/assets/chilopoda/godot_bundle/godot/chilopoda-atlas-00.png'),('tools/preview/rust_combat_sim.wasm','/rust_combat_sim.wasm')]:
 local=sha((R/rel).read_bytes());remote=sha(urllib.request.urlopen('http://localhost:8080'+url).read());assert local==remote,rel;hashes[rel]={'local':local,'http':remote}
packed=urllib.request.urlopen('http://localhost:8080/api/download-godot-pack.zip',timeout=120).read()
with zipfile.ZipFile(io.BytesIO(packed)) as z:
 assert z.testzip() is None
 roster=json.loads(z.read('assets/roster.json'));assert len(roster['characters'])==8;assert all(c['owner_animation_approval']['status']=='owner_approved' for c in roster['characters'])
 meta=json.loads(z.read('assets/chilopoda/godot_bundle/engine-export.json'));assert meta['provenance']['owner_approved'] and not meta['provenance']['atlas_demo_only']
 compared=0
 for name in z.namelist():
  if name.startswith('assets/chilopoda/godot_bundle/') or name in ['assets/roster.json','scenes/Chilopoda.tscn','scenes/ChilopodaFighter2D.gd','scenes/ChilopodaGroundClip.gdshader']:
   assert z.read(name)==(R/name).read_bytes(),name;compared+=1
receipt=json.loads((R/'assets/chilopoda/owner_approval.json').read_text());assert sha((R/receipt['engine_export_path']).read_bytes())==receipt['engine_export_sha256']
for path,digest in receipt['approved_runtime_files_sha256'].items():assert sha((R/path).read_bytes())==digest,path
result={'http_parity':payload['parity'],'hashes':hashes,'motion_quality':payload['motion_quality'],'zip_sha256':sha(packed),'zip_compared_files':compared,'zip_crc':'ok','zip_owner_approved_metadata':True,'all_eight_characters_owner_approved':True,'runtime_frozen_files':len(receipt['approved_runtime_files_sha256'])}
(V/'finalization-http-zip-parity.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'http_hash_parity':True,'zip_crc':'ok','zip_compared_files':compared,'owner_approved_characters':8,'runtime_frozen_files':len(receipt['approved_runtime_files_sha256'])}))
