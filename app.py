import streamlit as st
import sqlite3
import io
import hashlib
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from database import init_db, get_connection, hash_password

# =========================
# DB
# =========================
init_db()
conn = get_connection()
c = conn.cursor()

# =========================
# LOGIN
# =========================
def login_user(username, password):
    c.execute(
        "SELECT * FROM utenti WHERE username=? AND password=?",
        (username, hash_password(password))
    )
    return c.fetchone()

c.execute("SELECT * FROM utenti WHERE username='admin'")
if not c.fetchone():
    c.execute(
        "INSERT INTO utenti (username, password) VALUES (?, ?)",
        ("admin", hash_password("1234"))
    )
    conn.commit()

if "user" not in st.session_state:
    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(u, p)
        if user:
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Errore login")

    st.stop()

# =========================
# MENU
# =========================
st.sidebar.title("Menu")
menu = st.sidebar.radio(
    "Sezione",
    ["Dashboard", "Clienti", "Interventi", "Statistiche"]
)

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

st.title("🏠 Gestionale Portoni")

# =========================
# DASHBOARD STATISTICHE
# =========================
if menu == "Dashboard":
    st.subheader("📊 Riepilogo generale")

    c.execute("SELECT COUNT(*) FROM clienti")
    clienti = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM interventi")
    interventi = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM interventi WHERE stato='Completato'")
    completati = c.fetchone()[0]

    st.write(f"👤 Clienti: {clienti}")
    st.write(f"🛠 Interventi totali: {interventi}")
    st.write(f"✅ Completati: {completati}")

# =========================
# CLIENTI
# =========================
elif menu == "Clienti":
    st.subheader("👤 Clienti")

    nome = st.text_input("Nome")
    tel = st.text_input("Telefono")
    indirizzo = st.text_input("Indirizzo")

    if st.button("Aggiungi cliente"):
        if nome:
            c.execute(
                "INSERT INTO clienti (nome, telefono, indirizzo) VALUES (?, ?, ?)",
                (nome, tel, indirizzo)
            )
            conn.commit()
            st.success("Cliente aggiunto")

    c.execute("SELECT nome, telefono, indirizzo FROM clienti")

    for cl in c.fetchall():
        st.write(f"{cl[0]} - {cl[1]} - {cl[2]}")

# =========================
# INTERVENTI
# =========================
elif menu == "Interventi":
    st.subheader("🛠 Interventi")

    c.execute("SELECT nome FROM clienti")
    clienti = [x[0] for x in c.fetchall()]

    cliente = st.selectbox("Cliente", clienti if clienti else ["Nessuno"])
    desc = st.text_area("Descrizione")
    data = st.date_input("Data")
    stato = st.selectbox("Stato", ["Da fare", "Completato"])

    if st.button("Salva intervento"):
        c.execute(
            "INSERT INTO interventi (cliente, descrizione, data, stato) VALUES (?, ?, ?, ?)",
            (cliente, desc, str(data), stato)
        )
        conn.commit()
        st.success("Salvato")

# =========================
# STATISTICHE GUADAGNI
# =========================
elif menu == "Statistiche":
    st.subheader("💰 Guadagni")

    # prendiamo tutte le fatture simulate (manodopera + materiale)
    c.execute("SELECT data FROM interventi")
    date = c.fetchall()

    oggi = datetime.now().month
    anno = datetime.now().year

    # simulazione semplice: NON abbiamo ancora prezzi salvati nei DB interventi,
    # quindi usiamo esempio base (step successivo li colleghiamo davvero)
    st.info("📌 (Versione base: statistiche saranno complete nel prossimo step)")

    c.execute("SELECT COUNT(*) FROM interventi WHERE stato='Completato'")
    completati = c.fetchone()[0]

    st.write(f"💰 Interventi completati: {completati}")
