# -*- coding: utf-8 -*-
"""로그인 페이지의 폼 구조까지 확인하는 진단 (2단계)."""
import re
import config
config.LOGIN_ENABLED = False
import scraper
from bs4 import BeautifulSoup


def get(url):
    r = scraper._session.get(url, timeout=20)
    return r, scraper._decode(r)


# 1) 목록 요청 → 로그인 페이지로 튕기는 JS 주소 추출
r, html = get(config.LIST_URL + "?gotopage=1&code=")
print("목록 상태코드:", r.status_code, "| 길이:", len(html))
m = (re.search(r"location\.replace\(['\"]([^'\"]+)['\"]\)", html)
     or re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", html))
login_url = m.group(1) if m else None
print("발견한 로그인 주소:", login_url)

# 2) 로그인 페이지 폼 구조 확인
if login_url:
    lr, lhtml = get(login_url)
    print("로그인페이지 상태코드:", lr.status_code, "| 길이:", len(lhtml))
    lsoup = BeautifulSoup(lhtml, "lxml")
    forms = lsoup.find_all("form")
    print("폼 개수:", len(forms))
    for i, f in enumerate(forms):
        print(f"--- 폼 {i}: action={f.get('action')} method={f.get('method')}")
        for inp in f.find_all(["input", "select", "button"]):
            print("     ", inp.name, "| name=", inp.get("name"),
                  "| type=", inp.get("type"), "| value=", (inp.get("value") or "")[:20])
    print("========== 로그인페이지 HTML 앞부분 2000자 ==========")
    print(lhtml[:2000])
else:
    print("로그인 주소를 못 찾음. 아래 목록 HTML 확인:")
    print(html[:1000])
