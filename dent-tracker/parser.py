# -*- coding: utf-8 -*-
"""
HTML 파싱 + 치과 식별키 + 지역 분류.

실제 목록 구조: 각 글이 <ul><li>번호</li><li>구분</li>
  <li><a href="list2content.php?num=..">제목</a></li>
  <li><a href="javascript:memo_id(..)">작성자(치과)</a></li>
  <li>날짜</li><li>조회</li>...</ul>
식별키는 '작성자'(치과 상호) 우선.
"""
import re
from urllib.parse import urlparse, parse_qs, urljoin

from bs4 import BeautifulSoup

import config

# ── 전화번호 (본문 보관/보조 표시용) ─────────────────────────
_PHONE_RE = re.compile(
    r"(?<!\d)(0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}|1[5678]\d{2}[-.\s]?\d{4})(?!\d)"
)


def extract_phone(text):
    if not text:
        return None, None
    for m in _PHONE_RE.finditer(text):
        raw = m.group(1)
        digits = re.sub(r"\D", "", raw)
        if 9 <= len(digits) <= 12:
            return digits, raw.strip()
    return None, None


# ── 지역 분류 (제목 앞 "○○도 △△시 |" 에서 추출) ─────────────
# 전체 시·도명을 우선 매칭 (광주광역시 vs 경기도 광주시 혼동 방지)
REGION_MAP = [
    ("서울", ["서울특별시", "서울시", "서울"]),
    ("경기", ["경기도", "경기"]),
    ("인천", ["인천광역시", "인천"]),
    ("부산", ["부산광역시", "부산"]),
    ("대구", ["대구광역시", "대구"]),
    ("광주", ["광주광역시"]),
    ("대전", ["대전광역시", "대전"]),
    ("울산", ["울산광역시", "울산"]),
    ("세종", ["세종특별자치시", "세종시", "세종"]),
    ("충북", ["충청북도", "충북"]),
    ("충남", ["충청남도", "충남"]),
    ("전남", ["전라남도", "전남"]),
    ("전북", ["전북특별자치도", "전라북도", "전북"]),
    ("경북", ["경상북도", "경북"]),
    ("경남", ["경상남도", "경남"]),
    ("강원", ["강원특별자치도", "강원도", "강원"]),
    ("제주", ["제주특별자치도", "제주도", "제주"]),
]
REGION_ORDER = [r[0] for r in REGION_MAP]


def region_of(title):
    """제목 앞부분에서 시·도를 뽑아 짧은 라벨로 반환. 없으면 None."""
    if not title:
        return None
    head = title.split("|")[0]
    for label, names in REGION_MAP:
        for n in names:
            if n in head:
                return label
    return None


# ── 작성자/상호 정규화 ────────────────────────────────────────
def normalize_author(author):
    if not author:
        return ""
    return re.sub(r"\s+", " ", author.strip())


_CLINIC_NAME_RE = re.compile(r"([가-힣A-Za-z0-9]{1,12}(?:치과|의원|병원|덴탈|dental))",
                             re.IGNORECASE)


def extract_clinic_name(text):
    if not text:
        return None
    m = _CLINIC_NAME_RE.search(text)
    return re.sub(r"\s", "", m.group(1)).lower() if m else None


def build_clinic_key(author, title, phone_digits=None):
    """치과 식별키. 작성자(상호) 우선 → 제목 속 상호 → 전화 → 제목."""
    a = normalize_author(author)
    if a and a not in config.GENERIC_AUTHORS:
        return "author:" + a, "author"
    name = extract_clinic_name(title) or extract_clinic_name(author)
    if name and len(name) >= 3:
        return "clinic:" + name, "clinic"
    if phone_digits:
        return "phone:" + phone_digits, "phone"
    return "title:" + re.sub(r"[^0-9a-z가-힣]", "", (title or "unknown").lower()), "title"


# ── 날짜 파싱 ─────────────────────────────────────────────────
def parse_date(raw):
    if not raw:
        return None
    raw = raw.strip()
    if re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", raw):
        return None
    m = re.search(r"(\d{2,4})[-./](\d{1,2})[-./](\d{1,2})", raw)
    if m:
        y, mo, d = m.groups()
        y = int(y) + (2000 if int(y) < 100 else 0)
        return f"{y:04d}-{int(mo):02d}-{int(d):02d}"
    return None


# ── 목록 파싱 (<ul><li> 구조) ─────────────────────────────────
def parse_list(html):
    """목록 HTML -> [{no,category,title,author,posted_raw,posted_at,views,url,region}, ...]"""
    soup = BeautifulSoup(html, "lxml")
    rows = []
    seen = set()

    for a in soup.select('a[href*="list2content.php"]'):
        href = a.get("href", "")
        m = re.search(r"num=(\d+)", href)
        if not m:
            continue
        no = int(m.group(1))
        if no in seen:
            continue
        title = a.get_text(" ", strip=True)
        if not title:
            continue
        seen.add(no)

        ul = a.find_parent("ul")
        lis = ul.find_all("li") if ul else []
        texts = [li.get_text(" ", strip=True) for li in lis]

        category = next((t for t in texts if t in config.CATEGORY_WORDS), None)
        author = None
        if ul:
            am = ul.find("a", href=lambda h: h and "memo_id" in h)
            if am:
                author = am.get_text(strip=True)
        posted_raw = next((t for t in texts if re.search(r"\d{4}-\d{1,2}-\d{1,2}", t)), None)
        views = None
        for t in texts:
            if re.fullmatch(r"[\d,]+", t) and t.replace(",", "") != str(no):
                views = int(t.replace(",", ""))

        rows.append({
            "no": no,
            "category": category,
            "title": title,
            "author": author,
            "posted_raw": posted_raw,
            "posted_at": parse_date(posted_raw),
            "views": views,
            "url": urljoin(config.LIST_URL, href),
            "region": region_of(title),
        })

    return rows


# ── 상세 파싱 (본문 텍스트 추출) ──────────────────────────────
def parse_view(html):
    """content.php 에서 실제 본문(board_content_view)만 추출."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    body_el = (soup.select_one(".board_content_view")
               or soup.select_one("#qcontents"))
    if body_el:
        text = body_el.get_text("\n", strip=True)
        import re as _re
        text = _re.sub(r"[ \t]{2,}", " ", text)
        if len(text) > 5:
            return {"content": text}

    # 폴백: 지정 selector → 링크 적고 텍스트 많은 블록
    for sel in config.VIEW_CONTENT_SELECTORS:
        el = soup.select_one(sel)
        if el:
            t = el.get_text("\n", strip=True)
            if len(t) > 20:
                return {"content": t}
    best = ""
    for tag in soup.find_all(["td", "div", "article", "section", "p"]):
        links = sum(len(a.get_text(strip=True)) for a in tag.find_all("a"))
        t = tag.get_text("\n", strip=True)
        if links > len(t) * 0.5:
            continue
        if len(t) > len(best):
            best = t
    return {"content": best}
