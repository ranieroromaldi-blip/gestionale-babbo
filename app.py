import streamlit as st
import sqlite3
import hashlib
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from database import init_db, get_connection, hash_password

# =========================
# CONFIG UI
# =========================
st.set_page_config(page_title="Gestionale Portoni", layout="wide")

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
    st.title("🔐 Login Gestionale")

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
# SIDEBAR
# =========================
st.sidebar.title("📌 Menu")
menu = st.sidebar.radio(
    "Seleziona",
    ["🏠 Dashboard", "👤 Clienti", "🛠 Interventi", "💰 Guadagni"]
)

if st.sidebar.button("🚪 Logout"):
    del st.session_state.user
    st.rerun()

st.title("🏠 Gestionale Portoni Garage")

# =========================
# DASHBOARD (CARDS)
# =========================
if menu == "🏠 Dashboard":

    c.execute("SELECT COUNT(*) FROM clienti")
    clienti = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM interventi")
    interventi = c.fetchone()[0]

    c.execute("SELECT SUM(totale) FROM interventi")
    guadagni = c.fetchone()[0] or 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("👤 Clienti", clienti)

    with col2:
        st.metric("🛠 Interventi", interventi)

    with col3:
        st.metric("💰 Guadagni", f"€ {guadagni}")

# =========================
# CLIENTI (CARDS)
# =========================
elif menu == "👤 Clienti":

    st.subheader("Nuovo cliente")

    with st.container():
        col1, col2, col3 = st.columns(3)

        with col1:
            nome = st.text_input("Nome")

        with col2:
            tel = st.text_input("Telefono")

        with col3:
            indirizzo = st.text_input("Indirizzo")

    if st.button("➕ Aggiungi cliente"):
        if nome:
            c.execute(
                "INSERT INTO clienti (nome, telefono, indirizzo) VALUES (?, ?, ?)",
                (nome, tel, indirizzo)
            )
            conn.commit()
            st.success("Cliente aggiunto")

    st.divider()

    c.execute("SELECT nome, telefono, indirizzo FROM clienti")

    for cl in c.fetchall():
        st.info(f"👤 **{cl[0]}** | 📞 {cl[1]} | 📍 {cl[2]}")

# =========================
# INTERVENTI (CARDS)
# =========================
elif menu == "🛠 Interventi":

    c.execute("SELECT nome FROM clienti")
    clienti = [x[0] for x in c.fetchall()]

    st.subheader("Nuovo intervento")

    col1, col2 = st.columns(2)

    with col1:
        cliente = st.selectbox("Cliente", clienti if clienti else ["Nessuno"])
        data = st.date_input("Data")

    with col2:
        stato = st.selectbox("Stato", ["Da fare", "Completato"])

    desc = st.text_area("Descrizione")

    col3, col4 = st.columns(2)

    with col3:
        manodopera = st.number_input("Manodopera €", min_value=0.0)

    with col4:
        materiale = st.number_input("Materiale €", min_value=0.0)

    totale = manodopera + materiale

    st.success(f"💰 Totale intervento: € {totale}")

    if st.button("💾 Salva intervento"):
        c.execute("""
            INSERT INTO interventi 
            (cliente, descrizione, data, stato, manodopera, materiale, totale)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cliente, desc, str(data), stato, manodopera, materiale, totale))

        conn.commit()
        st.success("Intervento salvato")

# =========================
# GUADAGNI (SIMPLE DASHBOARD)
# =========================
elif menu == "💰 Guadagni":

    st.subheader("📊 Riepilogo guadagni")

    c.execute("SELECT SUM(totale) FROM interventi WHERE stato='Completato'")
    tot = c.fetchone()[0] or 0

    st.metric("💰 Totale incassato", f"€ {tot}")

    st.divider()

    c.execute("""
        SELECT cliente, data, totale
        FROM interventi
        WHERE stato='Completato'
        ORDER BY data DESC
    """)

    for i in c.fetchall():
        st.success(f"📅 {i[1]} | 👤 {i[0]} | € {i[2]}")
