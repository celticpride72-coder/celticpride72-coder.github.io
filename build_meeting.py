import re,json,sys,datetime
SRC=sys.argv[1] if len(sys.argv)>1 else '.'
OUT=sys.argv[2] if len(sys.argv)>2 else 'service_tech_meeting.html'

def balanced(s,start):
    i=s.find('{',start);d=0
    for j in range(i,len(s)):
        if s[j]=='{':d+=1
        elif s[j]=='}':
            d-=1
            if d==0:return s[i:j+1]
    return '{}'
def striptags(x):
    x=re.sub(r'<span class="sm">',' — ',x)
    return re.sub(r'<[^>]*>','',x).strip()

# ---- REVENUE rolling windows ----
rv=open(f'{SRC}/revenue_dashboard.html',encoding='utf-8').read()
DATA=json.loads(balanced(rv,rv.find('const DATA')))
tr=DATA['trailing']
def rollcard(k,lab):
    o=tr[k];a=o['actual'];g=o.get('goal');ly=o.get('ly')
    gp=(a/g*100) if g else None; yoy=((a-ly)/ly*100) if ly else None
    gtxt=f'{gp:.0f}% of goal' if gp is not None else '—'
    gcls='g' if (gp is not None and gp>=100) else ('a' if (gp is not None and gp>=95) else ('r' if gp is not None else 'n'))
    ycls='up' if (yoy is not None and yoy>=0) else 'down'
    ytxt=(f'{"▲" if yoy>=0 else "▼"} {abs(yoy):.1f}% YoY') if yoy is not None else '—'
    return f'<div class="mcard"><div class="ml">{lab}</div><div class="mv">${a:,.0f}</div><div class="mc"><span class="pill {gcls}">{gtxt}</span><span class="pill {ycls}">{ytxt}</span></div></div>'
rev_html=''.join(rollcard(k,l) for k,l in [('d30','Last 30 days'),('d60','Last 60 days'),('d90','Last 90 days'),('d365','Last 365 days')])

# ---- 4DX WIG 1-3 ----
fx=open(f'{SRC}/4dx_dashboard_2026.html',encoding='utf-8').read()
segs=re.split(r'<!-- WIG \d+ -->',fx)
wig_html=''
CMAP={'g':'g','a':'a','r':'r','p-g':'g','p-a':'a','p-r':'r','p-n':'n'}
for b in segs[1:4]:
    title=re.search(r'<h2>(.*?)</h2>',b).group(1)
    pill=re.search(r'<span class="pill (p-\w)">(.*?)</span>',b)
    pcls=CMAP.get(pill.group(1),'n'); ptxt=pill.group(2)
    base=striptags(re.search(r'<div class="base">(.*?)</div>',b,re.S).group(1))
    rows=re.findall(r'<td class="k">(.*?)</td>\s*<td class="v">(.*?)</td>\s*<td class="([gar])">(.*?)</td>\s*<td class="([gar])">(.*?)</td>',b,re.S)
    rh=''
    for per,act,gc,gtxt,yc,ytxt in rows:
        rh+=f'<tr><td class="k">{striptags(per)}</td><td>{striptags(act)}</td><td class="{CMAP[gc]}">{striptags(gtxt)}</td><td class="{CMAP[yc]}">{striptags(ytxt)}</td></tr>'
    wig_html+=f'<div class="card"><div class="chead"><h3>{title}</h3><span class="pill {pcls}">{ptxt}</span></div><div class="base">{base}</div><table class="wt"><tr><th>Period</th><th>Actual</th><th>vs Goal</th><th>vs Last Yr</th></tr>{rh}</table></div>'

# ---- SERVICE data (embed, render client-side; exclude TGL%) ----
sv=open(f'{SRC}/service_dashboard.html',encoding='utf-8').read()
SD=json.loads(balanced(sv,sv.find('var D=')))
SVCDATA=json.dumps({'svc':SD['svc'],'tgl':SD['tgl'],'goal':SD['goal']},separators=(',',':'))

# review month = previous calendar month
today=datetime.date.today()
first=today.replace(day=1); lastmonth=(first-datetime.timedelta(days=1))
MON=lastmonth.strftime('%B %Y')

html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Service Tech Meeting — %MON%</title><style>
:root{--bg:#0e1116;--panel:#161b22;--panel2:#1b212b;--edge:#232a34;--ink:#e7edf5;--dim:#93a1b3;--accent:#2bd4a7;--blue:#4c8dff;--red:#ff6b6b;--amber:#f5b74e;--green:#38d39f}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1120px;margin:0 auto;padding:20px 18px 70px}
h1{font-size:22px;margin:0 0 2px;font-weight:800}.sub{color:var(--dim);font-size:12.5px;margin-bottom:8px}
h2.sec{font-size:15px;margin:26px 0 10px;font-weight:750;border-bottom:1px solid var(--edge);padding-bottom:6px;color:#cfe}
.cards3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}@media(max-width:820px){.cards3{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--edge);border-radius:11px;padding:12px 13px}
.chead{display:flex;justify-content:space-between;align-items:center;gap:8px}.chead h3{font-size:13.5px;margin:0;font-weight:750}
.base{color:var(--dim);font-size:10.5px;margin:5px 0 8px;line-height:1.4}
.pill{font-size:10.5px;font-weight:750;padding:2px 8px;border-radius:20px;white-space:nowrap}
.g{background:rgba(56,211,159,.15);color:var(--green)}.a{background:rgba(245,183,78,.15);color:var(--amber)}.r{background:rgba(255,107,107,.15);color:var(--red)}.n{background:#222c38;color:var(--dim)}
.up{background:rgba(56,211,159,.15);color:var(--green)}.down{background:rgba(255,107,107,.15);color:var(--red)}
table{width:100%;border-collapse:collapse}.wt td,.wt th{font-size:11.5px;padding:5px 6px;border-bottom:1px solid var(--edge);text-align:right}.wt td:first-child,.wt th:first-child{text-align:left}.wt th{color:var(--dim);font-weight:650}
.mcards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}@media(max-width:820px){.mcards{grid-template-columns:1fr 1fr}}
.mcard{background:var(--panel);border:1px solid var(--edge);border-radius:11px;padding:12px 13px}.ml{color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:.4px}.mv{font-size:21px;font-weight:800;margin:3px 0 6px}.mc{display:flex;gap:6px;flex-wrap:wrap}
.seg{display:inline-flex;border:1px solid var(--edge);border-radius:9px;overflow:hidden;margin:2px 0 10px}.seg button{background:var(--panel);color:var(--dim);border:0;padding:7px 15px;cursor:pointer;font-weight:650;font-size:12.5px}.seg button.active{background:var(--accent);color:#06231b}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:8px}@media(max-width:820px){.kpis{grid-template-columns:1fr 1fr}}
.kpi{background:var(--panel);border:1px solid var(--edge);border-radius:10px;padding:10px 12px}.kpi .lab{color:var(--dim);font-size:10.5px;text-transform:uppercase;letter-spacing:.3px}.kpi .val{font-size:18px;font-weight:750;margin-top:2px}.kpi .row{display:flex;gap:6px;margin-top:5px;flex-wrap:wrap}.tag{font-size:10.5px;font-weight:700;padding:2px 7px;border-radius:20px}
.st{width:100%;border-collapse:collapse;margin-top:6px}.st td,.st th{font-size:12px;padding:6px 9px;border-bottom:1px solid var(--edge);text-align:right}.st td:first-child,.st th:first-child{text-align:left}.st th{background:#12161d;color:var(--dim);font-weight:650}.st tr.tot td{font-weight:750;background:#12161d}
.grid2{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:8px}@media(max-width:900px){.grid2{grid-template-columns:1fr}}
.vc{background:var(--panel);border:1px solid var(--edge);border-radius:10px;padding:4px 0 8px}.vc h4{font-size:12.5px;margin:9px 11px 4px}.bt{width:100%}.bt td{font-size:11.5px;padding:5px 11px;border-bottom:1px solid var(--edge)}.bar{height:14px;background:var(--accent);border-radius:3px;display:inline-block;vertical-align:middle;opacity:.85}
.notes{background:var(--panel2);border:1px dashed var(--edge);border-radius:10px;padding:12px 14px;color:var(--dim);min-height:70px}
footer{margin-top:22px;color:var(--dim);font-size:11px}
@media print{body{background:#fff;color:#000}.card,.mcard,.kpi,.vc,.notes{border-color:#ccc}}
</style></head><body><div class="wrap">
<h1>Service Tech Meeting</h1>
<div class="sub">Review month: <b>%MON%</b> &middot; prepared %PREP% &middot; figures pulled from the live CBD dashboards</div>

<h2 class="sec">4DX Scoreboard — WIG 1 · 2 · 3</h2>
<div class="cards3">%WIGS%</div>

<h2 class="sec">Company Revenue — Rolling Windows</h2>
<div class="mcards">%REV%</div>

<h2 class="sec">Service Department — MTD &amp; Last Month</h2>
<div class="seg" id="seg"><button data-p="lm" class="active">Last Month</button><button data-p="mtd">MTD</button></div>
<div class="kpis" id="skpis"></div>
<h4 style="margin:14px 0 4px;font-size:13px" id="butitle">By Business Unit</h4>
<table class="st" id="butbl"><thead><tr><th>Business Unit</th><th>Revenue</th><th>Jobs</th><th>Jobs w/ rev</th><th>Avg Ticket</th><th>Avg Job Rev</th></tr></thead><tbody id="butb"></tbody></table>
<h4 style="margin:16px 0 2px;font-size:13px">By Primary Tech</h4>
<div class="grid2">
 <div class="vc"><h4>Service Revenue by Tech</h4><table class="bt" id="v_rev"></table></div>
 <div class="vc"><h4>TGL Sales by Tech</h4><table class="bt" id="v_tgls"></table></div>
 <div class="vc"><h4>Avg Ticket by Tech</h4><table class="bt" id="v_avg"></table></div>
</div>

<h2 class="sec">Talking Points / Additional Data</h2>
<div class="notes">Add anything not on the dashboards here before the meeting (safety, callbacks, training, parts, recognition, goals…).</div>

<footer>%FOOT%</footer>
</div>
<script>
var SD=%SVCDATA%;var SVC=SD.svc,TGL=SD.tgl,GOAL=SD.goal;var cur='lm';var LY={mtd:'mtd_ly',lm:'lm_ly'};
function money(n){return '$'+Math.round(n).toLocaleString();}
function yoy(a,b){return (b==null||b===0)?null:(a-b)/Math.abs(b)*100;}
function yTag(v){if(v==null)return '<span class="tag n">n/a</span>';var c=v>=0?'g':'r';return '<span class="tag '+c+'">'+(v>=0?'+':'')+v.toFixed(1)+'% YoY</span>';}
function kpi(l,v,tags){return '<div class="kpi"><div class="lab">'+l+'</div><div class="val">'+v+'</div><div class="row">'+tags.join('')+'</div></div>';}
function esc(s){return (''+s).replace(/&/g,'&amp;').replace(/</g,'&lt;');}
function techBars(id,obj,fmt){var arr=Object.keys(obj).map(function(k){return [k,obj[k]];}).filter(function(x){return x[1]>0;});arr.sort(function(a,b){return b[1]-a[1];});arr=arr.slice(0,12);var mx=arr.length?arr[0][1]:1;document.getElementById(id).innerHTML=arr.map(function(x){var w=Math.max(2,x[1]/mx*110);return '<tr><td style="width:36%">'+esc(x[0])+'</td><td style="text-align:right;width:24%">'+fmt(x[1])+'</td><td><span class="bar" style="width:'+w+'px"></span></td></tr>';}).join('')||'<tr><td style="padding:9px 11px;color:var(--dim)">No data.</td></tr>';}
function render(){var s=SVC[cur],sly=SVC[LY[cur]],t=TGL[cur],tly=TGL[LY[cur]],goal=GOAL[cur];
 var rev=s.rev,jobs=s.n,jrev=s.nRev,at=jrev?rev/jrev:0,aj=jobs?rev/jobs:0;
 var atly=sly.nRev?sly.rev/sly.nRev:0,ajly=sly.n?sly.rev/sly.n:0;
 document.getElementById('skpis').innerHTML=
  kpi('Service Revenue',money(rev),['<span class="tag '+(rev>=goal?'g':'r')+'">'+(goal?Math.round(rev/goal*100):0)+'% of goal</span>',yTag(yoy(rev,sly.rev))])+
  kpi('TGL Sales',money(t.sales),[yTag(yoy(t.sales,tly.sales)),'<span class="tag n">'+t.count+' est</span>'])+
  kpi('Avg Ticket',money(at),[yTag(yoy(at,atly))])+
  kpi('Avg Job Revenue',money(aj),[yTag(yoy(aj,ajly))])+
  kpi('Service Jobs',jobs.toLocaleString(),[yTag(yoy(jobs,sly.n)),'<span class="tag n">'+jrev+' w/ rev</span>'])+
  kpi('Service Goal',money(goal),['<span class="tag '+(rev>=goal?'g':'r')+'">'+money(rev-goal)+' vs goal</span>']);
 document.getElementById('butitle').textContent='By Business Unit — '+(cur=='lm'?'Last Month':'MTD');
 var bus=Object.keys(s.byBU).sort(function(a,b){return s.byBU[b].rev-s.byBU[a].rev;});
 function row(name,x,tot){var at=x.nRev?x.rev/x.nRev:0,aj=x.n?x.rev/x.n:0;return '<tr'+(tot?' class="tot"':'')+'><td>'+name+'</td><td>'+money(x.rev)+'</td><td>'+x.n+'</td><td>'+x.nRev+'</td><td>'+money(at)+'</td><td>'+money(aj)+'</td></tr>';}
 var fp={rev:0,n:0,nRev:0},hv={rev:0,n:0,nRev:0};bus.forEach(function(b){var x=s.byBU[b],o=/^FIRE|^Fireplace/i.test(b)?fp:hv;o.rev+=x.rev;o.n+=x.n;o.nRev+=x.nRev;});
 var tb=document.getElementById('butb');tb.innerHTML=row('Fireplace — all service',fp,true)+row('HVAC — all service',hv,true)+bus.map(function(b){return row(b,s.byBU[b]);}).join('')+row('TOTAL',{rev:rev,n:jobs,nRev:jrev},true);
 var mo=function(o,f){var r={};Object.keys(o).forEach(function(k){r[k]=f(o[k]);});return r;};
 techBars('v_rev',mo(s.byTech,function(v){return v.rev;}),money);
 techBars('v_tgls',mo(t.byTech||{},function(v){return v.sales;}),money);
 var av={};Object.keys(s.byTech).forEach(function(k){var x=s.byTech[k];if(x.nRev>=3)av[k]=x.rev/x.nRev;});techBars('v_avg',av,money);
}
[].forEach.call(document.querySelectorAll('#seg button'),function(b){b.onclick=function(){cur=b.dataset.p;[].forEach.call(document.querySelectorAll('#seg button'),function(x){x.classList.remove('active');});b.classList.add('active');render();};});
render();
</script></body></html>'''
html=(html.replace('%MON%',MON).replace('%PREP%',today.strftime('%b %-d, %Y'))
 .replace('%WIGS%',wig_html).replace('%REV%',rev_html).replace('%SVCDATA%',SVCDATA)
 .replace('%FOOT%','Sources: 4DX Scoreboard (WIG 1–3), Revenue dashboard (rolling 30/60/90/365), Service dashboard (MTD & Last Month, TGL% intentionally omitted). Auto-assembled from the published dashboards; figures reflect their most recent daily refresh.'))
open(OUT,'w',encoding='utf-8').write(html)
print('wrote',OUT,'bytes',len(html),'| review month',MON)
