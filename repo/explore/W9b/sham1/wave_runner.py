"""SHAM Phase 1 GPU runner (W9b design; CL launches, in WSL, on the admitted GPU). One process = one block.
Environment, resource guard, model binding and engine settings are copied from CL's READY63/fresh6h runner
(explore/CL-5070-recovery-20261020-1740/ready63-reliability/run_overnight.py, sha e8360555...), so the endpoint is
the report's. Wave gating, pause, abandonment and caps are in wave_core.py (tested on CPU by test_wave_core.py).

Operator controls, in the run folder R (the folder holding this script, MANIFEST.json, REQUESTS.json, TRUTHS.json,
request_core.py, wave_core.py and CL's ADMISSION.json):
  touch R/PAUSE      finish the current wave, write its checkpoint, exit (GPU free). Latency up to one wave, ~80 min.
  touch R/STOP_NOW   exit within seconds; the current wave is abandoned (kept, never scored) and a make-up wave replaces it.
  resume             delete PAUSE / STOP_NOW and relaunch this script unchanged; it starts the next unstarted wave.
  killed process     python wave_core.py seal R/block-<id>, then relaunch.
  status             python wave_core.py status R
"""
import os, sys, pathlib, json, time, hashlib, subprocess, fcntl
R = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(R)); import wave_core as wc
canon, sha, read, put = wc.canon, wc.sha, wc.read, wc.put
admission = read(R / 'ADMISSION.json')
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2]); os.setpriority(os.PRIO_PROCESS, 0, 15)
for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'MAX_JOBS', 'NUMEXPR_NUM_THREADS'): os.environ[k] = '2'
os.environ.update(HF_HUB_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1', VLLM_NO_USAGE_STATS='1', VLLM_DO_NOT_TRACK='1', DO_NOT_TRACK='1', OTEL_SDK_DISABLED='true',
                  VLLM_ENABLE_V1_MULTIPROCESSING='0', VLLM_USE_FLASHINFER_SAMPLER='0', PYTHONDONTWRITEBYTECODE='1', CUDA_HOME='/opt/vllm/lib/python3.12/site-packages/nvidia/cu13')
os.environ['PATH'] = os.environ['CUDA_HOME'] + '/bin:' + os.environ.get('PATH', '')
for key, sub in [('TORCH_HOME', 'torch'), ('XDG_CACHE_HOME', 'cache'), ('TRITON_CACHE_DIR', 'triton'), ('VLLM_CACHE_ROOT', 'vllm-cache'), ('TORCHINDUCTOR_CACHE_DIR', 'inductor'),
                 ('CUDA_CACHE_PATH', 'cuda-cache'), ('TMPDIR', 'tmp'), ('VLLM_CONFIG_ROOT', 'vllm-config')]:
    p = pathlib.Path(admission['cache_root']) / sub; p.mkdir(parents=True, exist_ok=True); os.environ[key] = str(p)


def resource():
    command = ['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
               "@{free_gib=(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB;c_free=(Get-PSDrive C).Free;d_free=(Get-PSDrive D).Free}|ConvertTo-Json -Compress"]
    return json.loads(subprocess.check_output(command, text=True, timeout=15))


lock = (R / 'OWNED.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
m = read(R / 'MANIFEST.json')
assert admission['generation_authorized'] and admission['base_manifest_sha256'] == sha((R / 'MANIFEST.json').read_bytes())
assert m['scope'] == 'EXPLORATORY_ONLY' and sha((R / 'REQUESTS.json').read_bytes()) == m['request_sha256'] and sha((R / 'TRUTHS.json').read_bytes()) == m['truth_sha256']
for name, h in admission['code_sha256'].items(): assert sha((R / name).read_bytes()) == h, 'code changed since admission: ' + name
requests = read(R / 'REQUESTS.json'); assert len(requests) == m['requests']
res = resource(); assert res['free_gib'] >= 33 and res['c_free'] > 15 * 1024**3 and res['d_free'] > 20 * 1024**3
gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True).strip().split(',')
assert int(gpu[0]) < 1024 and int(gpu[1]) <= 5, 'GPU not idle'
cg = pathlib.Path('/sys/fs/cgroup') / ('cl-explore-sham1-' + str(os.getpid()) + '-' + str(time.time_ns())); cg.mkdir()
(cg / 'memory.max').write_text(str(7 * 1024**3)); (cg / 'memory.swap.max').write_text('0'); (cg / 'cgroup.procs').write_text(str(os.getpid()))
from transformers import AutoTokenizer
MODEL = admission['model_path']
cfg = read(pathlib.Path(MODEL) / 'config.json'); native = cfg.get('text_config', cfg).get('max_position_embeddings')
assert native and admission['max_model_len'] <= native, 'No implicit context extension'
tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
template = sha(json.dumps(tok.chat_template, sort_keys=True, ensure_ascii=False).encode()); assert template == m['settings']['template_sha256']
import torch
torch.set_num_threads(4); torch.set_num_interop_threads(1)
from vllm import LLM, SamplingParams
from vllm.config import CompilationConfig
from vllm.config.compilation import CUDAGraphMode
from vllm.sampling_params import RequestOutputKind
from request_core import parse_output
CAP = m['max_new_tokens']
llm = LLM(model=MODEL, dtype='bfloat16', max_model_len=admission['max_model_len'], max_num_seqs=m['max_active'], gpu_memory_utilization=.88, max_num_batched_tokens=2048,
          enforce_eager=False, compilation_config=CompilationConfig(mode=0, cudagraph_mode=CUDAGraphMode.FULL_DECODE_ONLY, cudagraph_capture_sizes=admission['capture_sizes']),
          enable_prefix_caching=True, seed=20261019, limit_mm_per_prompt={'image': 0, 'video': 0})


class Engine:
    def __init__(self): self.state = {}; self.render = {}
    def add(self, key, q):
        assert q['identity_sha256'] == sha(canon(q['identity'])) and sha(q['problem'].encode()) == q['identity']['text_sha256']
        assert type(q['seed']) is int and q['seed'] == int(key[:16], 16) & ((1 << 63) - 1) and q['settings']['enable_thinking'] is False
        ck = (q['system'], q['problem'])
        if ck not in self.render:
            msgs = [dict(role='system', content=q['system']), dict(role='user', content=q['problem'])]
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
            assert text.endswith('<think>\n\n</think>\n\n'), 'No-think template was not applied'
            ids = tok(text, add_special_tokens=False)['input_ids']; assert len(ids) <= 4000; self.render[ck] = ids
        self.state[key] = dict(ids=[], raw='')
        llm.llm_engine.add_request(key, {'prompt_token_ids': self.render[ck]}, SamplingParams(temperature=1, top_k=40, top_p=.95, max_tokens=CAP, seed=q['seed'],
                                   ignore_eos=False, stop=None, output_kind=RequestOutputKind.DELTA))
    def step(self):
        done, n = [], 0
        for out in llm.llm_engine.step():
            if not out.outputs: continue
            y = out.outputs[0]; s = self.state[out.request_id]; s['ids'].extend(y.token_ids); s['raw'] += y.text; n += len(y.token_ids)
            assert len(s['ids']) <= CAP
            if out.finished:
                done.append(dict(key=out.request_id, token_ids=s['ids'], text=s['raw'], finish_reason=y.finish_reason)); del self.state[out.request_id]
        return done, n
    def close(self): pass


last = dict(res=time.time(), prog=0.0)


def should_stop():
    if time.time() - last['res'] < 30: return None
    last['res'] = time.time(); r = resource()
    return 'resource_reserve' if r['free_gib'] < 26 or r['c_free'] <= 15 * 1024**3 else None


def progress(p):
    if time.time() - last['prog'] >= 60:
        last['prog'] = time.time(); (R / 'PROGRESS.json').write_text(json.dumps(dict(p, time=time.time(), gpu_peak_bytes=torch.cuda.max_memory_allocated())))


reason = wc.run_block(R, Engine(), requests, m, admission, status_of=lambda raw, fin: parse_output(raw, fin)['status'], on_progress=progress, should_stop=should_stop)
print('EXIT', reason)
