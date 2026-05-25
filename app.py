import streamlit as st
import joblib
import pandas as pd
import requests

# Configuration de la page
st.set_page_config(page_title="Assurance Agricole", layout="wide")

# 1. CHARGEMENT MODÈLE
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# 2. CONFIGURATION GÉOGRAPHIQUE
seuils_regionaux = {
    "Tunis": 30.0, "Nabeul": 32.0, "Bizerte": 35.0, 
    "Beja": 40.0, "Sousse": 28.0, "Monastir": 28.0, 
    "Kairouan": 22.0, "Kebili": 10.0, "Gabes": 15.0
}

# Coefficients de risque actuariel par région (Sensibilité au sinistre)
coeff_actuariel_map = {
    "Tunis": 4.0, "Nabeul": 4.5, "Bizerte": 3.5, 
    "Beja": 3.0, "Sousse": 4.2, "Monastir": 4.2, 
    "Kairouan": 5.5, "Kebili": 7.0, "Gabes": 6.5
}

coords = {
    "Tunis": (36.8, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.6), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.7, 8.97), "Gabes": (33.88, 10.09)
}

@st.cache_data(ttl=3600)
def get_weather(reg, m):
    lat, lon = coords[reg]
    p = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2026", "end": "2026", "format": "JSON"}
    try:
        r = requests.get("https://power.larc.nasa.gov/api/temporal/monthly/point", params=p, timeout=8)
        d = r.json()["properties"]["parameter"]
        k = f"2026{m:02d}"
        return [float(d["T2M"][k]), float(d["PRECTOTCORR"][k]), float(d["RH2M"][k]), float(d["WS2M"][k])]
    except: return [24.5, 12.0, 60.0, 4.0]

# 3. INTERFACE UTILISATEUR
st.title("🌾 Système d'Assurance Agricole Paramétrique")
col1, col2 = st.columns([1, 2])

with col1:
    region = st.selectbox("Région", list(coords.keys()))
    culture = st.selectbox("Culture", ["Céréales", "Olives"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    btn = st.button("🚀 LANCER L'ANALYSE", type="primary")

with col2:
    t, pl, hum, vent = get_weather(region, mois)
    st.subheader("📊 Données Climatiques (NASA Power)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f}°C")
    m2.metric("Précipitations", f"{pl:.1f} mm")
    m3.metric("Humidité", f"{hum:.1f}%")
    m4.metric("Vent", f"{vent:.1f} m/s")

    if btn:
        st.subheader("🔍 Rapport
