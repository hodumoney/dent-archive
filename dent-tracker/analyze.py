# -*- coding: utf-8 -*-
"""반복 게시 치과 분석 — 식별키로 묶어 횟수/타임라인 계산."""
import db

# 옛 파서 시절의 찌꺼기(작성자·구분이 모두 비어있는 행)를 모든 계산에서 제외
_REAL = "(author IS NOT NULL OR category IS NOT NULL)"


def _order_ts(p):
    """정렬용 시각: 게시판 날짜 우선, 없으면 최초 발견 시각."""
    return p.get("posted_at") or p.get("first_seen") or ""


def clinic_groups(min_posts=2, include_singletons=False):
    """
    치과별로 글을 묶어 반환.
    [{key, kind, label, phone_display, post_count, deleted_count,
      first, last, posts:[...] }] — 글 많은 순 정렬.
    """
    with db.get_db() as conn:
        rows = [dict(r) for r in conn.execute(f"SELECT * FROM posts WHERE {_REAL}").fetchall()]

    groups = {}
    for p in rows:
        groups.setdefault(p["clinic_key"], []).append(p)

    result = []
    for key, posts in groups.items():
        if not include_singletons and len(posts) < min_posts:
            continue
        posts.sort(key=_order_ts)
        # 각 글에 '몇 번째 게시'인지 부여
        for i, p in enumerate(posts, 1):
            p["repost_index"] = i
        deleted = sum(1 for p in posts if p["is_deleted"])
        sample = posts[-1]
        label = (sample.get("author")
                 or sample.get("phone_display")
                 or (sample.get("title") or "")[:24]
                 or key)
        result.append({
            "key": key,
            "kind": sample.get("key_kind"),
            "label": label,
            "phone_display": sample.get("phone_display"),
            "post_count": len(posts),
            "deleted_count": deleted,
            "first": _order_ts(posts[0]),
            "last": _order_ts(posts[-1]),
            "posts": posts,
        })

    result.sort(key=lambda g: (g["post_count"], g["deleted_count"]), reverse=True)
    return result


def all_posts(status="all", search=None, order="recent"):
    """게시판 뷰용 글 목록. status: all|deleted|active."""
    q = f"SELECT * FROM posts WHERE {_REAL}"
    args = []
    if status == "deleted":
        q += " AND is_deleted=1"
    elif status == "active":
        q += " AND is_deleted=0"
    if search:
        q += " AND (title LIKE ? OR content LIKE ? OR phone_display LIKE ?)"
        args += [f"%{search}%"] * 3
    if order == "reposts":
        q += " ORDER BY no DESC"
    else:
        q += " ORDER BY no DESC"
    with db.get_db() as conn:
        rows = [dict(r) for r in conn.execute(q, args).fetchall()]
    # 반복 횟수 주석
    counts = {}
    for r in rows:
        counts[r["clinic_key"]] = counts.get(r["clinic_key"], 0) + 1
    with db.get_db() as conn:
        full = {}
        for r in conn.execute(f"SELECT clinic_key, COUNT(*) c FROM posts WHERE {_REAL} GROUP BY clinic_key"):
            full[r["clinic_key"]] = r["c"]
    for r in rows:
        r["clinic_total"] = full.get(r["clinic_key"], 1)
    return rows


def summary():
    with db.get_db() as conn:
        total = conn.execute(f"SELECT COUNT(*) c FROM posts WHERE {_REAL}").fetchone()["c"]
        deleted = conn.execute(f"SELECT COUNT(*) c FROM posts WHERE is_deleted=1 AND {_REAL}").fetchone()["c"]
        repeat = conn.execute(
            f"SELECT COUNT(*) c FROM (SELECT clinic_key FROM posts WHERE {_REAL} "
            "GROUP BY clinic_key HAVING COUNT(*)>=2)"
        ).fetchone()["c"]
        last_run = conn.execute(
            "SELECT * FROM crawl_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return {
        "total": total,
        "deleted": deleted,
        "repeat_clinics": repeat,
        "last_run": dict(last_run) if last_run else None,
    }
