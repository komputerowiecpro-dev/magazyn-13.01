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
