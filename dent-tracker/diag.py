# -*- coding: utf-8 -*-
"""content.php 본문이 실제로 추출되는지 확인 (redirect 따라간 뒤)."""
import config
import scraper
import parser
from bs4 import BeautifulSoup

ok = scraper.ensure_login(verbose=True)
print("로그인:", ok)
if not ok:
    raise SystemExit(0)

rows = parser.parse_list(scraper.fetch_list_page(1))
# 공지용 더미(num 작음) 말고, 작성자 있는 진짜 글 하나 고르기
real = next((r for r in rows if r.get("author") and r["no"] > 1000), rows[0])
print("고른 글:", real["no"], "|", (real["title"] or "")[:30], "| 작성자:", real["author"])
print("상세 URL:", real["url"])

vhtml = scraper.fetch_view(real["url"])   # redirect 자동 추적
print("최종 상세 HTML 길이:", len(vhtml))

content = parser.parse_view(vhtml).get("content", "")
print("추출된 본문 길이:", len(content))
print("본문 미리보기:\n", content[:300])

print("\n=== content.php 본문 후보 블록 상위 8개 ===")
soup = BeautifulSoup(vhtml, "lxml")
for t in soup(["script", "style", "noscript"]):
    t.decompose()
cands = []
for el in soup.find_all(["div", "td", "table", "article", "section", "p", "pre"]):
    txt = el.get_text(" ", strip=True)
    links = sum(len(a.get_text(strip=True)) for a in el.find_all("a"))
    cands.append((len(txt), links, el))
cands.sort(key=lambda x: -x[0])
n = 0
for tlen, links, el in cands:
    if tlen < 15:
        continue
    print(f"  <{el.name} id={el.get('id')} class={el.get('class')}> 글자={tlen} 링크={links}")
    print("     ", el.get_text(' ', strip=True)[:100])
    n += 1
    if n >= 8:
        break
