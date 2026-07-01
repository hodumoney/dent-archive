# -*- coding: utf-8 -*-
"""로그인 후 실제 게시글 행/링크 구조 확인 (파서 교정용 v4)."""
import re
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

# [A] 진짜 제목 링크 후보 (view.php / read)
view_links = [a for a in soup.find_all("a", href=True)
              if "view.php" in a["href"] or "read" in a["href"].lower()]
print("\n[A] view/read 링크 수:", len(view_links))
for a in view_links[:6]:
    print("   href=", a["href"][:90], "| text=", a.get_text(strip=True)[:34])

# [B] 작성자(memo_id) 링크의 부모 행 전체 HTML = 실제 게시글 한 줄
memo = [a for a in soup.find_all("a", href=True) if "memo_id" in a["href"]]
print("\n[B] memo_id(작성자) 링크 수:", len(memo))
seen = 0
for a in memo:
    tr = a.find_parent("tr")
    if tr is not None and seen < 3:
        print(f"--- 게시글 행 {seen} 전체 HTML ---")
        print(str(tr)[:1600])
        seen += 1

# [C] 숫자 쿼리를 가진 링크 패턴
print("\n[C] 숫자 쿼리 링크 샘플:")
cnt = 0
for a in soup.find_all("a", href=True):
    h = a["href"]
    if re.search(r"(no|number|idx|wr_id|uid)=\d+", h):
        print("   ", h[:100], "| text=", a.get_text(strip=True)[:24])
        cnt += 1
        if cnt >= 8:
            break
print("   찾은 개수:", cnt)
