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

# Inicjalizacja klienta (najlepiej użyć st.cache_resource, aby nie tworzyć go co odświeżenie)
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = get_supabase()

# =============================
# FUNKCJE BAZY
# =============================
def pobierz_produkty():
    # Pobieramy produkty razem z nazwami kategorii (JOIN)
    res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    return res.data or []

def pobierz_kategorie():
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return res.data or []

def dodaj_produkt(nazwa, liczba, kategoria_id):
    supabase.table("produkty").insert({
        "nazwa": nazwa,
        "liczba": liczba,
        "kategoria_id": kategoria_id
    }).execute()

def zmniejsz_ilosc_produktu(produkt_id, ile_usunac):
    # POPRAWKA LINII 22: Bezpieczniejsze pobieranie danych
    res = supabase.table("produkty").select("liczba").eq("id", produkt_id).execute()
    
    if not res.data:
        st.error("Nie znaleziono produktu w bazie.")
        return

    aktualna_liczba = res.data[0]["liczba"]
    nowa_liczba = aktualna_liczba - ile_usunac

    if nowa_liczba > 0:
        supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", produkt_id).execute()
    else:
        # Jeśli liczba spadnie do 0 lub mniej, usuwamy produkt
        supabase.table("produkty").delete().eq("id", produkt_id).execute()

# =============================
# UI
# =============================
st.title("📦 Magazyn – produkty")
st.markdown("---")

# Pobieramy dane raz na początku
kategorie = pobierz_kategorie()
mapa_kategorii = {k["nazwa"]: k["id"] for k in kategorie}

# =============================
# DODAWANIE PRODUKTU
# =============================
st.subheader("➕ Dodaj produkt")

with st.form("formularz_dodaj", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        nazwa = st.text_input("Nazwa produktu")
    with col2:
        liczba = st.number_input("Liczba sztuk", min_value=1, step=1)
    with col3:
        wybrana_kategoria = st.selectbox("Kategoria", list(mapa_kategorii.keys())) if kategorie else st.error("Brak kategorii")
    
    submit = st.form_submit_button("Dodaj produkt")

    if submit and nazwa and wybrana_kategoria:
        dodaj_produkt(nazwa, liczba, mapa_kategorii[wybrana_kategoria])
        st.success(f"Dodano: {nazwa}")
        st.rerun()

st.markdown("---")

# =============================
# LISTA + ZMNIEJSZANIE ILOŚCI
# =============================
st.subheader("📋 Lista produktów")

produkty = pobierz_produkty()

if produkty:
    # Tworzenie czytelnej tabeli
    df = pd.DataFrame(produkty)
    
    # Wyciąganie nazwy kategorii z zagnieżdżonego słownika (dzięki JOIN w pobierz_produkty)
    if 'kategorie' in df.columns:
        df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
    
    st.dataframe(
        df[["nazwa", "liczba", "kategoria_nazwa"]].rename(columns={"kategoria_nazwa": "Kategoria"}),
        use_container_width=True
    )

    st.markdown("### ➖ Zmniejsz ilość produktu")
    
    col_sel, col_num, col_btn = st.columns([2, 1, 1])
    
    with col_sel:
        mapa_prod = {f'{p["nazwa"]} (stan: {p["liczba"]})': p
