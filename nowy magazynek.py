import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import time

# =============================
# 1. KONFIGURACJA
# =============================
st.set_page_config(page_title="Biznes Pro 2026", layout="wide", page_icon="🛒")

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
    except: return 0.0

def aktualizuj_saldo(nowe_saldo):
    try:
        supabase.table("finanse").update({"saldo": nowe_saldo}).eq("id", 1).execute()
        return True
    except: return False

def pobierz_produkty():
    try:
        res = supabase.table("produkty").select("*").execute()
        return res.data if res.data else []
    except: return []

def pobierz_sprzedaz():
    try:
        res = supabase.table("sprzedaz").select("nazwa_produktu, ilosc").execute()
        return res.data if res.data else []
    except: return []

def zapisz_sprzedaz(p_id, nazwa, ilosc):
    try:
        supabase.table("sprzedaz").insert({
            "produkt_id": p_id,
            "nazwa_produktu": nazwa,
            "ilosc": ilosc
        }).execute()
    except: pass

def usun_produkt_z_bazy(p_id):
    try:
        supabase.table("produkty").delete().eq("id", p_id).execute()
        return True
    except: return False

def sprawdz_rabat(kod_tekst):
    try:
        res = supabase.table("kody_rabatowe").select("*").eq("kod", kod_tekst).execute()
        return res.data[0]['znizka_procent'] if res.data else 0
    except: return 0

def kup_produkt(p_obj, ilosc_sztuk, cena_koncowa):
    obecne_saldo = pobierz_saldo()
    calkowity_koszt = cena_koncowa * ilosc_sztuk
    
    if obecne_saldo >= calkowity_koszt:
        aktualizuj_saldo(obecne_saldo - calkowity_koszt)
        nowa_ilosc = p_obj['liczba'] - ilosc_sztuk
        supabase.table("produkty").update({"liczba": nowa_ilosc}).eq("id", p_obj['id']).execute()
        zapisz_sprzedaz(p_obj['id'], p_obj['nazwa'], ilosc_sztuk)
        return True
    return False

# =============================
# 3. LOGOWANIE
# =============================
if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False
    st.session_state.rola = None

if not st.session_state.zalogowany:
    st.title("🔐 Logowanie do systemu")
    col_l1, col_l2 = st.columns(2)
    user = col_l1.text_input("Użytkownik (admin/klient)")
    pwd = col_l2.text_input("Hasło", type="password")
    if st.button("Zaloguj się", use_container_width=True):
        if user == "admin" and pwd == "admin123":
            st.session_state.zalogowany = True
            st.session_state.rola = "admin"
            st.rerun()
        elif user == "klient" and pwd == "klient123":
            st.session_state.zalogowany = True
            st.session_state.rola = "klient"
            st.rerun()
        else:
            st.error("Błędny login lub hasło!")
    st.stop()

# =============================
# 4. INTERFEJS UŻYTKOWNIKA
# =============================

with st.sidebar:
    st.title(f"Zalogowano jako: {st.session_state.rola.upper()}")
    if st.button("Wyloguj"):
        st.session_state.zalogowany = False
        st.rerun()
    st.divider()
    # Kody rabatowe (widoczne dla obu ról)
    st.header("🎟️ Kod rabatowy")
    kod_input = st.text_input("Wpisz kod tutaj")
    znizka = sprawdz_rabat(kod_input)
    if znizka > 0:
        st.success(f"Aktywowano: -{znizka}%")

# DEFINICJA ZAKŁADEK (Dla Admina wszystkie, dla Klienta tylko Sklep i BLIK)
if st.session_state.rola == "admin":
    tab1, tab2, tab3, tab4 = st.tabs(["📊 STATYSTYKI", "📦 MAGAZYN", "🛍️ SKLEP", "💰 BLIK"])
else:
    tab3, tab4 = st.tabs(["🛍️ SKLEP", "💰 DOŁADUJ KONTO"])
    tab1, tab2 = None, None # Klient nie ma do nich dostępu

# --- ZAKŁADKA 1: STATYSTYKI (ADMIN) ---
if tab1:
    with tab1:
        st.title("📊 Statystyki Sprzedaży")
        dane_s = pobierz_sprzedaz()
        if dane_s:
            df_s = pd.DataFrame(dane_s)
            top_s = df_s.groupby("nazwa_produktu")["ilosc"].sum().reset_index()
            
            c1, c2 = st.columns(2)
            with c1:
                fig_pie = px.pie(top_s, values='ilosc', names='nazwa_produktu', title="Co najlepiej się sprzedaje?", hole=0.3)
                st.plotly_chart(fig_pie, use_container_width=True)
            with c2:
                fig_bar = px.bar(top_s, x='nazwa_produktu', y='ilosc', title="Ilość sprzedanych sztuk", color='ilosc')
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Brak danych o sprzedaży.")

# --- ZAKŁADKA 2: MAGAZYN (ADMIN) ---
if tab2:
    with tab2:
        st.title("📦 Zarządzanie Magazynem")
        
        with st.expander("➕ Dodaj nowy produkt"):
            m_nazwa = st.text_input("Nazwa przedmiotu")
            m_ilosc = st.number_input("Ilość", min_value=1)
            m_cena = st.number_input("Cena (PLN)", min_value=0.0)
            m_img = st.text_input("Link do zdjęcia (URL)")
            if st.button("Zapisz w bazie"):
                supabase.table("produkty").insert({"nazwa": m_nazwa, "liczba": m_ilosc, "cena": m_cena, "image_url": m_img}).execute()
                st.success("Produkt dodany!")
                st.rerun()
        
        st.divider()
        st.subheader("🗑️ Usuwanie produktów")
        prods = pobierz_produkty()
        if prods:
            df_p = pd.DataFrame(prods)
            st.dataframe(df_p[["id", "nazwa", "liczba", "cena"]], use_container_width=True)
            opcje_del = {f"{p['nazwa']} (ID: {p['id']})": p['id'] for p in prods}
            cel = st.selectbox("Wybierz do usunięcia", list(opcje_del.keys()))
            if st.button("USUŃ NA ZAWSZE", type="primary"):
                if usun_produkt_z_bazy(opcje_del[cel]):
                    st.success("Usunięto.")
                    st.rerun()

# --- ZAKŁADKA 3: SKLEP (DLA WSZYSTKICH) ---
with tab3:
    st.title("🛍️ Sklep Online")
    saldo = pobierz_saldo()
    st.subheader(f"Twoje środki: :green[{saldo:.2f} PLN]")
    
    produkty = pobierz_produkty()
    if produkty:
        cols = st.columns(3)
        for idx, p in enumerate(produkty):
            if p.get('liczba', 0) > 0:
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.image(p.get('image_url') or "https://via.placeholder.com/150", use_container_width=True)
                        st.subheader(p['nazwa'])
                        cena_org = float(p.get('cena') or 0)
                        cena_final = cena_org * (1 - znizka/100)
                        
                        if znizka > 0:
                            st.write(f"Cena: ~~{cena_org}~~ **{cena_final:.2f} PLN**")
                        else:
                            st.write(f"Cena: **{cena_org} PLN**")
                        
                        ile = st.number_input(f"Sztuk", min_value=1, max_value=int(p['liczba']), key=f"buy_{p['id']}")
                        if st.button(f"Kup {p['nazwa']}", key=f"btn_{p['id']}", use_container_width=True):
                            if kup_produkt(p, ile, cena_final):
                                st.balloons()
                                st.success("Kupiono!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Brak środków!")

# --- ZAKŁADKA 4: BLIK (DLA WSZYSTKICH) ---
with tab4:
    st.title("💰 Doładowanie Portfela")
    with st.container(border=True):
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Blik_logo.svg/1200px-Blik_logo.svg.png", width=100)
        kwota = st.number_input("Kwota (PLN)", min_value=1.0)
        kod = st.text_input("Kod BLIK (6 cyfr)", max_chars=6)
        if st.button("WPŁAĆ TERAZ", use_container_width=True):
            if len(kod) == 6 and kod.isdigit():
                with st.spinner("Łączenie z bankiem..."):
                    time.sleep(2)
                    aktualizuj_saldo(pobierz_saldo() + kwota)
                    st.success("Środki dodane!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Niepoprawny kod BLIK!")
