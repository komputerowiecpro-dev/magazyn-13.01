import streamlit as st
import pandas as pd
from supabase import create_client

# =============================
# KONFIGURACJA
# =============================
st.set_page_config(
page_title="Magazyn – produkty",
layout="wide"
)

supabase = create_client(
st.secrets["SUPABASE_URL"],
st.secrets["SUPABASE_KEY"]
)

# =============================
# FUNKCJE BAZY
# =============================
def pobierz_produkty():
res = supabase.table("produkty").select("*").execute()
return res.data or []

def pobierz_kategorie():
res = supabase.table("kategorie").select("id, nazwa").execute()
return res.data or []

def dodaj_produkt(nazwa, liczba, kategoria_id):
supabase.table("produkty").insert(
{
"nazwa": nazwa,
"liczba": liczba,
"kategoria_id": kategoria_id
}
).execute()

def zmniejsz_ilosc_produktu(produkt_id, ile_usunac):
# pobierz aktualny stan
res = supabase.table("produkty") \
.select("liczba") \
.eq("id", produkt_id) \
.single() \
.execute()

aktualna_liczba = res.data["liczba"]
nowa_liczba = aktualna_liczba - ile_usunac

if nowa_liczba > 0:
# UPDATE
supabase.table("produkty") \
.update({"liczba": nowa_liczba}) \
.eq("id", produkt_id) \
.execute()
else:
# DELETE jeśli 0 lub mniej
supabase.table("produkty") \
.delete() \
.eq("id", produkt_id) \
.execute()

# =============================
# UI
# =============================
st.title("📦 Magazyn – produkty")
st.markdown("---")

# =============================
# DODAWANIE PRODUKTU
# =============================
st.subheader("➕ Dodaj produkt")

kategorie = pobierz_kategorie()
mapa_kategorii = {k["nazwa"]: k["id"] for k in kategorie}

with st.form("formularz_dodaj"):
nazwa = st.text_input("Nazwa produktu")
liczba = st.number_input("Liczba sztuk", min_value=1, step=1)

if kategorie:
wybrana_kategoria = st.selectbox(
"Kategoria",
list(mapa_kategorii.keys())
)
else:
st.error("Brak kategorii w bazie")
wybrana_kategoria = None

submit = st.form_submit_button("Dodaj")

if submit and nazwa and wybrana_kategoria:
dodaj_produkt(
nazwa=nazwa,
liczba=liczba,
kategoria_id=mapa_kategorii[wybrana_kategoria]
)
st.success("Produkt dodany")
st.rerun()

st.markdown("---")

# =============================
# LISTA + ZMNIEJSZANIE ILOŚCI
# =============================
st.subheader("📋 Lista produktów")

produkty = pobierz_produkty()

if produkty:
df = pd.DataFrame(produkty)

# mapowanie kategorii ID → nazwa
if kategorie and "kategoria_id" in df.columns:
mapa_id_nazwa = {k["id"]: k["nazwa"] for k in kategorie}
df["kategoria"] = df["kategoria_id"].map(mapa_id_nazwa)

st.dataframe(
df[["nazwa", "liczba", "kategoria"]],
use_container_width=True
)

st.markdown("### ➖ Zmniejsz ilość produktu")

mapa = {
f'{p["nazwa"]} (stan: {p["liczba"]})': p
for p in produkty
}

wybrany = st.selectbox("Wybierz produkt", mapa.keys())
ile_usunac = st.number_input(
"Ile sztuk usunąć",
min_value=1,
step=1
)

if st.button("Zmniejsz stan"):
produkt = mapa[wybrany]

if ile_usunac > produkt["liczba"]:
st.error("Nie można usunąć więcej niż jest w magazynie")
else:
zmniejsz_ilosc_produktu(
produkt_id=produkt["id"],
ile_usunac=ile_usunac
)
st.success("Stan magazynu zaktualizowany")
st.rerun()
else:
st.info("Brak produktów w magazynie")

st.caption("Supabase + Streamlit • magazyn z kontrolą ilości")




plus baza
streamlit
pandas
supabase
