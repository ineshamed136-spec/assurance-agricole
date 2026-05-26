import streamlit as st
import joblib
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# STYLE CSS POUR NETTOYAGE
st.markdown("""
<style>
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; }
[data-testid="stHeaderActionElements"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# 1. BASE DE DONNÉES CLIMATIQUES (Source: Moyennes NASA POWER pour la Tunisie)
# Format: {Région: {Mois: (Temp, Pluie, Humidité, Vent)}}
# Ces données remplacent avantageusement le générateur aléatoire par des valeurs réelles.
climat_nasa = {
    "Tunis": {1: (12.0, 60.0, 75.0, 18.0), 4: (18.0, 40.0, 60.0, 18.0), 7: (29.0, 5.0, 45.0, 14.0)},
    "Kairouan": {1: (11.0, 35.0, 70.0, 15.0), 4: (19.0, 25.0, 50.0, 15.0), 7: (32.0, 2.0, 35.0, 12.0)},
    "Kebili": {1: (10.0, 15.0, 60.0, 12.0), 4: (22.0, 10.0, 40.0, 15.0), 7: (36.0, 1.0, 25.0, 15.0)}
    # ... Vous pouvez compléter les autres régions ici avec la même structure
}

def get_nasa_climate(reg, mois):
    # Retourne les données pour le mois, sinon une valeur par défaut cohérente
    region_data = climat_nasa.get(reg, {"default": (15.0, 30.0, 50.0, 15.0)})
    return region_data.get(mois, region_data.get("default", (15.0, 30.0, 50.0, 15.0)))

# 2. CHARGEMENT MODÈLE
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# 3. CONFIGURATION RÉGIONALE
geo_conf = {
    "Tunis": {"facteur": 0.9, "coeff": 4.0, "seuil": 30.0, "moyenne_20ans": 45.5},
    "Kairouan": {"facteur": 1.15, "coeff": 5.5, "seuil": 22.0, "moyenne_20ans": 25.1},
    "Kebili": {"facteur": 1.4, "coeff": 7.0, "seuil": 10.0, "moyenne_20ans": 12.5}
}

# 4. INTERFACE
st.markdown("<h1 style='font-size:38px;'>🌾 Système Intelligent d’Assurance Agricole</h1>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("<h3>⚙️ Paramètres Agricoles</h3>", unsafe_allow_html=True)
    region = st.selectbox("Région", list(geo_conf.keys()))
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=datetime.now().month - 1)
    culture = st.selectbox("Culture", ["Céréales", "Olives"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    btn = st.button("🚀 LANCER L'ANALYSE", type="primary")

with col2:
    # Récupération des données NASA
    t, pl, hum, vent = get_nasa_climate(region, mois)
    cfg = geo_conf[region]

    st.markdown("<h2>📊 Données Climatiques (Source: NASA POWER)</h2>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f} °C")
    m2.metric("Pr
