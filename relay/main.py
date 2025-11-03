from relay import app
from flask import render_template, request, redirect, url_for
import sqlite3
from relay.db import fetch_random_item

DATABASE = 'databese.db'

@app.route('/')
def index():
    con = sqlite3.connect(DATABASE)
    db_items = con.execute("SELECT * FROM items").fetchall()
    con.close()

    items = []

    for row in db_items:
        items.append({
            'title':row[0],
            'detail':row[1],
            'category':row[2],
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
    con.execute("INSERT INTO items VALUES (?, ?, ?)", [title, detail, category])
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
