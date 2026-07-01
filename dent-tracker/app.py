# -*- coding: utf-8 -*-
"""
아카이브 뷰어 (Flask).

  python app.py    →  http://127.0.0.1:5000

화면:
  /            반복 치과 랭킹 (게시→삭제→재게시 타임라인)
  /posts       전체/삭제 게시글 목록
  /post/<no>   글 상세 (삭제된 글 포함)
"""
from flask import Flask, render_template, request, abort

import analyze
import db

app = Flask(__name__)


@app.template_filter("shortdt")
def shortdt(s):
    if not s:
        return "-"
    return str(s).replace("T", " ")[:16]


@app.route("/")
def home():
    groups = analyze.clinic_groups(min_posts=2)
    return render_template("clinics.html", groups=groups, s=analyze.summary())


@app.route("/posts")
def posts():
    status = request.args.get("status", "all")
    search = request.args.get("q", "").strip() or None
    rows = analyze.all_posts(status=status, search=search)
    return render_template("posts.html", rows=rows, status=status,
                           search=search or "", s=analyze.summary())


@app.route("/post/<int:no>")
def post_detail(no):
    with db.get_db() as conn:
        row = db.get_post(conn, no)
    if not row:
        abort(404)
    # 같은 치과의 다른 글
    siblings = []
    for g in analyze.clinic_groups(min_posts=1, include_singletons=True):
        if g["key"] == row["clinic_key"]:
            siblings = g["posts"]
            break
    return render_template("post_detail.html", p=row, siblings=siblings)


if __name__ == "__main__":
    db.init_db()
    app.run(debug=True, port=5000)
