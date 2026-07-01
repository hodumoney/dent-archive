# -*- coding: utf-8 -*-
"""
설정 파일 — 실제 게시판에 맞춰 여기만 수정하면 됩니다.

파싱/로그인이 안 맞으면:
  1) python inspect_site.py  로 로그인 시도 + 실제 HTML을 debug_*.html 로 저장
  2) 콘솔 출력과 저장된 HTML을 보고 아래 값을 조정
"""
import secret  # 로그인 정보 (secret.py, .gitignore 처리됨)

# ── 대상 게시판 ───────────────────────────────────────────────
SITE_ROOT = "https://board.dentphoto.com"
BASE_URL = SITE_ROOT + "/recruit_dental"
LIST_URL = BASE_URL + "/list.php"          # 목록 페이지
LIST_PARAMS = {"code": ""}                 # 고정 쿼리 파라미터
PAGE_PARAM = "gotopage"                     # 페이지 번호 파라미터 이름
PAGES_TO_CRAWL = 20                          # 매 실행 시 앞에서 몇 페이지까지 볼지

# ── 로그인 ────────────────────────────────────────────────────
LOGIN_ENABLED = True
LOGIN_ID = secret.LOGIN_ID
LOGIN_PW = secret.LOGIN_PW
# 로그인 폼이 있는 페이지 후보 (위에서부터 시도, 자동탐지 실패 시 사용).
# inspect_site.py 가 실제 URL을 알려주면 맨 앞에 넣어주세요.
LOGIN_URL_CANDIDATES = [
    SITE_ROOT + "/login.php",
    SITE_ROOT + "/member/login.php",
    SITE_ROOT + "/bbs/login.php",
    BASE_URL + "/login.php",
    SITE_ROOT + "/login_form.php",
]
# 폼 필드 이름을 자동탐지하지만, 틀리면 여기서 강제 지정 (예: "mb_id", "mb_password")
LOGIN_ID_FIELD = None
LOGIN_PW_FIELD = None

# ── 상세글 수집 ───────────────────────────────────────────────
# 목록의 실제 링크(href)를 그대로 사용합니다. 삭제글 본문 보관을 위해 권장.
FETCH_DETAIL = True

# ── HTTP 매너 (서버 부담 최소화) ──────────────────────────────
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
REQUEST_DELAY_SEC = 1.5      # 요청 사이 대기 (서버 예의)
REQUEST_TIMEOUT = 20

# ── 저장 ──────────────────────────────────────────────────────
DB_PATH = "dent_tracker.db"

# ── 파싱 힌트 ─────────────────────────────────────────────────
# 상세 링크로 인식할 문자열 (목록 <a> href 에 포함된 것)
VIEW_LINK_KEYWORD = "view.php"
NO_QUERY_KEYS = ["no", "number", "wr_id", "idx", "uid"]  # 글 번호가 담긴 쿼리 키 후보
CATEGORY_WORDS = ["구인", "구직", "양도"]                  # 구분 칸 값

# 상세 페이지 본문 영역 추정 selector (위에서부터 시도)
VIEW_CONTENT_SELECTORS = [
    "#view_content", ".view_content", "#content", ".content",
    ".board_view", ".view", ".view_con", "td.content", "#bo_v_con",
]

# 작성자로 흔히 쓰이는 일반 표현 (식별 보조용)
GENERIC_AUTHORS = {"관리자", "admin", "익명", "-", ""}
