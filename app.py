import streamlit as st
import joblib
import pandas as pd
import requests
import os

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# 1. CHARGEMENT DU MODELE
@st.cache_resource
def load_model():
    try:
        return joblib.load("model.pkl"), True
    except:
        return None, False

model_rf, model_charge = load_model()

# 2. CONFIGURATION ET METEO
coords = {
    "Tunis": (36.8, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.6), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.7, 8.97), "Gabes": (33.88, 10.09)
}

@st.cache_data(ttl=3600)
def get_weather(reg, m):
    lat, lon = coords[reg]
    p = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2025", "end": "2025", "format": "JSON"}
    try:
        r = requests.get("https://power.larc.nasa.gov/api/temporal/monthly/point", params=p, timeout=8)
        d = r.json()["properties"]["parameter"]
        k = f"2025{m:02d}"
        return [float(d["T2M"][k]), float(d["PRECTOTCORR"][k]), float(d["RH2M"][k]), float(d["WS2M"][k])]
    except:
        return [24.5, 12.0, 60.0, 4.0]

# 3. INTERFACE
st.title("🌾 Assurance Agricole")
col1, col2 = st.columns([1, 1.2])

with col1:
    region = st.selectbox("Région", list(coords.keys()))
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", value=15)
    prod = st.number_input("Rendement (T)", value=60)
    btn = st.button("🚀 ANALYSER", type="primary")

with col2:
    t, pl, hum, vent = get_weather(region, mois)
    st.write(f"**Météo :** {t}°C, {pl}mm pluie, {hum}% humidité, {vent}m/s vent")
    
    if btn:
        risque = 20.0
        if model_charge:
            try:
                # Création du DataFrame avec toutes les colonnes
                X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)
                # Mapping : assure-toi que les clés correspondent aux noms de colonnes du modèle
                mapping = {"temp": t, "précipitations": pl, "humidité": hum, "vent": vent, "mois": mois}
                for col in X.columns:
                    if col in mapping: X[col] = mapping[col]
                risque = model_rf.predict_proba(X)[0][1] * 100
            except Exception as e:
                st.error(f"Erreur modèle : {e}")
        
        prime = (risque * 4.2) + (sup * 12) + (prod * 1.1)
        st.metric("🔥 Risque Global", f"{risque:.1f} %")
        st.metric("💳 Prime Actuarielle", f"{prime:.1f} DT")
        st.progress(int(risque))
        
        if pl < 35:
            ind = ((35.0 - pl) / 27.0) * ((sup * 200) + (prod * 25))
            st.error(f"💰 Indemnité : {max(0, ind):.2f} DT")
