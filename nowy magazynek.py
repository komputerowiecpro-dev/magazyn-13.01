import streamlit as st
import sqlite3

# Połączenie z bazą danych
def get_connection():
    conn = sqlite3.connect('database.db')
    return conn

# Inicjalizacja tabel (zgodnie ze schematem na obrazku)
def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabela kategorie
    c.execute('''CREATE TABLE IF NOT EXISTS kategorie (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazwa TEXT NOT NULL,
                    opis TEXT)''')
    # Tabela produkty
    c.execute('''CREATE TABLE IF NOT EXISTS produkty (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazwa TEXT NOT NULL,
                    liczba INTEGER,
                    cena NUMERIC,
                    kategoria_id INTEGER,
                    FOREIGN KEY (kategoria_id) REFERENCES kategorie(id))''')
    conn.commit()
    conn.close()

init_db()

st.title("Zarządzanie Kategoriami Produktów")

# --- SEKCJA DODAWANIA ---
st.header("Dodaj nową kategorię")
with st.form("form_dodaj"):
    nowa_nazwa = st.text_input("Nazwa kategorii")
    nowy_opis = st.text_area("Opis")
    submit_button = st.form_submit_button("Dodaj")

    if submit_button and nowa_nazwa:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO kategorie (nazwa, opis) VALUES (?, ?)", (nowa_nazwa, nowy_opis))
        conn.commit()
        conn.close()
        st.success(f"Dodano kategorię: {nowa_nazwa}")

# --- SEKCJA LISTY I USUWANIA ---
st.header("Lista kategorii")
conn = get_connection()
c = conn.cursor()
kategorie = c.execute("SELECT id, nazwa, opis FROM kategorie").fetchall()
conn.close()

if kategorie:
    for kat in kategorie:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**{kat[1]}** - {kat[2]}")
        with col2:
            if st.button("Usuń", key=f"del_{kat[0]}"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("DELETE FROM kategorie WHERE id = ?", (kat[0],))
                conn.commit()
                conn.close()
                st.rerun()
else:
    st.info("Brak kategorii w bazie.")

import streamlit as st
import sqlite3

# Konfiguracja strony
st.set_page_config(page_title="Magazyn Lizaczkowy", layout="wide")

def get_connection():
    return sqlite3.connect('database.db')

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabela kategorie
    c.execute('''CREATE TABLE IF NOT EXISTS kategorie (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazwa TEXT NOT NULL)''')
    # Tabela produkty (dodano cenę i liczbę)
    c.execute('''CREATE TABLE IF NOT EXISTS produkty (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazwa TEXT NOT NULL,
                    liczba INTEGER DEFAULT 0,
                    cena_lizaki REAL DEFAULT 0,
                    kategoria_id INTEGER,
                    FOREIGN KEY (kategoria_id) REFERENCES kategorie(id))''')
    conn.commit()
    conn.close()

# Inicjalizacja portfela w sesji (żeby nie znikał podczas klikania)
if 'portfel' not in st.session_state:
    st.session_state.portfel = 0.0

init_db()

# --- SIDEBAR: PORTFEL ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/864/864818.png", width=100)
st.sidebar.header("Twój Portfel")
st.sidebar.metric("Stan konta", f"{st.session_state.portfel:.2f} 🍭 Lizaczków")
if st.sidebar.button("Doładuj 100 🍭"):
    st.session_state.portfel += 100
    st.rerun()

st.title("🍭 System Zarządzania i Sprzedaży")

tabs = st.tabs(["📦 Magazyn", "📂 Kategorie", "💰 Sprzedaż"])

# --- TAB 1: MAGAZYN (PRODUKTY) ---
with tabs[0]:
    st.header("Dodaj Produkt")
    conn = get_connection()
    kats = conn.execute("SELECT * FROM kategorie").fetchall()
    
    with st.form("produkt_form"):
        p_nazwa = st.text_input("Nazwa produktu")
        col1, col2 = st.columns(2)
        p_liczba = col1.number_input("Ilość (szt)", min_value=0, step=1)
        p_cena = col2.number_input("Cena jednostkowa (🍭)", min_value=0.0, step=0.5)
        p_kat = st.selectbox("Kategoria", options=[k[0] for k in kats], format_func=lambda x: next(k[1] for k in kats if k[0] == x) if kats else "Brak")
        
        if st.form_submit_button("Dodaj do magazynu"):
            conn.execute("INSERT INTO produkty (nazwa, liczba, cena_lizaki, kategoria_id) VALUES (?,?,?,?)", 
                         (p_nazwa, p_liczba, p_cena, p_kat))
            conn.commit()
            st.success("Produkt dodany!")
            st.rerun()

# --- TAB 2: KATEGORIE ---
with tabs[1]:
    st.header("Zarządzaj Kategoriami")
    nowa_kat = st.text_input("Nowa kategoria")
    if st.button("Dodaj kategorię"):
        conn.execute("INSERT INTO kategorie (nazwa) VALUES (?)", (nowa_kat,))
        conn.commit()
        st.rerun()
    
    st.write("---")
    for k_id, k_nazwa in kats:
        c1, c2 = st.columns([3, 1])
        c1.write(k_nazwa)
        if c2.button("Usuń", key=f"kat_{k_id}"):
            conn.execute("DELETE FROM kategorie WHERE id = ?", (k_id,))
            conn.commit()
            st.rerun()

# --- TAB 3: SPRZEDAŻ ---
with tabs[2]:
    st.header("Panel Sprzedaży")
    produkty = conn.execute("SELECT p.id, p.nazwa, p.liczba, p.cena_lizaki, k.nazwa FROM produkty p LEFT JOIN kategorie k ON p.kategoria_id = k.id").fetchall()
    
    if produkty:
        for p_id, p_n, p_l, p_c, p_k in produkty:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            col1.write(f"**{p_n}** ({p_k})")
            col2.write(f"{p_l} szt.")
            col3.write(f"{p_c} 🍭/szt")
            if p_l > 0:
                if col4.button("Sprzedaj 1 szt.", key=f"sale_{p_id}"):
                    conn.execute("UPDATE produkty SET liczba = liczba - 1 WHERE id = ?", (p_id,))
                    conn.commit()
                    st.session_state.portfel += p_c
                    st.success(f"Sprzedano {p_n}!")
                    st.rerun()
            else:
                col4.error("Brak towaru")
    else:
        st.info("Magazyn jest pusty.")

conn.close()

# Przycisk resetu projektu (usuwa wszystko)
st.sidebar.write("---")
if st.sidebar.button("⚠️ USUŃ CAŁY PROJEKT (Baza)"):
    import os
    if os.path.exists("database.db"):
        os.remove("database.db")
        st.session_state.portfel = 0
        st.rerun()
