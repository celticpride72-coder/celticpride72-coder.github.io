#!/usr/bin/env python3
"""Merge a rolling 7-day window (delta JSON) into a history ledger (data/<slug>.json.gz).

Usage: merge_ledger.py <slug> <delta.json>
delta.json = {"header":[...], "rows":[[...]...], "asOf":"YYYY-MM-DD"}  (same column names as the ledger; extra columns ignored)

Rules:
  * windowCol set  -> every ledger row whose windowCol date lies inside [min,max] of the delta's windowCol
                      is REMOVED, then all delta rows are appended (so cancellations/changes inside the window are caught).
  * windowCol null -> upsert by key columns only.
  * Key de-dupe (last wins) applies only in upsert mode; window mode keeps legitimate repeat rows.
Prints a one-line summary; exits non-zero on implausible input (empty delta, header mismatch).
"""
import sys, json, gzip, datetime, os

def serial_to_iso(v):
    if isinstance(v,(int,float)):
        d=datetime.date(1899,12,30)+datetime.timedelta(days=round(v)); return d.isoformat()
    return None

def main():
    slug, delta_path = sys.argv[1], sys.argv[2]
    root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lp=os.path.join(root,"data",slug+".json.gz")
    L=json.load(gzip.open(lp,"rt",encoding="utf-8"))
    D=json.load(open(delta_path,encoding="utf-8"))
    if not D.get("rows"): sys.exit("ABORT: delta has no rows")
    hdr=L["header"]; dh=D["header"]
    missing=[h for h in hdr if h not in dh]
    if missing: sys.exit("ABORT: delta missing columns: "+", ".join(missing[:8]))
    pos=[dh.index(h) for h in hdr]
    drows=[[r[i] if i<len(r) else None for i in pos] for r in D["rows"]]
    keyi=[hdr.index(k) for k in L["key"]]
    key=lambda r: "|".join("" if r[i] is None else str(r[i]) for i in keyi)
    before=len(L["rows"]); removed=0
    if L.get("windowCol"):
        wi=hdr.index(L["windowCol"])
        ds=sorted(x for x in (r[wi] for r in drows) if isinstance(x,(int,float)))
        if not ds: sys.exit("ABORT: no window dates in delta")
        lo,hi=ds[0],ds[-1]
        if hi-lo>31: sys.exit("ABORT: delta window spans %d days — not a 7-day file?"%(hi-lo))
        keep=[r for r in L["rows"] if not (isinstance(r[wi],(int,float)) and lo<=r[wi]<=hi)]
        removed=before-len(keep); L["rows"]=keep+drows
        win="%s..%s"%(serial_to_iso(lo),serial_to_iso(hi))
    else:
        L["rows"]=L["rows"]+drows; win="key-upsert"
    if not L.get("windowCol"):
        seen={}
        for r in L["rows"]: seen[key(r)]=r
        L["rows"]=list(seen.values())
    L["updated"]=D.get("asOf") or datetime.date.today().isoformat()
    L["lastMerge"]={"ran":datetime.datetime.now().isoformat(timespec="seconds"),"window":win,"deltaRows":len(drows),"removed":removed}
    with gzip.open(lp,"wt",encoding="utf-8") as f: json.dump(L,f,separators=(",",":"))
    print("%s: window=%s delta=%d removed=%d before=%d after=%d"%(slug,win,len(drows),removed,before,len(L["rows"])))

if __name__=="__main__": main()
