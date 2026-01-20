import streamlit as st
import pandas as pd
from supabase import create_client

# =============================
# KONFIGURACJA STRONY
# =============================
st.set_page_config(
    page_title="Magazyn – produkty",
    layout="wide"
)

# Inicjalizacja połączenia z Supabase
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError:
        st.error("Błąd: Brak kluczy SUPABASE_URL lub SUPABASE_KEY w Secrets!")
        st.stop()

supabase = init_connection()

# =============================
# FUNKCJE BAZY DANYCH
# =============================

def pobierz_produkty():
    res = supabase.table("produkty").select("*").execute()
    return res.data or []

def pobierz_kategorie():
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return res.data or []

def dodaj_produkt(nazwa, liczba, kategoria_id):
    try:
        supabase.table("produkty").insert({
            "nazwa": nazwa,
            "liczba": liczba,
            "kategoria_id": kategoria_id
        }).execute()
        return True
    except Exception as e:
        st.error(f"Błąd podczas dodawania: {e}")
        return False

def zmniejsz_ilosc_produktu(produkt_id, ile_usunac):
    res = supabase.table("produkty").select("liczba").eq("id", produkt_id).execute()
    if res.data:
        aktualna_liczba = res.data[0]["liczba"]
        nowa_liczba = aktualna_liczba - ile_usunac
        if nowa_liczba > 0:
            supabase.table("produkty").update({"liczba": nowa_liczba}).eq("id", produkt_id).execute()
        else:
            supabase.table("produkty").delete().eq("id", produkt_id).execute()

# =============================
# INTERFEJS UŻYTKOWNIKA (UI)
# =============================
st.title("📦 Magazyn – produkty")
st.markdown("---")

# Pobieranie danych na starcie
kategorie = pobierz_kategorie()
mapa_kategorii = {k["nazwa"]: k["id"] for k in kategorie}

# -----------------------------
# SEKCJA: DODAWANIE PRODUKTU
# -----------------------------
st.subheader("➕ Dodaj produkt")

with st.form("formularz_dodawania", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        nazwa_input = st.text_input("Nazwa produktu", placeholder="np. Chleb")
    with col2:
        liczba_input = st.number_input("Liczba sztuk", min_value=1, step=1, value=1)
    with col3:
        if kategorie:
            wybrana_kat = st.selectbox("Kategoria", list(mapa_kategorii.keys()))
        else:
            st.warning("⚠️ Brak kategorii w bazie!")
            wybrana_kat = None

    submit = st.form_submit_button("Dodaj do magazynu")

    if submit:
        if not nazwa_input:
            st.error("Podaj nazwę produktu!")
        elif not wybrana_kat:
            st.error("Wybierz kategorię (najpierw dodaj ją w bazie Supabase)!")
        else:
            if dodaj_produkt(nazwa_input, liczba_input, mapa_kategorii[wybrana_kat]):
                st.success(f"Dodano: {nazwa_input}")
                st.rerun()

st.markdown("---")

# -----------------------------
# SEKCJA: LISTA I ZARZĄDZANIE
# -----------------------------
st.subheader("📋 Aktualny stan magazynu")

produkty = pobierz_produkty()

if produkty:
    df = pd.DataFrame(produkty)
    
    # Mapowanie nazw kategorii dla czytelności
    if kategorie:
        mapa_id_nazwa = {k["id"]: k["nazwa"] for k in kategorie}
        df["kategoria"] = df["kategoria_id"].map(mapa_id_nazwa)

    # Wyświetlenie tabeli
    kolumny_widoczne = [c for c in ["nazwa", "liczba", "kategoria"] if c in df.columns]
    st.dataframe(df[kolumny_widoczne], use_container_width=True)

    st.markdown("### ➖ Wydaj produkt")
    
    # Mapa do selectboxa
    mapa_wyboru = {f"{p['nazwa']} (Stan: {p['liczba']})": p for p in produkty}
    wybrany_label = st.selectbox("Wybierz produkt do wydania", list(mapa_wyboru.keys()))
    
    c_ile, c_przycisk = st.columns([1, 1])
    with c_ile:
        ile_wydac = st.number_input("Ilość do odjęcia", min_value=1, step=1)
    with c_przycisk:
        st.write(" ") # wyrównanie
        if st.button("Zatwierdź wydanie", use_container_width=True):
            produkt_wybrany = mapa_wyboru[wybrany_label]
            if ile_wydac > produkt_wybrany["liczba"]:
                st.error("Błąd: Za mało towaru w magazynie!")
            else:
                zmniejsz_ilosc_produktu(produkt_wybrany["id"], ile_wydac)
                st.success("Zaktualizowano stan.")
                st.rerun()
else:
    st.info("Magazyn jest obecnie pusty. Dodaj pierwszy produkt powyżej.")

st.markdown("---")
st.caption("Aplikacja Magazynowa v1.0 | Streamlit + Supabase")
