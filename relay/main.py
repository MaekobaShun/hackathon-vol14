from relay import app
from flask import render_template, request, redirect, url_for, flash
from relay.db import DATABASE
import sqlite3
from relay.db import fetch_random_item
import uuid
from datetime import datetime
import os
from werkzeug.utils import secure_filename

ALLOWED_ICON_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}
MAX_NICKNAME_LENGTH = 32


def store_icon_file(icon_file, extension):
    uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}{extension}"
    save_path = os.path.join(uploads_dir, stored_filename)
    icon_file.stream.seek(0)
    icon_file.save(save_path)
    return os.path.join('uploads', stored_filename)


def delete_icon_file(icon_path):
    if not icon_path:
        return
    if not icon_path.startswith('uploads/'):
        return
    absolute_path = os.path.join(app.root_path, 'static', icon_path)
    if os.path.exists(absolute_path):
        os.remove(absolute_path)


def get_current_user_id():
    # TODO: 認証機能が実装されたらセッションから取得する
    return 'user_001'


@app.route('/')
def index():
    con = sqlite3.connect(DATABASE)
    db_items = con.execute("SELECT idea_id, title, detail, category, user_id, created_at FROM ideas ORDER BY created_at DESC").fetchall()
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

# マイページ
@app.route('/mypage/update', methods=['POST'])
def update_profile():
    user_id = get_current_user_id()

    nickname = request.form.get('nickname', '').strip()
    remove_icon = request.form.get('remove_icon') == '1'
    icon_file = request.files.get('icon')

    errors = []

    if not nickname:
        errors.append('ニックネームを入力してください。')
    elif len(nickname) > MAX_NICKNAME_LENGTH:
        errors.append(f'ニックネームは{MAX_NICKNAME_LENGTH}文字以内で入力してください。')

    icon_candidate = None
    if icon_file and icon_file.filename:
        filename = secure_filename(icon_file.filename)
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext not in ALLOWED_ICON_EXTENSIONS:
            errors.append('アイコン画像はPNG/JPG/GIF形式のみアップロードできます。')
        else:
            icon_candidate = (icon_file, ext)

    if errors:
        for message in errors:
            flash(message)
        return redirect(url_for('mypage'))

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        current_row = cur.execute(
            "SELECT icon_path FROM mypage WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        if not current_row:
            flash('ユーザー情報が見つかりません。')
            return redirect(url_for('mypage'))

        current_icon_path = current_row[0]
        new_icon_path = current_icon_path

        if icon_candidate:
            new_icon_path = store_icon_file(icon_candidate[0], icon_candidate[1])
        elif remove_icon:
            new_icon_path = None

        cur.execute(
            "UPDATE mypage SET nickname = ?, icon_path = ? WHERE user_id = ?",
            (nickname, new_icon_path, user_id)
        )
        con.commit()

    if (icon_candidate or remove_icon) and current_icon_path and current_icon_path != new_icon_path:
        delete_icon_file(current_icon_path)

    flash('プロフィールを更新しました。')
    return redirect(url_for('mypage'))


@app.route('/mypage')
def mypage():
    user_id = get_current_user_id()
    
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
            "SELECT idea_id, title, detail, category, created_at FROM ideas WHERE user_id = ? ORDER BY created_at DESC",
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
        
        # ガチャ履歴を取得（ideasテーブルとJOIN）
        gacha_rows = con.execute("""
            SELECT gr.result_id, gr.created_at, i.title, i.detail, i.category
            FROM gacha_result gr
            JOIN ideas i ON gr.idea_id = i.idea_id
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
            JOIN ideas i ON gr.idea_id = i.idea_id
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
