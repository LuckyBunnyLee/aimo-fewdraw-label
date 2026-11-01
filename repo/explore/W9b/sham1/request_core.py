"""CPU-only request preparation/parser. No engine, inference or label authority."""
import hashlib
import json
import re
from pathlib import Path

SYSTEM_PATH = Path(__file__).with_name('canonical-system-prompt.txt')
SYSTEM_SHA = '72283c58f504d7c3d32d66066fcb06aecc20d14e93136cd6b1589f7f3ce7b002'
KEY_FIELDS = ('model', 'problem_id', 'family', 'variant_id', 'replicate')
CONTENT_FIELDS = KEY_FIELDS + ('system', 'problem', 'model_revision', 'settings')

def prepare(request, *, prompt_tokens, context_limit):
    key = [request[f] for f in KEY_FIELDS]
    if any(type(v) is not str or not v for v in key[:4]):
        raise ValueError('invalid identity')
    if type(key[4]) is not int or key[4] < 0:
        raise ValueError('invalid replicate')
    system = SYSTEM_PATH.read_bytes()
    if hashlib.sha256(system).hexdigest() != SYSTEM_SHA:
        raise ValueError('canonical system hash mismatch')
    if request['system'].encode('utf-8') != system:
        raise ValueError('system mismatch')
    if type(request['problem']) is not str or not request['problem']:
        raise ValueError('empty problem')
    if type(request['model_revision']) is not str or not request['model_revision']:
        raise ValueError('model revision missing')
    settings = request['settings']
    expected = {'max_new_tokens': 100000, 'temperature': 1, 'top_k': 40, 'top_p': .95,
                'enable_thinking': True}
    allowed = set(expected) | {'tokenizer_revision', 'template_sha256', 'eos_policy', 'stop'}
    if set(settings) != allowed:
        raise ValueError('unknown or missing generation settings')
    if any(settings.get(k) != v for k, v in expected.items()):
        raise ValueError('generation settings mismatch')
    for field in ('tokenizer_revision', 'template_sha256', 'eos_policy', 'stop'):
        if field not in settings:
            raise ValueError('unfrozen setting: ' + field)
    if not settings['tokenizer_revision'] or not re.fullmatch('[0-9a-f]{64}', settings['template_sha256']):
        raise ValueError('unresolved tokenizer/template')
    if settings['eos_policy'] != 'model-eos' or settings['stop'] != []:
        raise ValueError('unsupported EOS or stop policy')
    if any(type(x) is not int or x < 0 for x in (prompt_tokens, context_limit)):
        raise ValueError('invalid context accounting')
    if prompt_tokens + 100000 > context_limit:
        raise ValueError('context_infeasible')
    payload = {f: request[f] for f in CONTENT_FIELDS}
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'),
                           ensure_ascii=False, allow_nan=False).encode('utf-8')
    digest = hashlib.sha256(canonical).digest()
    return {'key': key, 'request_sha256': digest.hex(),
            'seed': int.from_bytes(digest[:8], 'big') & ((1 << 63) - 1),
            'messages': [{'role': 'system', 'content': request['system']},
                         {'role': 'user', 'content': request['problem']}],
            'settings': json.loads(json.dumps(settings)), 'prompt_tokens': prompt_tokens,
            'context_limit': context_limit, 'labels_authorized': False}

def prepare_batch(requests, *, token_counter, context_limit):
    prepared, seen = [], set()
    for request in requests:
        item = prepare(request, prompt_tokens=token_counter(request), context_limit=context_limit)
        key = tuple(item['key'])
        if key in seen:
            raise ValueError('duplicate request identity')
        seen.add(key)
        prepared.append(item)
    return prepared

def parse_output(raw, finish_reason, error=None):
    result = {'status': 'error', 'answer': None}
    if error is not None:
        return result
    if finish_reason in ('length', 'max_tokens', 'context_limit'):
        result['status'] = 'truncated'
        return result
    if finish_reason not in ('stop', 'eos'):
        return result
    lines = [line for line in raw.rsplit('</think>', 1)[-1].splitlines() if line.strip()]
    match = re.fullmatch(r'\s*ANSWER:\s*(-?\d+|NaN)\s*', lines[-1]) if lines else None
    if not match:
        result['status'] = 'invalid_output'
    elif match[1] == 'NaN':
        result['status'] = 'abstain'
    else:
        # Chunk conversion preserves the legacy unlimited integer grammar without
        # changing Python's process-wide security limit for decimal conversion.
        digits = match[1].lstrip('-')
        answer = 0
        for offset in range(0, len(digits), 1000):
            chunk = digits[offset:offset + 1000]
            answer = answer * (10 ** len(chunk)) + int(chunk)
        result.update(status='complete', answer=-answer if match[1].startswith('-') else answer)
    return result
