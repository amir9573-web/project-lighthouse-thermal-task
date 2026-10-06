import csv, json, argparse
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from scipy.optimize import least_squares

NAMES = ['core-capacity','case-capacity','coupling-base','coupling-fan','loss-base','loss-fan']
SCALE = np.array([500.,900.,4.,2.,2.,3.])

def load(data):
    spec=json.loads((data/'protocol.json').read_text())
    cal=np.genfromtxt(data/'calibration.csv',delimiter=',',names=True)
    calibration={}
    for ch in ['core','case']:
        a=np.column_stack([cal['reference_C'],np.ones(len(cal))])
        calibration[ch]=np.linalg.lstsq(a,cal[ch+'_raw'],rcond=None)[0]
    runs={}
    for name in spec['training_runs']+spec['validation_runs']:
        x=np.genfromtxt(data/(name+'.csv'),delimiter=',',names=True)
        y=np.column_stack([(x[c+'_raw']-calibration[c][1])/calibration[c][0] for c in ['core','case']])
        valid=np.isfinite(y)&np.column_stack([x['core_valid']==1,x['case_valid']==1])
        runs[name]=(x,y,valid)
    cycle=np.genfromtxt(data/'proposed-cycle.csv',delimiter=',',names=True)
    return spec,calibration,runs,cycle

def forward(p,delay,x,initial,power_scale=1.):
    c1,c2,g0,gf,h0,hf=p
    states=np.empty((len(x),2)); states[0]=initial
    cache={}
    for i in range(len(x)-1):
        f=x['fan'][i]; dt=x['time_s'][i+1]-x['time_s'][i]
        key=(float(f),float(dt))
        if key not in cache:
            g=g0+gf*f; h=h0+hf*f
            A=np.array([[-g/c1,g/c1],[g/c2,-(g+h)/c2]])
            E=expm(A*dt)
            K=np.linalg.solve(A,E-np.eye(2))
            cache[key]=(E,K,h)
        E,K,h=cache[key]
        q=0. if i<delay else x['power_W'][i-delay]*power_scale
        b=np.array([q/c1,h*x['ambient_C'][i]/c2])
        states[i+1]=E@states[i]+K@b
    return states

def fit(spec,runs,names,delay):
    def residual(z):
        p=np.exp(z)*SCALE
        return np.concatenate([((forward(p,delay,runs[n][0],spec['initial_C'][n])-runs[n][1])/spec['noise_C'])[runs[n][2]] for n in names])
    best=None
    for multiplier in [1.,1.7]:
        r=least_squares(residual,np.log(np.full(6,multiplier)),bounds=(np.log(.1),np.log(10.)),ftol=1e-10,xtol=1e-10,gtol=1e-8,max_nfev=200)
        if not r.success: raise RuntimeError(r.message)
        if best is None or np.dot(r.fun,r.fun)<np.dot(best.fun,best.fun): best=r
    p=np.exp(best.x)*SCALE
    covariance=np.diag(p)@np.linalg.inv(best.jac.T@best.jac)@np.diag(p)
    return p,float(best.fun@best.fun),covariance

def solve(data,out):
    spec,cal,runs,cycle=load(data)
    profiles=[fit(spec,runs,spec['training_runs'],d) for d in spec['delay_samples']]
    idx=int(np.argmin([v[1] for v in profiles])); delay=spec['delay_samples'][idx]
    p,sse,cov=profiles[idx]
    deletion={}
    for omitted in spec['training_runs']:
        pp,ss,_=fit(spec,runs,[n for n in spec['training_runs'] if n!=omitted],delay)
        deletion[omitted]={'parameters':pp.tolist(),'weighted_sse':ss}
    rmses={}
    for n in spec['validation_runs']:
        e=forward(p,delay,runs[n][0],spec['initial_C'][n])-runs[n][1]
        rmses[n]=[float(np.sqrt(np.mean(e[:,j][runs[n][2][:,j]]**2))) for j in range(2)]
    ensemble=[p]+[np.array(v['parameters']) for v in deletion.values()]
    full=np.stack([forward(pp,delay,cycle,spec['cycle_initial_C']) for pp in ensemble])
    # The cycle ambient is constant and both bodies begin at ambient, so excess is linear in power.
    rise=float(np.max(full[:,:,0])-spec['cycle_initial_C'][0])
    cap=min(1.,(spec['core_limit_C']-spec['cycle_initial_C'][0])/rise)
    result={'parameter_order':NAMES,'calibration':{k:v.tolist() for k,v in cal.items()},'parameters':p.tolist(),'delay_samples':delay,'delay_profile':{str(d):v[1] for d,v in zip(spec['delay_samples'],profiles)},'weighted_sse':sse,'covariance':cov.tolist(),'leave_one_run_out':deletion,'validation_rmse_C':rmses,'power_scale':cap,'unscaled_core_peak_C':float(np.max(full[0,:,0])),'envelope_core_peak_C':float(np.max(full[:,:,0]))}
    out.mkdir(parents=True,exist_ok=True)
    (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    scaled=np.stack([forward(pp,delay,cycle,spec['cycle_initial_C'],cap) for pp in ensemble])
    with (out/'forecast.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['time_s','core_C','case_C','core_envelope_C','case_envelope_C'])
        for i,t in enumerate(cycle['time_s']): w.writerow([t,*scaled[0,i],*scaled[:,i,:].max(axis=0)])
    print('Reference solution completed; delay =',delay,'samples; power scale =',round(cap,6))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--data',type=Path,default=Path('/app/data'));a.add_argument('--out',type=Path,default=Path('/app/output'));args=a.parse_args();solve(args.data,args.out)
