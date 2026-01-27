import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import time

# --- STYLIZACJA I KONFIGURACJA ---
st.set_page_config(page_title="PRO Store 2026", layout="wide")

# Dodajemy CSS, żeby uniknąć "rozjechania" się strony
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    div.stButton > button:first-child { background-color: #007bff; color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE ---
@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"Błąd połączenia z bazą: {e}")
        return None

supabase = init_connection()

# --- FUNKCJE POMOCNICZE (Zabezpieczone przed None) ---
def pobierz_saldo():
    try:
        res = supabase.table("finanse").select("saldo").eq("id", 1).execute()
        return float(res.data[0]["saldo"]) if res.data else 0.0
    except: return 0.0

def pobierz_produkty():
    try:
        res = supabase.table("produkty").select("*").order("nazwa").execute()
        return res.data if res.data else []
    except: return []

# --- SYSTEM LOGOWANIA ---
if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False

if not st.session_state.zalogowany:
    st.title("🔐 Logowanie")
    u = st.text_input("Login")
    p = st.text_input("Hasło", type="password")
    if st.button("Wejdź"):
        if u == "admin" and p == "admin123":
            st.session_state.zalogowany, st.session_state.rola = True, "admin"
            st.rerun()
        elif u == "klient" and p == "klient123":
            st.session_state.zalogowany, st.session_state.rola = True, "klient"
            st.rerun()
        else:
            st.error("Nieprawidłowe dane!")
    st.stop()

# --- GŁÓWNY INTERFEJS ---
with st.sidebar:
    st.header(f"Witaj, {st.session_state.rola}!")
    if st.button("Wyloguj"):
        st.session_state.zalogowany = False
        st.rerun()
    st.divider()
    kod = st.text_input("Kod rabatowy (np. START20)")
    # Sprawdzanie rabatu
    rabat = 0
    if kod:
        res_r = supabase.table("kody_rabatowe").select("znizka_procent").eq("kod", kod).execute()
        if res_r.data:
            rabat = res_r.data[0]['znizka_procent']
            st.success(f"Aktywny rabat: {rabat}%")

# Zakładki z odpowiednimi uprawnieniami
if st.session_state.rola == "admin":
    t1, t2, t3, t4 = st.tabs(["📊 STATYSTYKI", "📦 MAGAZYN", "🛒 SKLEP", "💳 BLIK"])
else:
    t3, t4 = st.tabs(["🛒 SKLEP", "💳 PORTFEL"])
    t1 = t2 = None

# --- STATYSTYKI (TYLKO ADMIN) ---
if t1:
    with t1:
        st.title("📈 Analiza Biznesu")
        s_res = supabase.table("sprzedaz").select("*").execute()
        if s_res.data:
            df = pd.DataFrame(s_res.data)
            fig = px.bar(df.groupby("nazwa_produktu")["ilosc"].sum().reset_index(), 
                         x='nazwa_produktu', y='ilosc', title="Ranking Sprzedaży")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Brak danych o sprzedaży.")

# --- MAGAZYN (TYLKO ADMIN) ---
if t2:
    with t2:
        st.title("📦 Zarządzanie")
        with st.form("add_form"):
            new_n = st.text_input("Nazwa")
            new_l = st.number_input("Ilość", 1)
            new_c = st.number_input("Cena", 0.0)
            if st.form_submit_button("Dodaj produkt"):
                supabase.table("produkty").insert({"nazwa": new_n, "liczba": new_l, "cena": new_c}).execute()
                st.rerun()

# --- SKLEP (DLA WSZYSTKICH) ---
with t3:
    st.title("🛒 Sklep")
    saldo = pobierz_saldo()
    st.metric("Twoje Środki", f"{saldo:.2f} PLN")
    
    prods = pobierz_produkty()
    if prods:
        cols = st.columns(3)
        for i, p in enumerate(prods):
            with cols[i % 3]:
                with st.container(border=True):
                    st.write(f"### {p['nazwa']}")
                    c_org = float(p.get('cena') or 0)
                    c_final = c_org * (1 - rabat/100)
                    st.write(f"Cena: **{c_final:.2f} PLN**")
                    
                    if st.button(f"Kupuję", key=f"btn_{p['id']}"):
                        if saldo >= c_final and p['liczba'] > 0:
                            # Proces zakupu
                            supabase.table("finanse").update({"saldo": saldo - c_final}).eq("id", 1).execute()
                            supabase.table("produkty").update({"liczba": p['liczba'] - 1}).eq("id", p['id']).execute()
                            supabase.table("sprzedaz").insert({"produkt_id": p['id'], "nazwa_produktu": p['nazwa'], "ilosc": 1}).execute()
                            st.success("Kupiono!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Błąd zakupu!")

# --- BLIK ---
with t4:
    st.title("💳 Doładuj konto")
    kwota = st.number_input("Kwota", 1.0)
    if st.button("Doładuj BLIK"):
        supabase.table("finanse").update({"saldo": pobierz_saldo() + kwota}).eq("id", 1).execute()
        st.success("Dodano środki!")
        time.sleep(1)
        st.rerun()
