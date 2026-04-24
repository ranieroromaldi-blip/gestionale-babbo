st.subheader("📋 Lista interventi registrati")

# Prendo tutti gli interventi dal database
c.execute("""
    SELECT cliente, descrizione, data, stato, manodopera, materiale, totale
    FROM interventi
    ORDER BY data DESC
""")
interventi = c.fetchall()

if interventi:
    for i, iv in enumerate(interventi, start=1):
        st.info(
            f"{i}. 👤 {iv[0]} | 🛠 {iv[1]} | 📅 {iv[2]} | Stato: {iv[3]} | "
            f"Manodopera: € {iv[4]} | Materiale: € {iv[5]} | Totale: € {iv[6]}"
        )
else:
    st.warning("Nessun intervento registrato")
