# -*- coding: utf-8 -*-
"""로그인 후 실제 목록/상세 HTML 구조 확인 (파서 교정용)."""
import config
import scraper
import parser
from bs4 import BeautifulSoup

ok = scraper.ensure_login(verbose=True)
print("로그인 결과:", ok)
if not ok:
    raise SystemExit(0)

html = scraper.fetch_list_page(1)
print("목록 HTML 길이:", len(html))
soup = BeautifulSoup(html, "lxml")
tables = sorted(soup.find_all("table"), key=lambda t: len(t.find_all("tr")), reverse=True)
print("표 개수:", len(tables))
if tables:
    rows = tables[0].find_all("tr")
    print("가장 큰 표의 행 수:", len(rows))
    print("===== 처음 5개 행 raw HTML =====")
    for i, tr in enumerate(rows[:5]):
        print(f"--- 행 {i} ---")
        print(str(tr)[:1000])

print("\n===== 현재 파서 결과(상위 5) =====")
prows = parser.parse_list(html)
print("인식 글수:", len(prows))
for r in prows[:5]:
    print("  no=", r["no"], "|구분:", r["category"],
          "|제목:", (r["title"] or "")[:24], "|작성자:", r["author"], "|url:", r["url"])

if prows:
    url = prows[0]["url"]
    print("\n상세 URL:", url)
    vhtml = scraper.fetch_view(url)
    print("상세 HTML 길이:", len(vhtml))
    vsoup = BeautifulSoup(vhtml, "lxml")
    for sel in config.VIEW_CONTENT_SELECTORS:
        el = vsoup.select_one(sel)
        if el:
            print("  본문 매칭 selector:", sel, "| 글자수:", len(el.get_text(strip=True)))
    print("===== 상세 HTML 앞 1200자 =====")
    print(vhtml[:1200])
