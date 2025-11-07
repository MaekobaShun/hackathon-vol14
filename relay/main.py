from relay import app
from flask import render_template, request, redirect, url_for, session
from relay.db import DATABASE
import sqlite3
from relay.db import (
    fetch_random_item,
    get_user_by_email,
    get_user_by_user_id,
    insert_user,
)
import uuid
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            next_url = request.url
            return redirect(url_for('login', next=next_url))
        return view_func(*args, **kwargs)

    return wrapper

@app.route('/')
def index():
    con = sqlite3.connect(DATABASE)
    db_items = con.execute(
        """
        SELECT 
            i.idea_id,
            i.title,
            i.detail,
            i.category,
            i.user_id,
            i.created_at,
            u.nickname
        FROM ideas i
        LEFT JOIN mypage u ON i.user_id = u.user_id
        ORDER BY i.created_at DESC
        """
    ).fetchall()
    con.close()

    items = []

    for row in db_items:
        items.append({
            'idea_id': row[0],
            'title': row[1],
            'detail': row[2],
            'category': row[3],
            'user_id': row[4],
            'created_at': row[5],
            'nickname': row[6]
        })

    return render_template(
        'index.html',
        items=items
    )

@app.route('/form')
@login_required
def form():
    return render_template(
        'form.html'
    )

@app.route('/post', methods=['POST'])
def post():
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('form')))

    title = request.form['title']
    detail = request.form['detail']
    category = request.form['category']

    con = sqlite3.connect(DATABASE)
    idea_id = str(uuid.uuid4())
    user_id = session['user_id']
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    con.execute("INSERT INTO ideas VALUES (?, ?, ?, ?, ?, ?)", 
                [idea_id, title, detail, category, user_id, created_at])
    con.commit()
    con.close()

    return redirect(url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    errors = []
    success_message = None

    if request.method == 'GET' and request.args.get('success') == '1':
        success_message = 'ユーザー登録が完了しました。ログイン機能は今後追加予定です。'

    form_data = {
        'user_id': request.form.get('user_id', '@').strip() if request.method == 'POST' else '@',
        'nickname': request.form.get('nickname', '').strip() if request.method == 'POST' else '',
        'email': request.form.get('email', '').strip() if request.method == 'POST' else ''
    }

    if request.method == 'POST':
        raw_user_id = None
        user_id_input = form_data['user_id']
        nickname = form_data['nickname']
        email = form_data['email']
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        icon_file = request.files.get('icon')

        if not user_id_input:
            errors.append('ユーザーIDを入力してください。')
        elif not user_id_input.startswith('@'):
            errors.append('ユーザーIDは先頭に@を付けて入力してください。')
        elif len(user_id_input) == 1:
            errors.append('ユーザーIDが短すぎます。@の後に文字を入力してください。')
        else:
            raw_user_id = user_id_input[1:].strip()
            if not raw_user_id:
                errors.append('ユーザーIDが短すぎます。@の後に文字を入力してください。')
            elif len(raw_user_id) > 31:
                errors.append('ユーザーIDは31文字以内で入力してください。')
            elif not raw_user_id.replace('_', '').replace('-', '').isalnum():
                errors.append('ユーザーIDは英数字と-_のみ使用できます。')
            else:
                existing_user_id = get_user_by_user_id(raw_user_id)
                if existing_user_id:
                    errors.append('このユーザーIDは既に利用されています。')

        if not nickname:
            errors.append('ニックネームを入力してください。')

        if not email:
            errors.append('メールアドレスを入力してください。')
        elif '@' not in email or '.' not in email:
            errors.append('正しい形式のメールアドレスを入力してください。')

        if not password:
            errors.append('パスワードを入力してください。')
        elif len(password) < 8:
            errors.append('パスワードは8文字以上で入力してください。')
        elif password != confirm_password:
            errors.append('パスワードと確認用パスワードが一致しません。')

        existing_user = get_user_by_email(email) if email else None
        if existing_user:
            errors.append('このメールアドレスは既に登録されています。')

        icon_path = None
        icon_candidate = None
        if icon_file and icon_file.filename:
            filename = secure_filename(icon_file.filename)
            _, ext = os.path.splitext(filename)
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
            if ext.lower() not in allowed_extensions:
                errors.append('アイコン画像はPNG/JPG/GIF形式のみアップロードできます。')
            else:
                icon_candidate = (icon_file, ext.lower())

        if not errors:
            if icon_candidate:
                uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                stored_filename = f"{uuid.uuid4().hex}{icon_candidate[1]}"
                icon_stream, _ = icon_candidate
                icon_stream.stream.seek(0)
                icon_stream.save(os.path.join(uploads_dir, stored_filename))
                icon_path = os.path.join('uploads', stored_filename)

            user_id = raw_user_id if raw_user_id and not errors else None
            password_hash = generate_password_hash(password)
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            insert_user(user_id, nickname, password_hash, email, icon_path, created_at)
            return redirect(url_for('signup', success='1'))

    return render_template(
        'signup.html',
        errors=errors,
        form_data=form_data,
        success_message=success_message
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    errors = []
    form_data = {
        'identifier': request.form.get('identifier', '').strip() if request.method == 'POST' else ''
    }

    next_url = request.args.get('next') or request.form.get('next')

    if request.method == 'POST':
        identifier = form_data['identifier']
        password = request.form.get('password', '')

        if not identifier:
            errors.append('ユーザーIDまたはメールアドレスを入力してください。')

        if not password:
            errors.append('パスワードを入力してください。')

        user_row = None

        if identifier and not errors:
            if identifier.startswith('@'):
                candidate_id = identifier[1:].strip()
                if candidate_id:
                    user_row = get_user_by_user_id(candidate_id)
            else:
                user_row = get_user_by_email(identifier)
                if not user_row:
                    candidate_id = identifier.strip()
                    if candidate_id:
                        user_row = get_user_by_user_id(candidate_id)

            if not user_row:
                errors.append('該当するユーザーが見つかりませんでした。')

        if not errors and user_row:
            stored_hash = user_row[2]
            if not check_password_hash(stored_hash, password):
                errors.append('ユーザーIDまたはパスワードが正しくありません。')

        if not errors and user_row:
            session.clear()
            session.permanent = True
            session['user_id'] = user_row[0]
            session['nickname'] = user_row[1]
            session['email'] = user_row[3]
            session['icon_path'] = user_row[4]

            if next_url:
                return redirect(next_url)
            return redirect(url_for('index'))

    return render_template(
        'login.html',
        errors=errors,
        form_data=form_data,
        next_url=next_url
    )


@app.route('/logout')
@login_required
def logout():
    session.clear()
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
@login_required
def mypage():
    user_id = session['user_id']

    con = sqlite3.connect(DATABASE)

    user_row = con.execute(
        "SELECT user_id, nickname, email, icon_path, created_at FROM mypage WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    if not user_row:
        con.close()
        session.clear()
        return redirect(url_for('login'))

    user = {
        'user_id': user_row[0],
        'nickname': user_row[1],
        'email': user_row[2],
        'icon_path': user_row[3],
        'created_at': user_row[4]
    }

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
