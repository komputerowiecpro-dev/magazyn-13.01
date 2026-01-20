import streamlit as st
import pandas as pd
from supabase import create_client

# =============================
# 1. KONFIGURACJA
# =============================
st.set_page_config(page_title="Magazyn Pro", layout="wide")

@st.cache_resource
def init_connection():
    try:
        # Pobieranie danych z Secrets
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Błąd konfiguracji połączenia: {e}")
        return None

supabase = init_connection()

# =============================
# 2. FUNKCJE BAZY DANYCH
# =============================

def pobierz_produkty():
    """Pobiera listę produktów z bazy."""
    res = supabase.table("produkty").select("*").execute()
    return res.data if res.data else []

def pobierz_kategorie():
    """Pobiera listę kategorii z bazy."""
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return res.data if res.data else []

def dodaj_produkt(nazwa, liczba, kategoria_id):
    """Wstawia nowy wiersz do tabeli produkty."""
    try:
        supabase.table("produkty").insert({
            "nazwa": nazwa,
            "liczba": liczba,
            "kategoria_id": kategoria_id
        }).execute()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu w bazie danych: {e}")
        return False

def aktualizuj_stan(p_id, nowa_liczba):
    """Aktualizuje ilość lub usuwa rekord jeśli liczba = 0."""
    if nowa_liczba > 0:
        supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", p_id).execute()
    else:
        supabase.table("produkty").delete().eq("id", p_id).execute()

# =============================
# 3. INTERFEJS UŻYTKOWNIKA (UI)
# =============================
st.title("📦 System Zarządzania Magazynem")
st.markdown("---")

# Pobranie danych na start
kategorie_data = pobierz_kategorie()
produkty_data = pobierz_produkty()

# Mapy pomocnicze
mapa_nazwa_na_id = {k["nazwa"]: k["id"] for k in kategorie_data}
mapa_id_na_nazwe = {k["id"]: k["nazwa"] for k in kategorie_data}

# SEKCJA: DODAWANIE
st.subheader("➕ Dodaj nowy produkt")
with st.form("form_dodaj", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 2])
    
    nazwa_in = col1.text_input("Nazwa produktu")
    liczba_in = col2.number_input("Ilość", min_value=1, step=1, value=1)
    
    if kategorie_data:
        kat_nazwa = col3.selectbox("Wybierz kategorię", list(mapa_nazwa_na_id.keys()))
    else:
        st.warning("⚠️ Brak kategorii! Dodaj je najpierw w Supabase.")
        kat_nazwa = None

    if st.form_submit_button("Zatwierdź produkt"):
        if nazwa_in and kat_nazwa:
            sukces = dodaj_produkt(nazwa_in, liczba_in, mapa_nazwa_na_id[kat_nazwa])
            if sukces:
                st.success(f"Dodano: {nazwa_in}")
                st.rerun()

st.markdown("---")

# SEKCJA: LISTA I WYDAWANIE
st.subheader("📋 Stan magazynowy")

if produkty_data:
    df = pd.DataFrame(produkty_data)
    
    # Mapowanie ID kategorii na czytelną nazwę
    if "kategoria_id" in df.columns:
        df["kategoria"] = df["kategoria_id"].map(mapa_id_na_nazwe)
    
    # Wyświetlanie tabeli (tylko potrzebne kolumny)
    kolumny_pokaz = [c for c in ["nazwa", "liczba", "kategoria"] if c in df.columns]
    st.dataframe(df[kolumny_pokaz], use_container_width=True)

    # WYDAWANIE TOWARU
    st.markdown("### ➖ Wydaj produkt")
    c_sel, c_num, c_btn = st.columns([2, 1, 1])
    
    opcje = {f"{p['nazwa']} (Stan: {p['liczba']})": p for p in produkty_data}
    wybrany_label = c_sel.selectbox("Produkt do wydania", list(opcje.keys()))
    ile_odjac = c_num.number_input("Ile sztuk?", min_value=1, step=1)
    
    if c_btn.button("Zatwierdź wydanie", use_container_width=True):
        p_obj = opcje[wybrany_label]
        if ile_odjac > p_obj["liczba"]:
            st.error("Błąd: Nie masz tyle towaru na stanie!")
        else:
            nowy_stan = p_obj["liczba"] - ile_odjac
            aktualizuj_stan(p_obj["id"], nowy_stan)
            st.success("Zaktualizowano stan magazynu!")
            st.rerun()
else:
    st.info("Magazyn jest obecnie pusty.")

st.caption("Połączono z bazą danych Supabase | v1.1")
