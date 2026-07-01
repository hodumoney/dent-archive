# -*- coding: utf-8 -*-
"""
로그인 정보 — GitHub 방식에서는 여기에 비밀번호를 적지 않습니다.
GitHub 저장소의 Secrets(금고)에 DENT_ID / DENT_PW 로 넣으면, 실행 시 자동으로 읽힙니다.
(로컬에서 직접 돌릴 때만 아래 환경변수를 미리 설정하면 됩니다.)
"""
import os

LOGIN_ID = os.environ.get("DENT_ID", "")
LOGIN_PW = os.environ.get("DENT_PW", "")
