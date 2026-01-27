import streamlit as st
import pandas as pd
from supabase import create_client
import time

# =============================
# 1. KONFIGURACJA
# =============================
st.set_page_config(page_title="Sklep & Magazyn Pro", layout="wide", page_icon="🛒")

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

def pobierz_kategorie():
    try:
        res = supabase.table("kategorie").select("id, nazwa").execute()
        return res.data if res.data else []
    except: return []

def kup_produkt(p_obj, ilosc_sztuk):
    """Logika zakupu: sprawdza saldo, odejmuje środki i zabiera towar."""
    cena_calkowita = float(p_obj.get('cena', 0)) * ilosc_sztuk
    obecne_saldo = pobierz_saldo()
    
    if obecne_saldo < cena_calkowita:
        st.error(f"❌ Za mało środków! Brakuje Ci {(cena_calkowita - obecne_saldo):.2f} PLN")
        return False
    
    nowe_saldo = obecne_saldo - cena_calkowita
    nowa_ilosc = p_obj['liczba'] - ilosc_sztuk
    
    try:
        # 1. Zabierz pieniądze
        aktualizuj_saldo(nowe_saldo)
        # 2. Zabierz towar (jeśli 0, produkt zostaje z liczbą 0 lub można go usunąć)
        supabase.table("produkty").update({"liczba": nowa_ilosc}).eq("id", p_obj['id']).execute()
        return True
    except Exception as e:
        st.error(f"Błąd transakcji: {e}")
        return False

# =============================
# 3. INTERFEJS UŻYTKOWNIKA (UI)
# =============================

# Główne menu w zakładkach
tab_sklep, tab_magazyn, tab_blik = st.tabs(["🛍️ SKLEP", "📦 MAGAZYN", "💰 DOŁADUJ KONTO"])

# --- ZAKŁADKA 1: SKLEP (KLIENT) ---
with tab_sklep:
    st.title("🛍️ Witaj w naszym sklepie")
    saldo_klienta = pobierz_saldo()
    st.subheader(f"Twoje saldo: :green[{saldo_klienta:.2f} PLN]")
    
    produkty_sklep = pobierz_produkty()
    if produkty_sklep:
        df_s = pd.DataFrame(produkty_sklep)
        # Upewniamy się, że mamy kolumnę cena
        if 'cena' not in df_s.columns:
            st.warning("Produkty nie mają ustawionych cen.")
        else:
            # Wyświetlamy tylko produkty dostępne (liczba > 0)
            df_widok = df_s[df_s['liczba'] > 0][["nazwa", "liczba", "cena"]]
            st.dataframe(df_widok, use_container_width=True)
            
            st.markdown("### Złóż zamówienie")
            c1, c2, c3 = st.columns([2, 1, 1])
            
            opcje_zakupu = {f"{p['nazwa']} ({p['cena']} PLN/szt.)": p for p in produkty_sklep if p['liczba'] > 0}
            
            if opcje_zakupu:
                produkt_wybrany = c1.selectbox("Wybierz produkt", list(opcje_zakupu.keys()), key="shop_sel")
                ile_sztuk = c2.number_input("Ile sztuk?", min_value=1, step=1, key="shop_num")
                
                if c3.button("KUP TERAZ 💳", use_container_width=True):
                    dane_p = opcje_zakupu[produkt_wybrany]
                    if ile_sztuk > dane_p['liczba']:
                        st.error("Błąd: Brak wystarczającej ilości towaru!")
                    else:
                        with st.spinner("Przetwarzanie płatności..."):
                            time.sleep(1)
                            if kup_produkt(dane_p, ile_sztuk):
                                st.balloons()
                                st.success(f"Dziękujemy za zakup {dane_p['nazwa']}!")
                                time.sleep(1.5)
                                st.rerun()
            else:
                st.info("Obecnie brak towarów na sprzedaż.")
    else:
        st.info("Sklep jest pusty.")

# --- ZAKŁADKA 2: MAGAZYN (ZARZĄDZANIE) ---
with tab_magazyn:
    st.title("📦 Panel Magazyniera")
    
    with st.expander("➕ Dodaj nowy produkt do oferty"):
        kategorie = pobierz_kategorie()
        mapa_k = {k['nazwa']: k['id'] for k in kategorie}
        
        col_m1, col_m2, col_m3 = st.columns(3)
        m_nazwa = col_m1.text_input("Nazwa produktu")
        m_ilosc = col_m2.number_input("Ilość", min_value=1, step=1)
        m_cena = col_m3.number_input("Cena sprzedaży (PLN)", min_value=0.0, step=1.0)
        
        m_kat = st.selectbox("Wybierz kategorię", list(mapa_k.keys()))
        
        if st.button("Dodaj produkt do bazy"):
            if m_nazwa:
                supabase.table("produkty").insert({
                    "nazwa": m_nazwa, 
                    "liczba": m_ilosc, 
                    "cena": m_cena, 
                    "kategoria_id": mapa_k[m_kat]
                }).execute()
                st.success("Produkt dodany pomyślnie!")
                st.rerun()

# --- ZAKŁADKA 3: DOŁADUJ BLIK ---
with tab_blik:
    st.title("📲 Doładowanie konta BLIK")
    
    with st.container(border=True):
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Blik_logo.svg/1200px-Blik_logo.svg.png", width=100)
        kwota_blik = st.number_input("Kwota doładowania (PLN)", min_value=5.0, step=10.0)
        kod_input = st.text_input("Podaj 6-cyfrowy kod BLIK", max_chars=6, placeholder="000 000")
        
        if st.button("WPŁAĆ ŚRODKI", use_container_width=True):
            if len(kod_input) == 6 and kod_input.isdigit():
                with st.spinner("Autoryzacja płatności..."):
                    time.sleep(2)
                    aktualne = pobierz_saldo()
                    if aktualizuj_saldo(aktualne + kwota_blik):
                        st.success(f"Konto doładowane o {kwota_blik} PLN!")
                        time.sleep(1.5)
                        st.rerun()
            else:
                st.error("Wprowadź poprawny, 6-cyfrowy kod BLIK!")
