# -*- coding: utf-8 -*-
"""
정적 웹사이트 생성기 — DB를 읽어 site/index.html 한 파일을 만듭니다.
GitHub Pages 가 이 파일을 그대로 서비스합니다. (인터넷 연결 불필요)

  python build_site.py
"""
import json
import os

import analyze
import db
import parser

OUT_DIR = "site"


def collect_data():
    db.init_db()
    s = analyze.summary()
    groups = analyze.clinic_groups(min_posts=2)
    posts = analyze.all_posts(status="all")

    def slim_post(p):
        return {
            "no": p["no"], "category": p.get("category"),
            "title": p.get("title"), "author": p.get("author"),
            "posted": p.get("posted_at") or p.get("first_seen"),
            "is_deleted": bool(p.get("is_deleted")),
            "deleted_at": p.get("deleted_at"),
            "url": p.get("url"), "content": p.get("content") or "",
            "clinic_total": p.get("clinic_total", 1),
            "repost_index": p.get("repost_index"),
            "region": parser.region_of(p.get("title")),
        }

    clinics = []
    for g in groups:
        clinics.append({
            "label": g["label"], "kind": g["kind"],
            "post_count": g["post_count"], "deleted_count": g["deleted_count"],
            "posts": [slim_post(p) for p in g["posts"]],
        })

    return {
        "generated_at": db.now_iso(),
        "summary": s,
        "clinics": clinics,
        "posts": [slim_post(p) for p in posts],
    }


HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>치과 구인글 아카이브</title>
<style>
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css");
:root{
  --paper:#F6F7F9;--card:#FFFFFF;--ink:#181A1F;--muted:#6A7180;--line:#E6E9EF;--line2:#D3D8E0;
  --alarm:#E4483B;--alarm-soft:#FCE9E7;--struct:#2C6E8F;--ok:#3A9B6E;
  --mono:ui-monospace,"SF Mono",Menlo,monospace;--sans:"Pretendard Variable",Pretendard,system-ui,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.5;letter-spacing:-.01em}
a{color:var(--struct);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:960px;margin:0 auto;padding:0 20px 80px}
header.top{border-bottom:2px solid var(--ink);margin-bottom:22px}
.top-in{max-width:960px;margin:0 auto;padding:22px 20px 16px;display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap}
.brand .kicker{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.brand h1{margin:0;font-size:23px;font-weight:800;letter-spacing:-.03em}
nav.tabs{display:flex;gap:4px}
nav.tabs button{font-size:13.5px;font-weight:600;color:var(--muted);padding:7px 13px;border-radius:8px;border:1px solid transparent;background:none;cursor:pointer;font-family:var(--sans)}
nav.tabs button.on{color:var(--ink);background:var(--card);border-color:var(--line2)}
.chips{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px}
.chip{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;min-width:120px}
.chip .n{font-family:var(--mono);font-size:24px;font-weight:700;line-height:1}
.chip .l{font-size:12px;color:var(--muted);margin-top:5px}
.chip.warn .n{color:var(--alarm)}
.clinic{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 18px 14px;margin-bottom:14px}
.clinic-head{display:flex;justify-content:space-between;align-items:center;gap:12px}
.clinic-id{display:flex;align-items:baseline;gap:10px;min-width:0}
.clinic-id .name{font-weight:700;font-size:16px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.clinic-id .kind{font-family:var(--mono);font-size:11px;color:var(--muted);border:1px solid var(--line2);border-radius:5px;padding:1px 6px}
.count{font-family:var(--mono);font-weight:700;font-size:14px;background:var(--alarm-soft);color:var(--alarm);border-radius:20px;padding:5px 12px;white-space:nowrap}
.count .x{font-weight:400;color:var(--muted);margin-left:6px}
.timeline{margin-top:16px;padding-top:14px;border-top:1px dashed var(--line2);overflow-x:auto}
.tl-track{display:flex;align-items:flex-start;min-width:min-content}
.tl-node{display:flex;flex-direction:column;align-items:center;position:relative;flex:1 0 84px;text-align:center}
.tl-node::before{content:"";position:absolute;top:11px;left:-50%;width:100%;height:2px;background:var(--line2)}
.tl-node:first-child::before{display:none}
.tl-dot{width:24px;height:24px;border-radius:50%;background:var(--struct);color:#fff;display:flex;align-items:center;justify-content:center;font-family:var(--mono);font-size:11px;font-weight:700;position:relative;z-index:1;border:3px solid var(--card);cursor:pointer}
.tl-dot.del{background:var(--alarm)}
.tl-seq{font-family:var(--mono);font-size:10px;color:var(--muted);margin-top:6px}
.tl-date{font-size:11px;margin-top:2px}
.tl-tag{font-size:10px;margin-top:2px;font-weight:600}
.tl-tag.del{color:var(--alarm)}.tl-tag.live{color:var(--ok)}
table.posts{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden}
table.posts th,table.posts td{padding:11px 14px;text-align:left;border-bottom:1px solid var(--line);font-size:14px;vertical-align:top}
table.posts th{font-size:12px;color:var(--muted);font-weight:600;background:var(--paper)}
table.posts tr:last-child td{border-bottom:none}
table.posts .no{font-family:var(--mono);color:var(--muted);font-size:13px}
tr.deleted{background:var(--alarm-soft)}
tr.deleted .title{text-decoration:line-through;text-decoration-color:var(--alarm)}
.title-link{cursor:pointer}
.badge{font-family:var(--mono);font-size:11px;font-weight:700;border-radius:5px;padding:1px 7px;display:inline-block}
.badge.del{background:var(--alarm);color:#fff}
.badge.rep{background:var(--alarm-soft);color:var(--alarm);margin-left:6px}
.cat{font-size:11px;font-weight:700;color:var(--struct);background:#EAF2F6;border-radius:5px;padding:2px 6px;white-space:nowrap}
.regions{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 16px}
.regions button{font-size:12.5px;font-weight:600;color:var(--muted);background:var(--card);border:1px solid var(--line2);border-radius:8px;padding:5px 10px;cursor:pointer;font-family:var(--sans)}
.regions button.on{background:var(--struct);color:#fff;border-color:var(--struct)}
.regions .rc{font-family:var(--mono);font-size:10px;opacity:.65;margin-left:1px}
.rg-chip{font-size:11px;font-weight:700;color:#6A4AAF;background:#EEEAF7;border-radius:5px;padding:2px 6px;white-space:nowrap}
.toolbar{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;align-items:center}
.seg{display:flex;border:1px solid var(--line2);border-radius:9px;overflow:hidden}
.seg button{padding:7px 14px;font-size:13px;font-weight:600;color:var(--muted);background:var(--card);border:none;cursor:pointer;font-family:var(--sans)}
.seg button.on{background:var(--ink);color:#fff}
.toolbar .search{margin-left:auto}
.toolbar input{border:1px solid var(--line2);border-radius:9px;padding:7px 12px;font-size:14px;font-family:var(--sans);min-width:200px}
.empty{color:var(--muted);text-align:center;padding:60px 20px;background:var(--card);border:1px dashed var(--line2);border-radius:14px}
.updated{font-family:var(--mono);font-size:11px;color:var(--muted);text-align:right;margin-top:24px}
.overlay{position:fixed;inset:0;background:rgba(20,22,27,.5);display:none;align-items:flex-start;justify-content:center;padding:40px 16px;overflow-y:auto;z-index:10}
.overlay.on{display:flex}
.modal{background:var(--card);border-radius:16px;max-width:640px;width:100%;padding:24px;position:relative}
.modal h2{margin:0 0 4px;font-size:19px}
.modal .meta{font-family:var(--mono);font-size:12px;color:var(--muted);margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid var(--line)}
.modal .body{white-space:pre-wrap;line-height:1.7}
.modal .close{position:absolute;top:16px;right:16px;border:none;background:var(--paper);border-radius:8px;width:32px;height:32px;font-size:18px;cursor:pointer}
@media (max-width:560px){.brand h1{font-size:20px}.col-hide{display:none}}
</style>
</head>
<body>
<header class="top"><div class="top-in">
  <div class="brand"><span class="kicker">Dental Recruit Archive</span><h1>치과 구인글 아카이브</h1></div>
  <nav class="tabs" id="tabs">
    <button data-tab="clinics" class="on">반복 치과</button>
    <button data-tab="all">전체 글</button>
    <button data-tab="deleted">삭제된 글</button>
  </nav>
</div></header>
<div class="wrap"><div id="app"></div>
  <div class="updated" id="updated"></div>
</div>
<div class="overlay" id="overlay"><div class="modal">
  <button class="close" onclick="closeModal()">×</button>
  <div id="modalBody"></div>
</div></div>

<script>
const DATA = __DATA__;

function esc(s){return (s==null?"":String(s)).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function dt(s){return s?String(s).replace("T"," ").slice(0,16):"-";}
let curTab="clinics", curStatus="all", curSearch="", curRegion="전체";
const REGIONS=["전체","서울","경기","인천","부산","대구","광주","대전","울산","세종","충북","충남","전남","전북","경북","경남","강원","제주","기타"];

function chips(){
  const s=DATA.summary;
  return `<div class="chips">
    <div class="chip"><div class="n">${s.total}</div><div class="l">수집한 글</div></div>
    <div class="chip warn"><div class="n">${s.deleted}</div><div class="l">삭제 감지</div></div>
    <div class="chip warn"><div class="n">${s.repeat_clinics}</div><div class="l">반복 게시 치과</div></div>
  </div>`;
}

function renderClinics(){
  let h=chips();
  if(!DATA.clinics.length){
    h+=`<div class="empty">아직 반복 게시가 감지된 치과가 없습니다.<br>수집이 며칠 쌓이면 재게시 패턴이 나타납니다.</div>`;
    return h;
  }
  for(const g of DATA.clinics){
    h+=`<div class="clinic"><div class="clinic-head">
      <div class="clinic-id"><span class="name">${esc(g.label)}</span><span class="kind">${esc(g.kind)}</span></div>
      <span class="count">${g.post_count}회 게시<span class="x">삭제 ${g.deleted_count}</span></span>
    </div><div class="timeline"><div class="tl-track">`;
    for(const p of g.posts){
      h+=`<div class="tl-node">
        <div class="tl-dot ${p.is_deleted?'del':''}" onclick="showDetail(${p.no})">${p.repost_index}</div>
        <div class="tl-seq">#${p.no}</div><div class="tl-date">${dt(p.posted)}</div>
        ${p.is_deleted?`<div class="tl-tag del">삭제됨</div><div class="tl-seq">${dt(p.deleted_at)}</div>`:`<div class="tl-tag live">게시중</div>`}
      </div>`;
    }
    h+=`</div></div></div>`;
  }
  return h;
}

function renderPosts(){
  let base=DATA.posts;
  if(curStatus==="deleted") base=base.filter(p=>p.is_deleted);
  else if(curStatus==="active") base=base.filter(p=>!p.is_deleted);
  if(curSearch){
    const q=curSearch.toLowerCase();
    base=base.filter(p=>(p.title||"").toLowerCase().includes(q)||(p.author||"").toLowerCase().includes(q)||(p.content||"").toLowerCase().includes(q));
  }
  const rc={}; base.forEach(p=>{const k=p.region||"기타"; rc[k]=(rc[k]||0)+1;});
  let rows=base;
  if(curRegion!=="전체") rows=base.filter(p=>(p.region||"기타")===curRegion);

  let h=`<div class="toolbar"><div class="seg">
    <button data-st="all" class="${curStatus==='all'?'on':''}">전체</button>
    <button data-st="active" class="${curStatus==='active'?'on':''}">게시중</button>
    <button data-st="deleted" class="${curStatus==='deleted'?'on':''}">삭제됨</button>
  </div><div class="search"><input id="q" placeholder="제목·작성자·본문 검색" value="${esc(curSearch)}"></div></div>`;
  h+=`<div class="regions">`;
  for(const r of REGIONS){
    const c = r==="전체" ? base.length : (rc[r]||0);
    if(r!=="전체" && r!=="기타" && c===0 && curRegion!==r) continue;
    h+=`<button data-rg="${r}" class="${curRegion===r?'on':''}">${r}${r!=="전체"?` <span class="rc">${c}</span>`:''}</button>`;
  }
  h+=`</div>`;

  if(!rows.length){h+=`<div class="empty">해당하는 글이 없습니다.</div>`;return h;}
  h+=`<table class="posts"><thead><tr><th style="width:64px">번호</th><th style="width:42px">구분</th><th style="width:44px">지역</th><th>제목</th><th class="col-hide" style="width:132px">작성자(치과)</th><th class="col-hide" style="width:88px">게시일</th><th style="width:64px">상태</th></tr></thead><tbody>`;
  for(const p of rows){
    h+=`<tr class="${p.is_deleted?'deleted':''}">
      <td class="no">${p.no}</td><td><span class="cat">${esc(p.category||'-')}</span></td>
      <td><span class="rg-chip">${esc(p.region||'기타')}</span></td>
      <td><span class="title title-link" onclick="showDetail(${p.no})">${esc(p.title||'(제목 없음)')}</span>${p.clinic_total>=2?`<span class="badge rep">${p.clinic_total}회</span>`:''}</td>
      <td class="col-hide">${esc(p.author||'-')}</td><td class="col-hide no">${dt(p.posted)}</td>
      <td>${p.is_deleted?`<span class="badge del">삭제</span>`:`<span style="color:var(--ok);font-size:12px;font-weight:600">게시중</span>`}</td>
    </tr>`;
  }
  h+=`</tbody></table>`;
  return h;
}

function render(){
  const app=document.getElementById("app");
  if(curTab==="clinics"){app.innerHTML=renderClinics();}
  else{curStatus=(curTab==="deleted")?"deleted":curStatus; app.innerHTML=renderPosts(); bindPostControls();}
  document.getElementById("updated").textContent="마지막 업데이트 "+dt(DATA.generated_at);
}

function bindPostControls(){
  document.querySelectorAll(".seg button").forEach(b=>b.onclick=()=>{curStatus=b.dataset.st;render();});
  document.querySelectorAll(".regions button").forEach(b=>b.onclick=()=>{curRegion=b.dataset.rg;render();});
  const q=document.getElementById("q");
  if(q){q.oninput=()=>{curSearch=q.value; const app=document.getElementById("app"); app.innerHTML=renderPosts(); bindPostControls(); const nq=document.getElementById("q"); nq.focus(); nq.setSelectionRange(nq.value.length,nq.value.length);};}
}

function showDetail(no){
  const p=DATA.posts.find(x=>x.no===no); if(!p)return;
  const sibs=DATA.posts.filter(x=>x.clinic_total>=2&&x.author===p.author).sort((a,b)=>a.no-b.no);
  let h=`<h2>${esc(p.title||'(제목 없음)')} ${p.is_deleted?'<span class="badge del">삭제됨</span>':''}</h2>
  <div class="meta">#${p.no} · ${esc(p.author||'-')} · 게시 ${dt(p.posted)}${p.is_deleted?` · 삭제 감지 ${dt(p.deleted_at)}`:''} · <a href="${esc(p.url)}" target="_blank" rel="noopener">원본 링크</a></div>
  <div class="body">${esc(p.content)||'<span style="color:var(--muted)">본문을 수집하지 못했습니다. 원본 링크를 확인하세요.</span>'}</div>`;
  if(sibs.length>1){
    h+=`<h3 style="margin:22px 0 8px;font-size:14px">이 치과의 다른 글 (${sibs.length}건)</h3>`;
    for(const s of sibs){h+=`<div style="padding:6px 0;border-top:1px solid var(--line);font-size:13px"><span class="no" style="font-family:var(--mono)">${s===p?'▶ ':''}</span><span class="title-link" onclick="showDetail(${s.no})">${esc(s.title||'(제목 없음)')}</span> · ${dt(s.posted)} ${s.is_deleted?'<span class="badge del">삭제</span>':''}</div>`;}
  }
  document.getElementById("modalBody").innerHTML=h;
  document.getElementById("overlay").classList.add("on");
}
function closeModal(){document.getElementById("overlay").classList.remove("on");}
document.getElementById("overlay").onclick=e=>{if(e.target.id==="overlay")closeModal();};
document.querySelectorAll("#tabs button").forEach(b=>b.onclick=()=>{
  document.querySelectorAll("#tabs button").forEach(x=>x.classList.remove("on"));b.classList.add("on");
  curTab=b.dataset.tab; if(curTab==="all")curStatus="all"; render();
});
render();
</script>
</body>
</html>
"""


def main():
    data = collect_data()
    os.makedirs(OUT_DIR, exist_ok=True)
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = HTML.replace("__DATA__", blob)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"site/index.html 생성 완료 "
          f"(글 {data['summary']['total']} / 삭제 {data['summary']['deleted']} / "
          f"반복치과 {data['summary']['repeat_clinics']})")


if __name__ == "__main__":
    main()
