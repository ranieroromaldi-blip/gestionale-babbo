import sqlite3

def get_connection():
    return sqlite3.connect("gestionale.db", check_same_thread=False)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS clienti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        telefono TEXT,
        indirizzo TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS interventi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT,
        descrizione TEXT,
        data TEXT,
        stato TEXT
    )
    """)

    conn.commit()
    conn.close()