import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import time

# --- KONFIGURACJA ---
st.set_page_config(page_title="Biznes Pro 2026", layout="wide")

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- FUNKCJE ---
def pobierz_saldo():
    res = supabase.table("finanse").select("saldo").eq("id", 1).execute()
    return float(res.data[0]["saldo"]) if res.data else 0.0

def pobierz_produkty():
    res = supabase.table("produkty").select("*").order("nazwa").execute()
    return res.data if res.data else []

# --- LOGOWANIE ---
if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False

if not st.session_state.zalogowany:
    st.title("🔐 Logowanie")
    u = st.text_input("Użytkownik")
    p = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        if u == "admin" and p == "admin123":
            st.session_state.zalogowany, st.session_state.rola = True, "admin"
            st.rerun()
        elif u == "klient" and p == "klient123":
            st.session_state.zalogowany, st.session_state.rola = True, "klient"
            st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.write(f"Rola: **{st.session_state.rola.upper()}**")
    if st.button("Wyloguj"):
        st.session_state.zalogowany = False
        st.rerun()
    st.divider()
    kod = st.text_input("Kod rabatowy")
    znizka = 0
    if kod:
        res_k = supabase.table("kody_rabatowe").select("znizka_procent").eq("kod", kod).execute()
        if res_k.data:
            znizka = res_k.data[0]['znizka_procent']
            st.success(f"Rabat {znizka}%")

# --- ZAKŁADKI ---
if st.session_state.rola == "admin":
    tabs = st.tabs(["📊 STATYSTYKI", "📦 MAGAZYN", "🛍️ SKLEP", "💰 BLIK"])
else:
    tabs = st.tabs(["🛍️ SKLEP", "💰 PORTFEL"])

# 1. STATYSTYKI (ADMIN)
if st.session_state.rola == "admin":
    with tabs[0]:
        st.title("📊 Analiza")
        sprzedaz = supabase.table("sprzedaz").select("*").execute().data
        if sprzedaz:
            df = pd.DataFrame(sprzedaz)
            fig = px.pie(df.groupby("nazwa_produktu")["ilosc"].sum().reset_index(), 
                         values='ilosc', names='nazwa_produktu', title="Co się sprzedaje?")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Brak sprzedaży.")

    # 2. MAGAZYN (ADMIN)
    with tabs[1]:
        st.title("📦 Magazyn")
        with st.expander("Dodaj produkt"):
            n = st.text_input("Nazwa")
            l = st.number_input("Ilość", 1)
            c = st.number_input("Cena", 0.0)
            img = st.text_input("URL zdjęcia")
            if st.button("Zapisz"):
                supabase.table("produkty").insert({"nazwa": n, "liczba": l, "cena": c, "image_url": img}).execute()
                st.rerun()
        
        prods = pobierz_produkty()
        if prods:
            st.dataframe(pd.DataFrame(prods)[["id", "nazwa", "liczba", "cena"]], use_container_width=True)
            to_del = st.selectbox("Usuń produkt", [p['nazwa'] for p in prods])
            if st.button("Usuń", type="primary"):
                p_id = [p['id'] for p in prods if p['nazwa'] == to_del][0]
                supabase.table("produkty").delete().eq("id", p_id).execute()
                st.rerun()

# 3. SKLEP (KLIENT I ADMIN)
shop_tab = tabs[2] if st.session_state.rola == "admin" else tabs[0]
with shop_tab:
    st.title("🛍️ Sklep")
    saldo = pobierz_saldo()
    st.subheader(f"Portfel: :green[{saldo:.2f} PLN]")
    produkty = pobierz_produkty()
    
    if produkty:
        cols = st.columns(3)
        for i, p in enumerate(produkty):
            if p['liczba'] > 0:
                with cols[i % 3]:
                    with st.container(border=True):
                        # Zdjęcie
                        st.image(p.get('image_url') or "https://via.placeholder.com/150", use_container_width=True)
                        st.write(f"### {p['nazwa']}")
                        
                        # Cena po rabacie
                        cena_jednostkowa = float(p['cena'] or 0) * (1 - znizka/100)
                        st.write(f"Cena za 1 szt: **{cena_jednostkowa:.2f} PLN**")
                        st.write(f"Dostępne: {p['liczba']} szt.")
                        
                        # --- SUWAK WYBORU ILOŚCI ---
                        ile_sztuk = st.slider("Wybierz ilość", 1, int(p['liczba']), 1, key=f"s_{p['id']}")
                        koszt_calkowity = cena_jednostkowa * ile_sztuk
                        
                        st.write(f"Razem: **{koszt_calkowity:.2f} PLN**")
                        
                        # Przycisk zakupu
                        if st.button(f"Kupuję {ile_sztuk} szt.", key=f"k_{p['id']}", use_container_width=True):
                            if saldo >= koszt_calkowity:
                                # 1. Odejmij kasę
                                supabase.table("finanse").update({"saldo": saldo - koszt_calkowity}).eq("id", 1).execute()
                                # 2. Zmniejsz magazyn o wybraną ilość
                                supabase.table("produkty").update({"liczba": p['liczba'] - ile_sztuk}).eq("id", p['id']).execute()
                                # 3. Dodaj do statystyk sprzedaży
                                supabase.table("sprzedaz").insert({"produkt_id": p['id'], "nazwa_produktu": p['nazwa'], "ilosc": ile_sztuk}).execute()
                                
                                st.success(f"Kupiono {ile_sztuk} szt.!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Nie masz wystarczająco pieniędzy!")

# 4. PORTFEL / BLIK
blik_tab = tabs[3] if st.session_state.rola == "admin" else tabs[1]
with blik_tab:
    st.title("💰 Doładuj konto")
    ile = st.number_input("Kwota doładowania", 1.0)
    if st.button("Wpłać (BLIK)"):
        supabase.table("finanse").update({"saldo": pobierz_saldo() + ile}).eq("id", 1).execute()
        st.success("Kasa dodana!")
        time.sleep(1)
        st.rerun()
