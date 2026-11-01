"""Box CPU only: conditional normal-approximation power, NOT an empirical result."""
import json,math,pathlib
from statistics import NormalDist
N=NormalDist()
def calculate():
    rows=[]
    # Marginal variance adds unknown between-problem SD of true contrasts.
    for waves in (20,25):
        for accuracy in (.5,.8,.95):
            for tau in (0,.05,.10,.20):
                se=math.sqrt((1.5*accuracy*(1-accuracy)/(4*waves)+tau*tau)/100)
                mde=(1.959963984540054+.8416212335729143)*se
                for effect in (0,.02,.04,.06):
                    power=N.cdf(-1.959963984540054-effect/se)+1-N.cdf(1.959963984540054-effect/se)
                    rows.append(dict(waves=waves,accuracy=accuracy,tau=tau,effect=effect,se=se,ci_halfwidth=1.959963984540054*se,mde80=mde,power=power))
    return dict(kind='conditional analytic planning calculation',unit='original',n=100,rows=rows,
      assumptions=['independent originals and conditional Bernoulli draws','equal marginal family accuracy for variance only',
      'tau is unknown between-original SD; not estimated from this run','normal CI proxy, not guaranteed bootstrap coverage',
      'no allowance for correlated requests, runtime censoring, calibration or numeric eligibility'],
      reliability='No promised kappa power: prevalence and >=5-binary-wave eligibility unknown; descriptive secondary.')
if __name__=='__main__':
    with pathlib.Path('POWER.json').open('x') as f:json.dump(calculate(),f,indent=2,allow_nan=False)
