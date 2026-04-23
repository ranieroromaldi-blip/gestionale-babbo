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
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state.user = username
            st.rerun()
        else:
            st.error("Errore login")

    st.stop()

# =========================
# MENU
# =========================
st.sidebar.title("Menu")
st.sidebar.write(f"👤 {st.session_state.user}")

menu = st.sidebar.radio(
    "Sezione",
    ["Dashboard", "Clienti", "Interventi", "Fatture"]
)

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

# =========================
# PDF FATTURA
# =========================
def crea_fattura(cliente, descrizione, data, manodopera, materiale, totale):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 800, "FATTURA INTERVENTO PORTONI")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 760, f"Cliente: {cliente}")
    pdf.drawString(50, 740, f"Data: {data}")

    pdf.drawString(50, 710, f"Manodopera: € {manodopera}")
    pdf.drawString(50, 690, f"Materiale: € {materiale}")
    pdf.drawString(50, 670, f"TOTALE: € {totale}")

    pdf.drawString(50, 640, "Descrizione:")
    text = pdf.beginText(50, 620)
    text.textLines(descrizione)
    pdf.drawText(text)

    pdf.save()
    buffer.seek(0)
    return buffer

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("📊 Dashboard")

    c.execute("SELECT COUNT(*) FROM clienti")
    clienti = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM interventi")
    interventi = c.fetchone()[0]

    st.write(f"👤 Clienti: {clienti}")
    st.write(f"🛠 Interventi: {interventi}")

# =========================
# CLIENTI
# =========================
elif menu == "Clienti":
    st.title("👤 Clienti")

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

    c.execute("SELECT nome, telefono, indirizzo FROM clienti")

    for cl in c.fetchall():
        st.write(f"{cl[0]} - {cl[1]} - {cl[2]}")

# =========================
# INTERVENTI
# =========================
elif menu == "Interventi":
    st.title("🛠 Interventi")

    c.execute("SELECT nome FROM clienti")
    clienti = [x[0] for x in c.fetchall()]

    cliente = st.selectbox("Cliente", clienti if clienti else ["Nessuno"])
    desc = st.text_area("Descrizione")
    data = st.date_input("Data")

    manodopera = st.number_input("Costo manodopera", min_value=0.0)
    materiale = st.number_input("Costo materiale", min_value=0.0)

    totale = manodopera + materiale

    st.write(f"💰 Totale: € {totale}")

    if st.button("Salva intervento"):
        c.execute(
            "INSERT INTO interventi (cliente, descrizione, data, stato) VALUES (?, ?, ?, ?)",
            (cliente, desc, str(data), "Da fare")
        )
        conn.commit()
        st.success("Salvato")

# =========================
# FATTURE
# =========================
elif menu == "Fatture":
    st.title("💰 Fatture")

    c.execute("SELECT nome FROM clienti")
    clienti = [x[0] for x in c.fetchall()]

    cliente = st.selectbox("Cliente", clienti if clienti else ["Nessuno"])
    descrizione = st.text_area("Descrizione lavoro")
    data = st.date_input("Data")

    manodopera = st.number_input("Manodopera €", min_value=0.0)
    materiale = st.number_input("Materiale €", min_value=0.0)

    totale = manodopera + materiale

    st.write(f"💰 Totale: € {totale}")

    if st.button("Genera Fattura PDF"):
        pdf = crea_fattura(cliente, descrizione, str(data), manodopera, materiale, totale)

        st.download_button(
            "Scarica PDF",
            data=pdf,
            file_name="fattura.pdf",
            mime="application/pdf"
        )
