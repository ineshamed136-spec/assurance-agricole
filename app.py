import streamlit as st
import joblib
import pandas as pd
import requests

# Configuration
st.set_page_config(page_title="Assurance Agricole", layout="wide")

# Chargement du modèle
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

coords = {
    "Tunis": (36.8, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.6), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.7, 8.97), "Gabes": (33.88, 10.09)
}

# Fonction API NASA réelle
def get_nasa_data(reg, m):
    lat, lon = coords[reg]
    # URL vers l'API NASA POWER (Données agronomiques)
    url = f"https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M,PRECTOTCORR,RH2M,WS2M&community=AG&longitude={lon}&latitude={lat}&start=2026&end=2026&format=JSON"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Impossible de joindre les serveurs de la NASA.")
        return None

# --- Interface ---
st.title("🌾 Assurance Agricole - Données NASA Réelles")
region = st.sidebar.selectbox("Région", list(coords.keys()))
mois = st.sidebar.selectbox("Mois", list(range(1, 13)), index=4)

if st.button("Récupérer données NASA"):
    data_json = get_nasa_data(region, mois)
    if data_json:
        # Extraction dynamique basée sur la clé correcte du JSON NASA
        params = data_json["properties"]["parameter"]
        k = f"2026{mois:02d}"
        
        t = params["T2M"][k]
        pl = params["PRECTOTCORR"][k]
        hum = params["RH2M"][k]
        vent = params["WS2M"][k]
        
        st.success("Données récupérées avec succès !")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Température", f"{t} °C")
        m2.metric("Précipitations", f"{pl} mm")
        m3.metric("Humidité", f"{hum} %")
        m4.metric("Vent", f"{vent} m/s")
        
        # Affichage du JSON pour prouver la provenance
        with st.expander("Voir la structure JSON reçue"):
            st.json(data_json)
