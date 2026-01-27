import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import time

# =============================
# 1. KONFIGURACJA I STYLIZACJA (Innowacyjny Wygląd)
# =============================
st.set_page_config(page_title="PRO Store 2026", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .stButton>button { border-radius: 12px; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .product-card { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# =============================
# 2. FUNKCJE LOGIKI BIZNESOWEJ
# =============================

def pobierz_saldo():
    res = supabase.table("finanse").select("saldo").eq("id", 1).execute()
    return float(res.data[0]["saldo"]) if res.data else 0.0

def pobierz_produkty():
    res = supabase.table("produkty").select("*").order("nazwa").execute()
    return res.data if res.data else []

def pobierz_srednia_ocen(p_id):
    res = supabase.table("opinie").select("gwiazdki").eq("produkt_id", p_id).execute()
    if res.data:
        oceny = [o['gwiazdki'] for o in res.data]
        return sum(oceny) / len(oceny), len(oceny)
    return 0, 0

def kup_produkt(p_obj, ilosc_sztuk, cena_final):
    obecne_saldo = pobierz_saldo()
    koszt = cena_final * ilosc_sztuk
    if obecne_saldo >= koszt:
        # Płatność i Magazyn
        supabase.table("finanse").update({"saldo": obecne_saldo - koszt}).eq("id", 1).execute()
        supabase.table("produkty").update({"liczba": p_obj['liczba'] - ilosc_sztuk}).eq("id", p_obj['id']).execute()
        # Zapis sprzedazy do wykresów
        supabase.table("sprzedaz").insert({"produkt_id": p_obj['id'], "nazwa_produktu": p_obj['nazwa'], "ilosc": ilosc_sztuk}).execute()
        return True
    return False

# =============================
# 3. LOGOWANIE
# =============================
if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False

if not st.session_state.zalogowany:
    st.title("🔐 Witaj w PRO Store")
    u = st.text_input("Login")
    p = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        if u == "admin" and p == "admin123":
            st.session_state.zalogowany, st.session_state.rola = True, "admin"
            st.rerun()
        elif u == "klient" and p == "klient123":
            st.session_state.zalogowany, st.session_state.rola = True, "klient"
            st.rerun()
    st.stop()

# =============================
# 4. INTERFEJS GŁÓWNY
# =============================
with st.sidebar:
    st.title("🛍️ Menu")
    st.write(f"Zalogowany jako: **{st.session_state.rola.upper()}**")
    if st.button("Wyloguj"):
        st.session_state.zalogowany = False
        st.rerun()
    st.divider()
    kod_rabatowy = st.text_input("Masz kod rabatowy?")
    res_rabat = supabase.table("kody_rabatowe").select("znizka_procent").eq("kod", kod_rabatowy).execute()
    znizka = res_rabat.data[0]['znizka_procent'] if res_rabat.data else 0
    if znizka > 0: st.success(f"Rabat -{znizka}%!")

if st.session_state.rola == "admin":
    tabs = st.tabs(["📈 STATYSTYKI", "📦 MAGAZYN", "🛒 SKLEP", "💸 BLIK"])
else:
    tabs = st.tabs(["🛒 SKLEP", "💸 DOŁADUJ KONTO"])

# --- STATYSTYKI (ADMIN) ---
if st.session_state.rola == "admin":
    with tabs[0]:
        st.title("📊 Wyniki Sprzedaży")
        s_data = supabase.table("sprzedaz").select("*").execute().data
        if s_data:
            df = pd.DataFrame(s_data)
            stats = df.groupby("nazwa_produktu")["ilosc"].sum().reset_index()
            c1, c2 = st.columns(2)
            c1.plotly_chart(px.pie(stats, values='ilosc', names='nazwa_produktu', title="Udział produktów", hole=0.4), use_container_width=True)
            c2.plotly_chart(px.bar(stats, x='nazwa_produktu', y='ilosc', title="Ranking ilościowy", color='ilosc'), use_container_width=True)
        else: st.info("Czekamy na pierwszą sprzedaż!")

    with tabs[1]:
        st.title("📦 Zarządzanie Magazynem")
        with st.expander("Dodaj nowy produkt"):
            n = st.text_input("Nazwa")
            l = st.number_input("Ilość", 1)
            c = st.number_input("Cena", 0.0)
            img = st.text_input("URL Zdjęcia")
            if st.button("Dodaj do bazy"):
                supabase.table("produkty").insert({"nazwa": n, "liczba": l, "cena": c, "image_url": img}).execute()
                st.rerun()
        
        st.subheader("Aktualny Stan")
        prods = pobierz_produkty()
        if prods:
            df_p = pd.DataFrame(prods)
            st.dataframe(df_p[["id", "nazwa", "liczba", "cena"]], use_container_width=True)
            to_del = st.selectbox("Usuń produkt", [p['nazwa'] for p in prods])
            if st.button("USUŃ PRODUKT", type="primary"):
                p_id = [p['id'] for p in prods if p['nazwa'] == to_del][0]
                supabase.table("produkty").delete().eq("id", p_id).execute()
                st.rerun()

# --- SKLEP (ADMIN I KLIENT) ---
shop_tab = tabs[2] if st.session_state.rola == "admin" else tabs[0]
with shop_tab:
    st.title("🛒 Nasza Oferta")
    st.subheader(f"Twoje saldo: {pobierz_saldo():.2f} PLN")
    produkty = pobierz_produkty()
    if produkty:
        cols = st.columns(3)
        for i, p in enumerate(produkty):
            if p['liczba'] > 0:
                with cols[i % 3]:
                    with st.container(border=True):
                        st.image(p.get('image_url') or "https://via.placeholder.com/150")
                        st.subheader(p['nazwa'])
                        
                        # Gwiazdki
                        sr, licz = pobierz_srednia_ocen(p['id'])
                        st.write(f"{'⭐' * int(sr)}{'⚪' * (5-int(sr))} ({licz} opinii)")
                        
                        cena_final = float(p['cena'] or 0) * (1 - znizka/100)
                        st.write(f"Cena: **{cena_final:.2f} PLN**")
                        
                        with st.expander("Oceń"):
                            oc = st.slider("Gwiazdki", 1, 5, 5, key=f"s_{p['id']}")
                            kom = st.text_input("Komentarz", key=f"c_{p['id']}")
                            if st.button("Wyślij", key=f"b_{p['id']}"):
                                supabase.table("opinie").insert({"produkt_id": p['id'], "gwiazdki": oc, "komentarz": kom}).execute()
                                st.toast("Dziękujemy!")
                                time.sleep(1); st.rerun()

                        if st.button(f"Kupuję", key=f"k_{p['id']}", use_container_width=True):
                            if kup_produkt(p, 1, cena_final):
                                st.balloons(); st.success("Kupiono!"); time.sleep(1); st.rerun()
                            else: st.error("Brak środków!")

# --- BLIK / DOŁADOWANIE ---
blik_tab = tabs[3] if st.session_state.rola == "admin" else tabs[1]
with blik_tab:
    st.title("💰 Doładuj Portfel")
    kwota = st.number_input("Kwota PLN", 1.0)
    kod = st.text_input("Kod BLIK (6 cyfr)", max_chars=6)
    if st.button("WPŁAĆ"):
        if len(kod) == 6:
            supabase.table("finanse").update({"saldo": pobierz_saldo() + kwota}).eq("id", 1).execute()
            st.success("Wpłacono!"); time.sleep(1); st.rerun()
