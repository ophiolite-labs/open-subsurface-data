# Per-record seconds from consecutive checked_at in a results directory, and per-shard sums for
# candidate N (H2 strategy). Usage: uv run python estimate.py <results dir> <verify step end, ISO>
import json,glob,hashlib
from datetime import datetime
from urllib.parse import urlsplit
from osd.records import load_records
recs=load_records()
import sys; S=sys.argv[1]
v={}
for p in glob.glob(S+"/*.json"):
    d=json.load(open(p)); v[d["record_id"]]=d
order=sorted(v, key=lambda r:v[r]["checked_at"])
end=datetime.fromisoformat(sys.argv[2])
t={}
for a,b in zip(order, order[1:]+[None]):
    ta=datetime.fromisoformat(v[a]["checked_at"]); tb=datetime.fromisoformat(v[b]["checked_at"]) if b else end
    t[a]=(tb-ta).total_seconds()
print("records timed",len(t),"sum min",sum(t.values())/60)
for r in sorted(t,key=t.get,reverse=True)[:12]: print(f"{t[r]:7.0f}s {r} {urlsplit(recs[r]['origin']['url']).hostname if r in recs else '?'}")
def host(r): return (urlsplit(recs[r]["origin"]["url"]).hostname or "").lower()
def shard(h,n): return int.from_bytes(hashlib.sha256(h.encode()).digest()[:8],"big")%n+1
med=sorted(t.values())[len(t)//2]
est={r:t.get(r,med) for r in recs}
hosts={}
for r in recs: hosts.setdefault(host(r),[]).append(r)
print("hosts",len(hosts),"max per host",max(len(x) for x in hosts.values()), "median s",med)
hs=sorted(hosts.items(), key=lambda kv:-sum(est[r] for r in kv[1]))[:6]
for h,rs in hs: print(f"  host {h}: {len(rs)} records {sum(est[r] for r in rs)/60:.1f} min")
for n in (4,6,8,10,12,16):
    tot=[0]*n; cnt=[0]*n
    for r in recs: s=shard(host(r),n)-1; tot[s]+=est[r]; cnt[s]+=1
    print(n, "max min %.1f"%(max(tot)/60), "counts",cnt, "mins",[round(x/60,1) for x in tot])
