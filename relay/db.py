import sqlite3
import random

DATABASE = 'databese.db'

def create_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS items (title, detail, category)")
    con.close()

# データベースから全アイテムを取得する関数
def fetch_items():
    con = sqlite3.connect(DATABASE)
    cursor = con.cursor()
    cursor.execute("SELECT * FROM items")
    rows = cursor.fetchall()
    con.close()
    return rows


# ランダムに1つのアイテムを取得する関数
def fetch_random_item():
    items = fetch_items()
    if items:
        return random.choice(items)
    return None