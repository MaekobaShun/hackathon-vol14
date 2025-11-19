import os
import random

USE_SUPABASE = bool(
    os.environ.get('SUPABASE_DATABASE_URL')
    or os.environ.get('DATABASE_URL')
    or os.environ.get('SUPABASE_HOST')
)

if USE_SUPABASE:
    import psycopg  # type: ignore
else:
    import sqlite3  # type: ignore

_DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'database.db')
)
DATABASE = os.environ.get('DB_PATH', _DEFAULT_DB_PATH)

_SUPABASE_SETTINGS: dict[str, str | int] = {}

if USE_SUPABASE:
    conninfo = os.environ.get('SUPABASE_DATABASE_URL') or os.environ.get('DATABASE_URL')
    if conninfo:
        _SUPABASE_SETTINGS['conninfo'] = conninfo
    else:
        host = os.environ.get('SUPABASE_HOST')
        user = os.environ.get('SUPABASE_USER')
        password = os.environ.get('SUPABASE_PASSWORD')
        dbname = os.environ.get('SUPABASE_DB') or os.environ.get('SUPABASE_DATABASE')
        if host and user and password and dbname:
            _SUPABASE_SETTINGS = {
                'host': host,
                'port': int(os.environ.get('SUPABASE_PORT', 5432)),
                'user': user,
                'password': password,
                'dbname': dbname,
            }


def using_supabase() -> bool:
    return USE_SUPABASE and bool(_SUPABASE_SETTINGS)


def _prepare_query(query: str) -> str:
    if using_supabase():
        return query.replace('?', '%s')
    return query


class SupabaseCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=()):
        self._cursor.execute(_prepare_query(query), params)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def close(self):
        self._cursor.close()


class SupabaseConnection:
    def __init__(self):
        if not using_supabase():
            raise RuntimeError('Supabase connection settings are not configured.')
        self._conn = psycopg.connect(**_SUPABASE_SETTINGS)  # type: ignore[arg-type]
        self._conn.autocommit = False

    def execute(self, query, params=()):
        cursor = self._conn.cursor()
        return SupabaseCursor(cursor).execute(query, params)

    def cursor(self):
        return SupabaseCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.rollback()
        else:
            self.commit()
        self.close()
        return False


def get_connection():
    if using_supabase():
        return SupabaseConnection()
    return sqlite3.connect(DATABASE)  # type: ignore[return-value]


def create_table():
    with get_connection() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS mypage (
                user_id      VARCHAR(64) PRIMARY KEY,
                nickname     VARCHAR(32) NOT NULL,
                password     TEXT NOT NULL,
                email        VARCHAR(255) UNIQUE NOT NULL,
                icon_path    TEXT,
                created_at   TIMESTAMP NOT NULL
            )
        """)

        if using_supabase():
            con.execute("ALTER TABLE mypage ADD COLUMN IF NOT EXISTS icon_path TEXT")
            try:
                con.execute("ALTER TABLE mypage ALTER COLUMN password TYPE TEXT")
            except Exception:
                pass
            try:
                con.execute("ALTER TABLE mypage ALTER COLUMN email TYPE VARCHAR(255)")
            except Exception:
                pass
        else:
            try:
                con.execute("ALTER TABLE mypage ADD COLUMN icon_path TEXT")
            except Exception:
                pass

        con.execute("""
            CREATE TABLE IF NOT EXISTS ideas (
                idea_id      VARCHAR(64) PRIMARY KEY,
                title        VARCHAR(128) NOT NULL,
                detail       TEXT NOT NULL,
                category     VARCHAR(32) NOT NULL,
                user_id      VARCHAR(64) NOT NULL,
                created_at   TIMESTAMP NOT NULL
            )
        """)

        # Add inheritance_flag column to ideas table
        if using_supabase():
            con.execute("ALTER TABLE ideas ADD COLUMN IF NOT EXISTS inheritance_flag BOOLEAN DEFAULT FALSE")
        else:
            try:
                con.execute("ALTER TABLE ideas ADD COLUMN inheritance_flag INTEGER DEFAULT 0")
            except Exception:
                pass

        con.execute("""
            CREATE TABLE IF NOT EXISTS gacha_result (
                result_id    VARCHAR(64) PRIMARY KEY,
                user_id      VARCHAR(64) NOT NULL,
                idea_id      VARCHAR(64) NOT NULL,
                created_at   TIMESTAMP NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS revival_notify (
                notify_id    VARCHAR(64) PRIMARY KEY,
                idea_id      VARCHAR(64) NOT NULL,
                author_id    VARCHAR(64) NOT NULL,
                picker_id    VARCHAR(64) NOT NULL,
                created_at   TIMESTAMP NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS thanks (
                thanks_id       VARCHAR(64) PRIMARY KEY,
                gacha_type_id   VARCHAR(64) NOT NULL,
                sender_id       VARCHAR(64) NOT NULL,
                receiver_id     VARCHAR(64) NOT NULL,
                stamp_type      VARCHAR(32) NOT NULL,
                created_at      TIMESTAMP NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS idea_inheritance (
                inheritance_id  VARCHAR(64) PRIMARY KEY,
                parent_idea_id  VARCHAR(64),
                parent_user_id  VARCHAR(64),
                child_idea_id   VARCHAR(64),
                child_user_id   VARCHAR(64),
                add_point       VARCHAR(64),
                add_detail      TEXT,
                created_at      TIMESTAMP NOT NULL
            )
        """)
    

def fetch_items(exclude_user_id=None, category=None):
    with get_connection() as con:
        query = "SELECT * FROM ideas WHERE 1=1"
        params = []

        if exclude_user_id:
            query += " AND user_id != ?"
            params.append(exclude_user_id)

        if category:
            query += " AND category = ?"
            params.append(category)

        rows = con.execute(query, tuple(params)).fetchall()
    return rows


def fetch_random_item(exclude_user_id=None, category=None):
    items = fetch_items(exclude_user_id=exclude_user_id, category=category)
    if items:
        return random.choice(items)
    return None


def get_user_by_email(email: str):
    with get_connection() as con:
        row = con.execute(
            "SELECT user_id, nickname, password, email, icon_path, created_at FROM mypage WHERE email = ?",
            (email,)
        ).fetchone()
    return row


def get_user_by_user_id(user_id: str):
    with get_connection() as con:
        row = con.execute(
            "SELECT user_id, nickname, password, email, icon_path, created_at FROM mypage WHERE user_id = ?",
            (user_id,)
        ).fetchone()
    return row


def insert_user(user_id: str, nickname: str, password_hash: str, email: str, icon_path: str | None, created_at: str) -> None:
    with get_connection() as con:
        con.execute(
            "INSERT INTO mypage (user_id, nickname, password, email, icon_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, nickname, password_hash, email, icon_path, created_at)
        )