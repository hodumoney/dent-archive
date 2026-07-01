# -*- coding: utf-8 -*-
"""
HTML 파싱 + 치과 식별키 생성.

목록 컬럼 순서(스샷 기준): 번호 | 구분(구인/구직/양도) | 제목 | 작성자 | 날짜 | 조회수 | 추천 | 신고
식별키는 '작성자'(=치과 상호) 우선.
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
    if re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", raw):  # 시간만(오늘)
        return None
    m = re.search(r"(\d{2,4})[-./](\d{1,2})[-./](\d{1,2})", raw)
    if m:
        y, mo, d = m.groups()
        y = int(y) + (2000 if int(y) < 100 else 0)
        return f"{y:04d}-{int(mo):02d}-{int(d):02d}"
    return None


# ── 목록 파싱 ─────────────────────────────────────────────────
def _no_from_href(href):
    q = parse_qs(urlparse(href).query)
    for key in config.NO_QUERY_KEYS:
        if key in q and q[key] and q[key][0].isdigit():
            return int(q[key][0])
    m = re.search(r"(\d{3,})", urlparse(href).path)
    return int(m.group(1)) if m else None


def _is_date(s):
    return bool(re.search(r"\d{2,4}[-./]\d{1,2}[-./]\d{1,2}", s or ""))


def parse_list(html):
    """목록 HTML -> [{no,category,title,author,posted_raw,posted_at,views,url}, ...]"""
    soup = BeautifulSoup(html, "lxml")
    rows = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if config.VIEW_LINK_KEYWORD not in href and not re.search(r"\d{3,}", href):
            continue
        title = a.get_text(" ", strip=True)
        if not title or len(title) < 2:
            continue
        no = _no_from_href(href)

        tr = a.find_parent("tr")
        cells, title_idx = [], None
        if tr:
            tds = tr.find_all(["td", "th"])
            for i, td in enumerate(tds):
                cells.append(td.get_text(" ", strip=True))
                if td.find("a", href=True) is a or (a in td.find_all("a")):
                    title_idx = i

        # 글번호: href 우선, 없으면 제목 앞쪽 셀의 큰 정수
        if no is None:
            for c in cells[:title_idx or 0]:
                if re.fullmatch(r"\d{3,}", c):
                    no = int(c); break
        if no is None or no in seen:
            continue
        seen.add(no)

        category = author = posted_raw = None
        views = None
        if title_idx is not None:
            before = cells[:title_idx]
            after = cells[title_idx + 1:]
            for c in before:
                if c in config.CATEGORY_WORDS:
                    category = c
            # 제목 뒤 순서: 작성자, 날짜, 조회 ...
            date_pos = next((j for j, c in enumerate(after) if _is_date(c)), None)
            if date_pos is not None:
                posted_raw = after[date_pos]
                author = next((c for c in after[:date_pos] if c), None)
                for c in after[date_pos + 1:]:
                    if re.fullmatch(r"[\d,]+", c):
                        views = int(c.replace(",", "")); break
            else:
                author = next((c for c in after if c and not re.fullmatch(r"[\d,]+", c)), None)

        abs_url = urljoin(config.LIST_URL, href)
        rows.append({
            "no": no, "category": category, "title": title, "author": author,
            "posted_raw": posted_raw, "posted_at": parse_date(posted_raw),
            "views": views, "url": abs_url,
        })

    return rows


# ── 상세 파싱 ─────────────────────────────────────────────────
def parse_view(html):
    soup = BeautifulSoup(html, "lxml")
    for sel in config.VIEW_CONTENT_SELECTORS:
        el = soup.select_one(sel)
        if el:
            text = el.get_text("\n", strip=True)
            if len(text) > 20:
                return {"content": text}
    best = ""
    for tag in soup.find_all(["td", "div", "article", "section"]):
        text = tag.get_text("\n", strip=True)
        if len(text) > len(best):
            best = text
    return {"content": best}
