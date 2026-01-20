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
# FUNKCJE BAZY
# =============================

def pobierz_produkty():
    res = supabase.table("produkty").select("*").execute()
    return res.data or []

def pobierz_kategorie():
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return res.data or []

def dodaj_produkt(nazwa, liczba, kategoria_id):
    # Ważne: execute() na końcu jest kluczowe!
    try:
        supabase.table("produkty").insert(
            {
                "nazwa": nazwa,
                "liczba": liczba,
                "kategoria_id": kategoria_id
            }
        ).execute()
        return True
    except Exception as e:
        st.error(f"Błąd bazy danych: {e}")
        return False

def zmniejsz_ilosc_produktu(produkt_id, ile_usunac):
    res = supabase.table("produkty").select("liczba").eq("id", produkt_id).execute()
    if res.data:
        aktualna_liczba = res.data[0]["liczba"]
        nowa_liczba = aktualna_liczba - ile_usunac
        if nowa_liczba > 0:
            supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", produkt_id).execute()
        else:
            supabase.table("produkty").delete().eq("id", produkt_id).execute()

# =============================
# UI – INTERFEJS UŻYTKOWNIKA
# =============================
st.title("📦 Magazyn – produkty")

# Pobranie danych
kategorie = pobierz_kategorie()
mapa_kategorii = {k["nazwa"]: k["id"] for k in kategorie}

# =============================
# SEKCJA: DODAWANIE
# =============================
st.subheader("➕ Dodaj produkt")

# Używamy st.container(), aby formularz był wyraźny
with st.container():
    # Formularz z unikalnym kluczem
    with st.form("form_dodawania", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            nazwa_input = st.text_input("Nazwa produktu", placeholder="np. Chleb")
        with col2:
            liczba_input = st.number_input("Liczba sztuk", min_value=1, step=1, value=1)
        with col3:
            if kategorie:
                wybrana_kat = st.selectbox("Wybierz kategorię", list(mapa_kategorii.keys()))
            else:
                st.warning("⚠️ Brak kategorii w bazie! Najpierw dodaj kategorie w Supabase.")
                wybrana_kat = None

        przycisk_dodaj = st.form_submit_button("Dodaj produkt do magazynu")

        if przycisk_dodaj:
            if not nazwa_input:
                st.error("Musisz podać nazwę produktu!")
            elif not wybrana_kat:
                st.error("Musisz wybrać kategorię!")
            else:
                sukces = dodaj_produkt(
                    nazwa=nazwa_input,
                    liczba=liczba_input,
                    kategoria_id=mapa_kategorii[wybrana_kat]
                )
                if sukces:
                    st.success(f"✅ Produkt '{nazwa_input}' został dodany!")
                    # To wymusza przeładowanie aplikacji i pokazanie nowych danych
                    st.rerun()

st.markdown("---")

# =============================
# SEKCJA: LISTA
# =============================
st.subheader("📋 Aktualny stan magazynu")

produkty = pobierz_produkty()

if produkty:
    df = pd.DataFrame(produkty)
    
    # Mapowanie nazw kategorii
    if kategorie:
        mapa_id_nazwa = {k["id"]: k["nazwa"] for k in kategorie}
        df["kategoria"] = df["kategoria_id"].map(mapa_id_nazwa)

    # Wyświetlenie tabeli (tylko wybrane kolumny)
    kolumny = [c for c in ["nazwa", "liczba", "kategoria"] if c in df.columns]
    st.dataframe(df[kolumny], use_container_width=True)

    # Sekcja usuwania/zmniejszania
    st.markdown("### ➖ Wydaj produkt")
    opcje = {f"{p['nazwa']} (Dostępne: {p['liczba']})": p for p in produkty}
    wybrany_do_wydania = st.selectbox("Wybierz produkt", list(opcje.keys()))
    
    c_ile, c_przycisk = st.columns([1, 1])
    with c_ile:
        ile_wydac = st.number_input("Ilość", min_value=1, step=1)
    with c_przycisk:
        st.write(" ") # margines
        if st.button("Zatwierdź wydanie"):
            p_dane = opcje[wybrany_do_wydania]
            if ile_wydac > p_dane["liczba"]:
                st.error("Nie ma tyle towaru!")
            else:
        st.info("Magazyn jest obecnie pusty.")

        st.markdown("---")
        st.caption("Aplikacja Magazynowa v1.0 | Streamlit + Supabase")
