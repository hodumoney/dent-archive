# -*- coding: utf-8 -*-
"""HTTP 요청 계층 — 로그인 세션 + 한국어 인코딩 자동감지 + 요청 간 대기."""
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import config

_session = requests.Session()
_session.headers.update({
    "User-Agent": config.USER_AGENT,
    "Referer": config.BASE_URL + "/list.php",
    "Accept-Language": "ko-KR,ko;q=0.9",
})
_logged_in = False


def _decode(resp):
    raw = resp.content
    ct = resp.headers.get("Content-Type", "").lower()
    for enc in ("utf-8", "euc-kr", "cp949"):
        if enc in ct:
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                pass
    head = raw[:2000].decode("ascii", "ignore").lower()
    if "euc-kr" in head or "ks_c_5601" in head:
        try:
            return raw.decode("euc-kr")
        except UnicodeDecodeError:
            return raw.decode("cp949", "replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp949", "replace")


def _get(url, params=None):
    resp = _session.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    time.sleep(config.REQUEST_DELAY_SEC)
    return resp


def _js_redirect(html):
    """document.location.href='...' / location.replace('...') 같은 JS 이동 주소."""
    m = (re.search(r"location\.(?:href\s*=|replace\s*\()\s*['\"]([^'\"]+)['\"]", html)
         or re.search(r"<meta[^>]+url=([^'\">\s]+)", html, re.I))
    return m.group(1) if m else None


def _find_login_redirect(html):
    """JS 리디렉션(로그인 페이지로 튕김) 주소 추출."""
    m = (re.search(r"location\.replace\(['\"]([^'\"]+)['\"]\)", html)
         or re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", html)
         or re.search(r"<meta[^>]+url=([^'\">\s]+)", html, re.I))
    return m.group(1) if m else None


def _find_login_form(html, page_url):
    """비밀번호 입력이 있는 form 을 찾아 (action, method, data, id필드, pw필드) 반환."""
    soup = BeautifulSoup(html, "lxml")
    for form in soup.find_all("form"):
        pw = form.find("input", {"type": "password"})
        if not pw or not pw.get("name"):
            continue
        action = urljoin(page_url, form.get("action") or page_url)
        method = (form.get("method") or "post").lower()
        data, id_field = {}, None
        for inp in form.find_all("input"):
            name = inp.get("name")
            if not name:
                continue
            data[name] = inp.get("value", "") or ""
            itype = (inp.get("type") or "text").lower()
            if id_field is None and itype in ("text", "email", "id", "tel"):
                id_field = name
        return action, method, data, id_field, pw.get("name")
    return None


def _looks_logged_in(html):
    import parser
    return len(parser.parse_list(html)) > 0


def ensure_login(verbose=True):
    global _logged_in
    if _logged_in or not config.LOGIN_ENABLED:
        return True

    list_html = _decode(_get(config.LIST_URL, params={config.PAGE_PARAM: 1, **config.LIST_PARAMS}))
    if _looks_logged_in(list_html):
        if verbose:
            print("[login] 로그인 없이도 목록이 보입니다.")
        _logged_in = True
        return True

    # 로그인 페이지 찾기: JS 리디렉션 우선, 실패 시 후보 URL
    login_page = _find_login_redirect(list_html)
    if login_page:
        login_page = urljoin(config.LIST_URL, login_page)
        print("[login] 발견한 로그인 주소:", login_page)
    found = None
    if login_page:
        try:
            found = _find_login_form(_decode(_get(login_page)), login_page)
        except Exception as e:
            print("[login] 로그인 페이지 요청 실패:", repr(e))
    if not found:
        for url in config.LOGIN_URL_CANDIDATES:
            try:
                f = _find_login_form(_decode(_get(url)), url)
            except Exception:
                continue
            if f:
                found, login_page = f, url
                break
    if not found:
        print("[login] 로그인 폼을 찾지 못했습니다. (로그인 주소:", login_page, ")")
        return False

    action, method, data, id_field, pw_field = found
    id_field = config.LOGIN_ID_FIELD or id_field
    pw_field = config.LOGIN_PW_FIELD or pw_field
    print(f"[login] 폼 발견 → action={action} method={method} "
          f"id칸={id_field} pw칸={pw_field} 전체칸={list(data)}")
    if not id_field or not pw_field:
        print("[login] 아이디/비번 칸 자동감지 실패. config 에서 지정 필요.")
        return False
    if not config.LOGIN_ID or not config.LOGIN_PW:
        print("[login] 아이디/비번이 비었습니다. GitHub Secrets(DENT_ID/DENT_PW) 확인.")
        return False

    data[id_field] = config.LOGIN_ID
    data[pw_field] = config.LOGIN_PW
    _session.headers["Referer"] = login_page
    if method == "get":
        _session.get(action, params=data, timeout=config.REQUEST_TIMEOUT)
    else:
        _session.post(action, data=data, timeout=config.REQUEST_TIMEOUT)
    time.sleep(config.REQUEST_DELAY_SEC)

    check = _decode(_get(config.LIST_URL, params={config.PAGE_PARAM: 1, **config.LIST_PARAMS}))
    if _looks_logged_in(check):
        print("[login] 로그인 성공! 목록을 읽습니다.")
        _logged_in = True
        return True
    print("[login] 로그인 후에도 목록이 안 보입니다. (다시 로그인으로 이동:",
          _find_login_redirect(check), ")")
    print("[login] 응답 앞부분:", check[:300])
    return False


def fetch_list_page(page):
    ensure_login()
    params = dict(config.LIST_PARAMS)
    params[config.PAGE_PARAM] = page
    return _decode(_get(config.LIST_URL, params=params))


def fetch_view(url):
    ensure_login()
    html = _decode(_get(url))
    # list2content.php → content.php 처럼 JS로 넘기는 페이지를 따라간다 (최대 3회)
    for _ in range(3):
        red = _js_redirect(html)
        if not red or "login" in red.lower():
            break
        url = urljoin(url, red)
        html = _decode(_get(url))
    return html
