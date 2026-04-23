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

    st.title("🔐 Login Gestionale Portoni")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)

        if user:
            st.session_state.user = username
            st.rerun()
        else:
            st.error("Credenziali errate")

    st.stop()

# =========================
# SIDEBAR MENU
# =========================
st.sidebar.title("📌 Menu")
st.sidebar.write(f"👤 {st.session_state.user}")

menu = st.sidebar.radio(
    "Seleziona sezione",
    ["🏠 Dashboard", "👤 Clienti", "🛠 Interventi", "📄 Preventivi"]
)

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
# DASHBOARD
# =========================
if menu == "🏠 Dashboard":
    st.subheader("📊 Riepilogo")

    c.execute("SELECT COUNT(*) FROM clienti")
    clienti_tot = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM interventi")
    interventi_tot = c.fetchone()[0]

    st.write(f"👤 Clienti: {clienti_tot}")
    st.write(f"🛠 Interventi: {interventi_tot}")

# =========================
# CLIENTI
# =========================
elif menu == "👤 Clienti":

    st.subheader("Gestione Clienti")

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

    st.divider()

    c.execute("SELECT nome, telefono, indirizzo FROM clienti")
    for cl in c.fetchall():
        st.write(f"👤 {cl[0]} - 📞 {cl[1]} - 📍 {cl[2]}")

# =========================
# INTERVENTI
# =========================
elif menu == "🛠 Interventi":

    st.subheader("Gestione Interventi")

    c.execute("SELECT nome FROM clienti")
    clienti_nomi = [x[0] for x in c.fetchall()]

    cliente = st.selectbox("Cliente", clienti_nomi if clienti_nomi else ["Nessun cliente"])
    descrizione = st.text_area("Descrizione intervento")
    data = st.date_input("Data")
    stato = st.selectbox("Stato", ["Da fare", "Completato"])

    if st.button("➕ Aggiungi intervento"):
        if clienti_nomi:
            c.execute(
                "INSERT INTO interventi (cliente, descrizione, data, stato) VALUES (?, ?, ?, ?)",
                (cliente, descrizione, str(data), stato)
            )
            conn.commit()
            st.success("Intervento aggiunto")

    st.divider()

    c.execute("SELECT cliente, descrizione, data, stato FROM interventi ORDER BY data")

    for i in c.fetchall():
        st.write(f"👤 {i[0]} | 📅 {i[2]} | 📌 {i[3]}")
        st.write(f"🛠 {i[1]}")
        st.write("---")

# =========================
# PDF
# =========================
elif menu == "📄 Preventivi":

    st.subheader("Genera Preventivo PDF")

    c.execute("SELECT nome FROM clienti")
    clienti_nomi = [x[0] for x in c.fetchall()]

    cliente_pdf = st.selectbox("Cliente", clienti_nomi if clienti_nomi else ["Nessun cliente"])
    descrizione_pdf = st.text_area("Descrizione preventivo")
    data_pdf = st.date_input("Data")

    if st.button("📥 Genera PDF"):
        if clienti_nomi:
            pdf_file = crea_pdf(cliente_pdf, descrizione_pdf, str(data_pdf))

            st.download_button(
                "⬇️ Scarica PDF",
                data=pdf_file,
                file_name="preventivo.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Nessun cliente")
