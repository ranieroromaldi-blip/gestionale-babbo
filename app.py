import streamlit as st
import sqlite3
import hashlib
import io
import shutil
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

DB_FILE = "gestionale.db"

# =========================
# BACKUP FUNZIONE
# =========================
def crea_backup():
    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy(DB_FILE, backup_name)
    return backup_name

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
    ["Dashboard", "Clienti", "Interventi", "Backup"]
)

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

st.title("🏠 Gestionale Portoni Garage")

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    c.execute("SELECT COUNT(*) FROM clienti")
    clienti = c.fetchone()[0]

    c.execute("SELECT SUM(totale) FROM interventi")
    guadagni = c.fetchone()[0] or 0

    st.metric("👤 Clienti", clienti)
    st.metric("💰 Guadagni", f"€ {guadagni}")

# =========================
# CLIENTI
# =========================
elif menu == "Clienti":

    nome = st.text_input("Nome")
    tel = st.text_input("Telefono")
    indirizzo = st.text_input("Indirizzo")

    if st.button("Aggiungi"):
        if nome:
            c.execute(
                "INSERT INTO clienti (nome, telefono, indirizzo) VALUES (?, ?, ?)",
                (nome, tel, indirizzo)
            )
            conn.commit()
            st.success("Cliente aggiunto")

# =========================
# INTERVENTI
# =========================
elif menu == "Interventi":

    c.execute("SELECT nome FROM clienti")
    clienti = [x[0] for x in c.fetchall()]

    cliente = st.selectbox("Cliente", clienti if clienti else ["Nessuno"])
    desc = st.text_area("Descrizione")
    data = st.date_input("Data")

    manodopera = st.number_input("Manodopera €", min_value=0.0)
    materiale = st.number_input("Materiale €", min_value=0.0)

    totale = manodopera + materiale

    if st.button("Salva intervento"):
        c.execute("""
            INSERT INTO interventi 
            (cliente, descrizione, data, stato, manodopera, materiale, totale)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cliente, desc, str(data), "Completato", manodopera, materiale, totale))

        conn.commit()
        st.success("Salvato")

# =========================
# BACKUP
# =========================
elif menu == "Backup":

    st.subheader("☁️ Backup sistema")

    st.write("Crea una copia del database per sicurezza")

    if st.button("📦 Crea backup"):
        file = crea_backup()
        st.success("Backup creato!")

        with open(file, "rb") as f:
            st.download_button(
                "⬇️ Scarica backup",
                data=f,
                file_name=file,
                mime="application/octet-stream"
            )

    st.divider()

    st.info("Consiglio: fai backup almeno 1 volta a settimana")
