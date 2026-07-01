# -*- coding: utf-8 -*-
"""서버에서 게시판 목록이 실제로 어떻게 보이는지 진단."""
import config
config.LOGIN_ENABLED = False
import scraper
import parser
from bs4 import BeautifulSoup

print("요청 주소:", config.LIST_URL, config.LIST_PARAMS)
try:
    r = scraper._session.get(
        config.LIST_URL,
        params={config.PAGE_PARAM: 1, **config.LIST_PARAMS},
        timeout=20,
    )
    print("HTTP 상태코드:", r.status_code)
    print("최종 도착 주소:", r.url)
    html = scraper._decode(r)
except Exception as e:
    print("요청 중 오류:", repr(e))
    raise SystemExit(0)

print("받은 HTML 길이:", len(html), "자")
soup = BeautifulSoup(html, "lxml")
print("링크(a):", len(soup.find_all("a")),
      "/ 표(table):", len(soup.find_all("table")),
      "/ 행(tr):", len(soup.find_all("tr")),
      "/ 입력폼(form):", len(soup.find_all("form")))
pw = soup.find("input", {"type": "password"})
print("비밀번호 입력칸 존재:", bool(pw))
for f in soup.find_all("form"):
    names = [i.get("name") for i in f.find_all("input") if i.get("name")]
    print("  form action=", f.get("action"), "method=", f.get("method"), "inputs=", names)

rows = parser.parse_list(html)
print("파서가 인식한 글 수:", len(rows))
for x in rows[:6]:
    print("   글", x["no"], "|", x.get("category"), "|",
          (x.get("title") or "")[:20], "| 작성자:", x.get("author"))

print("========== HTML 앞부분 1500자 ==========")
print(html[:1500])
