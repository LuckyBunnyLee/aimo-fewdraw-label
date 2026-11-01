"""Frozen answer parser for the thinking-on reliability repeat (W9b, 24 Oct 2026). Pure; no I/O at import.
Written before any output of the run exists, from the failure categories in explore/W9b/WHY-PARSER-FAILS-20261023.md
(AN-47: boxed answers, bold ANSWER, LaTeX-wrapped ANSWER). Applied to the text after the last </think>.
  1. the last line that is an ANSWER line once markdown/LaTeX wrappers are removed; else
  2. the last \\boxed{...} (balanced braces) in the tail; else
  3. (r2) the last line labelled 'Final Answer:' or 'Answer:' (any case) once wrappers are removed; else no answer.
r2 (24 Oct, before any output, V14 fix 6): path 3 added and \\text{NaN} counts as abstain. Paths 1-2 are unchanged.
Statuses: numeric | abstain (NaN) | nonnumeric (answer found, not an exact number) | noanswer | unclosed (thinking never
closed) | truncated | error | invalid (other finish)."""
import re
from fractions import Fraction

WRAP = [r'\*\*', r'__', r'\$\$', r'\$', r'\\\[', r'\\\]', r'\\\(', r'\\\)', r'`']
ANS = re.compile(r'^(?:[#>\-\s]*)ANSWER\s*:\s*(.*?)\s*$')
LABEL = re.compile(r'^(?:[#>\-\s]*)(?:final\s+)?answer\s*:\s*(.*?)\s*$', re.I)
TEXT_ANS = re.compile(r'\\text(?:bf|rm)?\{\s*ANSWER\s*:?\s*\}\s*:?')


def norm_line(s):
    s = TEXT_ANS.sub('ANSWER: ', s)
    for w in WRAP:
        s = re.sub(w, '', s)
    return s.strip()


def last_boxed(t):
    i = t.rfind('\\boxed{')
    if i < 0:
        return None
    j = i + len('\\boxed{'); depth = 1; k = j
    while k < len(t) and depth:
        depth += {'{': 1, '}': -1}.get(t[k], 0); k += 1
    return t[j:k - 1] if depth == 0 else None


FRAC = re.compile(r'^(-?)\\[dt]?frac\{(-?[\d.]+)\}\{(-?[\d.]+)\}$')


def unwrap(v):
    v = v.strip()
    for _ in range(3):
        m = re.fullmatch(r'\\boxed\{(.*)\}', v) or re.fullmatch(r'\{(.*)\}', v) or re.fullmatch(r'\\text\{(.*)\}', v)
        if m:
            v = m[1].strip()
    return v


def to_fraction(v):
    v = unwrap(v)
    v = re.sub(r'\\[,!; ]', '', v).replace(',', '').replace(' ', '').rstrip('.')
    m = FRAC.fullmatch(v)
    if m:
        f = Fraction(m[2]) / Fraction(m[3])
        return -f if m[1] else f
    return Fraction(v)  # integers, decimals, a/b; raises ValueError/ZeroDivisionError otherwise


def parse(raw, finish, error, truth):
    """Returns dict(status, answer, correct, path). correct is 0/1 for numeric, else None; always None when truth is None
    (the r2 engine check reads statuses without truths)."""
    out = dict(status='invalid', answer=None, correct=None, path=None)
    if finish in ('length', 'max_tokens', 'context_limit'):
        out['status'] = 'truncated'; return out
    if error is not None:
        out['status'] = 'error'; return out
    if finish not in ('stop', 'eos'):
        return out
    if '</think>' not in raw:
        out['status'] = 'unclosed'; return out
    tail = raw.rsplit('</think>', 1)[1]
    val = None
    for line in reversed(tail.strip().splitlines()):
        m = ANS.fullmatch(norm_line(line))
        if m and m[1]:
            val, out['path'] = m[1], 'answer_line'; break
    if val is None:
        b = last_boxed(tail)
        if b is not None and b.strip():
            val, out['path'] = b, 'boxed'
    if val is None:
        for line in reversed(tail.strip().splitlines()):
            m = LABEL.fullmatch(norm_line(line))
            if m and m[1]:
                val, out['path'] = m[1], 'label_line'; break
    if val is None:
        out['status'] = 'noanswer'; return out
    if unwrap(val).rstrip('.').strip() == 'NaN':
        out['status'] = 'abstain'; return out
    try:
        a = to_fraction(val)
    except (ValueError, ZeroDivisionError):
        out['status'] = 'nonnumeric'; out['answer'] = val[:80]; return out
    out.update(status='numeric', answer=str(a), correct=None if truth is None else int(a == Fraction(str(truth))))
    return out


def boxed_disagrees(raw, parsed):
    """Diagnostic only: an ANSWER line was used and a different numeric \\boxed{} value is also present."""
    if parsed['path'] != 'answer_line' or '</think>' not in raw:
        return False
    b = last_boxed(raw.rsplit('</think>', 1)[1])
    try:
        return b is not None and str(to_fraction(b)) != parsed['answer']
    except (ValueError, ZeroDivisionError):
        return False


# Grading rules. O (primary, organiser-like): every parsed draw is graded; anything but a correct exact number is wrong
# (truncation counts as wrong, as in the organisers' FAQ). Only error / missing / binding failure is ungradable.
# S (secondary): only numeric draws are gradable (the X3-64 strict rule, with this parser).
GRADABLE_O = {'numeric', 'abstain', 'nonnumeric', 'noanswer', 'unclosed', 'truncated', 'invalid'}


def cell(p, rule):
    """Map a parse result to a fresh81_pure.tag cell: status 'numeric' means gradable."""
    if rule == 'O':
        if p['status'] in GRADABLE_O:
            return dict(status='numeric', correct=p['correct'] if p['status'] == 'numeric' else 0)
        return dict(status=p['status'], correct=None)
    if rule == 'S':
        return dict(status=p['status'], correct=p['correct'] if p['status'] == 'numeric' else None)
    raise ValueError(rule)
