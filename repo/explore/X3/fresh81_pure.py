"""Pure grading/statistics helpers: no file writes or legacy imports at import."""
import json,hashlib,re
from fractions import Fraction
import numpy as np
from scipy.stats import rankdata
METHODS=['interaction-A4','point-K','RF-length-source|alltrain','LR-text|alltrain'];BASE='point-K'
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def parse(raw,finish,error,truth):
 status='invalid';answer=None;correct=None
 if finish in ['length','max_tokens','context_limit']:status='truncated'
 elif error is not None:status='error'
 elif finish in ['stop','eos']:
  lines=raw.rsplit('</think>',1)[-1].strip().splitlines();m=re.fullmatch(r'ANSWER:\s*(.*?)\s*',lines[-1]) if lines else None
  if m:
   try:answer=Fraction(m[1].replace(',',''));status='numeric';correct=int(answer==Fraction(str(truth)))
   except (ValueError,ZeroDivisionError):status='abstain' if m[1]=='NaN' else 'invalid'
 return dict(status=status,answer=str(answer) if answer is not None else None,correct=correct)
def envelope(e):
 r=e['record'];assert e['record_sha256']==sha(canon(r));assert r['raw_sha256']==sha(r['raw'].encode());assert r['output_tokens']==len(r['token_ids']);return r
def sides(cells):
 out={s:{} for s in ['A','B']}
 for f,v in cells.items():
  vv=sorted(v,key=lambda x:sha(('X3-repro-v1|'+x['key']).encode()));assert len(vv)==4;out['A'][f]=vv[::2];out['B'][f]=vv[1::2]
 return out
def tag(cells,n):
 assert set(cells)=={'base','surface_gs','surface_dlm'} and all(len(v)==n for v in cells.values())
 if any(r['status']!='numeric' for v in cells.values() for r in v):return 'UNUSABLE'
 c={f:sum(r['correct'] for r in v) for f,v in cells.items()};return 'FLOOR' if c['base']==0 else 'NR' if min(c[f] for f in c if f!='base')<c['base'] else 'R'
def auc(y,p):
 y=np.asarray(y,dtype=int);n=int(y.sum());m=len(y)-n
 return float((rankdata(np.round(p,12))[y==1].sum()-n*(n+1)/2)/(n*m)) if n and m else None
def metrics(y,p):
 y=np.asarray(y);p=np.asarray(p);q=np.clip(p,1e-12,1-1e-12)
 return dict(AUC=auc(y,p),Brier=float(np.mean((p-y)**2)) if len(y) else None,logloss=float(np.mean(-y*np.log(q)-(1-y)*np.log1p(-q))) if len(y) else None,accuracy05=float(np.mean((p>=.5)==y)) if len(y) else None)
def pair_stats(rows,seed=8101945):
 y=np.array([r['label']=='NR' for r in rows],dtype=int);scores={k:np.array([r['scores'][k] for r in rows]) for k in METHODS};actual={k:metrics(y,p) for k,p in scores.items()};groups=np.array([r['template'] for r in rows]);ug=sorted(set(groups));rng=np.random.default_rng(seed);boot={};rawboot={}
 for mode in ['original','template']:
  vals=[];auc_count=0
  if len(rows):
   for _ in range(2000):
    ix=rng.choice(len(rows),len(rows),replace=True) if mode=='original' else np.concatenate([np.where(groups==g)[0] for g in rng.choice(ug,len(ug),replace=True)]);yy=y[ix];mb=metrics(yy,scores[BASE][ix]);v={}
    for k,p in scores.items():
     mm=metrics(yy,p[ix]);v[k]=dict(AUCgain=None if mm['AUC'] is None else mm['AUC']-mb['AUC'],Briergain=mb['Brier']-mm['Brier'])
    auc_count+=v[BASE]['AUCgain'] is not None;vals.append(v)
  boot[mode]=dict(planned=2000,completed=len(vals),AUC_nondegenerate=auc_count,interval95={k:{measure:np.quantile([v[k][measure] for v in vals if v[k][measure] is not None],[.025,.975]).tolist() if any(v[k][measure] is not None for v in vals) else None for measure in ['AUCgain','Briergain']} for k in METHODS});rawboot[mode]=vals
 nullA=[];nullB=[];null={}
 if len(rows) and len(set(y))==2:
  lengths=np.array([r['words'] for r in rows]);bands=np.digitize(lengths,np.quantile(lengths,[.25,.5,.75]),right=True)
  for _ in range(2000):
   yy=y.copy()
   for b in range(4):ix=np.where(bands==b)[0];yy[ix]=rng.permutation(yy[ix])
   base=auc(yy,scores[BASE]);nullA.append(max([0.]+[auc(yy,p)-base for p in scores.values()]))
  obs=max([0.]+[actual[k]['AUC']-actual[BASE]['AUC'] for k in METHODS]);null['AUC_lengthquartile']=dict(completed=2000,observed_max_gain=obs,upper_tail=(1+sum(v>=obs-1e-14 for v in nullA))/2001,assumption='Original exchangeability within length quartile; not template-valid/history-FWE')
 else:null['AUC_lengthquartile']=dict(completed=0,reason='No binary rows or one observed class')
 if len(rows):
  diffs=np.array([[np.mean(((scores[BASE]-y)**2-(scores[k]-y)**2)[groups==g]) for g in ug] for k in METHODS]);obs=max(0.,float(diffs.mean(1).max()))
  for _ in range(2000):nullB.append(max(0.,float((diffs*rng.choice([-1,1],len(ug))).mean(1).max())))
  null['Brier_cluster_symmetry']=dict(completed=2000,observed_macro_group_max_gain=obs,upper_tail=(1+sum(v>=obs-1e-14 for v in nullB))/2001,assumption='Symmetric independent group loss differences, equal-group mean; not original-weighted risk or history-FWE')
 else:null['Brier_cluster_symmetry']=dict(completed=0,reason='No binary rows')
 return dict(binary=len(rows),NR=int(y.sum()),R=int(len(y)-y.sum()),templates=len(ug),metrics=actual,bootstrap=boot,null=null),rawboot,dict(lengthquartile=nullA,cluster_symmetry=nullB)
