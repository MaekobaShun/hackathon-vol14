from relay import app
from flask import render_template, request, redirect, url_for
from relay.db import DATABASE
import sqlite3
from relay.db import fetch_random_item
import uuid
from datetime import datetime

@app.route('/')
def index():
    con = sqlite3.connect(DATABASE)
    db_items = con.execute("SELECT * FROM ideas").fetchall()
    con.close()

    items = []

    for row in db_items:
        items.append({
            'title': row[1],
            'detail': row[2],
            'category': row[3],
        })

    return render_template(
        'index.html',
        items=items
    )

@app.route('/form')
def form():
    return render_template(
        'form.html'
    )

@app.route('/register', methods=['POST'])
def register():
    title = request.form['title']
    detail = request.form['detail']
    category = request.form['category']

    con = sqlite3.connect(DATABASE)
    idea_id = str(uuid.uuid4())
    user_id = ''  # 一時的に空文字列（後で認証機能を追加する場合に修正）
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    con.execute("INSERT INTO ideas VALUES (?, ?, ?, ?, ?, ?)", 
                [idea_id, title, detail, category, user_id, created_at])
    con.commit()
    con.close()

    return redirect(url_for('index'))

# ここからガチャ機能
@app.route('/gacha')
def gacha():
    return render_template("gacha.html")

# ランダムに1つのアイテムを表示するルート
@app.route('/result')
def result():
    item = fetch_random_item()
    return render_template("result.html", item=item)

# ガチャを回して結果ページにリダイレクトするルート
@app.route('/spin')
def spin():
    return redirect(url_for('result'))
# ここまでガチャ機能
