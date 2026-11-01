"""BX score once after final EXIT. No GPU or generation. Refuses changed freeze/inputs."""
import hashlib,json,pathlib,sys,time,fcntl
R=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(R))
import wave_core as wc
import fresh81_pure as f
from analysis_random100 import analyse
def run(source,reviewed):
    source=pathlib.Path(source)
    assert wc.file_sha(R/'FREEZE.sha256')==reviewed
    for line in (R/'FREEZE.sha256').read_text().splitlines():
        h,n=line.split(None,1);assert wc.file_sha(R/n.strip())==h,n
    lock=(source/'OWNED.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for n in ('MANIFEST.json','REQUESTS.json','TRUTHS.json'):
        assert wc.file_sha(source/n)==wc.file_sha(R/n),n
    assert wc.read(source/'ADMISSION.json')['freeze_sha256']==reviewed
    m=wc.read(R/'MANIFEST.json');assert wc.read(source/'FINAL-FOR-SCORING.json')['no_more_generation'] is True
    st=wc.scan(source,m);assert not st['unsealed'];waves=st['complete'][:25]
    req=wc.read(R/'REQUESTS.json');truth=wc.read(R/'TRUTHS.json');by=wc.by_wave(req)
    out=R/'out';out.mkdir(exist_ok=True)
    with (out/'SCORE-ONCE-STARTED.json').open('x') as g:json.dump(dict(time=time.time(),source=str(source)),g)
    where={int(p.stem.rsplit('-',1)[1]):p for p in source.glob('block-*/WAVE-COMPLETE-*.json')};draws=[]
    for w in waves:
        cp=where[w]; records=wc.read(cp)['records'];assert set(records)=={q['identity_sha256'] for q in by[w]}
        for q in by[w]:
            k=q['identity_sha256'];r=f.envelope(wc.read(cp.parent/'records'/(k+'.json')))
            assert r['identity']==q['identity'] and r['identity_sha256']==k and r['seed']==q['seed'] and r['wave']==w
            assert r['request_sha256']==wc.sha(wc.canon(q)) and records[k]==wc.sha(wc.canon(r))
            v=f.parse(r['raw'],r['finish_reason'],r['error'],truth[k])
            draws.append(dict(pid=q['identity']['problem_id'],family=q['identity']['family'],wave=w,
                correct=int(v['correct'] or 0),status=v['status'],finish=r['finish_reason']))
    result=analyse(draws,f.tag) if waves else dict(reading='not measured under the planned exposure',waves=0)
    result.update(state=st,freeze_sha256=reviewed)
    text=json.dumps(result,indent=2,allow_nan=False)
    with (out/'RESULT.json').open('x') as g:g.write(text)
    print(result['reading'])
if __name__=='__main__':run(sys.argv[1],sys.argv[2])
