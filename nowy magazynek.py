# =============================
# LISTA + ZMNIEJSZANIE ILOŚCI
# =============
st.subheader("📋 Lista produktów")

produkty = pobierz_produkty()

if produkty:
    df = pd.DataFrame(produkty)

    # Bezpieczne mapowanie kategorii
    if kategorie and "kategoria_id" in df.columns:
        mapa_id_nazwa = {k["id"]: k["nazwa"] for k in kategorie}
        df["kategoria"] = df["kategoria_id"].map(mapa_id_nazwa)

    # Wyświetlamy tylko potrzebne kolumny, jeśli istnieją
    cols_to_show = [c for c in ["nazwa", "liczba", "kategoria"] if c in df.columns]
    st.dataframe(df[cols_to_show], use_container_width=True)

    st.markdown("### ➖ Zmniejsz ilość produktu")

    # Tworzymy mapę opcji dla selectboxa
    opcje = {f'{p["nazwa"]} (stan: {p["liczba"]})': p for p in produkty}
    
    wybrany_label = st.selectbox("Wybierz produkt", list(opcje.keys()))
    
    col_num, col_btn = st.columns([1, 1])
    with col_num:
        ile_usunac = st.number_input("Ile sztuk usunąć", min_value=1, step=1)
    
    with col_btn:
        st.write(" ") # wyrównanie do przycisku
        if st.button("Zmniejsz stan", use_container_width=True):
            # Pobieramy dane wybranego produktu z mapy
            produkt_dane = opcje[wybrany_label]
            
            if ile_usunac > produkt_dane["liczba"]:
                st.error(f"Nie można usunąć {ile_usunac} sztuk. W magazynie jest tylko {produkt_dane['liczba']}.")
            else:
                zmniejsz_ilosc_produktu(produkt_dane["id"], ile_usunac)
                st.success(f"Zaktualizowano produkt: {produkt_dane['nazwa']}")
                st.rerun()
else:
    st.info("Brak produktów w magazynie. Dodaj pierwszy produkt powyżej.")
