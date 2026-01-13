import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from decimal import Decimal

# --- KONFIGURACJA MODELI BAZY DANYCH ---
Base = declarative_base()

class Kategoria(Base):
    __tablename__ = 'kategorie'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nazwa = Column(String, nullable=False)
    opis = Column(String)
    produkty = relationship("Produkt", back_populates="kategoria_rel", cascade="all, delete-orphan")

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

# --- POŁĄCZENIE Z BAZĄ ---
# check_same_thread=False jest kluczowe dla stabilności Streamlit + SQLite
engine = create_engine('sqlite:///magazyn.db', connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

# --- USTAWIENIA STRONY ---
st.set_page_config(page_title="Magazyn Pro v3", page_icon="🏢", layout="wide")

# Stylizacja wizualna
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    </style>
""", unsafe_allow_html=True)

st.title("🏢 System Zarządzania Magazynem")
st.caption("Pełna kontrola nad asortymentem, dostawcami i finansami.")

# --- SIDEBAR: WYSZUKIWARKA I FILTRY ---
st.sidebar.header("🔍 Filtrowanie")
search_query = st.sidebar.text_input("Szukaj produktu po nazwie...")

# --- POBIERANIE DANYCH ---
all_prods = db.query(Produkt).all()
df = pd.DataFrame([{
    "ID": p.id,
    "Nazwa": p.nazwa,
    "Cena": float(p.cena),
    "Ilość": p.liczba,
    "Kategoria": p.kategoria_rel.nazwa if p.kategoria_rel else "Brak",
    "Dostawca": p.dostawca_rel.nazwa if p.dostawca_rel else "Brak",
    "Wartość": float(p.cena * p.liczba)
