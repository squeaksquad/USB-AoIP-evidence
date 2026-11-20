import json,glob,re,os,sys,datetime as dt,collections
def T(s): return dt.datetime.fromisoformat(s.replace('Z','+00:00'))
ev=[]  # (time, kind, info)
rate=None; preset=None; start=None
primes=[]
for line in open(sys.argv[1]):
    ts=T(line.split()[0]); 
    if 'START usb16x16' in line:
        rate=int(re.search(r'rate=(\d+)',line).group(1)); preset='direct'; start=ts
    elif 'DSP loaded' in line: preset='preset'
    elif 'USBLINK' in line:
        f=dict(kv.split('=') for kv in line.split() if '=' in kv)
        primes.append((ts,rate,preset,int(f['tx_prime_found']),int(f['tx_prime_dropped']),int(f['tx_unanchored']),int(f['tx_drained']),start))
opens=[]
for f in glob.glob('outputs/latency/*2026111[89]T*.json')+glob.glob('outputs/latency/*20261120T*.json')+glob.glob('outputs/latency/*2026111[89]T*-api/readiness-probe-*.json')+glob.glob('outputs/latency/*20261120T*-api/readiness-probe-*.json'):
    try: d=json.load(open(f))
    except Exception: continue
    c=d.get('correlation'); cfg=d.get('configuration',{})
    if not c or 'capturedAt' not in d: continue
    p=c.get('perImpulseDelaySamples') or []
    if not p: continue
    m=max(set(p),key=p.count)
    n=cfg.get('impulseCount',len(p)); dur=cfg.get('leadInMilliseconds',500)/1000+n*cfg.get('intervalMilliseconds',250)/1000
    end=T(d['capturedAt']); opens.append((end-dt.timedelta(seconds=dur+1.5),end,m,len(p),f.replace('outputs/latency/','')[:58]))
opens.sort()
rows=[]
for o in opens:
    # prime nearest the open's start (within 4 s)
    best=min(primes,key=lambda p:abs((p[0]-o[0]).total_seconds()))
    if abs((best[0]-o[0]).total_seconds())>4: continue
    rows.append((best[1],best[2],best[3],o[2],best[6],((best[0]-best[7]).total_seconds() if best[7] else -1),o[4],best[0]))
tab=collections.defaultdict(collections.Counter)
for r in rows: tab[(r[0],r[1])][(r[2],r[3])]+=1
for k in sorted(tab,key=str):
    print(k)
    for (found,lag),n in sorted(tab[k].items()): print(f"   found={found:4d} lag={lag:5d} x{n}")
if len(sys.argv)>2:
    for r in rows:
        if r[0]==96000: print(r[7].strftime('%d %H:%M:%S'),r[1],'found',r[2],'lag',r[3],'drained',r[4],'t',int(r[5]),r[6])
