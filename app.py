import streamlit as st
import joblib
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# CSS POUR NETTOYER L'UI
st.markdown("""
<style>
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; }
[data-testid="stHeaderActionElements"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# 1. CHARGEMENT MODÈLE
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# 2. CONFIGURATION RÉGIONALE AVEC COORDONNÉES (LAT/LON POUR NASA)
geo_conf = {
    "Tunis": {"lat": 36.80, "lon": 10.18, "facteur": 0.9, "coeff": 4.0, "seuil": 30.0, "moyenne_20ans": 45.5},
    "Nabeul": {"lat": 36.45, "lon": 10.73, "facteur": 0.85, "coeff": 4.5, "seuil": 32.0, "moyenne_20ans": 42.0},
    "Bizerte": {"lat": 37.27, "lon": 9.87, "facteur": 0.8, "coeff": 3.5, "seuil": 35.0, "moyenne_20ans": 55.2},
    "Beja": {"lat": 36.72, "lon": 9.18, "facteur": 0.75, "coeff": 3.0, "seuil": 40.0, "moyenne_20ans": 60.8},
    "Sousse": {"lat": 35.82, "lon": 10.60, "facteur": 0.95, "coeff": 4.2, "seuil": 28.0, "moyenne_20ans": 38.4},
    "Monastir": {"lat": 35.78, "lon": 10.83, "facteur": 0.95, "coeff": 4.2, "seuil": 28.0, "moyenne_20ans": 37.9},
    "Kairouan": {"lat": 35.67, "lon": 10.10, "facteur": 1.15, "coeff": 5.5, "seuil": 22.0, "moyenne_20ans": 25.1},
    "Kebili": {"lat": 33.70, "lon": 8.97, "facteur": 1.4, "coeff": 7.0, "seuil": 10.0, "moyenne_20ans": 12.5},
    "Gabes": {"lat": 33.88, "lon": 10.09, "facteur": 1.3, "coeff": 6.5, "seuil": 15.0, "moyenne_20ans": 18.2},
    "Médenine": {"lat": 33.35, "lon": 10.49, "facteur": 1.5, "coeff": 7.5, "seuil": 8.0, "moyenne_20ans": 10.5}
}

# 3. FONCTION NASA POWER (Remplace le générateur aléatoire)
@st.cache_data(ttl=3600)
def get_nasa_weather(lat, lon, mois):
    url = f"https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=T2M,PRECTOTCORR,RH2M,WS10M&community=AG&longitude={lon}&latitude={lat}&format=JSON"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()['properties']['parameter']
        m = str(mois)
        return data['T2M'][m], data['PRECTOTCORR'][m], data['RH2M'][m], data['WS10M'][m]
    except:
        return 20.0, 30.0, 50.0, 5.0

# 4. INTERFACE
st.markdown("<h1 style='font-size:38px;'>🌾 Système Intelligent d’Assurance Agricole</h1>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])

with col1:
    region = st.selectbox("Région", list(geo_conf.keys()))
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=datetime.now().month - 1)
    culture = st.selectbox("Culture", ["Céréales", "Olives"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    btn = st.button("🚀 LANCER L'ANALYSE", type="primary")

with col2:
    cfg = geo_conf[region]
    # APPEL NASA
    t, pl, hum, vent = get_nasa_weather(cfg['lat'], cfg['lon'], mois)

    st.markdown("<h2>📊 Données Climatiques (NASA POWER)</h2>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f} °C")
    m2.metric("Précipitations", f"{pl:.1f} mm")
    m3.metric("Vent", f"{vent:.1f} km/h")
    m4.metric("Humidité", f"{hum:.1f} %")

    if btn:
        risque_base = (25.0 * cfg["facteur"]) + (mois * 0.5) + (15 if irrigation == "Non" else 0)
        risque_final = min(max(risque_base, 5.0), 95.0)
        prod_totale = sup * prod
        prime = (risque_final * cfg["coeff"]) + (sup * 12) + (prod_totale * 1.1)
        cap_max = (sup * 200) + (prod_totale * 25)

        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("🔥 Risque Global", f"{risque_final:.1f} %")
        c2.metric("💳 Prime à payer", f"{prime:.2f} DT")
        
        st.divider
