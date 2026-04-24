import streamlit as st
import sqlite3
import hashlib
from datetime import date
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from database import init_db, get_connection, hash_password

# =========================
# CONFIG APP
# =========================
st.set_page_config(
    page_title="Gestionale C.R. Montaggi",
    page_icon="🏢",
    layout="wide"
)

# =========================
# DB
# =========================
init_db()
conn = get_connection()
c = conn.cursor()

# =========================
# LOGIN
# =========================
USERNAME_DEFAULT = "crmontaggi"
PASSWORD_DEFAULT = "1234"

c.execute("SELECT * FROM utenti WHERE username=?", (USERNAME_DEFAULT,))
if not c.fetchone():
    c.execute(
        "INSERT INTO utenti (username, password) VALUES (?, ?)",
        (USERNAME_DEFAULT, hash_password(PASSWORD_DEFAULT))
    )
    conn.commit()

def login_user(username, password):
    c.execute(
        "SELECT * FROM utenti WHERE username=? AND password=?",
        (username, hash_password(password))
    )
    return c.fetchone()

if "user" not in st.session_state:
    st.title("🏢 Gestionale C.R. Montaggi")
    st.subheader("🔐 Accesso sistema")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(u, p)
        if user:
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Credenziali errate")
    st.stop()

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🏢 C.R. Montaggi")
menu = st.sidebar.radio(
    "Menu",
    ["🏠 Dashboard", "👤 Clienti", "🛠 Interventi", "📋 Lista Interventi", "🔔 Notifiche"]
)

if st.sidebar.button("🚪 Logout"):
    del st.session_state.user
    st.rerun()

st.title("🏢 Gestionale C.R. Montaggi")
oggi = str(date.today())

# =========================
# DASHBOARD
# =========================
if menu == "🏠 Dashboard":
    st.subheader("📊 Riepilogo generale")
    c.execute("SELECT COUNT(*) FROM clienti")
    clienti = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM interventi")
    interventi = c.fetchone()[0]
    c.execute("SELECT SUM(totale) FROM interventi")
    guadagni = c.fetchone()[0] or 0

    col1, col2, col3 = st.columns(3)
    col1.metric("👤 Clienti", clienti)
    col2.metric("🛠 Interventi", interventi)
    col3.metric("💰 Guadagni", f"€ {guadagni}")

# =========================
# CLIENTI
# =========================
elif menu == "👤 Clienti":
    st.subheader("Nuovo cliente")
    nome = st.text_input("Nome")
    tel = st.text_input("Telefono")
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
    st.subheader("📋 Clienti registrati")
    c.execute("SELECT nome, telefono, indirizzo FROM clienti")
    for cl in c.fetchall():
        st.info(f"👤 **{cl[0]}** | 📞 {cl[1]} | 📍 {cl[2]}")

# =========================
# INTERVENTI
# =========================
elif menu == "🛠 Interventi":
    st.subheader("Nuovo Intervento")
    c.execute("SELECT nome FROM clienti")
    clienti = [x[0] for x in c.fetchall()]
    cliente = st.selectbox("Cliente", clienti if clienti else ["Nessuno"])
    data = st.date_input("Data")
    stato = st.selectbox("Stato", ["Da fare", "Completato"])
    desc = st.text_area("Descrizione")
    manodopera = st.number_input("Manodopera €", min_value=0.0)
    materiale = st.number_input("Materiale €", min_value=0.0)
    totale = manodopera + materiale
    st.success(f"💰 Totale: € {totale}")

    if st.button("💾 Salva intervento"):
        c.execute("""
            INSERT INTO interventi 
            (cliente, descrizione, data, stato, manodopera, materiale, totale)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cliente, desc, str(data), stato, manodopera, materiale, totale))
        conn.commit()
        st.success("Intervento salvato")

# =========================
# LISTA INTERVENTI
# =========================
elif menu == "📋 Lista Interventi":
    st.subheader("📋 Lista interventi registrati")
    c.execute("""
        SELECT id, cliente, descrizione, data, stato, manodopera, materiale, totale
        FROM interventi
        ORDER BY data DESC
    """)
    interventi = c.fetchall()

    if interventi:
        for iv in interventi:
            st.info(
                f"👤 {iv[1]} | 🛠 {iv[2]} | 📅 {iv[3]} | Stato: {iv[4]} | "
                f"Manodopera: € {iv[5]} | Materiale: € {iv[6]} | Totale: € {iv[7]}"
            )
            # Bottone PDF
            buffer = io.BytesIO()
            c_pdf = canvas.Canvas(buffer, pagesize=A4)
            c_pdf.setFont("Helvetica-Bold", 16)
            c_pdf.drawString(50, 800, "Preventivo Intervento")
            c_pdf.setFont("Helvetica", 12)
            c_pdf.drawString(50, 770, f"Cliente: {iv[1]}")
            c_pdf.drawString(50, 750, f"Data: {iv[3]}")
            c_pdf.drawString(50, 730, f"Descrizione: {iv[2]}")
            c_pdf.drawString(50, 710, f"Manodopera: € {iv[5]}")
            c_pdf.drawString(50, 690, f"Materiale: € {iv[6]}")
            c_pdf.drawString(50, 670, f"Totale: € {iv[7]}")
            c_pdf.showPage()
            c_pdf.save()
            buffer.seek(0)
            st.download_button(
                label="🖨 Scarica PDF",
                data=buffer,
                file_name=f"Preventivo_{iv[1]}_{iv[3]}.pdf",
                mime="application/pdf"
            )
    else:
        st.warning("Nessun intervento registrato")

# =========================
# NOTIFICHE
# =========================
elif menu == "🔔 Notifiche":
    st.subheader("🔔 Lavori di oggi")
    c.execute("""
        SELECT cliente, descrizione, stato
        FROM interventi
        WHERE data = ?
    """, (oggi,))
    lavori = c.fetchall()
    if not lavori:
        st.success("🎉 Nessun lavoro oggi")
    else:
        st.warning(f"⚠️ Hai {len(lavori)} interventi oggi")
        for l in lavori:
            if l[2] == "Da fare":
                st.error(f"🛠 {l[0]} → {l[1]}")
            else:
                st.success(f"✅ {l[0]} → {l[1]}")
