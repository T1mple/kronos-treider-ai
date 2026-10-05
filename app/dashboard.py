from fastapi.responses import HTMLResponse

HTML = '''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kronos Trader AI</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;margin:0;background:#0b1020;color:#eef}
main{max-width:1180px;margin:30px auto;padding:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
.card{background:#151d33;border:1px solid #293454;border-radius:14px;padding:18px}
h1{margin-bottom:4px}.muted{color:#9aa8c7}.metric{font-size:28px;font-weight:700}
pre{white-space:pre-wrap;overflow:auto;max-height:260px}
svg{width:100%;height:260px;background:#10172a;border-radius:10px}
.row{display:flex;gap:20px;flex-wrap:wrap}.pill{padding:5px 9px;border:1px solid #33415f;border-radius:999px}
</style>
</head>
<body><main>
<h1>Kronos Trader AI</h1>
<p class="muted">Research / PAPER dashboard. Real trading is OFF.</p>
<div class="grid">
<div class="card"><div class="muted">Equity</div><div id="equity" class="metric">...</div></div>
<div class="card"><div class="muted">Total PnL</div><div id="pnl" class="metric">...</div></div>
<div class="card"><div class="muted">Win rate</div><div id="winrate" class="metric">...</div></div>
<div class="card"><div class="muted">Max drawdown</div><div id="dd" class="metric">...</div></div>
</div>
<div class="card" style="margin-top:14px"><h3>Equity curve</h3><svg id="chart" viewBox="0 0 1000 260" preserveAspectRatio="none"></svg></div>
<div class="grid" style="margin-top:14px">
<div class="card"><h3>Service / Risk</h3><pre id="risk">loading...</pre></div>
<div class="card"><h3>7-day breakdown</h3><pre id="breakdown">loading...</pre></div>
<div class="card"><h3>Recent trades</h3><pre id="trades">loading...</pre></div>
</div>
<script>
const money=x=>Number(x||0).toFixed(2);
async function get(url){const r=await fetch(url);if(!r.ok)throw new Error(await r.text());return r.json()}
function draw(points){
 const svg=document.getElementById('chart'); svg.innerHTML='';
 if(!points.length)return;
 const vals=points.map(x=>x.equity), min=Math.min(...vals), max=Math.max(...vals), span=(max-min)||1;
 const pts=points.map((p,i)=>{const x=20+i*(960/Math.max(1,points.length-1));const y=235-((p.equity-min)/span)*210;return x.toFixed(1)+','+y.toFixed(1)}).join(' ');
 svg.innerHTML='<polyline fill="none" stroke="currentColor" stroke-width="3" points="'+pts+'"/><text x="20" y="22" fill="currentColor">max '+money(max)+'</text><text x="20" y="252" fill="currentColor">min '+money(min)+'</text>';
}
async function load(){
 try{
  const [r,e,b,tr,risk]=await Promise.all([get('/api/paper/report'),get('/api/paper/equity?limit=500'),get('/api/paper/breakdown'),get('/api/paper/trades?limit=20'),get('/risk')]);
  document.getElementById('equity').textContent=money(r.equity);
  document.getElementById('pnl').textContent=money(r.total_pnl);
  document.getElementById('winrate').textContent=(Number(r.win_rate)*100).toFixed(1)+'%';
  document.getElementById('dd').textContent=(Number(r.max_drawdown)*100).toFixed(2)+'%';
  draw(e.points);
  document.getElementById('risk').textContent=JSON.stringify(risk,null,2);
  document.getElementById('breakdown').textContent=JSON.stringify(b.last_7d,null,2);
  document.getElementById('trades').textContent=JSON.stringify(tr.trades,null,2);
 }catch(err){document.body.insertAdjacentHTML('beforeend','<p>'+String(err)+'</p>')}
}
load();setInterval(load,60000);
</script></main></body></html>'''

def dashboard_html():
    return HTMLResponse(HTML)
