import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# 1. Konfiguracja Bazy Danych
Base = declarative_base()

class Kategoria(Base):
    __tablename__ = 'kategorie'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nazwa = Column(String, nullable=False)
    opis = Column(String)
    produkty = relationship("Produkt", back_populates="kategoria_rel", cascade="all, delete-orphan")

class Produkt(Base):
    __tablename__ = 'produkty'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nazwa = Column(String, nullable=False)
    liczba = Column(Integer)
    cena = Column(Numeric)
    kategoria = Column(Integer, ForeignKey('kategorie.id'))
    kategoria_rel = relationship("Kategoria", back_populates="produkty")

# Połączenie (SQLite dla łatwego wdrożenia)
engine = create_engine('sqlite:///magazyn.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# 2. Interfejs Streamlit
st.title("📦 Zarządzanie Kategoriami")

menu = ["Dodaj Kategorię", "Usuń Kategorię", "Lista Kategorii"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Dodaj Kategorię":
    st.subheader("Nowa Kategoria")
    with st.form("form_add"):
        nazwa = st.text_input("Nazwa Kategorii")
        opis = st.text_area("Opis")
        submit = st.form_submit_button("Zapisz")
        
        if submit and nazwa:
            nowa_kat = Kategoria(nazwa=nazwa, opis=opis)
            session.add(nowa_kat)
            session.commit()
            st.success(f"Dodano kategorię: {nazwa}")

elif choice == "Usuń Kategorię":
    st.subheader("Usuwanie Kategorii")
    kategorie = session.query(Kategoria).all()
    opcje = {k.nazwa: k.id for k in kategorie}
    
    if opcje:
        wybrana = st.selectbox("Wybierz kategorię do usunięcia", list(opcje.keys()))
        if st.button("⚠️ Usuń na zawsze"):
            kat_do_usuniecia = session.query(Kategoria).get(opcje[wybrana])
            session.delete(kat_do_usuniecia)
            session.commit()
            st.warning(f"Usunięto kategorię: {wybrana}")
            st.rerun()
    else:
        st.info("Brak kategorii w bazie.")

elif choice == "Lista Kategorii":
    st.subheader("Wszystkie Kategorie")
    kategorie = session.query(Kategoria).all()
    for k in kategorie:
        st.write(f"**{k.nazwa}** (ID: {k.id})")
        st.caption(f"Opis: {k.opis}")
        st.divider()

import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from decimal import Decimal

# Konfiguracja Bazy Danych
Base = declarative_base()

class Kategoria(Base):
    __tablename__ = 'kategorie'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nazwa = Column(String, nullable=False)
    opis = Column(String)
    produkty = relationship("Produkt", back_populates="kategoria_rel", cascade="all, delete-orphan")

class Produkt(Base):
    __tablename__ = 'produkty'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nazwa = Column(String, nullable=False)
    liczba = Column(Integer, default=0)
    cena = Column(Numeric(10, 2)) # Obsługa ceny jednostkowej (np. 10.99)
    kategoria = Column(Integer, ForeignKey('kategorie.id'))
    kategoria_rel = relationship("Kategoria", back_populates="produkty")

# Inicjalizacja połączenia
engine = create_engine('sqlite:///magazyn.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# --- INTERFEJS STREAMLIT ---
st.set_page_config(page_title="System Magazynowy", layout="centered")
st.title("📦 Zarządzanie Produktami i Cenami")

menu = ["Lista Produktów", "Dodaj Produkt", "Zarządzaj Kategoriami"]
choice = st.sidebar.selectbox("Nawigacja", menu)

if choice == "Dodaj Produkt":
    st.subheader("Dodawanie nowego produktu")
    
    # Pobieranie dostępnych kategorii do selectboxa
    kategorie = session.query(Kategoria).all()
    lista_kat = {k.nazwa: k.id for k in kategorie}
    
    if not lista_kat:
        st.warning("Najpierw dodaj przynajmniej jedną kategorię w menu bocznym!")
    else:
        with st.form("form_produkt"):
            nazwa_p = st.text_input("Nazwa produktu")
            kat_p = st.selectbox("Wybierz kategorię", list(lista_kat.keys()))
            ilosc_p = st.number_input("Ilość (szt.)", min_value=0, step=1)
            # Pole ceny jednostkowej
            cena_p = st.number_input("Cena jednostkowa (PLN)", min_value=0.0, step=0.01, format="%.2f")
            
            submit_p = st.form_submit_button("Dodaj produkt do bazy")
            
            if submit_p and nazwa_p:
                nowy_produkt = Produkt(
                    nazwa=nazwa_p, 
                    kategoria=lista_kat[kat_p], 
                    liczba=ilosc_p, 
                    cena=Decimal(str(cena_p))
                )
                session.add(nowy_produkt)
                session.commit()
                st.success(f"Dodano produkt: {nazwa_p} w cenie {cena_p} PLN")

elif choice == "Lista Produktów":
    st.subheader("Aktualny stan magazynowy")
    produkty = session.query(Produkt).all()
    
    if produkty:
        for p in produkty:
            kat_nazwa = p.kategoria_rel.nazwa if p.kategoria_rel else "Brak"
            st.info(f"**{p.nazwa}**")
            col1, col2, col3 = st.columns(3)
            col1.metric("Cena", f"{p.cena} PLN")
            col2.metric("Ilość", f"{p.liczba} szt.")
            col3.write(f"Kategoria: {kat_nazwa}")
            st.divider()
    else:
        st.write("Baza produktów jest pusta.")

elif choice == "Zarządzaj Kategoriami":
    # (Tutaj kod dodawania/usuwania kategorii z poprzedniej odpowiedzi)
    st.subheader("Zarządzanie kategoriami")
    # ... [kod kategorii] ...
    nazwa_k = st.text_input("Nazwa nowej kategorii")
    if st.button("Dodaj kategorię") and nazwa_k:
        session.add(Kategoria(nazwa=nazwa_k))
        session.commit()
        st.rerun()
