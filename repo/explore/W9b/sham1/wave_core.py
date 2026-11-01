"""SHAM Phase 1 wave-gated run core (W9b). Engine-agnostic, so the pause/resume rules can be tested on CPU
(test_wave_core.py) with a fake engine; wave_runner.py wraps vLLM around run_block(). Rules are in
SHAM-PHASE1-AMENDMENT-20261025.md section 4:
- Waves run whole and in index order. Wave w starts with WAVE-STARTED-w.json and ends with WAVE-COMPLETE-w.json, written
  only after every one of its requests has a terminal record in this block.
- Checkpoint = wave boundary. At each boundary the block stops if PAUSE exists (reason paused_at_wave_boundary),
  if a cap or the deadline would be crossed by one more wave, or if the planned number of waves is complete.
- STOP_NOW, an engine error, the deadline or a hard cap inside a wave ends the block at once. That wave is then
  ABANDONED (started, never complete): its records are kept and never scored, and its identities are never issued again.
  The next block starts the next unstarted wave index, so make-up waves replace abandoned ones.
- A block without EXIT.json (process killed) blocks every resume until the operator seals it with
  `python wave_core.py seal <block>`, which records what is on disk and changes nothing else.
No outcome is read: a record's correctness is never computed here.
"""
import hashlib, json, os, sys, time, uuid
from pathlib import Path

canon = lambda x: json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
sha = lambda b: hashlib.sha256(b).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())


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


def scan(R, manifest):
    """State of the run folder R across all blocks. Raises if a block is unsealed."""
    st = dict(complete=[], started=[], abandoned=[], tokens=0, hours=0.0, blocks=[], unsealed=[])
    for b in sorted(Path(R).glob('block-*')):
        st['blocks'].append(b.name)
        ex = b / 'EXIT.json' if (b / 'EXIT.json').exists() else b / 'EXIT-SEALED-BY-OPERATOR.json'
        if not ex.exists(): st['unsealed'].append(b.name); continue
        e = read(ex); st['tokens'] += e['new_tokens']; st['hours'] += e['elapsed'] / 3600
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


def run_block(R, engine, requests, manifest, admission, clock=time.time, status_of=None, on_progress=None, should_stop=None):
    """One block: waves until a boundary says stop, or an in-wave stop abandons the current wave.
    engine.add(key, q) submits; engine.step() returns finished items dict(key, token_ids, text, finish_reason) and
    the number of tokens generated in this step. status_of(raw, finish) is the runner's operational status only;
    should_stop() returns a reason string (e.g. resource reserve) to end the block at once, abandoning the wave."""
    R = Path(R); st = scan(R, manifest)
    assert not st['unsealed'], 'unsealed block(s) ' + str(st['unsealed']) + ': seal with `wave_core.py seal <block>` first'
    waves = by_wave(requests); assert len(waves) == manifest['waves_built']
    O = R / ('block-' + str(time.time_ns())); O.mkdir(); (O / 'records').mkdir()
    started = clock(); block_tokens = 0; reason = None; failure = None; current = None; wave_tokens, wave_seconds = [], []
    for b in st['blocks']:  # wave sizes measured in earlier blocks inform the boundary projection
        for f in (R / b).glob('WAVE-COMPLETE-*.json'):
            c = read(f); wave_tokens.append(c['tokens']); wave_seconds.append(c['seconds'])
    put(O / 'START.json', dict(state=st, started=started, admission_sha256=sha(canon(admission)), manifest_sha256=sha(canon(manifest))))
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
                if st['tokens'] + block_tokens > manifest['global_token_cap']: reason = 'token_cap_in_wave'; break
                if should_stop and (why := should_stop()): reason = why; break
                while i < len(todo) and len(active) < manifest['max_active']:
                    engine.add(todo[i]['identity_sha256'], todo[i]); active.add(todo[i]['identity_sha256']); i += 1
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
        engine.close()
        put(O / 'EXIT.json', dict(reason=reason, engine_error=failure, abandoned_wave=current, new_tokens=block_tokens,
                                  elapsed=clock() - started, complete=sorted(st['complete']), scope='EXPLORATORY_ONLY'))
    if failure: raise RuntimeError(failure)
    return reason


def seal(block):
    """Operator seal for a block whose process died without EXIT.json. Records what is on disk; deletes nothing."""
    b = Path(block); assert not (b / 'EXIT.json').exists() and not (b / 'EXIT-SEALED-BY-OPERATOR.json').exists()
    recs = sorted(p.name for p in (b / 'records').glob('*.json'))
    toks = sum(read(b / 'records' / n)['record']['output_tokens'] for n in recs)
    started = read(b / 'START.json')['started']
    put(b / 'EXIT-SEALED-BY-OPERATOR.json', dict(reason='process_died_sealed_by_operator', records=len(recs), new_tokens=toks,
                                                 elapsed=max([0.0] + [os.path.getmtime(b / 'records' / n) - started for n in recs]),
                                                 note='tokens counted from terminal records only; in-flight work is lost, so the started-not-complete wave is abandoned'))


if __name__ == '__main__':
    if sys.argv[1:2] == ['seal']: seal(sys.argv[2]); print('sealed', sys.argv[2])
    elif sys.argv[1:2] == ['status']:
        print(json.dumps(scan(sys.argv[2], read(Path(sys.argv[2]) / 'MANIFEST.json')), indent=1))
    else: raise SystemExit('usage: wave_core.py seal <block> | status <run>')
