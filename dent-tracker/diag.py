# -*- coding: utf-8 -*-
"""상세 페이지(본문) 구조 확인 — 본문 추출 교정용."""
import config
import scraper
import parser
from bs4 import BeautifulSoup

ok = scraper.ensure_login(verbose=True)
print("로그인:", ok)
if not ok:
    raise SystemExit(0)

html = scraper.fetch_list_page(1)
rows = parser.parse_list(html)
print("목록 글수:", len(rows))
if not rows:
    raise SystemExit(0)

url = rows[0]["url"]
print("상세 URL:", url)
vhtml = scraper.fetch_view(url)
print("상세 HTML 길이:", len(vhtml))

soup = BeautifulSoup(vhtml, "lxml")
for t in soup(["script", "style", "noscript"]):
    t.decompose()

print("\n=== 텍스트 많은 블록 상위 12개 (본문 후보) ===")
cands = []
for el in soup.find_all(["div", "td", "table", "article", "section", "p", "pre"]):
    txt = el.get_text(" ", strip=True)
    links = sum(len(a.get_text(strip=True)) for a in el.find_all("a"))
    cands.append((len(txt), links, el))
cands.sort(key=lambda x: -x[0])
n = 0
for tlen, links, el in cands:
    if tlen < 20:
        continue
    print(f"  <{el.name} id={el.get('id')} class={el.get('class')}> 글자={tlen} 링크글자={links}")
    print("     ", el.get_text(' ', strip=True)[:110])
    n += 1
    if n >= 12:
        break

print("\n=== 상세 HTML 앞 2500자 ===")
print(vhtml[:2500])
