import streamlit as st
import pandas as pd
from supabase import create_client

# =============================
# KONFIGURACJA
# =============================
st.set_page_config(
    page_title="Magazyn – produkty",
    layout="wide"
)

# Inicjalizacja klienta Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# =============================
# FUNKCJE BAZY (Z POPRAWNYMI WCIĘCIAMI)
# =============================

def pobierz_produkty():
    # Pobieramy produkty
    res = supabase.table("produkty").select("*").execute()
    return res.data or []

def pobierz_kategorie():
    # Pobieramy kategorie dla selectboxa
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return res.data or []

def dodaj_produkt(nazwa, liczba, kategoria_id):
    # Dodawanie nowego wiersza
    supabase.table("produkty").insert(
        {
            "nazwa": nazwa,
            "liczba": liczba,
            "kategoria_id": kategoria_id
        }
    ).execute()

def zmniejsz_ilosc_produktu(produkt_id, ile_usunac):
    # Pobieramy aktualny stan dla konkretnego ID
    res = supabase.table("produkty").select("liczba").eq("id", produkt_id).execute()
    
    if res.data:
        aktualna_liczba = res.data[0]["liczba"]
        nowa_liczba = aktualna_liczba - ile_usunac

        if nowa_liczba > 0:
            # Aktualizacja liczby
            supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", produkt_id).execute()
        else:
            # Usuwanie produktu, jeśli stan spadnie do 0
            supabase.table("produkty").delete().eq("id", produkt_id).execute()

# =============================
# UI – INTERFEJS UŻYTKOWNIKA
# =============================
st.title("📦 Magazyn – produkty")
st.markdown("---")

# Pobranie danych na start
kategorie = pobierz_kategorie()
mapa_kategorii = {k["nazwa"]: k["id"] for k in kategorie}

# =============================
# SEKCJA: DODAWANIE
# =============================
st.subheader("➕ Dodaj produkt")

with st.form("formularz_dodaj", clear_on_submit=True):
    c1, c2, c3 = st.columns([2, 1, 2])
    
    with c1:
        nazwa = st.text_input("Nazwa produktu")
    with c2:
        liczba = st.number_input("Liczba sztuk", min_value=1, step=1)
    with c3:
        if kategorie:
            wybrana_kategoria = st.selectbox("Kategoria", list(mapa_kategorii.keys()))
        else:
            st.error("Brak kategorii w bazie!")
            wybrana_kategoria = None

    submit = st.form_submit_button("Dodaj produkt do bazy")

    if submit and nazwa and wybrana_kategoria:
        dodaj_produkt(
            nazwa=nazwa,
            liczba=liczba,
            kategoria_id=mapa_kategorii[wybrana_kategoria]
        )
        st.success(f"Dodano produkt: {nazwa}")
        st.rerun()

st.markdown("---")

# =============================
# SEKCJA: LISTA I ZARZĄDZANIE
# =============================
st.subheader("📋 Aktualny stan magazynu")

produkty = pobierz_produkty()

if produkty:
    df = pd.DataFrame(produkty)
    
    # Mapowanie nazw kategorii dla tabeli
    if kategorie:
        mapa_id_nazwa = {k["id"]: k["nazwa"] for k in kategorie}
        df["kategoria"] = df["kategoria_id"].map(mapa_id_nazwa)

    # Wyświetlenie tabeli
    st.dataframe(df[["nazwa", "liczba", "kategoria"]], use_container_width=True)

    st.markdown("### ➖ Wydaj produkt z magazynu")
    
    # Tworzymy opcje do wyboru w formie: "Chleb (stan: 10)"
    opcje_produktow = {f"{p['nazwa']} (stan: {p['liczba']})": p for p in produkty}
    wybrany_label = st.selectbox("Wybierz produkt do zmniejszenia stanu", list(opcje_produktow.keys()))
    
    c_ile, c_przycisk = st.columns([1, 1])
    
    with c_ile:
        ile_do_usuniecia = st.number_input("Ilość do wydania", min_value=1, step=1)
    
    with c_przycisk:
        st.write(" ") # Odstęp pionowy
        if st.button("Zatwierdź wydanie", use_container_width=True):
            produkt_dane = opcje_produktow[wybrany_label]
            
            if ile_do_usuniecia > produkt_dane["liczba"]:
                st.error("Błąd: Nie masz tyle towaru w magazynie!")
            else:
                zmniejsz_ilosc_produktu(produkt_dane["id"], ile_do_usuniecia)
                st.success(f"Wydano {ile_do_usuniecia} szt. produktu {produkt_dane['nazwa']}")
                st.rerun()
else:
    st.info("Magazyn jest obecnie pusty.")

st.markdown("---")
st.caption("Aplikacja Magazynowa v1.0 | Streamlit + Supabase")
