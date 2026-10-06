# This verifier imports no reference-solution code. It uses RK4 transition
# polynomials and fits physical parameters rather than logarithms.
import argparse,csv,json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

ORDER=['core-capacity','case-capacity','coupling-base','coupling-fan','loss-base','loss-fan']
UNITS=np.array([500.,900.,4.,2.,2.,3.])

def read_inputs(folder):
    s=json.loads((folder/'protocol.json').read_text())
    a=np.genfromtxt(folder/'calibration.csv',names=True,delimiter=',')
    X=np.stack((a['reference_C'],np.ones(a.size)),axis=1)
    gains={ch:np.linalg.solve(X.T@X,X.T@a[ch+'_raw']) for ch in ('core','case')}
    records={}
    for name in s['training_runs']+s['validation_runs']:
        v=np.genfromtxt(folder/(name+'.csv'),names=True,delimiter=',')
        measured=np.stack([(v[c+'_raw']-gains[c][1])/gains[c][0] for c in ('core','case')],axis=1)
        masks=np.stack([v[c+'_valid']==1 for c in ('core','case')],axis=1)&np.isfinite(measured)
        records[name]=(v,measured,masks)
    return s,gains,records,np.genfromtxt(folder/'proposed-cycle.csv',names=True,delimiter=',')

def integrate(theta,lag,record,start,factor=1.):
    C,D,G,F,H,J=theta
    v=np.empty((len(record),2));v[0]=start
    operators={}
    for k in range(len(record)-1):
        fan=record['fan'][k]; interval=record['time_s'][k+1]-record['time_s'][k]
        key=(float(fan),float(interval))
        if key not in operators:
            g=G+F*fan;h=H+J*fan
            mat=np.array([[-g/C,g/C],[g/D,-(g+h)/D]])
            dt=interval/20
            B=dt*mat;B2=B@B;B3=B2@B;B4=B3@B
            R=np.eye(2)+B+B2/2+B3/6+B4/24
            S=dt*(np.eye(2)+B/2+B2/6+B3/24)
            E=np.eye(2);K=np.zeros((2,2))
            for _ in range(20):K=R@K+S;E=R@E
            operators[key]=(E,K,h)
        E,K,h=operators[key]
        heater=0 if k<lag else factor*record['power_W'][k-lag]
        v[k+1]=E@v[k]+K@np.array([heater/C,h*record['ambient_C'][k]/D])
    return v

def recompute(folder):
    spec,gains,records,cycle=read_inputs(folder)
    def estimate(names,lag,need_cov=False):
        def errors(z):
            return np.hstack([((integrate(z*UNITS,lag,records[n][0],spec['initial_C'][n])-records[n][1])/spec['noise_C'])[records[n][2]] for n in names])
        options=[]
        for start in (.8,1.4):
            fit=least_squares(errors,np.full(6,start),bounds=(.1,10.),max_nfev=250,ftol=1e-10,xtol=1e-10,gtol=1e-8)
            if not fit.success:raise RuntimeError('Independent fit did not converge')
            options.append(fit)
        fit=min(options,key=lambda r:r.fun@r.fun)
        theta=fit.x*UNITS
        covariance=None
        if need_cov:
            eps=1e-5
            basis=np.eye(6)*eps
            jac=np.stack([(errors(fit.x+step)-errors(fit.x-step))/(2*eps) for step in basis],axis=1)
            covariance=np.diag(UNITS)@np.linalg.inv(jac.T@jac)@np.diag(UNITS)
        return theta,float(fit.fun@fit.fun),covariance
    profile={str(d):estimate(spec['training_runs'],d) for d in spec['delay_samples']}
    lag=int(min(profile,key=lambda k:profile[k][1]))
    theta,sse,cov=estimate(spec['training_runs'],lag,True)
    deletions={}
    for omit in spec['training_runs']:
        p,q,_=estimate([n for n in spec['training_runs'] if n!=omit],lag)
        deletions[omit]={'parameters':p.tolist(),'weighted_sse':q}
    rmses={}
    for n in spec['validation_runs']:
        residual=integrate(theta,lag,records[n][0],spec['initial_C'][n])-records[n][1]
        rmses[n]=[float(np.sqrt(np.mean(residual[:,j][records[n][2][:,j]]**2))) for j in (0,1)]
    members=[theta]+[np.array(d['parameters']) for d in deletions.values()]
    nominal=np.array([integrate(p,lag,cycle,spec['cycle_initial_C']) for p in members])
    # Independent bisection of the constrained operating envelope.
    left,right=0.,1.
    if nominal[:,:,0].max()<=spec['core_limit_C']:left=1.
    else:
        for _ in range(35):
            middle=(left+right)/2
            peak=max(integrate(p,lag,cycle,spec['cycle_initial_C'],middle)[:,0].max() for p in members)
            if peak<=spec['core_limit_C']:left=middle
            else:right=middle
    safe=left
    scaled=np.array([integrate(p,lag,cycle,spec['cycle_initial_C'],safe) for p in members])
    result={'parameter_order':ORDER,'calibration':{c:v.tolist() for c,v in gains.items()},'parameters':theta.tolist(),'delay_samples':lag,'delay_profile':{k:v[1] for k,v in profile.items()},'weighted_sse':sse,'covariance':cov.tolist(),'leave_one_run_out':deletions,'validation_rmse_C':rmses,'power_scale':safe,'unscaled_core_peak_C':float(nominal[0,:,0].max()),'envelope_core_peak_C':float(nominal[:,:,0].max())}
    trajectory=np.column_stack([cycle['time_s'],scaled[0],scaled.max(axis=0)])
    return result,trajectory

def compare(actual,expected,path='result'):
    if isinstance(expected,dict):
        assert isinstance(actual,dict) and set(actual)==set(expected),path+' keys'
        for k in expected:compare(actual[k],expected[k],path+'.'+k)
    elif isinstance(expected,list) and expected and isinstance(expected[0],str):
        assert actual==expected,path
    elif isinstance(expected,(list,float,int)):
        a=np.asarray(actual,dtype=float);e=np.asarray(expected,dtype=float)
        assert a.shape==e.shape and np.isfinite(a).all(),path+' shape or nonfinite value'
        if path.endswith('covariance'):
            assert np.max(np.abs(a-a.T))<1e-6,path+' symmetry'
            assert np.linalg.eigvalsh(a).min()>0,path+' positive definiteness'
            denom=np.sqrt(np.outer(np.diag(e),np.diag(e)))
            assert np.max(np.abs(a-e)/denom)<.015,path+' information matrix'
        elif path.endswith('delay_samples'):assert actual==expected,path
        else:assert np.allclose(a,e,rtol=.003,atol=.003),path+' scientific mismatch'
    else:assert actual==expected,path

def grade(data,output,reward):
    reward.parent.mkdir(parents=True,exist_ok=True);reward.write_text('0.0\n')
    try:
        actual=json.loads((output/'result.json').read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
        forecast=np.genfromtxt(output/'forecast.csv',names=True,delimiter=',')
        assert forecast.dtype.names==('time_s','core_C','case_C','core_envelope_C','case_envelope_C'),'forecast columns'
        expected,trajectory=recompute(data)
        compare(actual,expected)
        observed=np.column_stack([forecast[n] for n in forecast.dtype.names])
        assert observed.shape==trajectory.shape and np.isfinite(observed).all(),'forecast shape'
        assert np.array_equal(observed[:,0],trajectory[:,0]),'forecast time grid'
        assert np.allclose(observed[:,1:],trajectory[:,1:],rtol=0,atol=.012),'forecast mismatch'
        reward.write_text('1.0\n');print('PASS: independent scientific recomputation; reward = 1.000')
        return 0
    except Exception as error:
        print('FAIL:',type(error).__name__,str(error),'; reward = 0.000')
        return 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data',type=Path,default=Path('/app/data'));parser.add_argument('--output',type=Path,default=Path('/app/output'));parser.add_argument('--reward',type=Path,default=Path('/logs/verifier/reward.txt'));a=parser.parse_args();sys.exit(grade(a.data,a.output,a.reward))
