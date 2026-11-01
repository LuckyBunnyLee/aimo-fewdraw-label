"""SHAM v1.1 launch shim, lead deviation D2 (LEAD-DECISIONS-20261025-1855 item 4). CL3, 25 Oct 2026.
Not part of the freeze; copied into the WSL run folder R beside the frozen files and hashed in LAUNCH-NOTES.

Only change: wave_core.bind_model (blob-NAME test on HF cache symlinks) is replaced in memory by the byte-level binding
of ADMIT-CHECK-D1 (every weight shard's sha256 must equal its HF LFS sha256 for rev 851bf6e8). The returned record has
the same shape and values as bind_model would return on a blob-structured cache. Waves, requests, seeds, caps, engine,
ledger and scoring are untouched: wave_runner.py runs unchanged from R via runpy.

The binding is checked here BEFORE the runner starts, so a binding failure opens and charges no block.
  python launch_shim_d2.py --test   dry run: all pre-launch checks + binding; never imports the runner; proves the
                                    run folder (block ledger) is byte-identical before/after; writes TEST-MODE-D2.json.
  python launch_shim_d2.py          same checks, then runs wave_runner.py (which opens/charges its block itself)."""
import sys, os, json, hashlib, pathlib, runpy, time
R = pathlib.Path(__file__).resolve().parent
REVIEWED = 'cf704ca303b4791351426d97f9be715e7a475644be557e1498e1f11794a94b5b'
PINNED = {'wave_core.py': '814d851efa858fbf53dbc9e1617ec9744bd154cebe191fda81b0a5b54a4bf203',
          'request_core.py': '49d2049a8eb9f4c9cefe5f55eddf1b8dc71d400241094ff01dc44110e99f32c0'}
REV = '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
LFS = {'model.safetensors-00001-of-00002.safetensors': '26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61',
       'model.safetensors-00002-of-00002.safetensors': 'cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188'}
assert not list(R.glob('RETIRED-*.json')), 'this run folder is retired; the live run folder is named in its RETIRED marker'
for name, h in PINNED.items(): assert hashlib.sha256((R / name).read_bytes()).hexdigest() == h, 'not the reviewed ' + name
sys.path.insert(0, str(R)); import wave_core as wc
admission = wc.read(R / 'ADMISSION.json'); wc.check_admission(R, admission, REVIEWED); m = wc.read(R / 'MANIFEST.json')
assert m['model_revision'] == REV and admission['model_path'] == wc.MODEL_PATH
d1 = wc.read(R / 'ADMIT-CHECK-D1.json'); assert d1['admission'] == 'ok' and d1['freeze'] == REVIEWED and d1['revision'] == REV
for s, h in LFS.items(): assert d1['files'][s]['sha256'] == h


def bind_model_bytes(path, revision):
    """bind_model with the blob-name test replaced by sha256 == HF LFS sha256 (D2). Everything else as frozen."""
    p = pathlib.Path(path); assert p.name == revision and p.parent.name == 'snapshots' and p.parent.parent.name == 'models--Qwen--Qwen3.5-4B', 'not the pinned snapshot'
    out = dict(snapshot=str(p), revision=revision, files={})
    for name, h in wc.MODEL_FILES.items():
        got = wc.file_sha(p / name); assert got == h, 'model file differs from the pinned hash: ' + name; out['files'][name] = got
    shards = sorted(x.name for x in p.glob('*.safetensors')); assert shards == sorted(LFS), 'weight files differ from rev ' + REV
    idx = p / 'model.safetensors.index.json'
    if idx.exists():
        listed = sorted(set(wc.read(idx)['weight_map'].values())); assert listed == shards, 'index and shards differ'; out['files']['model.safetensors.index.json'] = wc.file_sha(idx)
    for s in shards:
        got = wc.file_sha(p / s); assert got == LFS[s], 'weight file does not match its HF LFS sha256: ' + s; out['files'][s] = got
    return out


def snapshot_R():
    return {str(x.relative_to(R)): (wc.file_sha(x) if x.is_file() else 'dir') for x in sorted(R.rglob('*')) if '__pycache__' not in x.parts and x.name != 'TEST-MODE-D2.json'}


t = time.time(); binding = bind_model_bytes(admission['model_path'], m['model_revision']); bind_seconds = time.time() - t
for b in sorted(R.glob('block-*')):
    if (b / 'MODEL-BINDING.json').exists(): assert wc.read(b / 'MODEL-BINDING.json')['files'] == binding['files'], 'model bytes differ from ' + b.name
if sys.argv[1:] == ['--test']:
    before = snapshot_R(); st_before = wc.scan(R, m)
    wc.bind_model = bind_model_bytes; again = wc.bind_model(admission['model_path'], m['model_revision']); assert again == binding
    after = snapshot_R(); st_after = wc.scan(R, m)
    assert before == after and st_before == st_after and not st_after['blocks'], 'dry run changed the run folder'
    wc.put(R / 'TEST-MODE-D2.json', dict(test_mode=True, binding_pass=True, binding=binding, bind_seconds=bind_seconds, blocks_before=st_before['blocks'],
                                        blocks_after=st_after['blocks'], charged_tokens=st_after['tokens'], charged_hours=st_after['hours'],
                                        run_folder_unchanged=True, runner_imported=False, shim_sha256=wc.file_sha(pathlib.Path(__file__)), at=time.time()))
    print('TEST_MODE PASS: binding ok, no block, ledger untouched', json.dumps(dict(blocks=st_after['blocks'], tokens=st_after['tokens'], hours=st_after['hours'])))
    sys.exit(0)
assert sys.argv[1:] == [], 'usage: launch_shim_d2.py [--test]'
assert (R / 'TEST-MODE-D2.json').exists(), 'TEST_MODE dry run required before launch'
wc.bind_model = bind_model_bytes
sys.argv = [str(R / 'wave_runner.py')]
runpy.run_path(str(R / 'wave_runner.py'), run_name='__main__')
