# -*- coding: utf-8 -*-
"""HTTP 요청 계층 — 로그인 세션 + 한국어 인코딩 자동감지 + 요청 간 대기."""
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
    """EUC-KR / CP949 / UTF-8 자동 디코딩."""
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


# ── 로그인 ───────────────────────────────────────────────────
def _find_login_form(html, page_url):
    """비밀번호 입력이 있는 <form> 을 찾아 (action, method, data, id필드, pw필드) 반환."""
    soup = BeautifulSoup(html, "lxml")
    for form in soup.find_all("form"):
        pw = form.find("input", {"type": "password"})
        if not pw or not pw.get("name"):
            continue
        action = urljoin(page_url, form.get("action") or page_url)
        method = (form.get("method") or "post").lower()
        data = {}
        id_field = None
        for inp in form.find_all("input"):
            name = inp.get("name")
            if not name:
                continue
            data[name] = inp.get("value", "") or ""
            itype = (inp.get("type") or "text").lower()
            if id_field is None and itype in ("text", "email", "id"):
                id_field = name
        return action, method, data, id_field, pw.get("name")
    return None


def _looks_logged_in(html):
    """목록에 글 행이 보이면 로그인 성공으로 간주."""
    import parser  # 지연 import (순환 방지)
    return len(parser.parse_list(html)) > 0


def ensure_login(verbose=True):
    """세션에 로그인. 이미 목록이 보이면 건너뜀."""
    global _logged_in
    if _logged_in or not config.LOGIN_ENABLED:
        return True

    # 1) 이미 볼 수 있으면 로그인 불필요
    list_html = _decode(_get(config.LIST_URL, params={config.PAGE_PARAM: 1, **config.LIST_PARAMS}))
    if _looks_logged_in(list_html):
        if verbose:
            print("[login] 로그인 없이도 목록이 보입니다.")
        _logged_in = True
        return True

    # 2) 로그인 폼 찾기 — 후보 URL 들을 순회
    found = _find_login_form(list_html, config.LIST_URL)
    login_page = config.LIST_URL
    if not found:
        for url in config.LOGIN_URL_CANDIDATES:
            try:
                html = _decode(_get(url))
            except Exception:
                continue
            f = _find_login_form(html, url)
            if f:
                found, login_page = f, url
                break
    if not found:
        print("[login] 로그인 폼을 찾지 못했습니다. inspect_site.py 로 로그인 페이지 HTML을 "
              "확인하고 config.LOGIN_URL_CANDIDATES 를 조정하세요.")
        return False

    action, method, data, id_field, pw_field = found
    id_field = config.LOGIN_ID_FIELD or id_field
    pw_field = config.LOGIN_PW_FIELD or pw_field
    if not id_field or not pw_field:
        print(f"[login] 폼 필드 자동감지 실패 (id={id_field}, pw={pw_field}). "
              "config.LOGIN_ID_FIELD / LOGIN_PW_FIELD 를 지정하세요.")
        return False

    data[id_field] = config.LOGIN_ID
    data[pw_field] = config.LOGIN_PW
    if verbose:
        print(f"[login] 로그인 시도: {action} (id필드={id_field})")

    _session.headers["Referer"] = login_page
    if method == "get":
        _session.get(action, params=data, timeout=config.REQUEST_TIMEOUT)
    else:
        _session.post(action, data=data, timeout=config.REQUEST_TIMEOUT)
    time.sleep(config.REQUEST_DELAY_SEC)

    # 3) 검증
    check = _decode(_get(config.LIST_URL, params={config.PAGE_PARAM: 1, **config.LIST_PARAMS}))
    if _looks_logged_in(check):
        print("[login] 로그인 성공.")
        _logged_in = True
        return True
    print("[login] 로그인 후에도 목록이 안 보입니다. 아이디/비번 또는 폼 필드명을 확인하세요.")
    return False


# ── 페이지 요청 ───────────────────────────────────────────────
def fetch_list_page(page):
    ensure_login()
    params = dict(config.LIST_PARAMS)
    params[config.PAGE_PARAM] = page
    return _decode(_get(config.LIST_URL, params=params))


def fetch_view(url):
    ensure_login()
    return _decode(_get(url))
