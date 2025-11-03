import sqlite3

DATABASE = 'databese.db'

def create_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS books (title, price, arrial_day)")
    con.close()