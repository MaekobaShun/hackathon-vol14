import sqlite3
import random
from datetime import datetime

DATABASE = 'database.db'

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
def fetch_items():
    con = sqlite3.connect(DATABASE)
    cursor = con.cursor()
    cursor.execute("SELECT * FROM ideas")
    rows = cursor.fetchall()
    con.close()
    return rows


# ランダムに1つのアイテムを取得する関数
def fetch_random_item():
    items = fetch_items()
    if items:
        return random.choice(items)
    return None