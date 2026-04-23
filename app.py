import streamlit as st
import sqlite3
import hashlib
import io
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
    ["Dashboard", "Clienti", "Interventi", "Fatture"]
)

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

st.title("🏠 Gestionale Portoni Garage")

# =========================
# NUMERO FATTURA
# =========================
def get_next_invoice_number():
    c.execute("SELECT COUNT(*) FROM fatture")
    n = c.fetchone()[0] + 1
    return f"FAT-{datetime.now().year}-{n:04d}"

# =========================
# PDF FATTURA
# =========================
def crea_fattura(numero, cliente, data, imponibile, iva, totale):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 800, f"FATTURA {numero}")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 760, f"Cliente: {cliente}")
    pdf.drawString(50, 740, f"Data: {data}")

    pdf.drawString(50, 710, f"Imponibile: € {imponibile}")
    pdf.drawString(50, 690, f"IVA (22%): € {iva}")
    pdf.drawString(50, 670, f"TOTALE: € {totale}")

    pdf.save()
    buffer.seek(0)
    return buffer

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    c.execute("SELECT COUNT(*) FROM clienti")
    clienti = c.fetchone()[0]

    c.execute("SELECT SUM(totale) FROM interventi")
    guadagni = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM fatture")
    fatture = c.fetchone()[0]

    st.metric("👤 Clienti", clienti)
    st.metric("💰 Guadagni", f"€ {guadagni}")
    st.metric("📄 Fatture", fatture)

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
# FATTURE
# =========================
elif menu == "Fatture":

    st.subheader("📄 Genera fattura")

    c.execute("SELECT nome FROM clienti")
    clienti = [x[0] for x in c.fetchall()]

    cliente = st.selectbox("Cliente", clienti if clienti else ["Nessuno"])
    data = st.date_input("Data fattura")

    imponibile = st.number_input("Imponibile €", min_value=0.0)

    iva = round(imponibile * 0.22, 2)
    totale = round(imponibile + iva, 2)

    st.write(f"IVA: € {iva}")
    st.write(f"TOTALE: € {totale}")

    if st.button("Genera fattura PDF"):
        numero = get_next_invoice_number()

        pdf = crea_fattura(numero, cliente, str(data), imponibile, iva, totale)

        c.execute("""
            INSERT INTO fatture (numero, cliente, data, imponibile, iva, totale)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (numero, cliente, str(data), imponibile, iva, totale))

        conn.commit()

        st.download_button(
            "Scarica PDF",
            data=pdf,
            file_name=f"{numero}.pdf",
            mime="application/pdf"
        )
