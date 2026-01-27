import streamlit as st
import pandas as pd
from supabase import create_client

# =============================
# 1. KONFIGURACJA I POŁĄCZENIE
# =============================
st.set_page_config(page_title="Magazyn Pro", layout="wide", page_icon="📦")

@st.cache_resource
def init_connection():
    """Inicjalizuje połączenie z bazą Supabase."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Błąd konfiguracji połączenia: {e}")
        return None

supabase = init_connection()

# =============================
# 2. FUNKCJE LOGIKI BIZNESOWEJ
# =============================

def pobierz_produkty():
    """Pobiera wszystkie produkty z bazy danych."""
    try:
        res = supabase.table("produkty").select("*").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"❌ Nie można pobrać produktów: {e}")
        return []

def pobierz_kategorie():
    """Pobiera listę kategorii dla selectboxów."""
    try:
        res = supabase.table("kategorie").select("id, nazwa").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"❌ Nie można pobrać kategorii: {e}")
        return []

def dodaj_produkt(nazwa, liczba, kategoria_id):
    """Dodaje nowy rekord do tabeli 'produkty'."""
    try:
        data = {
            "nazwa": nazwa,
            "liczba": liczba,
            "kategoria_id": kategoria_id
        }
        supabase.table("produkty").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"❌ Błąd zapisu w bazie danych: {e}")
        # Podpowiedź dla Ciebie, jeśli nazwa kolumny w bazie jest inna
        st.info("💡 Sprawdź, czy kolumna w Supabase na pewno nazywa się 'kategoria_id'.")
        return False

def aktualizuj_stan(p_id, nowa_liczba):
    """Aktualizuje ilość towaru lub usuwa go, jeśli stan wynosi 0."""
    try:
        if nowa_liczba > 0:
            supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", p_id).execute()
        else:
            supabase.table("produkty").delete().eq("id", p_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ Błąd podczas aktualizacji stanu: {e}")
        return False

# =============================
# 3. INTERFEJS UŻYTKOWNIKA (UI)
# =============================

st.title("📦 System Zarządzania Magazynem")
st.markdown("Zarządzaj zapasami w czasie rzeczywistym.")

# Pobranie aktualnych danych
kategorie_data = pobierz_kategorie()
produkty_data = pobierz_produkty()

# Przygotowanie mapowań dla łatwiejszej obsługi UI
mapa_kat_nazwa_id = {k["nazwa"]: k["id"] for k in kategorie_data}
mapa_kat_id_nazwa = {k["id"]: k["nazwa"] for k in kategorie_data}

# --- SEKCJA 1: DODAWANIE ---
st.subheader("➕ Dodaj nowy produkt")
with st.form("form_dodawania", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 2])
    
    nazwa_input = col1.text_input("Nazwa produktu", placeholder="np. Koszulka bawełniana")
    liczba_input = col2.number_input("Ilość startowa", min_value=1, step=1, value=1)
    
    if kategorie_data:
        kat_wybor = col3.selectbox("Kategoria", options=list(mapa_kat_nazwa_id.keys()))
    else:
        st.warning("Brak zdefiniowanych kategorii w bazie!")
        kat_wybor = None

    if st.form_submit_button("Zatwierdź i dodaj"):
        if nazwa_input and kat_wybor:
            id_kat = mapa_kat_nazwa_id[kat_wybor]
            if dodaj_produkt(nazwa_input, liczba_input, id_kat):
                st.success(f"Dodano produkt: {nazwa_input}")
                st.rerun()
        else:
            st.error("Uzupełnij wszystkie pola przed zapisem.")

st.divider()

# --- SEKCJA 2: TABELA I WYDAWANIE ---
st.subheader("📋 Aktualny stan magazynowy")

if produkty_data:
    # Przygotowanie danych do tabeli
    df = pd.DataFrame(produkty_data)
    
    # Mapowanie ID na nazwy dla czytelności
    if "kategoria_id" in df.columns:
        df["kategoria"] = df["kategoria_id"].map(mapa_kat_id_nazwa)
    
    # Wyświetlanie tylko istotnych kolumn
    cols_to_show = ["nazwa", "liczba", "kategoria"]
    st.dataframe(df[cols_to_show], use_container_width=True)

    # Logika wydawania towaru
    st.markdown("### ➖ Operacja: Wydaj towar")
    c_p, c_l, c_b = st.columns([2, 1, 1])
    
    # Klucz unikalny dla selectboxa, aby uniknąć konfliktów przy odświeżaniu
    lista_produktow = {f"{p['nazwa']} (Dostępne: {p['liczba']})": p for p in produkty_data}
    wybrany_label = c_p.selectbox("Wybierz produkt z listy", options=list(lista_produktow.keys()))
    ile_odjac = c_l.number_input("Ile sztuk wydajesz?", min_value=1, step=1)

    if c_b.button("Zatwierdź wydanie", use_container_width=True):
        produkt_obj = lista_produktow[wybrany_label]
        if ile_odjac > produkt_obj["liczba"]:
            st.error("Nie możesz wydać więcej niż masz na stanie!")
        else:
            nowy_stan = produkt_obj["liczba"] - ile_odjac
            if aktualizuj_stan(produkt_obj["id"], nowy_stan):
                st.toast(f"Wydano {ile_odjac} szt. {produkt_obj['nazwa']}", icon="✅")
                st.rerun()
else:
    st.info("Magazyn jest obecnie pusty. Dodaj pierwszy produkt powyżej.")

st.sidebar.markdown("---")
st.sidebar.caption("Połączono z: Supabase Cloud")
st.sidebar.caption("Wersja aplikacji: 1.2")
