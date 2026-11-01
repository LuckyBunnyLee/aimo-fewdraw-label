"""SHAM Phase 1 wave-gated run core (W9b), v1.1. Engine-agnostic, so the pause/resume and cap rules can be tested on CPU
(test_wave_core.py) with a fake engine; wave_runner.py wraps vLLM around it. Rules: SHAM-PHASE1-AMENDMENT-20261025.md
section 4 as changed by SHAM-PHASE1-v1.1-ADDENDUM.md (V23 fixes 1-2).
- A block is opened (open_block) before the model is loaded, and its clock starts at process start, so loading, load
  failures and dead time are charged. Every block ends with EXIT.json (close_block) or an operator seal.
- Waves run whole and in index order. Wave w starts with WAVE-STARTED-w.json and ends with WAVE-COMPLETE-w.json, written
  only after every one of its requests has a terminal record in this block.
- Checkpoint = wave boundary. At each boundary the block stops if PAUSE exists (reason paused_at_wave_boundary),
  if a cap or the deadline would be crossed by one more wave, or if the planned number of waves is complete.
- Hard caps inside a wave. GPU hours: the block stops once used hours plus a 60 s shutdown margin reach the cap.
  Tokens: a request is submitted only if used tokens plus max_new_tokens for every active request (itself included)
  stay within the cap, so no sequence of steps can cross it; if the next submission would, the block stops.
- STOP_NOW, an engine error, the deadline or a hard cap inside a wave ends the block at once. That wave is then
  ABANDONED (started, never complete): its records are kept and never scored, and its identities are never issued again.
  The next block starts the next unstarted wave index, so make-up waves replace abandoned ones.
- Every submission is first appended to the block's ADMITTED.jsonl and fsynced. A block without EXIT.json (process
  killed) blocks every resume until the operator seals it with `python wave_core.py seal <block>`. The seal requires
  the run lock to be free (the process is dead) and charges a bound, not a count: tokens = terminal-record tokens +
  max_new_tokens for each admitted request without a record; hours = seal time - process start. Nothing is deleted.
- scan() refuses to resume if any block's cost cannot be bounded (no ledger, no exit or seal, or a malformed ledger).
No outcome is read: a record's correctness is never computed here.
"""
import hashlib, json, os, sys, time, uuid
from pathlib import Path

canon = lambda x: json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
sha = lambda b: hashlib.sha256(b).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
SHUTDOWN_MARGIN_S = 60.0
LEDGER = 'ADMITTED.jsonl'


def put(p, x):
    """Atomic exclusive write: stage, fsync, hard-link into place (fails if p exists)."""
    p = Path(p); stage = p.with_name(p.name + '.' + uuid.uuid4().hex + '.pending')
    with stage.open('xb') as f: f.write(canon(x)); f.flush(); os.fsync(f.fileno())
    os.link(stage, p); os.unlink(stage)


def by_wave(requests):
    out = {}
    for q in requests: out.setdefault(q['wave'], []).append(q)
    assert sorted(out) == list(range(len(out))), 'waves must be 0..W-1'
    return out


def ledger(b):
    """Admitted keys of block b. A torn final line was never fsynced, so its requests were never submitted."""
    p = Path(b) / LEDGER; assert p.exists(), 'cost cannot be bounded: no ' + LEDGER + ' in ' + Path(b).name
    lines = p.read_bytes().split(b'\n'); keys = []
    for i, ln in enumerate(lines):
        if not ln: continue
        try: e = json.loads(ln)
        except ValueError:
            assert i == len(lines) - 1, 'cost cannot be bounded: malformed ledger line in ' + Path(b).name; continue
        keys.extend(e['keys'])
    assert len(keys) == len(set(keys)), 'a key was admitted twice in ' + Path(b).name
    return keys


def scan(R, manifest):
    """State of the run folder R across all blocks, with charged tokens and hours. Raises if a block is unsealed
    or its cost cannot be bounded."""
    st = dict(complete=[], started=[], abandoned=[], tokens=0, hours=0.0, blocks=[], unsealed=[])
    for b in sorted(Path(R).glob('block-*')):
        st['blocks'].append(b.name)
        ex = b / 'EXIT.json' if (b / 'EXIT.json').exists() else b / 'EXIT-SEALED-BY-OPERATOR.json'
        if not ex.exists(): st['unsealed'].append(b.name); continue
        e = read(ex); assert e.get('charged_tokens') is not None and e.get('charged_seconds') is not None, 'cost cannot be bounded: ' + b.name
        ledger(b); st['tokens'] += e['charged_tokens']; st['hours'] += e['charged_seconds'] / 3600
        for f in b.glob('WAVE-STARTED-*.json'): st['started'].append(int(f.stem.rsplit('-', 1)[1]))
        for f in b.glob('WAVE-COMPLETE-*.json'): st['complete'].append(int(f.stem.rsplit('-', 1)[1]))
    assert len(st['started']) == len(set(st['started'])), 'a wave was started twice'
    st['started'].sort(); st['complete'].sort()
    assert set(st['complete']) <= set(st['started'])
    st['abandoned'] = [w for w in st['started'] if w not in st['complete']]
    return st


def boundary(R, st, manifest, admission, block_tokens, block_started, wave_tokens, wave_seconds, now):
    """Decision at a wave boundary: ('run', w) or ('stop', reason). Order of checks is frozen."""
    n_waves = manifest['waves_built']; planned = manifest['waves_planned']
    done = len(st['complete'])
    if done >= planned: return ('stop', 'complete')
    nxt = next((w for w in range(n_waves) if w not in st['started']), None)
    if nxt is None: return ('stop', 'wave_pool_exhausted')
    if (Path(R) / 'PAUSE').exists(): return ('stop', 'paused_at_wave_boundary')
    if (Path(R) / 'STOP_NOW').exists(): return ('stop', 'operator_stop_at_boundary')
    est_tok = 1.25 * (max(wave_tokens) if wave_tokens else manifest['requests_per_wave'] * 1000)
    est_sec = 1.25 * (max(wave_seconds) if wave_seconds else 2.0 * 3600)
    used_tok = st['tokens'] + block_tokens; used_h = st['hours'] + (now - block_started) / 3600
    if used_tok + est_tok > manifest['global_token_cap']: return ('stop', 'token_cap_at_boundary')
    if used_h + est_sec / 3600 > manifest['gpu_hour_cap']: return ('stop', 'gpu_hour_cap_at_boundary')
    if now + est_sec > admission['absolute_deadline']: return ('stop', 'deadline_at_boundary')
    return ('run', nxt)


def open_block(R, manifest, admission, started, clock=time.time):
    """Create the block before the model loads. `started` is the process start time: the block is charged from then."""
    R = Path(R); st = scan(R, manifest)
    assert not st['unsealed'], 'unsealed block(s) ' + str(st['unsealed']) + ': seal with `wave_core.py seal <block>` first'
    assert st['tokens'] < manifest['global_token_cap'] and st['hours'] < manifest['gpu_hour_cap'], 'a cap is already used up'
    O = R / ('block-' + str(time.time_ns())); O.mkdir(); (O / 'records').mkdir()
    with (O / LEDGER).open('xb') as f: f.flush(); os.fsync(f.fileno())
    put(O / 'START.json', dict(state=st, started=started, opened=clock(), admission_sha256=sha(canon(admission)), manifest_sha256=sha(canon(manifest))))
    return dict(R=R, O=O, st=st, started=started)


def bound_tokens(O, max_new):
    """Upper bound on tokens generated in block O: terminal-record tokens + max_new for each admitted key without a record."""
    keys = ledger(O); have = {p.stem for p in (Path(O) / 'records').glob('*.json')}
    assert have <= set(keys), 'record without ledger entry in ' + Path(O).name
    return sum(read(Path(O) / 'records' / (k + '.json'))['record']['output_tokens'] for k in have) + max_new * (len(keys) - len(have)), len(keys), len(have)


def close_block(blk, reason, failure, current, counted_tokens, manifest, clock=time.time):
    """EXIT.json. A clean stop charges the counted tokens; an error, a load failure or an interrupt (reason None)
    charges the ledger bound (never less than counted)."""
    O = blk['O']; bound, admitted, terminal = bound_tokens(O, manifest['max_new_tokens'])
    clean = failure is None and reason is not None and reason not in ('engine_error', 'load_error')
    charged = counted_tokens if clean else max(counted_tokens, bound); reason = reason or 'interrupted'
    now = clock()
    put(O / 'EXIT.json', dict(reason=reason, engine_error=failure, abandoned_wave=current, new_tokens=counted_tokens, token_bound=bound,
                              charged_tokens=charged, elapsed=now - blk['started'], charged_seconds=now - blk['started'],
                              admitted=admitted, terminal=terminal, complete=sorted(blk['st']['complete']), scope='EXPLORATORY_ONLY'))


def run_block(R, engine, requests, manifest, admission, clock=time.time, status_of=None, on_progress=None, should_stop=None, block=None):
    """One block: waves until a boundary says stop, or an in-wave stop abandons the current wave.
    engine.add(key, q) submits; engine.step() returns finished items dict(key, token_ids, text, finish_reason) and
    the number of tokens generated in this step. status_of(raw, finish) is the runner's operational status only;
    should_stop() returns a reason string (e.g. resource reserve) to end the block at once, abandoning the wave.
    block: from open_block (the runner opens it before loading); if None it is opened here with started = now."""
    blk = block or open_block(R, manifest, admission, clock(), clock); R, O, st, started = blk['R'], blk['O'], blk['st'], blk['started']
    waves = by_wave(requests); assert len(waves) == manifest['waves_built']
    CAP, TCAP, HCAP = manifest['max_new_tokens'], manifest['global_token_cap'], manifest['gpu_hour_cap']
    block_tokens = 0; reason = None; failure = None; current = None; wave_tokens, wave_seconds = [], []
    for b in st['blocks']:  # wave sizes measured in earlier blocks inform the boundary projection
        for f in (R / b).glob('WAVE-COMPLETE-*.json'):
            c = read(f); wave_tokens.append(c['tokens']); wave_seconds.append(c['seconds'])
    led = (O / LEDGER).open('ab')
    try:
        while True:
            act = boundary(R, st, manifest, admission, block_tokens, started, wave_tokens, wave_seconds, clock())
            if act[0] == 'stop': reason = act[1]; break
            w = act[1]; current = w; todo = list(waves[w]); qmap = {q['identity_sha256']: q for q in todo}; keys = set(qmap)
            put(O / f'WAVE-STARTED-{w}.json', dict(wave=w, requests=len(todo), time=clock())); st['started'].append(w)
            w0, wt0, active, done, i = clock(), block_tokens, set(), {}, 0
            while len(done) < len(todo):
                if (R / 'STOP_NOW').exists(): reason = 'operator_stop_now'; break
                if clock() >= admission['absolute_deadline']: reason = 'deadline_in_wave'; break
                if st['hours'] + (clock() - started + SHUTDOWN_MARGIN_S) / 3600 >= HCAP: reason = 'gpu_hour_cap_in_wave'; break
                if should_stop and (why := should_stop()): reason = why; break
                batch = []
                while i < len(todo) and len(active) + len(batch) < manifest['max_active']:
                    if st['tokens'] + block_tokens + CAP * (len(active) + len(batch) + 1) > TCAP: break
                    batch.append(todo[i]); i += 1
                if i < len(todo) and len(active) + len(batch) < manifest['max_active']:
                    reason = 'token_cap_in_wave'; break  # the cap blocks the next submission, so the wave cannot finish: stop now, abandoning it
                if batch:
                    led.write(canon(dict(keys=[q['identity_sha256'] for q in batch], wave=w, time=clock())) + b'\n'); led.flush(); os.fsync(led.fileno())
                    for q in batch: engine.add(q['identity_sha256'], q); active.add(q['identity_sha256'])
                finished, ntok = engine.step(); block_tokens += ntok
                for y in finished:
                    k = y['key']; assert k in active and k in keys and k not in done; q = qmap[k]
                    rec = dict(identity=q['identity'], identity_sha256=k, seed=q['seed'], request_sha256=sha(canon(q)), raw=y['text'], raw_sha256=sha(y['text'].encode()), token_ids=y['token_ids'],
                               output_tokens=len(y['token_ids']), finish_reason=y['finish_reason'], error=None, wave=w,
                               status=status_of(y['text'], y['finish_reason']) if status_of else None, scope='EXPLORATORY_ONLY')
                    put(O / 'records' / (k + '.json'), dict(record=rec, record_sha256=sha(canon(rec))))
                    active.discard(k); done[k] = sha(canon(rec))
                if on_progress: on_progress(dict(wave=w, completed=len(done), submitted=i, active=len(active), block_tokens=block_tokens))
            if reason: break
            assert set(done) == keys
            put(O / f'WAVE-COMPLETE-{w}.json', dict(wave=w, records=done, tokens=block_tokens - wt0, seconds=clock() - w0, time=clock()))
            st['complete'].append(w); wave_tokens.append(block_tokens - wt0); wave_seconds.append(clock() - w0); current = None
            put(O / f'CHECKPOINT-{w}.json', dict(after_wave=w, complete=sorted(st['complete']), abandoned=[x for x in st['started'] if x not in st['complete']],
                                                  block_tokens=block_tokens, time=clock()))
    except Exception as exc:
        failure = repr(exc); reason = 'engine_error'
    finally:
        led.close(); engine.close()
        close_block(blk, reason, failure, current, block_tokens, manifest, clock)
    if failure: raise RuntimeError(failure)
    return reason


def seal(block, now=None, lock_check=True):
    """Operator seal for a block whose process died without EXIT.json. Charges a conservative bound; deletes nothing.
    lock_check: the run's OWNED.lock must be free, which proves no runner holds the folder (Linux, where CL runs it)."""
    b = Path(block); assert not (b / 'EXIT.json').exists() and not (b / 'EXIT-SEALED-BY-OPERATOR.json').exists()
    if lock_check:
        import fcntl
        with (b.parent / 'OWNED.lock').open('a') as lk:
            try: fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError: raise SystemExit('refused: the run lock is held, so a runner may still be alive')
            fcntl.flock(lk, fcntl.LOCK_UN)
    m = read(b.parent / 'MANIFEST.json'); s = read(b / 'START.json'); now = time.time() if now is None else now
    bound, admitted, terminal = bound_tokens(b, m['max_new_tokens'])
    put(b / 'EXIT-SEALED-BY-OPERATOR.json', dict(reason='process_died_sealed_by_operator', admitted=admitted, records=terminal, token_bound=bound,
                                                 charged_tokens=bound, charged_seconds=now - s['started'], sealed_at=now,
                                                 note='conservative: in-flight requests charged max_new_tokens each, time charged from process start to the seal; '
                                                      'the started-not-complete wave is abandoned'))


# Admission binding (V23 fix 3). Shared by wave_runner.py (before anything loads) and by CL's CPU check
# `python wave_core.py admit-check <RUN> <reviewed-freeze-sha256>` before launch.
CODE = ('wave_runner.py', 'wave_core.py', 'request_core.py')
BOUND = CODE + ('MANIFEST.json', 'REQUESTS.json', 'TRUTHS.json')
FREEZE = 'SHAM1-FREEZE-v1.1.sha256'
MODEL_PATH = '/root/.cache/huggingface/hub/models--Qwen--Qwen3.5-4B/snapshots/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
# config / tokenizer hashes recorded by all 120 earlier CL MODEL-BINDING.json files for this snapshot (READY63, fresh6h)
MODEL_FILES = {'config.json': 'ddc63e1c717afa86c865bb5e01313d89d72bb53b97ad4a8a03ba8510c0621670',
               'tokenizer_config.json': '316230d6a809701f4db5ea8f8fc862bc3a6f3229c937c174e674ff3ca0a64ac8',
               'tokenizer.json': '5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42'}
ENGINE = dict(max_model_len=8192, capture_sizes=[1, 2, 4, 8, 16, 32])


def file_sha(p, chunk=1 << 24):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while (b := f.read(chunk)): h.update(b)
    return h.hexdigest()


def check_admission(R, admission, reviewed_freeze=None):
    """Bind the run folder to the reviewed v1.1 freeze. Returns the freeze map. Raises on any mismatch."""
    R = Path(R); fz = R / FREEZE; assert fz.exists(), 'no ' + FREEZE + ' in the run folder'
    fsha = sha(fz.read_bytes()); assert admission.get('freeze_sha256') == fsha, 'ADMISSION.freeze_sha256 does not match ' + FREEZE
    if reviewed_freeze is not None: assert fsha == reviewed_freeze, 'freeze is not the reviewed one'
    fm = {}
    for line in fz.read_text().splitlines():
        h, p = line.split(None, 1); n = Path(p.strip()).name; assert n not in fm, 'freeze names two files ' + n; fm[n] = h
    for name in BOUND: assert name in fm and file_sha(R / name) == fm[name], 'not the frozen file: ' + name
    cs = admission.get('code_sha256'); assert isinstance(cs, dict) and set(cs) == set(CODE), 'code_sha256 must name exactly ' + str(CODE)
    for name in CODE: assert cs[name] == fm[name], 'code_sha256 differs from the freeze: ' + name
    assert admission.get('generation_authorized') is True and admission.get('base_manifest_sha256') == fm['MANIFEST.json']
    assert admission.get('model_path') == MODEL_PATH, 'model_path must be the pinned snapshot ' + MODEL_PATH
    for k, v in ENGINE.items(): assert admission.get(k) == v, f'{k} must be {v}'
    assert isinstance(admission.get('absolute_deadline'), (int, float)) and isinstance(admission.get('cache_root'), str)
    return fm


def bind_model(path, revision):
    """Hash the admitted snapshot: pinned config/tokenizer files, and every weight file, whose content-addressed
    blob name (Hugging Face cache, sha256 for LFS files) must equal its hash. Returns the binding record."""
    p = Path(path); assert p.name == revision and p.parent.name == 'snapshots' and p.parent.parent.name == 'models--Qwen--Qwen3.5-4B', 'not the pinned snapshot'
    out = dict(snapshot=str(p), revision=revision, files={})
    for name, h in MODEL_FILES.items():
        got = file_sha(p / name); assert got == h, 'model file differs from the pinned hash: ' + name; out['files'][name] = got
    shards = sorted(x.name for x in p.glob('*.safetensors')); assert shards, 'no weight files'
    idx = p / 'model.safetensors.index.json'
    if idx.exists():
        listed = sorted(set(read(idx)['weight_map'].values())); assert listed == shards, 'index and shards differ'; out['files']['model.safetensors.index.json'] = file_sha(idx)
    for s in shards:
        got = file_sha(p / s); blob = Path(os.path.realpath(p / s)).name
        assert len(blob) == 64 and blob == got, 'weight file does not match its content-addressed blob: ' + s; out['files'][s] = got
    return out


if __name__ == '__main__':
    if sys.argv[1:2] == ['admit-check']:
        R = Path(sys.argv[2]); a = read(R / 'ADMISSION.json'); check_admission(R, a, sys.argv[3]); m = read(R / 'MANIFEST.json')
        b = bind_model(a['model_path'], m['model_revision']); print(json.dumps(dict(admission='ok', freeze=sys.argv[3], model=b), indent=1))
    elif sys.argv[1:2] == ['seal']: seal(sys.argv[2]); print('sealed', sys.argv[2])
    elif sys.argv[1:2] == ['status']:
        print(json.dumps(scan(sys.argv[2], read(Path(sys.argv[2]) / 'MANIFEST.json')), indent=1))
    else: raise SystemExit('usage: wave_core.py admit-check <run> <reviewed-freeze-sha256> | seal <block> | status <run>')
