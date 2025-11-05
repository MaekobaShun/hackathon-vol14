from relay import app
from flask import render_template, request, redirect, url_for
from relay.db import DATABASE
import sqlite3
from relay.db import fetch_random_item

@app.route('/')
def index():
    con = sqlite3.connect(DATABASE)
    db_items = con.execute("SELECT idea_id, title, detail, category, user_id, created_at FROM idea ORDER BY created_at DESC").fetchall()
    con.close()

    items = []

    for row in db_items:
        items.append({
            'idea_id': row[0],
            'title': row[1],
            'detail': row[2],
            'category': row[3],
            'user_id': row[4],
            'created_at': row[5]
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
    con.execute("INSERT INTO ideas VALUES (?, ?, ?)", [title, detail, category])
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

# マイページ
@app.route('/mypage')
def mypage():
    # テスト用：user_id = 'test_user_001' で固定
    # 実際の実装では、セッションからuser_idを取得
    user_id = 'user_001'
    
    con = sqlite3.connect(DATABASE)
    
    # ユーザー情報を取得
    user_row = con.execute(
        "SELECT user_id, nickname, email, icon_path, created_at FROM mypage WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    
    if not user_row:
        # ユーザーが存在しない場合はダミーデータを返す（開発用）
        user = {
            'user_id': user_id,
            'nickname': 'テストユーザー',
            'email': 'test@example.com',
            'icon_path': None,
            'created_at': '2024-01-01 00:00:00'
        }
        ideas = []
        gacha_results = []
        revival_notifications = []
    else:
        user = {
            'user_id': user_row[0],
            'nickname': user_row[1],
            'email': user_row[2],
            'icon_path': user_row[3],
            'created_at': user_row[4]
        }
        
        # ユーザーが投稿したアイデアを取得
        idea_rows = con.execute(
            "SELECT idea_id, title, detail, category, created_at FROM idea WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        
        ideas = []
        for row in idea_rows:
            ideas.append({
                'idea_id': row[0],
                'title': row[1],
                'detail': row[2],
                'category': row[3],
                'created_at': row[4]
            })
        
        # ガチャ履歴を取得（ideaテーブルとJOIN）
        gacha_rows = con.execute("""
            SELECT gr.result_id, gr.created_at, i.title, i.detail, i.category
            FROM gacha_result gr
            JOIN idea i ON gr.idea_id = i.idea_id
            WHERE gr.user_id = ?
            ORDER BY gr.created_at DESC
        """, (user_id,)).fetchall()
        
        gacha_results = []
        for row in gacha_rows:
            gacha_results.append({
                'result_id': row[0],
                'created_at': row[1],
                'idea_title': row[2],
                'detail': row[3],
                'category': row[4]
            })
        
        # 復活通知履歴を取得（自分のアイデアが他のユーザーにガチャで引かれた履歴）
        revival_rows = con.execute("""
            SELECT 
                gr.result_id,
                gr.created_at,
                gr.user_id as picker_id,
                u.nickname as picker_nickname,
                i.idea_id,
                i.title,
                i.detail,
                i.category
            FROM gacha_result gr
            JOIN idea i ON gr.idea_id = i.idea_id
            LEFT JOIN mypage u ON gr.user_id = u.user_id
            WHERE i.user_id = ? AND gr.user_id != ?
            ORDER BY gr.created_at DESC
        """, (user_id, user_id)).fetchall()
        
        revival_notifications = []
        for row in revival_rows:
            revival_notifications.append({
                'result_id': row[0],
                'created_at': row[1],
                'picker_id': row[2],
                'picker_nickname': row[3] if row[3] else '不明なユーザー',
                'idea_id': row[4],
                'idea_title': row[5],
                'detail': row[6],
                'category': row[7]
            })
    
    con.close()
    
    return render_template(
        'mypage.html',
        user=user,
        ideas=ideas,
        gacha_results=gacha_results,
        revival_notifications=revival_notifications
    )
