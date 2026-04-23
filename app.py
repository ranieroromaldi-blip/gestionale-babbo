import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date

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
    ["Dashboard", "Clienti", "Interventi", "Calendario"]
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

    c.execute("SELECT COUNT(*) FROM interventi")
    interventi = c.fetchone()[0]

    c.execute("SELECT SUM(totale) FROM interventi WHERE stato='Completato'")
    guadagni = c.fetchone()[0] or 0

    st.metric("👤 Clienti", clienti)
    st.metric("🛠 Interventi", interventi)
    st.metric("💰 Guadagni", f"€ {guadagni}")

# =========================
# CLIENTI
# =========================
elif menu == "Clienti":

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

    c.execute("SELECT nome FROM clienti")
    clienti = [x[0] for x in c.fetchall()]

    cliente = st.selectbox("Cliente", clienti if clienti else ["Nessuno"])
    desc = st.text_area("Descrizione")
    data = st.date_input("Data intervento")
    stato = st.selectbox("Stato", ["Da fare", "Completato"])

    manodopera = st.number_input("Manodopera €", min_value=0.0)
    materiale = st.number_input("Materiale €", min_value=0.0)

    totale = manodopera + materiale

    if st.button("Salva intervento"):
        c.execute("""
            INSERT INTO interventi 
            (cliente, descrizione, data, stato, manodopera, materiale, totale)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cliente, desc, str(data), stato, manodopera, materiale, totale))

        conn.commit()
        st.success("Salvato")

# =========================
# CALENDARIO LAVORI
# =========================
elif menu == "Calendario":

    st.subheader("📅 Calendario lavori")

    oggi = date.today()

    tab1, tab2, tab3 = st.tabs(["📍 Oggi", "📆 Prossimi lavori", "📋 Tutti"])

    # ================= OGGI =================
    with tab1:
        c.execute("""
            SELECT cliente, descrizione, data, stato
            FROM interventi
            WHERE data = ?
        """, (str(oggi),))

        lavori = c.fetchall()

        if not lavori:
            st.info("Nessun lavoro oggi")
        else:
            for l in lavori:
                st.write(f"👤 {l[0]} | 🛠 {l[1]} | 📌 {l[3]}")

    # ================= PROSSIMI =================
    with tab2:
        c.execute("""
            SELECT cliente, descrizione, data, stato
            FROM interventi
            WHERE data > ?
            ORDER BY data ASC
        """, (str(oggi),))

        for l in c.fetchall():
            st.write(f"📅 {l[2]} | 👤 {l[0]} | 🛠 {l[1]} | 📌 {l[3]}")

    # ================= TUTTI =================
    with tab3:
        c.execute("""
            SELECT cliente, descrizione, data, stato
            FROM interventi
            ORDER BY data DESC
        """)

        for l in c.fetchall():
            st.write(f"{l[2]} | {l[0]} | {l[1]} | {l[3]}")
