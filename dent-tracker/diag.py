# -*- coding: utf-8 -*-
"""작성자(memo_id) 링크 주변의 실제 게시글 행 구조 덤프 (v5)."""
import config
import scraper
from bs4 import BeautifulSoup

ok = scraper.ensure_login(verbose=True)
print("로그인 결과:", ok)
if not ok:
    raise SystemExit(0)

html = scraper.fetch_list_page(1)
print("목록 HTML 길이:", len(html))
soup = BeautifulSoup(html, "lxml")

memo = [a for a in soup.find_all("a", href=True) if "memo_id" in a["href"]]
print("memo_id 링크 수:", len(memo))


def row_ancestor(a):
    node = a
    for _ in range(7):
        p = node.parent
        if p is None:
            break
        if len(p.get_text(" ", strip=True)) > 40:
            return p
        node = p
    return a.parent


# 작성자 링크 3개의 '행 컨테이너' 전체 HTML
for i, a in enumerate(memo[2:5]):
    anc = row_ancestor(a)
    print(f"\n===== 행 {i} (작성자 '{a.get_text(strip=True)[:22]}', 컨테이너=<{anc.name}>) =====")
    print(str(anc)[:1800])

# 원본 HTML에서 첫 memo_id 앞뒤 통째로 (구조 파악 보조)
idx = html.find("memo_id")
if idx > 0:
    print("\n===== 원본 HTML: 첫 memo_id 앞 1000 ~ 뒤 300자 =====")
    print(html[max(0, idx - 1000):idx + 300])
