import streamlit as st
import pandas as pd
from supabase import create_client
import time
import plotly.express as px  # Biblioteka do wykresów

# =============================
# 1. KONFIGURACJA I LOGOWANIE
# =============================
st.set_page_config(page_title="Biznes Pro", layout="wide")

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# Prosty system uprawnień w sesji
if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False
    st.session_state.rola = None

def login():
    st.title("🔐 Logowanie do systemu")
    user = st.text_input("Użytkownik (admin/klient)")
    pwd = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        if user == "admin" and pwd == "admin123":
            st.session_state.zalogowany = True
            st.session_state.rola = "admin"
            st.rerun()
        elif user == "klient" and pwd == "klient123":
            st.session_state.zalogowany = True
            st.session_state.rola = "klient"
            st.rerun()
        else:
            st.error("Błędne dane!")

if not st.session_state.zalogowany:
    login()
    st.stop()

# =============================
# 2. FUNKCJE POMOCNICZE
# =============================

def pobierz_produkty():
    res = supabase.table("produkty").select("*").execute()
    return res.data if res.data else []

def pobierz_saldo():
    res = supabase.table("finanse").select("saldo").eq("id", 1).execute()
    return float(res.data[0]["saldo"]) if res.data else 0.0

def sprawdz_rabat(kod_tekst):
    res = supabase.table("kody_rabatowe").select("*").eq("kod", kod_tekst).execute()
    return res.data[0]['znizka_procent'] if res.data else 0

# =============================
# 3. INTERFEJS (TABS)
# =============================

# Definicja dostępnych zakładek zależnie od roli
if st.session_state.rola == "admin":
    tabs = st.tabs(["📊 STATYSTYKI", "📦 MAGAZYN", "🛍️ SKLEP", "📲 BLIK"])
else:
    tabs = st.tabs(["🛍️ SKLEP", "📲 BLIK"])
    # Klient nie widzi statystyk i magazynu

# --- TAB: STATYSTYKI (TYLKO ADMIN) ---
if st.session_state.rola == "admin":
    with tabs[0]:
        st.title("📊 Analiza Biznesowa")
        produkty = pobierz_produkty()
        if produkty:
            df = pd.DataFrame(produkty)
            df['wartosc'] = df['liczba'] * df['cena'].fillna(0)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Wartość Magazynu", f"{df['wartosc'].sum():.2f} PLN")
            c2.metric("Liczba Produktów", len(df))
            c3.metric("Twoje Saldo (Zysk)", f"{pobierz_saldo():.2f} PLN")

            col_left, col_right = st.columns(2)
            # Wykres 1: Stan magazynowy
            fig1 = px.bar(df, x='nazwa', y='liczba', title="Ilość sztuk na stanie", color='nazwa')
            col_left.plotly_chart(fig1, use_container_width=True)
            
            # Wykres 2: Udział wartościowy
            fig2 = px.pie(df, values='wartosc', names='nazwa', title="Udział produktów w wartości magazynu")
            col_right.plotly_chart(fig2, use_container_width=True)

# --- TAB: MAGAZYN (TYLKO ADMIN) ---
if st.session_state.rola == "admin":
    with tabs[1]:
        st.title("📦 Zarządzanie")
        # Tutaj kod usuwania i dodawania (ten co już masz)
        st.write("Wybierz produkt i kliknij Usuń lub Edytuj...")
        # ... (kod z poprzedniej odpowiedzi)

# --- TAB: SKLEP (ADMIN I KLIENT) ---
shop_tab = tabs[2] if st.session_state.rola == "admin" else tabs[0]
with shop_tab:
    st.title("🛍️ Sklep")
    produkty = pobierz_produkty()
    
    # SYSTEM KODÓW RABATOWYCH
    with st.sidebar:
        st.header("🎟️ Kupony")
        kod_input = st.text_input("Masz kod rabatowy?")
        znizka = sprawdz_rabat(kod_input)
        if znizka > 0:
            st.success(f"Aktywowano rabat: -{znizka}%")
        elif kod_input:
            st.error("Kod nieprawidłowy")

    cols = st.columns(3)
    for idx, p in enumerate(produkty):
        if p['liczba'] > 0:
            with cols[idx % 3]:
                with st.container(border=True):
                    cena_org = float(p.get('cena') or 0)
                    cena_final = cena_org * (1 - znizka/100)
                    
                    st.image(p.get('image_url') or "https://via.placeholder.com/150")
                    st.subheader(p['nazwa'])
                    
                    if znizka > 0:
                        st.write(f"Cena: ~~{cena_org}~~ **{cena_final:.2f} PLN**")
                    else:
                        st.write(f"Cena: **{cena_org} PLN**")
                    
                    if st.button(f"Kupuję", key=f"s_{p['id']}"):
                        # Tutaj wywołanie funkcji kup_produkt z uwzględnieniem cena_final
                        st.success("Dodano do koszyka!")

# Przycisk wylogowania
if st.sidebar.button("Wyloguj"):
    st.session_state.zalogowany = False
    st.rerun()
