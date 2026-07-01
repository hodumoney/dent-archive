# -*- coding: utf-8 -*-
"""
데모 데이터 넣기 — 실제 크롤 전에 대시보드 모습을 미리 보고 싶을 때.

  python seed_demo.py
  python app.py

주의: 가짜 데이터입니다. 실제 사용 전 dent_tracker.db 를 지우고 crawl.py 를 돌리세요.
"""
import parser
import db

# (번호, 구분, 제목, 작성자(치과), 게시일, 삭제여부)
SAMPLE = [
    (234400, "구인", "서울특별시 강남구 | 수술보철 원장님 모십니다", "석플란트치과병원", "2026-06-12", True),
    (234512, "구인", "강남 석플란트 수술 원장님 재모집합니다", "석플란트치과병원", "2026-06-22", True),
    (234595, "구인", "서울특별시 강남구 | 근무협의, 최고대우 수술보철 원장님", "석플란트치과병원", "2026-06-30", False),
    (234410, "구인", "광주 북구 소재 치과 부원장님 모십니다", "제이플치과의원", "2026-06-13", True),
    (234605, "구인", "광주광역시 북구 | 광주 북구 소재 치과 부원장님", "제이플치과의원", "2026-06-30", False),
    (234480, "구인", "대구 킹플란트치과 수술원장님 모십니다", "킹플란트치과", "2026-06-18", True),
    (234603, "구인", "대구광역시 달서구 | 대구 킹플란트치과 수술원장님", "킹플란트치과", "2026-06-30", False),
    (234590, "구인", "광주광역시 서구 | 매주 일요일 파트타임 원장님", "튼튼이치과의원", "2026-06-29", False),
    (234582, "구인", "충청남도 서산시 | 서산 트라닉스 성연,지곡 공장 출장검진", "파인트리치과의원", "2026-06-29", False),
]


def main():
    db.init_db()
    with db.get_db() as conn:
        for no, cat, title, author, date, deleted in SAMPLE:
            if db.get_post(conn, no):
                continue
            key, kind = parser.build_clinic_key(author, title)
            db.insert_post(conn, dict(
                no=no, category=cat, title=title, author=author, posted_raw=date,
                posted_at=parser.parse_date(date), views=0,
                url=f"https://board.dentphoto.com/recruit_dental/view.php?no={no}",
                content=f"[데모] {title}\n자세한 내용은 원본 링크를 참고하세요.",
                phone=None, phone_display=None,
                clinic_key=key, key_kind=kind,
                title_sig=parser.normalize_author(author),
            ))
            if deleted:
                db.mark_deleted(conn, [no])
        db.log_run(conn, len(SAMPLE), len(SAMPLE), 4, 234400, 234605, note="demo seed")
    print("데모 데이터 입력 완료. python app.py 로 확인하세요.")
    print("실사용 전 dent_tracker.db 를 지우고 crawl.py 를 돌리세요.")


if __name__ == "__main__":
    main()
