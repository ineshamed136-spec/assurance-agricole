import streamlit as st
import joblib
import pandas as pd
import requests

# 1. CHARGEMENT MODÈLE
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# 2. CONFIGURATION RÉGIONALE (Réelles)
geo_conf = {
    "Tunis": {"coeff": 4.0, "seuil": 30.0, "lat": 36.8, "lon": 10.18},
    "Nabeul": {"coeff": 4.5, "seuil": 32.0, "lat": 36.45, "lon": 10.73},
    "Bizerte": {"coeff": 3.5, "seuil": 35.0, "lat": 37.27, "lon": 9.87},
    "Beja": {"coeff": 3.0, "seuil": 40.0, "lat": 36.72, "lon": 9.18},
    "Sousse": {"coeff": 4.2, "seuil": 28.0, "lat": 35.82, "lon": 10.6},
    "Monastir": {"coeff": 4.2, "seuil": 28.0, "lat": 35.76, "lon": 10.81},
    "Kairouan": {"coeff": 5.5, "seuil": 22.0, "lat": 35.67, "lon": 10.09},
    "Kebili": {"coeff": 7.0, "seuil": 10.0, "lat": 33.7, "lon": 8.97},
    "Gabes": {"coeff": 6.5, "seuil": 15.0, "lat": 33.88, "lon": 10.09}
}

# 3. RÉCUPÉRATION DONNÉES RÉELLES NASA POWER
@st.cache_data(ttl=3600)
def get_nasa_data(reg, year, month):
    lat = geo_conf[reg]["lat"]
    lon = geo_conf[reg]["lon"]
    # URL officielle NASA POWER avec paramètres corrects
    url = f"https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M,PRECTOTCORR,RH2M,WS2M&community=AG&longitude={lon}&latitude={lat}&start={year}&end={year}&format=JSON"
    
    response = requests.get(url, timeout=15)
    if response.status_code == 200:
        data = response.json()
        param = data["properties"]["parameter"]
        k = f"{year}{month:02d}"
        # Extraction sécurisée
        return [
            float(param["T2M"][k]), 
            float(param["PRECTOTCORR"][k]), 
            float(param["RH2M"][k]), 
            float(param["WS2M"][k])
        ]
    return None

# 4. INTERFACE
st.title("🌾 Assurance Agricole - Données NASA Réelles")
region = st.selectbox("Région", list(geo_conf.keys()))
mois = st.selectbox("Mois", list(range(1, 13)), index=4)
btn = st.button("🚀 APPELER NASA")

if btn:
    res = get_nasa_data(region, 2026, mois)
    if res:
        t, pl, hum, vent = res
        st.success("Données récupérées avec succès !")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Température", f"{t:.1f}°C")
        m2.metric("Précipitations", f"{pl:.1f} mm")
        m3.metric("Humidité", f"{hum:.1f}%")
        m4.metric("Vent", f"{vent:.1f} m/s")
        
        # Logique financière ici...
        cfg = geo_conf[region]
        if pl < cfg["seuil"]:
            st.error(f"Déficit hydrique détecté : Indemnisation activée.")
    else:
        st.error("Erreur : Impossible de contacter l'API NASA. Vérifiez la connexion.")
