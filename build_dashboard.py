#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera um dashboard HTML auto-contido (dados embutidos) a partir de
data/programs_summary.json. Basta dar duplo-clique no dashboard.html depois.

    python build_dashboard.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "data" / "programs_summary.json"
OUT = ROOT / "dashboard.html"

data = json.loads(SRC.read_text(encoding="utf-8"))
payload = json.dumps(data, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HackenProof — Painel de Programas</title>
<style>
  :root{
    --bg:#0c0f17; --panel:#141a26; --panel2:#1b2333; --line:#26304a;
    --txt:#e7ecf5; --mut:#8b97ad; --acc:#5b8cff; --grn:#27d17f; --grn2:#0f3d2a;
    --ylw:#ffce5b; --red:#ff6b6b; --pur:#b48cff;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);
    font:14px/1.4 system-ui,Segoe UI,Roboto,Arial,sans-serif}
  header{padding:16px 20px;border-bottom:1px solid var(--line);
    background:linear-gradient(180deg,#10141f,#0c0f17)}
  h1{margin:0;font-size:18px;letter-spacing:.3px}
  h1 span{color:var(--acc)}
  .sub{color:var(--mut);font-size:12px;margin-top:3px}
  .cards{display:flex;gap:10px;flex-wrap:wrap;padding:14px 20px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:10px;
    padding:10px 14px;min-width:130px}
  .card .v{font-size:20px;font-weight:700}
  .card .k{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.5px}
  .card.g .v{color:var(--grn)} .card.b .v{color:var(--acc)} .card.y .v{color:var(--ylw)}
  .bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:6px 20px 14px}
  input[type=search],select{background:var(--panel2);border:1px solid var(--line);
    color:var(--txt);border-radius:8px;padding:8px 10px;font-size:13px}
  input[type=search]{min-width:240px}
  .chk{display:inline-flex;gap:6px;align-items:center;background:var(--panel);
    border:1px solid var(--line);padding:7px 11px;border-radius:8px;cursor:pointer;
    user-select:none;font-size:13px}
  .chk input{accent-color:var(--grn)}
  .presets{display:flex;gap:8px;flex-wrap:wrap;padding:0 20px 10px}
  .pbtn{background:var(--panel2);border:1px solid var(--line);color:var(--txt);
    padding:7px 12px;border-radius:20px;cursor:pointer;font-size:12.5px}
  .pbtn:hover{border-color:var(--acc);color:#fff}
  .pbtn.active{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:600}
  .wrap{padding:0 20px 40px;overflow-x:auto}
  table{border-collapse:collapse;width:100%;font-size:13px}
  th,td{padding:8px 10px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line)}
  th:first-child,td:first-child{text-align:left}
  th{position:sticky;top:0;background:var(--panel);cursor:pointer;font-size:11.5px;
    text-transform:uppercase;letter-spacing:.4px;color:var(--mut);z-index:2}
  th:hover{color:var(--txt)}
  th.sort-asc::after{content:" ▲";color:var(--acc)} th.sort-desc::after{content:" ▼";color:var(--acc)}
  tbody tr:hover{background:#121826}
  td a{color:var(--txt);text-decoration:none;font-weight:600}
  td a:hover{color:var(--acc);text-decoration:underline}
  .co{color:var(--mut);font-size:11.5px;display:block;font-weight:400}
  .tag{display:inline-block;background:var(--panel2);border:1px solid var(--line);
    border-radius:5px;padding:1px 6px;font-size:11px;color:var(--mut)}
  .pill{padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700}
  .rep0{background:var(--grn2);color:var(--grn)}
  .repN{color:var(--ylw)}
  .new{background:#1d2b52;color:#86b0ff;padding:1px 6px;border-radius:5px;font-size:10.5px;
    font-weight:700;margin-left:5px;vertical-align:middle}
  .active{color:var(--grn)} .inactive{color:var(--mut)}
  .money{color:var(--grn);font-weight:600}
  .score{font-weight:800}
  .sc-hi{color:var(--grn)} .sc-md{color:var(--ylw)} .sc-lo{color:var(--mut)}
  .bar2{height:6px;background:var(--panel2);border-radius:4px;overflow:hidden;width:60px;display:inline-block;vertical-align:middle}
  .bar2 i{display:block;height:100%;background:var(--grn)}
  .count{color:var(--mut);font-size:12px;padding:4px 20px}
  .foot{color:var(--mut);font-size:11px;padding:0 20px 20px}
</style>
</head>
<body>
<header>
  <h1><span>HackenProof</span> — Painel de Programas</h1>
  <div class="sub" id="sub"></div>
</header>

<div class="cards" id="cards"></div>

<div class="presets" id="presets">
  <button class="pbtn" data-preset="all">Todos</button>
  <button class="pbtn" data-preset="easy">🟢 Fácil & Novo (0 reputação)</button>
  <button class="pbtn" data-preset="bigbounty">💰 Maior bounty máximo</button>
  <button class="pbtn" data-preset="lowcomp">🎯 Menos concorrência</button>
  <button class="pbtn" data-preset="pays">✅ Mais já pagou</button>
  <button class="pbtn" data-preset="score">⭐ Melhor oportunidade</button>
</div>

<div class="bar">
  <input type="search" id="q" placeholder="Buscar nome, empresa, tipo, linguagem...">
  <label class="chk"><input type="checkbox" id="f_rep0"> Rep 0 / sem exigência</label>
  <label class="chk"><input type="checkbox" id="f_new"> Novo</label>
  <label class="chk"><input type="checkbox" id="f_active"> Ativo</label>
  <label class="chk"><input type="checkbox" id="f_nokyc"> Sem KYC</label>
  <label class="chk"><input type="checkbox" id="f_pays"> Já pagou ($)</label>
  <select id="ptype"><option value="">Todos os tipos</option></select>
</div>

<div class="count" id="count"></div>
<div class="wrap">
  <table id="tbl">
    <thead><tr id="head"></tr></thead>
    <tbody id="body"></tbody>
  </table>
</div>
<div class="foot">
  Reputação <b>0/—</b> = sem exigência. <b>Reports</b> = concorrência (quanto menor, menos disputado).
  <b>Aceite%</b> = válidos ÷ enviados. <b>Pago</b> = recompensas já distribuídas (prova que paga).
  <b>Score</b> = heurística: combina bounty alto + já paga + pouca concorrência + sem reputação + novo.
</div>

<script>
const DATA = __DATA__;

// ---- normaliza / deriva metricas ----
const num = v => { const n = parseFloat(v); return isNaN(n)?0:n; };
DATA.forEach(d=>{
  d._rep = (d.min_reputation_points==null)?0:num(d.min_reputation_points);
  d._maxb = num(d.max_bounty);
  d._minb = num(d.min_bounty);
  d._paid = num(d.total_rewards);
  d._reports = num(d.submitted_reports);
  d._valid = num(d.valid_reports_count);
  d._views = num(d.views_count);
  d._accept = d._reports>0 ? d._valid/d._reports : 0;
  d._active = (d.status==='Active');
  d._search = [d.title,d.company,d.types,d.languages,d.project_types,d.platforms]
                .join(' ').toLowerCase();
});

// ---- score de oportunidade (0-100, explicavel) ----
const max = k => Math.max(1, ...DATA.map(d=>d[k]));
const MB=max('_maxb'), PD=max('_paid'), RP=max('_reports');
DATA.forEach(d=>{
  const sBounty = Math.sqrt(d._maxb/MB);              // bounty alto
  const sPaid   = Math.sqrt(d._paid/PD);              // ja paga
  const sComp   = 1 - Math.sqrt(d._reports/RP);       // pouca concorrencia
  const sRep    = d._rep===0 ? 1 : 0.3;               // sem reputacao
  const sNew    = d.new_program ? 1 : 0.5;            // novo
  const sActive = d._active ? 1 : 0.2;                // ativo
  d._score = Math.round(
    (sBounty*26 + sPaid*22 + sComp*22 + sRep*14 + sNew*8 + sActive*8)
  );
});

// ---- colunas ----
const COLS = [
  {k:'title',   t:'Programa', s:r=>r.title.toLowerCase(), render:r=>
    `<a href="${r.url}" target="_blank">${esc(r.title)}${r.new_program?'<span class="new">NOVO</span>':''}</a>
     <span class="co">${esc(r.company||'')} · ${esc(r.project_types||r.types||'')}</span>`},
  {k:'_score',  t:'Score',  s:r=>r._score, render:r=>{
    const c=r._score>=70?'sc-hi':r._score>=45?'sc-md':'sc-lo';
    return `<span class="score ${c}">${r._score}</span>`;}},
  {k:'_rep',    t:'Reputação', s:r=>r._rep, render:r=>
    r._rep===0?'<span class="pill rep0">0 / —</span>':`<span class="repN">${r._rep}</span>`},
  {k:'_maxb',   t:'Bounty máx', s:r=>r._maxb, render:r=>r._maxb?`<span class="money">$${fmt(r._maxb)}</span>`:'—'},
  {k:'_minb',   t:'Bounty mín', s:r=>r._minb, render:r=>r._minb?`$${fmt(r._minb)}`:'—'},
  {k:'_paid',   t:'Já pago', s:r=>r._paid, render:r=>r._paid?`<span class="money">$${fmt(r._paid)}</span>`:'—'},
  {k:'_reports',t:'Reports', s:r=>r._reports, render:r=>fmt(r._reports)},
  {k:'_valid',  t:'Válidos', s:r=>r._valid, render:r=>fmt(r._valid)},
  {k:'_accept', t:'Aceite%', s:r=>r._accept, render:r=>{
    const p=Math.round(r._accept*100);
    return r._reports? `<span class="bar2"><i style="width:${p}%"></i></span> ${p}%` : '—';}},
  {k:'_views',  t:'Views', s:r=>r._views, render:r=>fmt(r._views)},
  {k:'status',  t:'Status', s:r=>r.status||'', render:r=>
    `<span class="${r._active?'active':'inactive'}">${esc(r.status||r.state||'—')}</span>`},
  {k:'kyc_required', t:'KYC', s:r=>r.kyc_required?1:0, render:r=>r.kyc_required?'🔒':'—'},
];

function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function fmt(n){ if(n>=1e6)return (n/1e6).toFixed(1)+'M'; if(n>=1e3)return (n/1e3).toFixed(n>=1e4?0:1)+'k'; return n%1?n.toFixed(0):n;}

let sortKey='_score', sortDir=-1;

// header
const head=document.getElementById('head');
COLS.forEach(c=>{const th=document.createElement('th');th.textContent=c.t;th.dataset.k=c.k;
  th.onclick=()=>{ if(sortKey===c.k){sortDir*=-1;}else{sortKey=c.k;sortDir=-1;} render();};
  head.appendChild(th);});

// tipos
const types=[...new Set(DATA.flatMap(d=>(d.project_types||'').split(';')).filter(Boolean))].sort();
const sel=document.getElementById('ptype');
types.forEach(t=>{const o=document.createElement('option');o.value=t;o.textContent=t;sel.appendChild(o);});

// presets
let preset='all';
document.querySelectorAll('.pbtn').forEach(b=>b.onclick=()=>{
  preset=b.dataset.preset;
  document.querySelectorAll('.pbtn').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  // ajusta filtros/sort por preset
  if(preset==='easy'){f_rep0.checked=true;f_active.checked=true;sortKey='_score';sortDir=-1;}
  if(preset==='bigbounty'){sortKey='_maxb';sortDir=-1;}
  if(preset==='lowcomp'){f_active.checked=true;sortKey='_reports';sortDir=1;}
  if(preset==='pays'){f_pays.checked=true;sortKey='_paid';sortDir=-1;}
  if(preset==='score'){f_active.checked=true;sortKey='_score';sortDir=-1;}
  if(preset==='all'){f_rep0.checked=f_active.checked=f_pays.checked=false;sortKey='_score';sortDir=-1;}
  render();
});

['q','ptype'].forEach(id=>document.getElementById(id).addEventListener('input',render));
['f_rep0','f_new','f_active','f_nokyc','f_pays'].forEach(id=>
  document.getElementById(id).addEventListener('change',render));

function filtered(){
  const q=document.getElementById('q').value.toLowerCase().trim();
  const pt=document.getElementById('ptype').value;
  const r0=f_rep0.checked,nw=f_new.checked,ac=f_active.checked,nk=f_nokyc.checked,pp=f_pays.checked;
  return DATA.filter(d=>{
    if(q && !d._search.includes(q)) return false;
    if(pt && !(d.project_types||'').split(';').includes(pt)) return false;
    if(r0 && d._rep!==0) return false;
    if(nw && !d.new_program) return false;
    if(ac && !d._active) return false;
    if(nk && d.kyc_required) return false;
    if(pp && d._paid<=0) return false;
    return true;
  });
}

function render(){
  const col=COLS.find(c=>c.k===sortKey)||COLS[1];
  const rows=filtered().sort((a,b)=>{
    const x=col.s(a),y=col.s(b);
    return (x<y?-1:x>y?1:0)*sortDir;
  });
  // head arrows
  document.querySelectorAll('th').forEach(th=>{th.classList.remove('sort-asc','sort-desc');
    if(th.dataset.k===sortKey)th.classList.add(sortDir>0?'sort-asc':'sort-desc');});
  // body
  const body=document.getElementById('body');
  body.innerHTML=rows.map(r=>'<tr>'+COLS.map(c=>`<td>${c.render(r)}</td>`).join('')+'</tr>').join('');
  document.getElementById('count').textContent=`${rows.length} de ${DATA.length} programas`;
}

// cards resumo
function cards(){
  const tot=DATA.length;
  const rep0=DATA.filter(d=>d._rep===0).length;
  const news=DATA.filter(d=>d.new_program).length;
  const easy=DATA.filter(d=>d._rep===0 && d._active).length;
  const paid=DATA.reduce((s,d)=>s+d._paid,0);
  const c=document.getElementById('cards');
  const add=(k,v,cls='')=>c.insertAdjacentHTML('beforeend',
    `<div class="card ${cls}"><div class="v">${v}</div><div class="k">${k}</div></div>`);
  add('Programas',tot);
  add('Sem reputação',rep0,'g');
  add('Fácil + Ativo',easy,'g');
  add('Novos',news,'b');
  add('Total já pago','$'+fmt(paid),'y');
  document.getElementById('sub').textContent=
    'Dados coletados via API. Clique nos títulos das colunas pra ordenar. '+
    'Clique no nome do programa pra abrir no HackenProof.';
}

cards();
document.querySelector('[data-preset="score"]').classList.add('active');
f_active.checked=true;
render();
</script>
</body>
</html>"""

OUT.write_text(HTML.replace("__DATA__", payload), encoding="utf-8")
print(f"-> {OUT}  ({len(data)} programas embutidos)")
