import streamlit as st
import pandas as pd
from supabase import create_client

# =============================
# 1. KONFIGURACJA
# =============================
st.set_page_config(page_title="Magazyn & Finanse Pro", layout="wide", page_icon="💰")

@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")
        return None

supabase = init_connection()

# =============================
# 2. FUNKCJE BAZY DANYCH
# =============================

# --- MAGAZYN ---
def pobierz_produkty():
    try:
        res = supabase.table("produkty").select("*").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Błąd pobierania produktów: {e}")
        return []

def pobierz_kategorie():
    try:
        res = supabase.table("kategorie").select("id, nazwa").execute()
        return res.data if res.data else []
    except Exception as e:
        return []

def aktualizuj_stan(p_id, nowa_liczba):
    try:
        if nowa_liczba > 0:
            supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", p_id).execute()
        else:
            supabase.table("produkty").delete().eq("id", p_id).execute()
        return True
    except Exception as e:
        st.error(f"Błąd aktualizacji magazynu: {e}")
        return False

# --- FINANSE ---
def pobierz_saldo():
    try:
        # Zakładamy, że masz tabelę 'finanse' z jednym wierszem (id=1)
        res = supabase.table("finanse").select("saldo").eq("id", 1).execute()
        if res.data:
            return float(res.data[0]["saldo"])
        return 0.0
    except Exception as e:
        st.sidebar.warning("Brak tabeli 'finanse' w bazie. Saldo wyświetlane lokalnie.")
        return 0.0

def wplac_pieniadze(kwota):
    try:
        obecne = pobierz_saldo()
        nowe_saldo = obecne + kwota
        supabase.table("finanse").update({"saldo": nowe_saldo}).eq("id", 1).execute()
        return True
    except Exception as e:
        st.error(f"Błąd wpłaty: {e}")
        return False

# =============================
# 3. INTERFEJS UŻYTKOWNIKA (UI)
# =============================

# --- SIDEBAR: FINANSE ---
st.sidebar.title("💰 Twój Portfel")
saldo_aktualne = pobierz_saldo()
st.sidebar.metric("Saldo konta", f"{saldo_aktualne:.2f} PLN")

with st.sidebar.form("form_finanse"):
    kwota_wplaty = st.number_input("Kwota wpłaty (PLN)", min_value=0.01, step=10.0)
    if st.form_submit_button("Wpłać pieniądze"):
        if wplac_pieniadze(kwota_wplaty):
            st.sidebar.success(f"Wpłacono {kwota_wplaty} PLN")
            st.rerun()

st.sidebar.divider()
st.sidebar.caption("System v1.5 | 2026")

# --- PANEL GŁÓWNY ---
st.title("📦 System Zarządzania Magazynem")

produkty_data = pobierz_produkty()
kategorie_data = pobierz_kategorie()
mapa_id_na_nazwe = {k["id"]: k["nazwa"] for k in kategorie_data}

# SEKCJA: LISTA PRODUKTÓW
if produkty_data:
    df = pd.DataFrame(produkty_data)
    
    # Mapowanie kategorii (naprawa błędu z poprzednich kroków)
    if "kategoria_id" in df.columns:
        df["kategoria"] = df["kategoria_id"].map(mapa_id_na_nazwe)
    
    st.subheader("📋 Aktualny stan magazynu")
    pokaz_df = df[["nazwa", "liczba", "kategoria"]] if "kategoria" in df.columns else df
    st.dataframe(pokaz_df, use_container_width=True)

    # SEKCJA: WYDAWANIE (Naprawiony KeyError: "id")
    st.divider()
    st.subheader("➖ Wydaj towar")
    c1, c2, c3 = st.columns([2, 1, 1])
    
    opcje = {f"{p.get('nazwa', '???')} (Stan: {p.get('liczba', 0)})": p for p in produkty_data}
    wybor = c1.selectbox("Wybierz produkt do wydania", list(opcje.keys()))
    ile_wydac = c2.number_input("Ilość", min_value=1, step=1, key="wydaj_num")

    if c3.button("Zatwierdź wydanie", use_container_width=True):
        p_obj = opcje[wybor]
        if "id" not in p_obj:
            st.error("Błąd: Produkt nie posiada kolumny 'id' w bazie danych!")
        elif ile_wydac > p_obj.get("liczba", 0):
            st.error("Niewystarczająca ilość towaru!")
        else:
            nowy_stan = p_obj["liczba"] - ile_wydac
            if aktualizuj_stan(p_obj["id"], nowy_stan):
                st.success("Zaktualizowano stan magazynu!")
                st.rerun()
else:
    st.info("Magazyn jest pusty.")

# SEKCJA: DODAWANIE (Opcjonalnie pod spodem)
st.divider()
st.subheader("➕ Szybkie dodawanie")
with st.expander("Rozwiń, aby dodać nowy przedmiot"):
    # Tutaj możesz wkleić swój stary kod formularza 'form_dodaj'
    st.write("Skorzystaj z formularza dodawania, aby wprowadzić nowe towary.")
