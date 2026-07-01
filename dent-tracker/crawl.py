# -*- coding: utf-8 -*-
"""
매일 실행하는 크롤 작업.

  python crawl.py

동작:
  1) 앞쪽 N페이지 목록 수집
  2) 신규 글은 상세까지 받아 전화번호/식별키 저장
  3) 순번 공백(gap) 으로 삭제된 글 감지 → is_deleted 표시 (기록은 유지)
"""
import sys
import traceback

import config
import db
import parser
import scraper


def run_crawl(verbose=True):
    db.init_db()
    if not scraper.ensure_login(verbose=verbose):
        print("[error] 로그인 실패로 중단합니다.")
        return
    present = {}   # no -> list row dict (이번 크롤에서 실제로 보인 글)

    for page in range(1, config.PAGES_TO_CRAWL + 1):
        try:
            html = scraper.fetch_list_page(page)
        except Exception as e:
            print(f"[warn] {page}페이지 요청 실패: {e}")
            continue
        rows = parser.parse_list(html)
        if verbose:
            print(f"  {page}페이지: 글 {len(rows)}건")
        for r in rows:
            present[r["no"]] = r

    if not present:
        print("[error] 목록에서 글을 하나도 못 읽었습니다. "
              "inspect_site.py 로 실제 HTML을 확인하고 config/parser 를 조정하세요.")
        with db.get_db() as conn:
            db.log_run(conn, 0, 0, 0, 0, 0, note="목록 파싱 실패")
        return

    present_nos = set(present)
    lo, hi = min(present_nos), max(present_nos)

    new_count = 0
    with db.get_db() as conn:
        # 1) 신규/기존 처리
        for no, r in sorted(present.items()):
            existing = db.get_post(conn, no)
            if existing:
                db.touch_seen(conn, no)
                continue
            # 신규 → 상세 받아 본문 보관(+전화번호 보조 추출)
            content = None
            if config.FETCH_DETAIL and r.get("url"):
                try:
                    vhtml = scraper.fetch_view(r["url"])
                    content = parser.parse_view(vhtml).get("content")
                except Exception as e:
                    print(f"[warn] 상세 {no} 실패: {e}")
            phone_digits, phone_disp = parser.extract_phone(
                (content or "") + " " + (r.get("title") or "")
            )
            key, kind = parser.build_clinic_key(r.get("author"), r.get("title"), phone_digits)
            r.update({
                "content": content,
                "phone": phone_digits,
                "phone_display": phone_disp,
                "clinic_key": key,
                "key_kind": kind,
                "title_sig": parser.normalize_author(r.get("author")),
            })
            db.insert_post(conn, r)
            new_count += 1
            if verbose:
                print(f"  + 신규 #{no} [{r.get('category') or '-'}] {r['title'][:26]}  "
                      f"→ {r.get('author') or '?'}")

        # 2) 삭제 감지 — [lo,hi] 안에서 우리가 살아있다고 알던 글이 이번에 안 보이면 공백=삭제
        known_alive = db.active_nos_in_range(conn, lo, hi)
        gone = sorted(known_alive - present_nos)
        db.mark_deleted(conn, gone)
        if verbose and gone:
            print(f"  ! 삭제 감지: {gone}")

        db.log_run(conn, len(present_nos), new_count, len(gone), lo, hi)

    print(f"[완료] 발견 {len(present_nos)} / 신규 {new_count} / 삭제감지 {len(gone)} "
          f"(글번호 {lo}~{hi})")


if __name__ == "__main__":
    try:
        run_crawl()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
