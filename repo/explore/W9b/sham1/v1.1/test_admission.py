"""CPU test of the v1.1 admission binding (V23 fix 3): wave_core.check_admission and wave_core.bind_model.
usage: python -I explore/W9b/sham1/v1.1/test_admission.py
Builds a temp run folder (copies of the v1.1 code and the v1.0 data, a test freeze) and a fake model snapshot with
test-only pinned hashes. Deletes nothing: temp folders are kept. Real model bytes are checked by CL's admit-check."""
import hashlib, json, os, shutil, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); import wave_core as wc
REV = '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
H = lambda b: hashlib.sha256(b).hexdigest()


def run_folder():
    R = Path(tempfile.mkdtemp(prefix='sham1-v11-adm-'))
    src = dict(wave_runner=HERE / 'wave_runner.py', wave_core=HERE / 'wave_core.py', request_core=HERE.parent / 'request_core.py')
    for p in list(src.values()) + [HERE.parent / n for n in ('MANIFEST.json', 'REQUESTS.json', 'TRUTHS.json')]:
        shutil.copyfile(p, R / p.name)
    lines = [f'{wc.file_sha(R / n)}  {"../" if n in ("request_core.py", "MANIFEST.json", "REQUESTS.json", "TRUTHS.json") else ""}{n}' for n in wc.BOUND]
    (R / wc.FREEZE).write_text('\n'.join(lines) + '\n')
    fz = wc.file_sha(R / wc.FREEZE)
    adm = dict(generation_authorized=True, base_manifest_sha256=wc.file_sha(R / 'MANIFEST.json'), freeze_sha256=fz,
               code_sha256={n: wc.file_sha(R / n) for n in wc.CODE}, model_path=wc.MODEL_PATH, max_model_len=8192,
               capture_sizes=[1, 2, 4, 8, 16, 32], cache_root='/x', absolute_deadline=2e9)
    return R, adm, fz


def refuses(fn, words):
    try: fn()
    except AssertionError as e:
        assert words in str(e), (words, str(e)); return
    raise AssertionError('accepted, expected refusal: ' + words)


def admission_cases():
    R, adm, fz = run_folder()
    assert wc.check_admission(R, adm, fz)['wave_core.py'] == adm['code_sha256']['wave_core.py']
    refuses(lambda: wc.check_admission(R, adm, '0' * 64), 'not the reviewed')
    refuses(lambda: wc.check_admission(R, dict(adm, code_sha256={}), fz), 'exactly')
    refuses(lambda: wc.check_admission(R, dict(adm, code_sha256=dict(adm['code_sha256'], **{'wave_core.py': '1' * 64})), fz), 'differs from the freeze')
    refuses(lambda: wc.check_admission(R, dict(adm, model_path='/mnt/d/models/other'), fz), 'model_path')
    refuses(lambda: wc.check_admission(R, dict(adm, capture_sizes=[1, 2, 4]), fz), 'capture_sizes')
    refuses(lambda: wc.check_admission(R, dict(adm, max_model_len=16384), fz), 'max_model_len')
    refuses(lambda: wc.check_admission(R, dict(adm, freeze_sha256='2' * 64), fz), 'freeze_sha256')
    (R / 'wave_core.py').rename(R / 'wave_core.py.orig'); (R / 'wave_core.py').write_bytes((R / 'wave_core.py.orig').read_bytes() + b'\n# edited\n')
    refuses(lambda: wc.check_admission(R, adm, fz), 'not the frozen file: wave_core.py')
    print('PASS admission binding: ok case, unreviewed freeze, empty/altered code map, model path, engine args, edited code')


def model_cases():
    M = Path(tempfile.mkdtemp(prefix='sham1-v11-model-')); hub = M / 'models--Qwen--Qwen3.5-4B'; snap = hub / 'snapshots' / REV; blobs = hub / 'blobs'
    snap.mkdir(parents=True); blobs.mkdir()
    pins = {}
    for n in wc.MODEL_FILES:
        b = json.dumps(dict(name=n)).encode(); (snap / n).write_bytes(b); pins[n] = H(b)
    w = b'fake weights ' * 1000; (blobs / H(w)).write_bytes(w)
    try: os.symlink(blobs / H(w), snap / 'model.safetensors')
    except OSError: print('SKIP model positive case: this account cannot make symlinks'); return
    saved = dict(wc.MODEL_FILES); wc.MODEL_FILES.clear(); wc.MODEL_FILES.update(pins)
    try:
        b = wc.bind_model(snap, REV); assert b['files']['model.safetensors'] == H(w)
        refuses(lambda: wc.bind_model(snap, '0' * 40), 'pinned snapshot')
        (snap / 'tokenizer.json').rename(snap / 'tokenizer.json.orig'); (snap / 'tokenizer.json').write_bytes(b'{}')
        refuses(lambda: wc.bind_model(snap, REV), 'tokenizer.json')
        (snap / 'tokenizer.json').rename(snap / 'tokenizer.json.bad'); (snap / 'tokenizer.json.orig').rename(snap / 'tokenizer.json')
        (blobs / H(w)).write_bytes(w + b'x')
        refuses(lambda: wc.bind_model(snap, REV), 'content-addressed blob')
    finally:
        wc.MODEL_FILES.clear(); wc.MODEL_FILES.update(saved)
    print('PASS model binding: pinned files, wrong revision, altered tokenizer, altered weight blob')


admission_cases(); model_cases(); print('ALL PASS')
