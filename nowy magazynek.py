import streamlit as st
import pandas as pd
from supabase import create_client

# ==========================================
# 1. KONFIGURACJA I POŁĄCZENIE
# ==========================================
st.set_page_config(page_title="Magazyn Pro", layout="wide")

@st.cache_resource
def polacz_z_baza():
    try:
        # Pobieranie danych z Secrets
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Problem z połączeniem: {e}")
        return None

supabase = polacz_z_baza()

# ==========================================
# 2. FUNKCJE BAZY DANYCH (Z POPRAWNYMI WCIĘCIAMI)
# ==========================================

def pobierz_produkty():
    """Pobiera listę wszystkich produktów."""
    res = supabase.table("produkty").select("*").execute()
    return res.data if res.data else []

def pobierz_kategorie():
    """Pobiera listę kategorii."""
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return res.data if res.data else []

def dodaj_produkt(nazwa, liczba, kategoria_id):
    """Wstawia nowy wiersz do tabeli produkty."""
    supabase.table("produkty").insert({
        "nazwa": nazwa,
        "liczba": liczba,
        "kategoria_id": kategoria_id
    }).execute()

def aktualizuj_stan(produkt_id, nowa_liczba):
    """Zmienia ilość lub usuwa produkt jeśli stan = 0."""
    if nowa_liczba > 0:
        supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", produkt_id).execute()
    else:
        supabase.table("produkty").delete().eq("id", produkt_id).execute()

# ==========================================
# 3. INTERFEJS UŻYTKOWNIKA (UI)
# ==========================================
st.title("📦 System Zarządzania Magazynem")
st.markdown("---")

# Pobieranie danych na start
produkty = pobierz_produkty()
kategorie = pobierz_kategorie()

# Mapy pomocnicze (ID <-> Nazwa)
mapa_kategorii = {k["nazwa"]: k["id"] for k in kategorie}
mapa_id_na_nazwe = {k["id"]: k["nazwa"] for k in kategorie}

# --- SEKCJA: DODAWANIE ---
st.subheader("➕ Dodaj nowy produkt")

with st.form("form_dodaj", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        nazwa_wpisana = st.text_input("Nazwa produktu")
    with col2:
        liczba_wpisana = st.number_input("Ilość", min_value=1, step=1)
    with col3:
        if kategorie:
            wybrana_kat = st.selectbox("Wybierz kategorię", list(mapa_kategorii.keys()))
        else:
            st.error("Brak kategorii w bazie!")
            wybrana_kat = None

    przycisk_dodaj = st.form_submit_button("Dodaj do magazynu")

    if przycisk_dodaj and nazwa_wpisana and wybrana_kat:
        dodaj_produkt(nazwa_wpisana, liczba_wpisana, mapa_kategorii[wybrana_kat])
        st.success(f"Dodano: {nazwa_wpisana}")
        st.rerun()

st.markdown("---")

# --- SEKCJA: LISTA I WYDAWANIE ---
st.subheader("📋 Aktualny stan magazynu")

if produkty:
    # Przygotowanie tabeli do wyświetlenia
    df = pd.DataFrame(produkty)
    
    # Dodanie kolumny z nazwą kategorii zamiast ID
    if "kategoria_id" in df.columns:
        df["kategoria"] = df["kategoria_id"].map(mapa_id_na_nazwe)
    
    # Wyświetlenie tabeli
    st.dataframe(df[["nazwa", "liczba", "kategoria"]], use_container_width=True)

    # --- FORMULARZ WYDANIA ---
    st.markdown("### ➖ Wydaj produkt")
    c_sel, c_num, c_btn = st.columns([2, 1, 1])
    
    opcje = {f"{p['nazwa']} (Stan: {p['liczba']})": p for p in produkty}
    wybrany_label = c_sel.selectbox("Wybierz produkt", list(opcje.keys()))
    ile_odjac = c_num.number_input("Ile sztuk odjąć?", min_value=1, step=1)
    
    if c_btn.button("Zatwierdź wydanie", use_container_width=True):
        prod_obj = opcje[wybrany_label]
        if ile_odjac > prod_obj["liczba"]:
            st.error("Błąd: Za mała ilość na stanie!")
        else:
            nowy_stan = prod_obj["liczba"] - ile_odjac
            aktualizuj_stan(prod_obj["id"], nowy_stan)
            st.success("Stan magazynu zaktualizowany!")
            st.rerun()
else:
    st.info("Magazyn jest obecnie pusty.")

st.markdown("---")
st.caption("Aplikacja Magazynowa | Supabase + Streamlit")
