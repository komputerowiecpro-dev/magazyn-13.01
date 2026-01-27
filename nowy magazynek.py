import streamlit as st
import pandas as pd
from supabase import create_client
import time

# =============================
# 1. KONFIGURACJA
# =============================
st.set_page_config(page_title="Magazyn & BLIK Pro", layout="wide", page_icon="📦")

@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Błąd połączenia z Supabase: {e}")
        return None

supabase = init_connection()

# =============================
# 2. FUNKCJE BAZY DANYCH
# =============================

def pobierz_saldo():
    try:
        res = supabase.table("finanse").select("saldo").eq("id", 1).execute()
        return float(res.data[0]["saldo"]) if res.data else 0.0
    except: return 0.0

def zrealizuj_wplate(kwota):
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
        st.error(f"Błąd zapisu produktu: {e}")
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

# --- SIDEBAR: PORTFEL I BLIK ---
st.sidebar.title("💰 Twój Portfel")
saldo_obecne = pobierz_saldo()
st.sidebar.metric("Saldo konta", f"{saldo_obecne:,.2f} PLN")

st.sidebar.divider()
st.sidebar.subheader("Doładuj konto BLIK")

if "proces_blik" not in st.session_state:
    st.session_state.proces_blik = False
    st.session_state.kwota_do_wplaty = 0.0

with st.sidebar.form("form_wplata"):
    kwota_input = st.number_input("Kwota doładowania (PLN)", min_value=1.0, step=10.0)
    if st.form_submit_button("Wpłać przez BLIK", use_container_width=True):
        st.session_state.proces_blik = True
        st.session_state.kwota_do_wplaty = kwota_input
        st.rerun()

# --- MODAL PŁATNOŚCI BLIK ---
if st.session_state.proces_blik:
    st.markdown("---")
    st.warning(f"### 📲 Autoryzacja płatności: {st.session_state.kwota_do_wplaty} PLN")
    
    c_img, c_form = st.columns([1, 3])
    with c_img:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Blik_logo.svg/1200px-Blik_logo.svg.png", width=120)
    
    with c_form:
        blik_code = st.text_input("Wpisz 6-cyfrowy kod BLIK z aplikacji bankowej", max_chars=6, placeholder="000 000")
        
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("✅ POTWIERDZAM", use_container_width=True):
            if len(blik_code) == 6 and blik_code.isdigit():
                with st.spinner("Łączenie z bankiem..."):
                    time.sleep(2) # Symulacja procesowania
                    if zrealizuj_wplate(st.session_state.kwota_do_wplaty):
                        st.success("🎉 Płatność pomyślna! Środki dodane.")
                        st.session_state.proces_blik = False
                        time.sleep(1.5)
                        st.rerun()
            else:
                st.error("Kod BLIK musi składać się z 6 cyfr!")
        
        if col_b2.button("❌ ANULUJ", use_container_width=True):
            st.session_state.proces_blik = False
            st.rerun()
    st.stop() # Blokuje resztę strony podczas płatności

# --- PANEL GŁÓWNY: MAGAZYN ---
st.title("📦 System Zarządzania Magazynem")

# SEKCJA: DODAWANIE
with st.expander("➕ Dodaj nowy produkt do bazy", expanded=False):
    kategorie = pobierz_kategorie()
    if kategorie:
        mapa_kat = {k['nazwa']: k['id'] for k in kategorie}
        
        c1, c2, c3 = st.columns([2, 1, 2])
        nazwa_in = c1.text_input("Nazwa przedmiotu")
        ilosc_in = c2.number_input("Ilość", min_value=1, step=1)
        kat_in = c3.selectbox("Kategoria", list(mapa_kat.keys()))
        
        if st.button("Zatwierdź i wprowadź"):
            if nazwa_in:
                if dodaj_produkt(nazwa_in, ilosc_in, mapa_kat[kat_in]):
                    st.success(f"Wprowadzono: {nazwa_in}")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Podaj nazwę produktu!")
    else:
        st.error("Błąd: Nie znaleziono kategorii w bazie danych. Dodaj je w Supabase!")

st.divider()

# SEKCJA: LISTA I WYDAWANIE
produkty = pobierz_produkty()
kategorie_lista = pobierz_kategorie()
mapa_id_kat = {k['id']: k['nazwa'] for k in kategorie_lista}

if produkty:
    st.subheader("📋 Stan magazynowy")
    df = pd.DataFrame(produkty)
    
    # Mapowanie kategorii dla czytelności
    if 'kategoria_id' in df.columns:
        df['kategoria'] = df['kategoria_id'].map(mapa_id_kat)
    
    kolumny = [c for c in ["nazwa", "liczba", "kategoria"] if c in df.columns]
    st.dataframe(df[kolumny], use_container_width=True)

    st.markdown("### ➖ Wydaj produkt")
    # Tworzymy listę produktów z ich ID
    opcje_wydania = {f"{p['nazwa']} (Stan: {p.get('liczba', 0)})": p for p in produkty if 'id' in p}
    
    if opcje_wydania:
        col_w1, col_w2, col_w3 = st.columns([2, 1, 1])
        wybor_w = col_w1.selectbox("Który produkt wydajemy?", list(opcje_wydania.keys()), key="sel_w")
        ile_w = col_w2.number_input("Ilość sztuk", min_value=1, step=1, key="num_w")
        
        if col_w3.button("Zatwierdź wydanie", use_container_width=True):
            wybrany_p = opcje_wydania[wybor_w]
            if ile_w <= wybrany_p['liczba']:
                nowy_stan = wybrany_p['liczba'] - ile_w
                if aktualizuj_stan(wybrany_p['id'], nowy_stan):
                    st.toast(f"Wydano {ile_w} sztuk")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Błąd: Nie masz tyle towaru na stanie!")
else:
    st.info("Magazyn jest obecnie pusty.")

st.sidebar.caption("Połączono z bazą danych | Status: Online")
