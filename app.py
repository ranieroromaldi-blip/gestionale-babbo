import streamlit as st
import sqlite3
import io
import hashlib
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from database import init_db, get_connection, hash_password

# =========================
# INIT DB
# =========================
init_db()
conn = get_connection()
c = conn.cursor()

# =========================
# LOGIN FUNCTIONS
# =========================
def login_user(username, password):
    c.execute(
        "SELECT * FROM utenti WHERE username=? AND password=?",
        (username, hash_password(password))
    )
    return c.fetchone()

# =========================
# CREATE DEFAULT USER (solo 1 volta)
# =========================
c.execute("SELECT * FROM utenti WHERE username='admin'")
if not c.fetchone():
    c.execute(
        "INSERT INTO utenti (username, password) VALUES (?, ?)",
        ("admin", hash_password("1234"))
    )
    conn.commit()

# =========================
# LOGIN PAGE
# =========================
if "user" not in st.session_state:

    st.title("🔐 Login Gestionale Portoni")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)

        if user:
            st.session_state.user = username
            st.success("Login effettuato!")
            st.rerun()
        else:
            st.error("Credenziali errate")

    st.stop()

# =========================
# LOGGED IN HEADER
# =========================
st.sidebar.write(f"👤 Utente: {st.session_state.user}")

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

st.title("🏠 Gestionale Portoni Garage")

# =========================
# PDF FUNCTION
# =========================
def crea_pdf(cliente, descrizione, data):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 800, "PREVENTIVO PORTONI GARAGE")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 760, f"Cliente: {cliente}")
    pdf.drawString(50, 740, f"Data: {data}")

    pdf.drawString(50, 710, "Descrizione:")
    text = pdf.beginText(50, 690)
    text.textLines(descrizione)
    pdf.drawText(text)

    pdf.save()
    buffer.seek(0)
    return buffer

# =========================
# CLIENTI
# =========================
st.header("👤 Clienti")

nome = st.text_input("Nome cliente")
telefono = st.text_input("Telefono")
indirizzo = st.text_input("Indirizzo")

if st.button("➕ Aggiungi cliente"):
    if nome:
        c.execute(
            "INSERT INTO clienti (nome, telefono, indirizzo) VALUES (?, ?, ?)",
            (nome, telefono, indirizzo)
        )
        conn.commit()
        st.success("Cliente aggiunto")

st.subheader("Lista clienti")

c.execute("SELECT nome, telefono, indirizzo FROM clienti")
clienti = c.fetchall()

for cl in clienti:
    st.write(f"👤 {cl[0]} - 📞 {cl[1]} - 📍 {cl[2]}")

st.divider()

# =========================
# INTERVENTI
# =========================
st.header("🛠 Interventi")

c.execute("SELECT nome FROM clienti")
clienti_nomi = [x[0] for x in c.fetchall()]

cliente = st.selectbox("Cliente", clienti_nomi if clienti_nomi else ["Nessun cliente"])
descrizione = st.text_area("Descrizione intervento")
data = st.date_input("Data intervento")
stato = st.selectbox("Stato", ["Da fare", "Completato"])

if st.button("➕ Aggiungi intervento"):
    if clienti_nomi:
        c.execute(
            "INSERT INTO interventi (cliente, descrizione, data, stato) VALUES (?, ?, ?, ?)",
            (cliente, descrizione, str(data), stato)
        )
        conn.commit()
        st.success("Intervento aggiunto")

st.subheader("Lista interventi")

c.execute("SELECT cliente, descrizione, data, stato FROM interventi ORDER BY data")
interventi = c.fetchall()

for i in interventi:
    st.write(f"👤 {i[0]}")
    st.write(f"🛠 {i[1]}")
    st.write(f"📅 {i[2]} | 📌 {i[3]}")
    st.write("---")

# =========================
# AGENDA
# =========================
st.header("📅 Agenda lavori")

c.execute("""
SELECT cliente, descrizione, data, stato
FROM interventi
ORDER BY data
""")

agenda = c.fetchall()

for a in agenda:
    st.write(f"📅 {a[2]} - 👤 {a[0]} - 🛠 {a[1]} - 📌 {a[3]}")

# =========================
# PDF
# =========================
st.header("📄 Preventivo PDF")

cliente_pdf = st.selectbox("Cliente preventivo", clienti_nomi if clienti_nomi else ["Nessun cliente"])
descrizione_pdf = st.text_area("Descrizione preventivo")
data_pdf = st.date_input("Data preventivo")

if st.button("📥 Genera PDF"):
    if clienti_nomi:
        pdf_file = crea_pdf(cliente_pdf, descrizione_pdf, str(data_pdf))

        st.download_button(
            label="⬇️ Scarica PDF",
            data=pdf_file,
            file_name="preventivo.pdf",
            mime="application/pdf"
        )
    else:
        st.error("Nessun cliente disponibile")
