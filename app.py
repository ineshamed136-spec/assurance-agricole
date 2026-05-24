import streamlit as st
import joblib
import pandas as pd
import requests
import os

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# 1. CHARGEMENT MODELE
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# 2. LOGIQUE METEO
coords = {"Tunis": (36.8, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87), "Beja": (36.72, 9.18), "Sousse": (35.82, 10.6), "Monastir": (35.76, 10.81), "Kairouan": (35.67, 10.09), "Kebili": (33.7, 8.97), "Gabes": (33.88, 10.09)}

@st.cache_data(ttl=3600)
def get_weather(reg, m):
    lat, lon = coords[reg]
    p = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2025", "end": "2025", "format": "JSON"}
    r = requests.get("https://power.larc.nasa.gov/api/temporal/monthly/point", params=p, timeout=8)
    d = r.json()["properties"]["parameter"]
    k = f"2025{m:02d}"
    return [float(d["T2M"][k]), float(d["PRECTOTCORR"][k]), float(d["RH2M"][k]), float(d["WS2M"][k])]

# 3. INTERFACE
st.title("🌾 Tableau de Bord - Assurance Agricole")
col1, col2 = st.columns([1, 2])

with col1:
    region = st.selectbox("Région", list(coords.keys()))
    mois = st.selectbox("Mois", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T)", value=60.0)
    btn = st.button("🚀 CALCULER L'ASSURANCE", type="primary")

with col2:
    t, pl, hum, vent = get_weather(region, mois)
    saison = "Hiver" if mois in [12, 1, 2] else "Printemps" if mois in [3, 4, 5] else "Été" if mois in [6, 7, 8] else "Automne"
    
    st.subheader(f"Données climatiques : {saison}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f}°C")
    m2.metric("Pluviométrie", f"{pl:.0f} mm")
    m3.metric("Humidité", f"{hum:.0f} %")
    m4.metric("Vent", f"{vent:.1f} m/s")

    if btn:
        risque = 20.0
        if model_charge:
            X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)
            mapping = {"temp": t, "précipitations": pl, "humidité": hum, "vent": vent, "mois": mois}
            for col in X.columns:
                if col in mapping: X[col] = mapping[col]
            risque = model_rf.predict_proba(X)[0][1] * 100
        
        # FORMULES
        prime = (risque * 4.2) + (sup * 12) + (prod * 1.1)
        cap_max = (sup * 200) + (prod * 25)
        ind = max(0, ((35.0 - pl) / 27.0) * cap_max) if pl < 35 else 0

        st.divider()
        r1, r2 = st.columns(2)
        r1.metric("🔥 Risque Calculé", f"{risque:.1f} %")
        r2.metric("💳 Prime à payer", f"{prime:.2f} DT")
        st.error(f"💰 Indemnité estimée en cas de sécheresse : {ind:.2f} DT")
