import streamlit as st
import joblib
import pandas as pd
import random

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# STYLE POUR SUPPRIMER LES ÉLÉMENTS DE LIEN
st.markdown("""
<style>
h1 a, h2 a, h3 a {display: none !important;}
[data-testid="stHeaderActionElements"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# 1. CHARGEMENT DU MODÈLE (Ajouté)
@st.cache_resource
def load_model():
    return joblib.load('modele_risque.joblib') # Assurez-vous que le fichier est présent

model = load_model()

# 1. CONFIGURATION RÉGIONALE
geo_conf = {
    "Tunis": {"facteur": 0.9, "seuil": 30.0, "type": "nord"},
    "Nabeul": {"facteur": 0.85, "seuil": 32.0, "type": "nord"},
    "Bizerte": {"facteur": 0.8, "seuil": 35.0, "type": "nord"},
    "Beja": {"facteur": 0.75, "seuil": 40.0, "type": "nord"},
    "Sousse": {"facteur": 0.95, "seuil": 28.0, "type": "centre"},
    "Monastir": {"facteur": 0.95, "seuil": 28.0, "type": "centre"},
    "Kairouan": {"facteur": 1.15, "seuil": 22.0, "type": "centre"},
    "Kebili": {"facteur": 1.4, "seuil": 10.0, "type": "sud"},
    "Gabes": {"facteur": 1.3, "seuil": 15.0, "type": "sud"},
    "Médenine": {"facteur": 1.5, "seuil": 8.0, "type": "sud"}
}

# 2. GÉNÉRATEUR DE DONNÉES CLIMATIQUES CORRIGÉ
def get_local_weather(reg, mois):
    random.seed(reg + str(mois))
    cfg = geo_conf[reg]
    
    # Température : pic en été (mois 7)
    base_t = 16 if cfg["type"] == "nord" else (22 if cfg["type"] == "centre" else 25)
    t = base_t + (10 * ((mois - 7) / 6)) + random.uniform(-2, 2)
    
    # Précipitations : plus élevées au nord, baisse drastique en été
    base_pl = {"nord": 50, "centre": 25, "sud": 8}
    saison_pl = 0.2 if 6 <= mois <= 8 else 1.2
    pl = max(0, (base_pl[cfg["type"]] * saison_pl) + random.uniform(-5, 10))
    
    h = random.uniform(40.0, 70.0)
    v = random.uniform(5.0, 15.0)
    return round(t, 1), round(pl, 1), round(h, 1), round(v, 1)

# 3. INTERFACE
st.markdown("<h1 style='font-size:38px;'>🌾 Système Intelligent d’Assurance Agricole</h1>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("<h3>⚙️ Paramètres Agricoles</h3>", unsafe_allow_html=True)
    region = st.selectbox("Région", list(geo_conf.keys()))
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    btn = st.button("🚀 LANCER L'ANALYSE", type="primary")

with col2:
    t, pl, hum, vent = get_local_weather(region, mois)
    cfg = geo_conf[region]
    st.markdown("<h2>📊 Données Climatiques (Modèle)</h2>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
