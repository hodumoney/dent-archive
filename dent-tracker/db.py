# -*- coding: utf-8 -*-
"""SQLite 저장소 — 스키마 정의 및 접근 함수."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

import config


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@contextmanager
def get_db():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    no            INTEGER PRIMARY KEY,   -- 게시판 글 번호 (고유)
    category      TEXT,                  -- 구분: 구인 / 구직 / 양도
    title         TEXT,
    author        TEXT,
    posted_raw    TEXT,                  -- 게시판이 보여주는 날짜 원문
    posted_at     TEXT,                  -- 파싱한 ISO 날짜 (가능한 경우)
    views         INTEGER,
    url           TEXT,
    content       TEXT,                  -- 상세 본문
    phone         TEXT,                  -- 본문에서 추출한 대표 전화번호(숫자만)
    phone_display TEXT,                  -- 보기용 전화번호
    clinic_key    TEXT,                  -- 치과 식별키 (전화 우선, 없으면 제목 시그니처)
    key_kind      TEXT,                  -- 'phone' | 'title' | 'author'
    title_sig     TEXT,                  -- 제목 정규화 시그니처
    first_seen    TEXT,                  -- 우리 크롤러가 처음 발견한 시각
    last_seen     TEXT,                  -- 살아있는 것으로 마지막 확인한 시각
    is_deleted    INTEGER DEFAULT 0,     -- 삭제 감지 여부
    deleted_at    TEXT                   -- 삭제 감지 시각
);

CREATE INDEX IF NOT EXISTS idx_posts_clinic ON posts(clinic_key);
CREATE INDEX IF NOT EXISTS idx_posts_deleted ON posts(is_deleted);

-- 크롤 실행 로그 (몇 개 발견/신규/삭제감지 됐는지)
CREATE TABLE IF NOT EXISTS crawl_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ran_at      TEXT,
    seen_count  INTEGER,
    new_count   INTEGER,
    deleted_count INTEGER,
    min_no      INTEGER,
    max_no      INTEGER,
    note        TEXT
);
"""


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)


def get_post(conn, no):
    row = conn.execute("SELECT * FROM posts WHERE no=?", (no,)).fetchone()
    return dict(row) if row else None


def insert_post(conn, p):
    ts = now_iso()
    conn.execute(
        """INSERT INTO posts
           (no,category,title,author,posted_raw,posted_at,views,url,content,phone,
            phone_display,clinic_key,key_kind,title_sig,first_seen,last_seen,is_deleted)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)""",
        (p["no"], p.get("category"), p.get("title"), p.get("author"),
         p.get("posted_raw"), p.get("posted_at"), p.get("views"), p.get("url"),
         p.get("content"), p.get("phone"), p.get("phone_display"), p.get("clinic_key"),
         p.get("key_kind"), p.get("title_sig"), ts, ts),
    )


def touch_seen(conn, no):
    """이미 있는 글이 아직 살아있음을 갱신."""
    conn.execute("UPDATE posts SET last_seen=? WHERE no=?", (now_iso(), no))


def mark_deleted(conn, nos):
    ts = now_iso()
    for no in nos:
        conn.execute(
            "UPDATE posts SET is_deleted=1, deleted_at=? WHERE no=? AND is_deleted=0",
            (ts, no),
        )


def active_nos_in_range(conn, lo, hi):
    """살아있다고 저장돼 있고 [lo,hi] 범위에 드는 글 번호들."""
    rows = conn.execute(
        "SELECT no FROM posts WHERE is_deleted=0 AND no>=? AND no<=?", (lo, hi)
    ).fetchall()
    return {r["no"] for r in rows}


def log_run(conn, seen, new, deleted, min_no, max_no, note=""):
    conn.execute(
        """INSERT INTO crawl_runs (ran_at,seen_count,new_count,deleted_count,min_no,max_no,note)
           VALUES (?,?,?,?,?,?,?)""",
        (now_iso(), seen, new, deleted, min_no, max_no, note),
    )
