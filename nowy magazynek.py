import streamlit as st
import pandas as pd
from supabase import create_client

# =============================
# 1. KONFIGURACJA
# =============================
st.set_page_config(page_title="Magazyn & Portfel", layout="wide", page_icon="💰")

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

def pobierz_saldo():
    try:
        res = supabase.table("finanse").select("saldo").eq("id", 1).execute()
        return float(res.data[0]["saldo"]) if res.data else 0.0
    except:
        return 0.0

def wplac_pieniadze(kwota):
    try:
        nowe = pobierz_saldo() + kwota
        supabase.table("finanse").update({"saldo": nowe}).eq("id", 1).execute()
        return True
    except: return False

def pobierz_produkty():
    try:
        res = supabase.table("produkty").select("*").execute()
        return res.data if res.data else []
    except: return []

def pobierz_kategorie():
    try:
        res = supabase.table("kategorie").select("id, nazwa").execute()
        return res.data if res.data else []
    except: return []

def dodaj_produkt(nazwa, liczba, kat_id):
    try:
        supabase.table("produkty").insert({"nazwa": nazwa, "liczba": liczba, "kategoria_id": kat_id}).execute()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu: {e}")
        return False

def aktualizuj_stan(p_id, nowa_liczba):
    try:
        if nowa_liczba > 0:
            supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", p_id).execute()
        else:
            supabase.table("produkty").delete().eq("id", p_id).execute()
        return True
    except: return False

# =============================
# 3. INTERFEJS UŻYTKOWNIKA (UI)
# =============================

# SIDEBAR
st.sidebar.title("💰 Twój Portfel")
saldo = pobierz_saldo()
st.sidebar.metric("Saldo konta", f"{saldo:,.2f} PLN")

with st.sidebar.form("wplata"):
    kwota = st.number_input("Wpłać (PLN)", min_value=1.0, step=10.0)
    if st.form_submit_button("Zatwierdź wpłatę"):
        if wplac_pieniadze(kwota):
            st.rerun()

# PANEL GŁÓWNY
st.title("📦 Zarządzanie Magazynem")

# Formularz dodawania
with st.expander("➕ Dodaj nowy produkt", expanded=True):
    kategorie = pobierz_kategorie()
    mapa_kat = {k['nazwa']: k['id'] for k in kategorie}
    
    col1, col2, col3 = st.columns([2, 1, 2])
    n_in = col1.text_input("Nazwa")
    l_in = col2.number_input("Ilość", min_value=1)
    
    if kategorie:
        k_in = col3.selectbox("Kategoria", list(mapa_kat.keys()))
        if st.button("Dodaj produkt"):
            if n_in and dodaj_produkt(n_in, l_in, mapa_kat[k_in]):
                st.success(f"Dodano {n_in}")
                st.rerun()
    else:
        st.warning("⚠️ Brak kategorii w bazie danych!")

st.divider()

# Lista i Wydawanie
produkty = pobierz_produkty()
if produkty:
    df = pd.DataFrame(produkty)
    st.subheader("📋 Stan magazynowy")
    pokaz = [c for c in ["nazwa", "liczba", "kategoria_id"] if c in df.columns]
    st.dataframe(df[pokaz], use_container_width=True)

    st.subheader("➖ Wydaj towar")
    # Zabezpieczenie przed KeyError: 'id'
    opcje = {f"{p['nazwa']} ({p.get('liczba', 0)} szt.)": p for p in produkty if 'id' in p}
    
    if opcje:
        c1, c2, c3 = st.columns([2, 1, 1])
        wyb = c1.selectbox("Wybierz produkt", list(opcje.keys()))
        ile = c2.number_input("Ile sztuk?", min_value=1, key="wyd")
        if c3.button("Zatwierdź wydanie"):
            p_obj = opcje[wyb]
            if ile <= p_obj['liczba']:
                if aktualizuj_stan(p_obj['id'], p_obj['liczba'] - ile):
                    st.success("Wydano towar!")
                    st.rerun()
            else: st.error("Za mało towaru!")
else:
    st.info("Magazyn jest pusty.")
