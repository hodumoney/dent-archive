# -*- coding: utf-8 -*-
"""
로그인 + 파서 튜닝 도우미.

  python inspect_site.py

- 로그인 시도 결과 출력
- 1페이지 HTML을 debug_list.html 로 저장
- 파서가 뽑아낸 결과(번호/구분/제목/작성자/날짜) 미리보기
- 첫 글 상세를 debug_view.html 로 저장
"""
import config
import parser
import scraper


def main():
    print("로그인 확인 중...")
    ok = scraper.ensure_login(verbose=True)
    if not ok:
        print("\n로그인에 실패했습니다. 다음을 확인하세요:")
        print("  - secret.py 의 아이디/비밀번호")
        print("  - config.LOGIN_URL_CANDIDATES (로그인 페이지 주소)")
        print("  - 로그인 페이지 HTML을 브라우저 개발자도구로 열어 form 필드명 확인")
        return

    print("\n목록 1페이지 요청 중...")
    html = scraper.fetch_list_page(1)
    with open("debug_list.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  -> debug_list.html 저장 ({len(html):,} chars)")

    rows = parser.parse_list(html)
    print(f"\n파서가 인식한 글: {len(rows)}건")
    for r in rows[:12]:
        print(f"  #{r['no']:>7} [{(r['category'] or '-'):<2}] {(r['title'] or '')[:30]:30} "
              f"| 작성자={r['author']} | {r['posted_raw']}")

    if not rows:
        print("\n⚠ 글을 못 읽었습니다. debug_list.html 의 <table>/<a> 구조를 보고")
        print("  config.py 의 VIEW_LINK_KEYWORD, NO_QUERY_KEYS 를 조정하세요.")
        return

    r0 = rows[0]
    print(f"\n첫 글 #{r0['no']} 상세 요청: {r0['url']}")
    vhtml = scraper.fetch_view(r0["url"])
    with open("debug_view.html", "w", encoding="utf-8") as f:
        f.write(vhtml)
    print(f"  -> debug_view.html 저장 ({len(vhtml):,} chars)")
    content = parser.parse_view(vhtml)["content"]
    print(f"  본문 길이: {len(content)}자")
    print(f"  본문 미리보기: {content[:150]}...")


if __name__ == "__main__":
    main()
