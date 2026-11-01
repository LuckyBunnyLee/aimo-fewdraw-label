"""Offline stdlib builder for the AIMO report drafts (M1g, 22 Oct 2026).
Usage: python pair/aimo/report/build_report_html.py --source pair/aimo/report/REPORT-DRAFT-v0.1.source.md

Same measured-key discipline as pair/aimo/paper/build_paper_html.py, plus three report rules:
- An unresolved \\result{} key or any \\prereg{} slot is an error, not a red placeholder.
- Every paragraph, list item or table row that shows a measured number must carry a claim tag
  ([E-pre], [E], [E-post], [C] or [D]); otherwise the build fails.
- The manifest records a ledger of every literal number left in the text, and main-text word counts.
The key loading is copied from the paper builder; PAPER_BUILDER_SHA pins the version it was copied
from, so a change there stops this build until the copy is re-synced.
No models, subprocesses, network or sealed data.
"""
import argparse, base64, datetime, hashlib, html, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = HERE.parent / 'paper'
E = HERE.parent / 'evidence'
REPO = P.parent.parent.parent.resolve()
PAPER_BUILDER_SHA = '0702733cdd90c42d7cae78d46b4daca3b02f8a8ef5823946bba43941538a954e'
TAG = re.compile(r'\[(E-pre|E-post|E|C|D)\]')

ap = argparse.ArgumentParser()
ap.add_argument('--source', required=True, help='versioned REPORT-DRAFT-vX.Y.source.md')
args = ap.parse_args()
src_path = Path(args.source).resolve()
m = re.fullmatch(r'(REPORT-DRAFT-v\d+\.\d+[a-z]?)\.source\.md', src_path.name)
assert m, 'source must be named REPORT-DRAFT-vX.Y.source.md'
stem = m[1]
TRIM = tuple(map(int, re.match(r'REPORT-DRAFT-v(\d+)\.(\d+)', stem).groups())) >= (0, 2)  # v0.2 display rule, see scalar()
V07 = tuple(map(int, re.match(r'REPORT-DRAFT-v(\d+)\.(\d+)', stem).groups())) >= (0, 7)  # v0.7: citation metadata checked; appendices on a new page
V08 = tuple(map(int, re.match(r'REPORT-DRAFT-v(\d+)\.(\d+)', stem).groups())) >= (0, 8)  # v0.8: compact status line, page numbers, build ledger kept out of print
V09 = tuple(map(int, re.match(r'REPORT-DRAFT-v(\d+)\.(\d+)', stem).groups())) >= (0, 9)  # v0.9: fixed precision (no trim), _{sub} ^{sup}, $$ display lines
V09_DP = {'ready_diff_min': 1, 'ready_diff_max': 1, 'sh1_gpu_h': 1}  # publisher difficulty and a GPU-hour estimate, stored at 1 dp
targets = {s: src_path.with_name(stem + s) for s in ('.html', '.build.json')}
assert not any(p.exists() for p in targets.values()), 'Versioned outputs already exist; choose a fresh version.'
assert hashlib.sha256((P / 'build_paper_html.py').read_bytes()).hexdigest() == PAPER_BUILDER_SHA, \
    'paper builder changed; re-sync the copied key loading below'

inputs = {}; values = {}; provenance = {}


def read(path):
    path = Path(path).resolve()
    assert not {'test', 'sealed', 'sealed-test', 'sealed_test'} & {p.lower() for p in path.parts}
    data = path.read_bytes(); inputs[str(path)] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    return data


def js(path): return json.loads(read(path).decode('utf-8-sig'))


def shown(path):
    try: return Path(path).resolve().relative_to(REPO).as_posix()
    except ValueError: return 'external: ' + '/'.join(Path(path).parts[-2:])


def add(key, value, path, pointer, scope):
    assert key not in values, 'Conflicting measured key: ' + key
    values[key] = value
    provenance[key] = {'source': str(Path(path).resolve()), 'sha256': inputs[str(Path(path).resolve())]['sha256'],
                       'pointer': pointer, 'scope': scope}


# ---- copied from build_paper_html.py lines 33-67 (sha PAPER_BUILDER_SHA), unchanged in effect ----
nativepath = P / 'numbers/codex-native-t007.json'; native = js(nativepath)
for key, value in native['values'].items(): add(key, value, nativepath, '/values/' + key, native['tier'])
for path, sha in native['_manifest'].items():
    data = read(Path(path)); assert hashlib.sha256(data).hexdigest() == sha, 'Native source changed: ' + path
domainpath = P / 'numbers/domain-gen-t004.json'; domain = js(domainpath)
for key, value in domain.items():
    if key.startswith('dg_'): add(key, value, domainpath, '/' + key, 'Exploratory frozen domain summary')
rep_path = E / 'replication.json'; rep = js(rep_path)
for row, label in zip(rep['scorer_reruns'][:4], ('constant', 'constant_spurious', 'bow', 'r4')):
    ix = rep['scorer_reruns'].index(row)
    for metric, short in (('accuracy', 'acc'), ('balanced_accuracy', 'ba')):
        add('dev_' + short + '_' + label, row['scores'][metric], rep_path, f'/scorer_reruns/{ix}/scores/{metric}', 'DEV fixed-prediction scorer replay')
        add('dev_' + short + '_' + label + '_ci', row['ci95'][metric], rep_path, f'/scorer_reruns/{ix}/ci95/{metric}', 'Cluster bootstrap of fixed predictions')
sens_path = E / 'native-objective-text-sensitivity.json'; sens = js(sens_path)
for arm, label in (('surfaces4__default', 'surfaces4'), ('tfidf_wide__default', 'tfidf_wide')):
    assert arm in sens['arms'], arm
    for metric, short in (('accuracy', 'acc'), ('balanced_accuracy', 'ba')):
        add('dev_' + short + '_' + label, sens['arms'][arm]['metrics'][metric], sens_path, f'/arms/{arm}/metrics/{metric}', 'Exploratory sensitivity arm')
for label, raw in (('constant', 'constant'), ('surfaces', 'surfaces4'), ('pool', 'pool')):
    add('native_minus_' + label + '_ba_ci', sens['paired'][raw]['balanced_accuracy_ci95'], sens_path, f'/paired/{raw}/balanced_accuracy_ci95', 'Paired cluster bootstrap')
poolpath = E / 'pool-independent-rerun.txt'; pool = json.loads(read(poolpath).decode('utf-8-sig').splitlines()[1])
for metric, short in (('accuracy', 'acc'), ('balanced_accuracy', 'ba')):
    add('dev_' + short + '_pool', pool['scores'][metric], poolpath, 'line 2: /scores/' + metric, 'Exploratory independently replayed pooled text')
x1path = E / 'x1-independent-audit.json'; x1 = js(x1path)
for key, pointer, value in [('x1_pairs', '/sample_pairs', x1['sample_pairs']), ('x1_excluded', '/excluded', x1['excluded']), ('x1_included', '/included', x1['included']), ('x1_preserved', '/counts/PRESERVED', x1['counts']['PRESERVED']), ('x1_changed', '/counts/CHANGED', x1['counts']['CHANGED']), ('x1_no_solution', '/counts/UNANSWERABLE', x1['counts']['UNANSWERABLE']), ('x1_mixed', '/counts/MIXED', x1['counts']['MIXED']), ('x1_preserved_share', '/preserved_share', x1['preserved_share']), ('x1_preserved_ci', '/wilson95', x1['wilson95'])]:
    add(key, value, x1path, pointer, 'Operational dual-Claude outcomes; released strings; not semantic gold')
pilotpath = E / 'pilot-semantic-coverage-008.json'; pilot = js(pilotpath)
for key, pointer, value in [('pilot_k4_eligible', '/eligible_in_pool', pilot['eligible_in_pool']), ('pilot_k4_candidates', '/summary_k4/candidate_variants', pilot['summary_k4']['candidate_variants']), ('pilot_k4_provisional', '/summary_k4/provisional_verified_variants', pilot['summary_k4']['provisional_verified_variants']), ('pilot_k4_control_qualified', '/summary_k4/verified_with_controls_variants', pilot['summary_k4']['verified_with_controls_variants'])]:
    add(key, value, pilotpath, pointer, 'saved-screen snapshot; solver agreement not semantic gold')
NUMBER_FILES = [P / 'numbers' / n for n in ('w9-t019.json', 'w9-t019b.json', 'w9b-t030.json', 'w9b-t034.json', 'w9b-t035.json', 'w9b-t036b.json', 'w9b-t037.json', 'w9b-t038.json', 'w9b-t039.json', 'w9b-t040.json', 'w9b-t041b.json', 'w9b-t042.json', 'w9b-t043.json', 'w9b-t044.json')]
# ---- end of copied block; report-only numbers files follow ----
NUMBER_FILES += sorted((HERE / 'numbers').glob('*.json'))
for npath in NUMBER_FILES:
    nf = js(npath); tag = npath.stem
    for path, sha in nf['_manifest'].items():
        data = read(Path(path)); assert hashlib.sha256(data).hexdigest() == sha, tag + ' source changed: ' + path
    for key, value in nf['values'].items(): add(key, value, npath, '/values/' + key, tag + ': ' + nf['raw_pointers'][key])

source = read(src_path); text = source.decode('utf-8-sig'); source_sha = hashlib.sha256(source).hexdigest()
used = {}; unresolved = set(); prereg = set(); untagged = []


def scalar(key, v):
    """Display rule (report only): dev_acc/dev_ba as percentages, as in the paper; other floats at
    3 decimals, or 2 significant figures below 0.01. Stored values are unchanged.
    From v0.2 (TRIM), trailing zeros are dropped, so a value stored at 1 or 2 dp is not shown as if
    it had 3 (v0.1 showed 0.55 as "0.550" and 11.2 as "11.200")."""
    if isinstance(v, float):
        if key.startswith(('dev_acc_', 'dev_ba_')): return f'{100 * v:.1f}%'
        if key.startswith('native_minus_'): return f'{100 * v:+.1f} pp'
        if v != 0 and abs(v) < 0.01: return f'{v:.2g}'.replace('-', '−')
        if V09:  # v0.9: no trim; a key stored at k dp (its pointer says "; k dp") shows k decimals, anything else 3
            dp = re.search(r'[;,] (\d) dp', provenance[key]['scope'])
            dp = V09_DP.get(key, int(dp[1]) if dp else 3)  # V09_DP: non-probabilities whose pointer gives no precision
            return f'{v:.{dp}f}'.replace('-', '−')
        s = f'{v:.3f}'
        if TRIM: s = s.rstrip('0'); s = s + '0' if s.endswith('.') else s
        return s.replace('-', '−')
    return str(v).replace('-', '−') if isinstance(v, (int,)) else str(v)


def formatted(key, value):
    return ' to '.join(scalar(key, v) for v in value) if isinstance(value, list) else scalar(key, value)


def macro(m):
    kind, key = m.group(1), m.group(2)
    if kind == 'prereg': prereg.add(key); return 'NOT FROZEN: ' + html.escape(key)
    if key not in values: unresolved.add(key); return 'NOT MEASURED: ' + html.escape(key)
    used.setdefault(key, len(used) + 1)
    return ('<span class="measured" title="' + html.escape(shown(provenance[key]['source']) + ' ' + provenance[key]['pointer']) + '">'
            + html.escape(formatted(key, values[key])) + '</span>')


def inline(s):
    s = html.escape(s)
    codes = []  # code spans are literal text: a \result{} inside backticks is a syntax example, not a slot

    def stash(m):
        codes.append('<code>' + m.group(1) + '</code>'); return '\x00' + str(len(codes) - 1) + '\x00'
    s = re.sub(r'`([^`]+)`', stash, s)
    if V09:
        s = re.sub(r'_\{([^{}]+)\}', r'<sub>\1</sub>', s); s = re.sub(r'\^\{([^{}]+)\}', r'<sup>\1</sup>', s)
        s = re.sub('(\\w[̂̃])', r'<span class="acc">\1</span>', s)  # p̂, q̂: Georgia misplaces combining accents before a <sub>
    s = re.sub(r'\\(result|prereg)\{([^{}]+)\}', macro, s)
    s = re.sub(r'\x00(\d+)\x00', lambda m: codes[int(m.group(1))], s)
    s = re.sub(r'\*\*\[(E-pre|E-post|E|C|D)\]\*\*', r'<span class="tag t-\1">[\1]</span>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', s)
    return s


def tagcheck(raw, where):
    raw = re.sub(r'`[^`]+`', '', raw)
    if '\\result{' in raw and not TAG.search(raw): untagged.append(where + ': ' + raw[:90])


lines = text.splitlines(); body = []; paragraph = []; listkind = None; i = 0
para_start = [0]


def flush():
    if paragraph:
        raw = ' '.join(paragraph); tagcheck(raw, f'paragraph at line {para_start[0]}')
        body.append('<p>' + inline(raw) + '</p>'); paragraph.clear()


def close_list():
    global listkind
    if listkind: body.append('</' + listkind + '>'); listkind = None


while i < len(lines):
    line = lines[i]
    if not line.strip(): flush(); close_list(); i += 1; continue
    if line.startswith('|') and i + 1 < len(lines) and re.fullmatch(r'[| :\-]+', lines[i + 1]):
        flush(); close_list(); table = [line]; start = i + 1; i += 2
        while i < len(lines) and lines[i].startswith('|'): table.append(lines[i]); i += 1
        body.append('<table><thead><tr>' + ''.join('<th>' + inline(x.strip()) + '</th>' for x in table[0].strip('|').split('|')) + '</tr></thead><tbody>')
        for n, row in enumerate(table[1:]):
            tagcheck(row, f'table row at line {start + n + 2}')
            body.append('<tr>' + ''.join('<td>' + inline(x.strip()) + '</td>' for x in row.strip('|').split('|')) + '</tr>')
        body.append('</tbody></table>'); continue
    heading = re.match(r'^(#{1,6}) (.*)', line)
    if heading:
        flush(); close_list(); n = len(heading[1])
        if n == 1: i += 1; continue  # the title goes on the cover
        cls = ' class="newpage"' if V07 and n == 2 and heading[2].startswith('Appendix A') else ''
        body.append(f'<h{n}{cls}>' + inline(heading[2]) + f'</h{n}>'); i += 1; continue
    item = re.match(r'^(?:([-*]) |(\d+)\. )(.*)', line)
    if item:
        flush(); kind = 'ol' if item[2] else 'ul'
        if listkind != kind: close_list(); body.append('<' + kind + '>'); listkind = kind
        tagcheck(item[3], f'list item at line {i + 1}')
        body.append('<li>' + inline(item[3]) + '</li>'); i += 1; continue
    if line == '---': flush(); close_list(); body.append('<hr>'); i += 1; continue
    if V09 and line.startswith('$$ '):
        flush(); close_list(); body.append('<p class="eq">' + inline(line[3:].strip()) + '</p>'); i += 1; continue
    figure = re.fullmatch(r'!\[(.+)\]\(([^()]+\.png)\)', line)
    if figure:
        flush(); close_list(); png = read(REPO / figure[2])
        body.append('<figure><img alt="' + html.escape(figure[2]) + '" src="data:image/png;base64,' + base64.b64encode(png).decode()
                    + '"><figcaption>' + inline(figure[1]) + '</figcaption></figure>'); i += 1; continue
    if i == 2 and not paragraph: i += 1; continue  # the byline goes on the cover
    if not paragraph: para_start[0] = i + 1
    paragraph.append(line.strip()); i += 1
flush(); close_list()

errors = []
if unresolved: errors.append('unresolved result keys: ' + ', '.join(sorted(unresolved)))
if prereg: errors.append('prereg slots in a report: ' + ', '.join(sorted(prereg)))
if untagged: errors.append('measured numbers without a claim tag:\n  ' + '\n  '.join(untagged))
if errors: raise SystemExit('BUILD REFUSED\n' + '\n'.join(errors))

# Literal-number ledger and word counts (main text = Abstract up to References).
ledger = []
for n, line in enumerate(lines, 1):
    if line.startswith('!['): line = re.sub(r'\]\([^()]+\)$', ']', line)
    scrub = re.sub(r'\\result\{[^{}]+\}|`[^`]+`|arXiv \d{4}\.\d{4,5}', ' ', line)
    for tok in re.finditer(r'(?<![A-Za-z\d.\-])[-−]?\d[\d,.]*%?', scrub):
        ledger.append({'line': n, 'literal': tok.group(), 'context': scrub[max(0, tok.start() - 40):tok.end() + 30].strip()})
main_lo = next(n for n, l in enumerate(lines) if l.startswith('## Abstract'))
main_hi = next(n for n, l in enumerate(lines) if l.startswith('## References'))
main = lines[main_lo:main_hi]


def words(ls): return sum(len(re.sub(r'\\result\{[^{}]+\}', 'X', l).split()) for l in ls)


wc = {'main_prose': words([l for l in main if not l.startswith(('|', '![', '#'))]),
      'main_tables': words([l for l in main if l.startswith('|')]),
      'main_captions': words([l for l in main if l.startswith('![')]),
      'appendices': words(lines[main_hi:])}
tags = {t: len(re.findall(r'\*\*\[' + re.escape(t) + r'\]\*\*', text)) for t in ('E-pre', 'E', 'E-post', 'C', 'D')}

title = lines[0][2:]; byline = lines[2]
css = '''@page{size:A4;margin:18mm 17mm}body{font:10.5pt/1.42 Georgia,'Times New Roman',serif;color:#172d3c;max-width:950px;margin:auto}h1{font-size:21pt;line-height:1.2}h2{font-size:14pt;color:#126965;margin-top:20pt;break-after:avoid}h3{font-size:11.5pt;break-after:avoid}p,li{orphans:3;widows:3}table{border-collapse:collapse;width:100%;font:8.4pt/1.3 Arial,sans-serif;margin:10pt 0}th,td{border:1px solid #bdcdd5;padding:4px 5px;vertical-align:top;overflow-wrap:anywhere}th{background:#edf5f4}thead{display:table-header-group}tr{break-inside:avoid}code{font-size:8.2pt;overflow-wrap:anywhere}.tag{font:bold 7.5pt Arial,sans-serif;padding:0 2px;border-radius:2px;white-space:nowrap}td:last-child{width:9%}.t-E-pre{background:#e2efe9;color:#14523c}.t-E{background:#fff0d7;color:#7a4b06}.t-E-post{background:#fbe3dc;color:#8a2f17}.t-C{background:#e6e9f5;color:#2c3a78}.t-D{background:#eef0f1;color:#3d4b55}.banner{padding:12pt;background:#fff0d7;border-left:5px solid #b87815;font-family:Arial,sans-serif;font-size:9.5pt}.cover{padding-top:10pt}.provenance{break-before:page;font-size:8pt;overflow-wrap:anywhere}figure{break-inside:avoid;margin:10pt 0;text-align:center}figure img{max-width:100%;max-height:120mm}figcaption{font-size:8.8pt;text-align:left;margin-top:5pt}.newpage{break-before:page}'''
if V08: css += ('@page{@bottom-center{content:counter(page);font:8pt Arial,sans-serif;color:#52514e}}.tag{font-size:6.5pt;opacity:.8}'
                '.banner{padding:5pt 8pt;font-size:8.5pt}.banner p{margin:2pt 0}@media print{.provenance{display:none}}')
if V09: css += '.eq{text-align:center;margin:6pt 0;font-style:normal}sub,sup{font-size:70%;line-height:0}figure img{max-height:98mm}.acc{font-family:"Cambria Math",Cambria,serif}'
status = ('<div class="banner"><p><strong>Exploratory draft, not submitted.</strong> No result is confirmatory. Measured numbers are filled from sha-pinned files; '
          'tags: [E-pre] frozen and scored once, [E] screen, [E-post] post hoc, [C] constructed, [D] descriptive.</p></div>') if V08 else None
cover = ('<section class="cover"><p style="font-family:Arial;font-size:9pt">AIMO | REPORT DRAFT ' + stem.split('-v')[1] + '</p><h1>' + html.escape(title)
         + '</h1><p>' + html.escape(byline) + '</p><div class="banner"><strong>EXPLORATORY DRAFT — QA INCOMPLETE — ' + ('CITATION METADATA CHECKED ON ARXIV' if V07 else 'CITATIONS UNVERIFIED') + ' — NO SUBMISSION YET</strong>'
         '<p>No result in this report is confirmatory. Every measured number is filled from a sha-pinned numbers file, and every claim that rests on one carries a tag: '
         '[E-pre] frozen or preregistered and scored once; [E] exploratory screen; [E-post] post hoc; [C] constructed; [D] descriptive count.</p></div></section>')
if V08: cover = cover[:cover.index('<div class="banner">')] + status + '</section>'
source_ids = {}
for key in used: source_ids.setdefault(provenance[key]['source'], len(source_ids) + 1)
prov = ['<section class="provenance"><h2>Build provenance</h2><p>Source ' + html.escape(src_path.name) + ', SHA256 <code>' + source_sha
        + '</code>. ' + str(len(used)) + ' measured keys from ' + str(len(source_ids)) + ' numbers files; hover a number in the HTML for its source and pointer. '
        'The per-key table and the literal-number ledger are in ' + html.escape(stem) + '.build.json.</p><ol>']
for sp, ix in source_ids.items():
    prov.append('<li>' + html.escape(shown(sp)) + '; SHA256 <code>' + provenance[next(k for k in used if provenance[k]['source'] == sp)]['sha256'] + '</code></li>')
prov.append('</ol></section>')
output = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>AIMO report draft ' + stem + '</title><style>' + css
          + '</style></head><body>' + cover + '\n'.join(body + prov) + '</body></html>')
manifest = dict(mode='Exploratory report draft; not QA, not readiness', stem=stem, built_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                source=shown(src_path), source_sha256=source_sha, html_sha256=hashlib.sha256(output.encode()).hexdigest(),
                builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), paper_builder_sha256=PAPER_BUILDER_SHA,
                word_counts=wc, claim_tags=tags, inputs=inputs,
                measured_keys={k: dict(index=used[k], value=values[k], shown=formatted(k, values[k]), **provenance[k]) for k in used},
                literal_numbers=ledger,
                limitations=[('Citation metadata (title, first author, year, arXiv id) checked against arXiv; characterisations checked against abstracts only' if V07 else 'Citations unverified (D6)'), 'HTML-to-PDF route, not the NeurIPS template (D5)', 'Literal numbers are listed for review, not verified'])
with targets['.html'].open('xb') as f: f.write(output.encode('utf-8'))
with targets['.build.json'].open('x', encoding='utf-8') as f: json.dump(manifest, f, indent=1, ensure_ascii=False)
print(json.dumps({'outputs': {k: str(v) for k, v in targets.items()}, 'measured_keys': len(used), 'word_counts': wc,
                  'claim_tags': tags, 'literal_numbers': len(ledger), 'source_sha256': source_sha}, indent=1))
