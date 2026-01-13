import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from decimal import Decimal

Base = declarative_base()

# --- MODELE BAZY DANYCH ---

class Kategoria(Base):
    __tablename__ = 'kategorie'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nazwa = Column(String, nullable=False)
    opis = Column(String)
    produkty = relationship("Produkt", back_populates="kategoria_rel")

class Dostawca(Base):
    __tablename__ = 'dostawcy'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nazwa = Column(String, nullable=False, unique=True)
    produkty = relationship("Produkt", back_populates="dostawca_rel")

class Produkt(Base):
    __tablename__ = 'produkty'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nazwa = Column(String, nullable=False)
    liczba = Column(Integer, default=0)
    cena = Column(Numeric(10, 2))
    kategoria_id = Column(Integer, ForeignKey('kategorie.id'))
    dostawca_id = Column(Integer, ForeignKey('dostawcy.id'))
    
    kategoria_rel = relationship("Kategoria", back_populates="produkty")
    dostawca_rel = relationship("Dostawca", back_populates="produkty")

# Połączenie i inicjalizacja bazy
engine = create_engine('sqlite:///magazyn.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# --- INTERFEJS STREAMLIT ---

st.title("📦 System Zarządzania Magazynem")

menu = ["Podgląd Magazynu", "Dodaj Produkt", "Konfiguracja (Kategorie/Dostawcy)"]
choice = st.sidebar.selectbox("Nawigacja", menu)

if choice == "Dodaj Produkt":
    st.subheader("➕ Dodaj nowy przedmiot")
    
    kategorie = session.query(Kategoria).all()
    dostawcy = session.query(Dostawca).all()
    
    if not kategorie or not dostawcy:
        st.warning("⚠️ Skonfiguruj najpierw Kategorie i Dostawców w menu 'Konfiguracja'!")
    else:
        with st.form("form_produkt"):
            nazwa = st.text_input("Nazwa produktu")
            cena = st.number_input("Cena jednostkowa (PLN)", min_value=0.0, step=0.01)
            ilosc = st.number_input("Ilość", min_value=1, step=1)
            
            # Wybór z bazy danych
            kat_opcje = {k.nazwa: k.id for k in kategorie}
            dost_opcje = {d.nazwa: d.id for d in dostawcy}
            
            wybrana_kat = st.selectbox("Kategoria", list(kat_opcje.keys()))
            wybrany_dostawca = st.selectbox("Dostawca (Kurier)", list(dost_opcje.keys()))
            
            if st.form_submit_button("Zatwierdź"):
                nowy = Produkt(
                    nazwa=nazwa,
                    cena=Decimal(str(cena)),
                    liczba=ilosc,
                    kategoria_id=kat_opcje[wybrana_kat],
                    dostawca_id=dost_opcje[wybrany_dostawca]
                )
                session.add(nowy)
                session.commit()
                st.success(f"Dodano: {nazwa} (Dostawca: {wybrany_dostawca})")

elif choice == "Podgląd Magazynu":
    st.subheader("📋 Lista produktów")
    produkty = session.query(Produkt).all()
    for p in produkty:
        with st.expander(f"{p.nazwa} - {p.cena} PLN"):
            st.write(f"**Dostawca:** {p.dostawca_rel.nazwa if p.dostawca_rel else 'Nie przypisano'}")
            st.write(f"**Kategoria:** {p.kategoria_rel.nazwa if p.kategoria_rel else 'Brak'}")
            st.write(f"**Stan:** {p.liczba} szt.")

elif choice == "Konfiguracja (Kategorie/Dostawcy)":
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Zarządzaj Kategoriami")
        nowa_kat = st.text_input("Nowa kategoria")
        if st.button("Dodaj Kategorię"):
            session.add(Kategoria(nazwa=nowa_kat))
            session.commit()
            st.rerun()

    with col2:
        st.write("### Zarządzaj Dostawcami")
        nowy_dostawca = st.text_input("Nazwa kuriera (np. DHL, InPost)")
        if st.button("Dodaj Dostawcę"):
            session.add(Dostawca(nazwa=nowy_dostawca))
            session.commit()
            st.rerun()
