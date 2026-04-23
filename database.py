import sqlite3
import hashlib

def get_connection():
    return sqlite3.connect("gestionale.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # CLIENTI
    c.execute("""
    CREATE TABLE IF NOT EXISTS clienti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        telefono TEXT,
        indirizzo TEXT
    )
    """)

    # INTERVENTI CON SOLDI VERI
    c.execute("""
    CREATE TABLE IF NOT EXISTS interventi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT,
        descrizione TEXT,
        data TEXT,
        stato TEXT,
        manodopera REAL,
        materiale REAL,
        totale REAL
    )
    """)

    # UTENTI LOGIN
    c.execute("""
    CREATE TABLE IF NOT EXISTS utenti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
