import sqlite3
import hashlib

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
        stato TEXT,
        manodopera REAL,
        materiale REAL,
        totale REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS fatture (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        cliente TEXT,
        data TEXT,
        imponibile REAL,
        iva REAL,
        totale REAL
    )
    """)

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
