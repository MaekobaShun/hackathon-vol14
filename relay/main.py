from relay import app
from flask import render_template, request, redirect, url_for
from relay.db import DATABASE
import sqlite3

@app.route('/')
def index():
    con = sqlite3.connect(DATABASE)
    db_items = con.execute("SELECT * FROM items").fetchall()
    con.close()

    items = []

    for row in db_items:
        items.append({
            'title': row[0],
            'detail': row[1],
            'category': row[2],
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

