# -*- coding: utf-8 -*-
"""
정적 웹사이트 생성기 — DB를 읽어 site/index.html 한 파일을 만듭니다.
GitHub Pages 가 이 파일을 그대로 서비스합니다. (인터넷 연결 불필요)

  python build_site.py
"""
import json
import os
import re

import analyze
import db
import parser

OUT_DIR = "site"


def sig_of(title):
    """지역 접두어를 뺀 제목 내용의 시그니처 (같은 게시물 판별용)."""
    if not title:
        return ""
    body = title.split("|", 1)[-1]
    return re.sub(r"[^0-9A-Za-z가-힣]", "", body)


def collect_data():
    db.init_db()
    s = analyze.summary()
    groups = analyze.clinic_groups(min_posts=2)
    posts = [p for p in analyze.all_posts(status="all")
             if p.get("author") or p.get("category")]  # 옛 찌꺼기 제외

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
            "key": p.get("clinic_key"),
            "sig": sig_of(p.get("title")),
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
  --bg:#F2F4F6;--card:#FFFFFF;--ink:#191F28;--sub:#4E5968;--mut:#8B95A1;
  --line:#E5E8EB;--blue:#3182F6;--blue-soft:#E8F1FE;--red:#F04452;--red-soft:#FDECEE;--green:#12B886;
  --sans:"Pretendard Variable",Pretendard,-apple-system,system-ui,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55;letter-spacing:-.02em;-webkit-font-smoothing:antialiased}
a{color:var(--blue);text-decoration:none}
.wrap{max-width:920px;margin:0 auto;padding:24px 16px 80px}
header.top{background:var(--card);position:sticky;top:0;z-index:5;box-shadow:0 1px 0 rgba(0,0,0,.05)}
.top-in{max-width:920px;margin:0 auto;padding:16px 16px 0}
.brand .kicker{font-size:12px;font-weight:700;color:var(--blue)}
.brand h1{margin:2px 0 0;font-size:22px;font-weight:800;letter-spacing:-.03em}
nav.tabs{display:flex;gap:20px;margin-top:12px}
nav.tabs button{font-size:15px;font-weight:700;color:var(--mut);padding:10px 0;border:none;background:none;cursor:pointer;font-family:var(--sans);border-bottom:2.5px solid transparent}
nav.tabs button.on{color:var(--ink);border-bottom-color:var(--ink)}
.chips{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:0 0 22px}
.chip{background:var(--card);border-radius:16px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.chip .n{font-size:26px;font-weight:800;line-height:1;letter-spacing:-.03em}
.chip .l{font-size:13px;color:var(--mut);margin-top:7px;font-weight:500}
.chip.warn .n{color:var(--red)}
.chip.blue .n{color:var(--blue)}
.clinic{background:var(--card);border-radius:18px;padding:18px 18px 8px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.clinic-head{display:flex;justify-content:space-between;align-items:center;gap:12px}
.clinic-id{display:flex;align-items:center;gap:8px;min-width:0}
.clinic-id .name{font-weight:800;font-size:16px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.clinic-id .kind{font-size:11px;font-weight:700;color:var(--mut);background:var(--bg);border-radius:6px;padding:2px 7px}
.count{font-size:13px;font-weight:800;background:var(--red-soft);color:var(--red);border-radius:999px;padding:6px 12px;white-space:nowrap}
.count .x{font-weight:600;color:var(--mut);margin-left:6px}
.timeline{margin-top:14px;padding-top:12px;border-top:1px solid var(--line);overflow-x:auto}
.tl-track{display:flex;align-items:flex-start;min-width:min-content;padding-bottom:6px}
.tl-node{display:flex;flex-direction:column;align-items:center;position:relative;flex:1 0 82px;text-align:center}
.tl-node::before{content:"";position:absolute;top:13px;left:-50%;width:100%;height:3px;background:var(--line)}
.tl-node:first-child::before{display:none}
.tl-dot{width:28px;height:28px;border-radius:50%;background:var(--blue);color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;position:relative;z-index:1;box-shadow:0 0 0 4px var(--card);cursor:pointer}
.tl-dot.del{background:var(--red)}
.tl-seq{font-size:11px;color:var(--mut);margin-top:7px;font-weight:600}
.tl-date{font-size:12px;margin-top:2px;color:var(--sub);font-weight:600}
.tl-tag{font-size:11px;margin-top:3px;font-weight:700}
.tl-tag.del{color:var(--red)}.tl-tag.live{color:var(--green)}
.toolbar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center}
.seg{display:flex;background:var(--bg);border-radius:12px;padding:3px;gap:2px}
.seg button{padding:8px 15px;font-size:14px;font-weight:700;color:var(--mut);background:none;border:none;border-radius:9px;cursor:pointer;font-family:var(--sans)}
.seg button.on{background:var(--card);color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.1)}
.search{margin-left:auto;flex:1;min-width:170px}
.search input{width:100%;border:none;background:var(--card);border-radius:12px;padding:11px 14px;font-size:14px;font-family:var(--sans);box-shadow:0 1px 2px rgba(0,0,0,.05)}
.search input:focus{outline:2px solid var(--blue)}
.regions{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 16px}
.regions button{font-size:13px;font-weight:700;color:var(--sub);background:var(--card);border:none;border-radius:999px;padding:7px 13px;cursor:pointer;font-family:var(--sans);box-shadow:0 1px 2px rgba(0,0,0,.04)}
.regions button.on{background:var(--blue);color:#fff}
.regions .rc{font-size:11px;opacity:.7;margin-left:3px;font-weight:700}
.list{background:var(--card);border-radius:18px;box-shadow:0 1px 3px rgba(0,0,0,.05);overflow:hidden}
.row{display:flex;align-items:center;gap:11px;padding:14px 18px;border-bottom:1px solid var(--line);cursor:pointer}
.row:last-child{border-bottom:none}
.row:hover{background:#F9FAFB}
.row.del{background:var(--red-soft)}
.row .main{flex:1;min-width:0}
.row .t{font-weight:700;font-size:14.5px;color:var(--ink);display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row.del .t{color:var(--sub);text-decoration:line-through;text-decoration-color:var(--red)}
.row .meta{font-size:12.5px;color:var(--mut);margin-top:4px;display:flex;gap:7px;flex-wrap:wrap;align-items:center}
.rg-chip{font-size:11px;font-weight:800;color:var(--blue);background:var(--blue-soft);border-radius:6px;padding:3px 7px;white-space:nowrap;flex-shrink:0}
.cat{font-size:11px;font-weight:800;color:var(--sub);background:var(--bg);border-radius:6px;padding:2px 7px}
.badge{font-size:11px;font-weight:800;border-radius:6px;padding:3px 8px;white-space:nowrap;flex-shrink:0}
.badge.del{background:var(--red);color:#fff}
.badge.rep{background:var(--red-soft);color:var(--red)}
.badge.live{background:#E7F8F0;color:var(--green)}
.title-link{cursor:pointer;color:var(--blue)}
.empty{color:var(--mut);text-align:center;padding:56px 20px;background:var(--card);border-radius:18px}
.updated{font-size:12px;color:var(--mut);text-align:center;margin-top:22px;font-weight:500}
.overlay{position:fixed;inset:0;background:rgba(0,0,0,.4);display:none;align-items:flex-end;justify-content:center;z-index:10}
.overlay.on{display:flex}
.modal{background:var(--card);border-radius:22px 22px 0 0;max-width:640px;width:100%;padding:24px 22px 34px;position:relative;max-height:88vh;overflow-y:auto}
@media(min-width:640px){.overlay{align-items:center}.modal{border-radius:22px}}
.modal h2{margin:0 30px 6px 0;font-size:19px;font-weight:800;line-height:1.4}
.modal .meta{font-size:13px;color:var(--mut);margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid var(--line);font-weight:500}
.modal .body{white-space:pre-wrap;line-height:1.75;font-size:15px;color:var(--sub)}
.modal .close{position:absolute;top:16px;right:16px;border:none;background:var(--bg);border-radius:999px;width:34px;height:34px;font-size:19px;cursor:pointer;color:var(--sub)}
</style>
</head>
<body>
<header class="top"><div class="top-in">
  <div class="brand"><span class="kicker">Dental Recruit Archive</span><h1>치과 구인글 아카이브</h1></div>
  <nav class="tabs" id="tabs">
    <button data-tab="all" class="on">전체 글</button>
    <button data-tab="clinics">반복 치과</button>
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
let curTab="all", curSearch="", curRegion="전체";
const REGIONS=["전체","서울","경기","인천","부산","대구","광주","대전","울산","세종","충북","충남","전남","전북","경북","경남","강원","제주","기타"];

function chips(){
  const s=DATA.summary;
  return `<div class="chips">
    <div class="chip blue"><div class="n">${s.total}</div><div class="l">수집한 글</div></div>
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
  if(curTab==="deleted") base=base.filter(p=>p.is_deleted);
  if(curSearch){
    const q=curSearch.toLowerCase();
    base=base.filter(p=>(p.title||"").toLowerCase().includes(q)||(p.author||"").toLowerCase().includes(q)||(p.content||"").toLowerCase().includes(q));
  }
  // 같은 게시물(같은 치과 + 같은 내용)끼리 하나로 합치기
  const gm=new Map();
  for(const p of base){
    const k=(p.key||p.author||("n"+p.no))+"¦"+(p.sig||("n"+p.no));
    const g=gm.get(k);
    if(!g){ gm.set(k,{rep:p,count:1}); }
    else { g.count++; if(p.no>g.rep.no) g.rep=p; }
  }
  const allItems=[...gm.values()].sort((a,b)=>b.rep.no-a.rep.no);
  const rc={}; allItems.forEach(it=>{const r=it.rep.region||"기타"; rc[r]=(rc[r]||0)+1;});
  let items=allItems;
  if(curRegion!=="전체") items=allItems.filter(it=>(it.rep.region||"기타")===curRegion);

  let h=`<div class="toolbar"><div class="search"><input id="q" placeholder="제목·작성자·지역·본문 검색" value="${esc(curSearch)}"></div></div>`;
  h+=`<div class="regions">`;
  for(const r of REGIONS){
    const c = r==="전체" ? allItems.length : (rc[r]||0);
    if(r!=="전체" && r!=="기타" && c===0 && curRegion!==r) continue;
    h+=`<button data-rg="${r}" class="${curRegion===r?'on':''}">${r}${r!=="전체"?` <span class="rc">${c}</span>`:''}</button>`;
  }
  h+=`</div>`;

  if(!items.length){h+=`<div class="empty">해당하는 글이 없습니다.</div>`;return h;}
  h+=`<div class="list">`;
  for(const it of items){
    const p=it.rep;
    h+=`<div class="row ${p.is_deleted?'del':''}" onclick="showDetail(${p.no})">
      <span class="rg-chip">${esc(p.region||'기타')}</span>
      <div class="main">
        <span class="t">${esc(p.title||'(제목 없음)')}</span>
        <div class="meta"><span class="cat">${esc(p.category||'-')}</span><span>${esc(p.author||'-')}</span><span>${dt(p.posted)}</span>${it.count>=2?`<span class="badge rep">${it.count}회 게시</span>`:''}</div>
      </div>
      ${p.is_deleted?`<span class="badge del">삭제</span>`:`<span class="badge live">게시중</span>`}
    </div>`;
  }
  h+=`</div>`;
  return h;
}

function render(){
  const app=document.getElementById("app");
  if(curTab==="clinics"){app.innerHTML=renderClinics();}
  else{app.innerHTML=renderPosts(); bindPostControls();}
  document.getElementById("updated").textContent="마지막 업데이트 "+dt(DATA.generated_at);
}

function bindPostControls(){
  document.querySelectorAll(".regions button").forEach(b=>b.onclick=()=>{curRegion=b.dataset.rg;render();});
  const q=document.getElementById("q");
  if(q){q.oninput=()=>{curSearch=q.value; const app=document.getElementById("app"); app.innerHTML=renderPosts(); bindPostControls(); const nq=document.getElementById("q"); nq.focus(); nq.setSelectionRange(nq.value.length,nq.value.length);};}
}

function showDetail(no){
  const p=DATA.posts.find(x=>x.no===no); if(!p)return;
  const sibs=DATA.posts.filter(x=>x.clinic_total>=2&&x.author===p.author).sort((a,b)=>a.no-b.no);
  let h=`<h2>${esc(p.title||'(제목 없음)')} ${p.is_deleted?'<span class="badge del">삭제됨</span>':''}</h2>
  <div class="meta">#${p.no} · ${esc(p.author||'-')} · 게시 ${dt(p.posted)}${p.is_deleted?` · 삭제 감지 ${dt(p.deleted_at)}`:''} · <a href="${esc(p.url)}" target="_blank" rel="noopener">원본 링크</a></div>
  <div class="body">${esc(p.content)||'<span style="color:var(--mut)">본문을 수집하지 못했습니다. 원본 링크를 확인하세요.</span>'}</div>`;
  if(sibs.length>1){
    h+=`<h3 style="margin:22px 0 8px;font-size:14px">이 치과의 다른 글 (${sibs.length}건)</h3>`;
    for(const s of sibs){h+=`<div style="padding:6px 0;border-top:1px solid var(--line);font-size:13px"><span style="color:var(--mut)">${s===p?'▶ ':''}</span><span class="title-link" onclick="showDetail(${s.no})">${esc(s.title||'(제목 없음)')}</span> · ${dt(s.posted)} ${s.is_deleted?'<span class="badge del">삭제</span>':''}</div>`;}
  }
  document.getElementById("modalBody").innerHTML=h;
  document.getElementById("overlay").classList.add("on");
  const mo=document.querySelector(".modal"); if(mo) mo.scrollTop=0;
}
function closeModal(){document.getElementById("overlay").classList.remove("on");}
document.getElementById("overlay").onclick=e=>{if(e.target.id==="overlay")closeModal();};
document.querySelectorAll("#tabs button").forEach(b=>b.onclick=()=>{
  document.querySelectorAll("#tabs button").forEach(x=>x.classList.remove("on"));b.classList.add("on");
  curTab=b.dataset.tab; render();
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
