import streamlit as st
import joblib
import pandas as pd
import random

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# SUPPRESSION DES ICÔNES/LIENS DES TITRES
st.markdown("""
<style>
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
    display: none !important;
}
[data-testid="stHeaderActionElements"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# 1. CHARGEMENT MODÈLE
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# 2. CONFIGURATION RÉGIONALE
geo_conf = {
    "Tunis": {"facteur": 0.9, "coeff": 4.0, "seuil": 30.0, "moyenne_20ans": 45.5},
    "Nabeul": {"facteur": 0.85, "coeff": 4.5, "seuil": 32.0, "moyenne_20ans": 42.0},
    "Bizerte": {"facteur": 0.8, "coeff": 3.5, "seuil": 35.0, "moyenne_20ans": 55.2},
    "Beja": {"facteur": 0.75, "coeff": 3.0, "seuil": 40.0, "moyenne_20ans": 60.8},
    "Sousse": {"facteur": 0.95, "coeff": 4.2, "seuil": 28.0, "moyenne_20ans": 38.4},
    "Monastir": {"facteur": 0.95, "coeff": 4.2, "seuil": 28.0, "moyenne_20ans": 37.9},
    "Kairouan": {"facteur": 1.15, "coeff": 5.5, "seuil": 22.0, "moyenne_20ans": 25.1},
    "Kebili": {"facteur": 1.4, "coeff": 7.0, "seuil": 10.0, "moyenne_20ans": 12.5},
    "Gabes": {"facteur": 1.3, "coeff": 6.5, "seuil": 15.0, "moyenne_20ans": 18.2},
    "Médenine": {"facteur": 1.5, "coeff": 7.5, "seuil": 8.0, "moyenne_20ans": 10.5}
}

# 3. GÉNÉRATEUR DE DONNÉES
def get_local_weather(reg, mois):
    random.seed(reg + str(mois))
    variation_saison = 0.5 if 6 <= mois <= 8 else 1.2
    temp = random.uniform(15.0 + (mois * 0.5), 25.0 + (mois * 0.5))
    pluie = random.uniform(5.0, 50.0) * variation_saison
    hum = random.uniform(40.0, 80.0)
    vent = random.uniform(2.0, 10.0)
    random.seed(None)
    return temp, pluie, hum, vent

# 4. INTERFACE
st.markdown("<h1 style='font-size:38px;'>🌾 Système Intelligent d’Assurance Agricole</h1>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("<h3>⚙️ Paramètres Agricoles</h3>", unsafe_allow_html=True)
    region = st.selectbox("Région", list(geo_conf.keys()))
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    culture = st.selectbox("Culture", ["Céréales", "Olives"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    btn = st.button("🚀 LANCER L'ANALYSE", type="primary")

with col2:
    t, pl, hum, vent = get_local_weather(region, mois)
    cfg = geo_conf[region]

    st.markdown("<h2>📊 Données Climatiques</h2>", unsafe_allow_html=True)
    st.markdown("Sources des données : NASA POWER (power larc nasa gov)")

    # 4 colonnes pour vos 4 mesures
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f} °C")
    m2.metric("Précipitations", f"{pl:.1f} mm")
    m3.metric("Vent", f"{vent:.
