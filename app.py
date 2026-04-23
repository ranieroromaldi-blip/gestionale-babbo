import streamlit as st
from database import init_db, get_connection

init_db()
conn = get_connection()
c = conn.cursor()

st.title("🏠 Gestionale Portoni Garage")

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

c.execute("SELECT id, nome, telefono, indirizzo FROM clienti")
clienti = c.fetchall()

for cl in clienti:
    col1, col2 = st.columns([4,1])
    with col1:
        st.write(f"👤 {cl[1]} - 📞 {cl[2]} - 📍 {cl[3]}")
    with col2:
        if st.button("🗑", key=f"del_cli_{cl[0]}"):
            c.execute("DELETE FROM clienti WHERE id=?", (cl[0],))
            conn.commit()
            st.rerun()

st.divider()

# =========================
# INTERVENTI
# =========================
st.header("🛠 Interventi")

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

st.subheader("Lista interventi")

c.execute("SELECT id, cliente, descrizione, data, stato FROM interventi ORDER BY data")
interventi = c.fetchall()

for i in interventi:
    col1, col2 = st.columns([5,1])

    with col1:
        st.write(f"👤 {i[1]}")
        st.write(f"🛠 {i[2]}")
        st.write(f"📅 {i[3]} | 📌 {i[4]}")
        st.write("---")

    with col2:
        if st.button("🗑", key=f"del_int_{i[0]}"):
            c.execute("DELETE FROM interventi WHERE id=?", (i[0],))
            conn.commit()
            st.rerun()

# =========================
# AGENDA
# =========================
st.header("📅 Agenda lavori (ordinati per data)")

c.execute("""
SELECT cliente, descrizione, data, stato
FROM interventi
ORDER BY data
""")

agenda = c.fetchall()

for a in agenda:
    st.write(f"📅 {a[2]} - 👤 {a[0]} - 🛠 {a[1]} - 📌 {a[3]}")