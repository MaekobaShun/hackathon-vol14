import os
import sqlite3
import random
from datetime import datetime

_DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'database.db')
)
DATABASE = os.environ.get('DB_PATH', _DEFAULT_DB_PATH)

def create_table():
    con = sqlite3.connect(DATABASE)
    
    # マイページ（ユーザー情報）
    con.execute("""
        CREATE TABLE IF NOT EXISTS mypage (
            user_id      VARCHAR(64) PRIMARY KEY UNIQUE NOT NULL,
            nickname     VARCHAR(32) NOT NULL,
            password     VARCHAR(128) NOT NULL,
            email        VARCHAR(128) UNIQUE NOT NULL,
            icon_path    VARCHAR(255),
            created_at   DATETIME NOT NULL
        )
    """)
    
    # 既存のテーブルにicon_pathカラムを追加（存在しない場合）
    try:
        con.execute("ALTER TABLE mypage ADD COLUMN icon_path VARCHAR(255)")
    except sqlite3.OperationalError:
        # カラムが既に存在する場合はスキップ
        pass
    
    # アイデア
    con.execute("""
        CREATE TABLE IF NOT EXISTS ideas (
            idea_id      VARCHAR(64) PRIMARY KEY UNIQUE NOT NULL,
            title        VARCHAR(128) NOT NULL,
            detail       TEXT NOT NULL,
            category     VARCHAR(32) NOT NULL,
            user_id      VARCHAR(64) NOT NULL,
            created_at   DATETIME NOT NULL
        )
    """)
    
    # ガチャリザルト（ガチャ結果）
    con.execute("""
        CREATE TABLE IF NOT EXISTS gacha_result (
            result_id    VARCHAR(64) PRIMARY KEY UNIQUE NOT NULL,
            user_id      VARCHAR(64) NOT NULL,
            idea_id      VARCHAR(64) NOT NULL,
            created_at   DATETIME NOT NULL
        )
    """)
    
    # 復活通知
    con.execute("""
        CREATE TABLE IF NOT EXISTS revival_notify (
            notify_id    VARCHAR(64) PRIMARY KEY UNIQUE NOT NULL,
            idea_id      VARCHAR(64) NOT NULL,
            author_id    VARCHAR(64) NOT NULL,
            picker_id    VARCHAR(64) NOT NULL,
            created_at   DATETIME NOT NULL
        )
    """)
    
    # サンクス
    con.execute("""
        CREATE TABLE IF NOT EXISTS thanks (
            thanks_id       VARCHAR(64) PRIMARY KEY UNIQUE NOT NULL,
            gacha_type_id   VARCHAR(64) NOT NULL,
            sender_id       VARCHAR(64) NOT NULL,
            receiver_id     VARCHAR(64) NOT NULL,
            stamp_type      VARCHAR(32) NOT NULL,
            created_at      DATETIME NOT NULL
        )
    """)
    
    con.commit()
    con.close()

# データベースから全アイテムを取得する関数
def fetch_items(exclude_user_id=None, category=None):
    con = sqlite3.connect(DATABASE)
    cursor = con.cursor()

    query = "SELECT * FROM ideas WHERE 1=1"
    params = []

    if exclude_user_id:
        query += " AND user_id != ?"
        params.append(exclude_user_id)

    if category:
        query += " AND category = ?"
        params.append(category)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    con.close()
    return rows


# ランダムに1つのアイテムを取得する関数
def fetch_random_item(exclude_user_id=None, category=None):
    items = fetch_items(exclude_user_id=exclude_user_id, category=category)
    if items:
        return random.choice(items)
    return None


def get_user_by_email(email: str):
    con = sqlite3.connect(DATABASE)
    cursor = con.cursor()
    cursor.execute(
        "SELECT user_id, nickname, password, email, icon_path, created_at FROM mypage WHERE email = ?",
        (email,)
    )
    row = cursor.fetchone()
    con.close()
    return row


def get_user_by_user_id(user_id: str):
    con = sqlite3.connect(DATABASE)
    cursor = con.cursor()
    cursor.execute(
        "SELECT user_id, nickname, password, email, icon_path, created_at FROM mypage WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    con.close()
    return row


def insert_user(user_id: str, nickname: str, password_hash: str, email: str, icon_path: str | None, created_at: str) -> None:
    con = sqlite3.connect(DATABASE)
    con.execute(
        "INSERT INTO mypage (user_id, nickname, password, email, icon_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, nickname, password_hash, email, icon_path, created_at)
    )
    con.commit()
    con.close()