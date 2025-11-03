import sqlite3

DATABASE = 'databese.db'

def create_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS items (title, detail, category)")
    con.close()