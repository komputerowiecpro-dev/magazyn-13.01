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

def usun_produkt_z_bazy(p_id):
    """Całkowicie usuwa produkt z tabeli produkty."""
    try:
        supabase.table("produkty").delete().eq("id", p_id).execute()
        return True
    except Exception as e:
        st.error(f"Błąd usuwania: {e}")
        return False

def kup_produkt(p_obj, ilosc_sztuk):
    # Naprawiony błąd TypeError: obsługa ceny None
    cena_jednostkowa = float(p_obj.get('cena') or 0) 
    cena_calkowita = cena_jednostkowa * ilosc_sztuk
    obecne_saldo = pobierz_saldo()
    
    if obecne_saldo < cena_calkowita:
        st.error(f"❌ Za mało środków! Brakuje {(cena_calkowita - obecne_saldo):.2f} PLN")
        return False
    
    try:
        aktualizuj_saldo(obecne_saldo - cena_calkowita)
        supabase.table("produkty").update({"liczba": p_obj['liczba'] - ilosc_sztuk}).eq("id", p_obj['id']).execute()
        return True
    except: return False

# =============================
# 3. INTERFEJS UŻYTKOWNIKA (UI)
# =============================

tab_sklep, tab_magazyn, tab_blik = st.tabs(["🛍️ SKLEP", "📦 MAGAZYN", "💰 DOŁADUJ KONTO"])

# --- ZAKŁADKA: SKLEP ---
with tab_sklep:
    st.title("🛍️ Nasza Oferta")
    saldo_klienta = pobierz_saldo()
    st.subheader(f"Twoje saldo: :green[{saldo_klienta:.2f} PLN]")
    
    produkty_sklep = pobierz_produkty()
    if produkty_sklep:
        cols = st.columns(3)
        for idx, p in enumerate(produkty_sklep):
            if p.get('liczba', 0) > 0:
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.image(p.get('image_url') or "https://via.placeholder.com/150", use_container_width=True)
                        st.subheader(p['nazwa'])
                        # Wyświetlanie ceny (obsługa None)
                        cena_pokaz = p.get('cena') or 0
                        st.write(f"Cena: **{cena_pokaz} PLN**")
                        
                        ile_kupic = st.number_input(f"Sztuk ({p['nazwa']})", min_value=1, max_value=int(p['liczba']), key=f"n_{p['id']}")
                        if st.button(f"Kupuję", key=f"btn_{p['id']}", use_container_width=True):
                            if kup_produkt(p, ile_kupic):
                                st.balloons()
                                st.success(f"Zakupiono {p['nazwa']}!")
                                time.sleep(1)
                                st.rerun()
    else:
        st.info("Sklep jest pusty.")

# --- ZAKŁADKA: MAGAZYN (TU JEST USUWANIE) ---
with tab_magazyn:
    st.title("📦 Panel Magazyniera")
    
    # 1. Dodawanie
    with st.expander("➕ Dodaj nowy produkt"):
        m_nazwa = st.text_input("Nazwa")
        m_ilosc = st.number_input("Ilość", min_value=1)
        m_cena = st.number_input("Cena", min_value=0.0)
        if st.button("Zatwierdź"):
            supabase.table("produkty").insert({"nazwa": m_nazwa, "liczba": m_ilosc, "cena": m_cena}).execute()
            st.rerun()

    st.divider()

    # 2. Zarządzanie / Usuwanie
    st.subheader("📋 Stan i Usuwanie")
    wszystkie_p = pobierz_produkty()
    if wszystkie_p:
        df = pd.DataFrame(wszystkie_p)
        st.dataframe(df[["id", "nazwa", "liczba", "cena"]], use_container_width=True)
        
        st.markdown("### 🗑️ Usuń produkt z systemu")
        opcje_usuwania = {f"{p['nazwa']} (ID: {p['id']})": p['id'] for p in wszystkie_p}
        do_usuniecia = st.selectbox("Wybierz produkt do skasowania", list(opcje_usuwania.keys()))
        
        if st.button("USUŃ PRODUKT NA ZAWSZE", type="primary"):
            id_p = opcje_usuwania[do_usuniecia]
            if usun_produkt_z_bazy(id_p):
                st.toast(f"Usunięto produkt!")
                time.sleep(1)
                st.rerun()
    else:
        st.info("Brak produktów do wyświetlenia.")

# --- ZAKŁADKA: BLIK ---
with tab_blik:
    st.title("📲 Doładowanie BLIK")
    kwota = st.number_input("Kwota", min_value=1.0)
    kod = st.text_input("Kod BLIK", max_chars=6)
    if st.button("WPŁAĆ"):
        if len(kod) == 6:
            aktualizuj_saldo(pobierz_saldo() + kwota)
            st.success("Gotowe!")
            st.rerun()
