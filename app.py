import streamlit as st
import joblib
import pandas as pd
import numpy as np
import requests
import os

# ==================================
# CONFIG
# ==================================
st.set_page_config(
    page_title="Assurance Agricole",
    layout="wide"
)

# ==================================
# CHARGEMENT MODELE (ROBUSTE)
# ==================================
@st.cache_resource
def load_model():
    model_path = os.path.join(os.path.dirname(__file__), "model.pkl")

    if os.path.exists(model_path):
        model = joblib.load(model_path)
        return model, True
    else:
        return None, False

model_rf, model_charge = load_model()

st.title("🌾 Assurance Agricole - Prédiction Sinistres")

# DEBUG (utile pour Streamlit Cloud)
st.write("📂 Fichiers disponibles :", os.listdir())

# ==================================
# DONNÉES RÉGION
# ==================================
coords = {
    "Tunis": (36.80, 10.18),
    "Nabeul": (36.45, 10.73),
    "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18),
    "Sousse": (35.82, 10.60),
    "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09),
    "Kebili": (33.70, 8.97),
    "Gabes": (33.88, 10.09)
}

# ==================================
# MÉTÉO NASA (SAFE)
# ==================================
@st.cache_data(ttl=3600)
def get_weather(region, month):
    lat, lon = coords[region]

    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"

    params = {
        "parameters": "T2M,PRECTOTCORR,RH2M,WS2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": "2025",
        "end": "2025",
        "format": "JSON"
    }

    try:
        r = requests.get(url, params=params, timeout=8)

        if r.status_code != 200:
            return [25, 10, 60, 4]

        data = r.json()["properties"]["parameter"]
        key = f"2025{month:02d}"

        return [
            float(data["T2M"][key]),
            float(data["PRECTOTCORR"][key]),
            float(data["RH2M"][key]),
            float(data["WS2M"][key])
        ]

    except:
        return [25, 10, 60, 4]

# ==================================
# UI
# ==================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Paramètres")

    region = st.selectbox("Région", list(coords.keys()))
    culture = st.selectbox("Culture", ["Olives", "Céréales"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"])
    mois = st.selectbox("Mois", list(range(1, 13)))
    sup = st.number_input("Superficie (Ha)", 1, 100, 10)
    prod = st.number_input("Production (T)", 1, 200, 50)

    btn = st.button("🚀 Analyser", use_container_width=True)

# ==================================
# MÉTÉO
# ==================================
t, pl, hum, vent = get_weather(region, mois)

# ==================================
# ANALYSE
# ==================================
if btn:

    # ---------------- ML ----------------
    if model_charge and model_rf is not None:
        try:
            proba = model_rf.predict_proba(
                np.array([[t, pl, hum, vent, mois]])
            )[0][1]

            risk_ml = proba * 100

        except:
            risk_ml = min(90, max(10, t * 2))
    else:
        risk_ml = min(90, max(10, t * 2))

    # ---------------- RULES ----------------
    risk_rule = 10

    if pl < 35:
        risk_rule += (35 - pl) * 2
    if t > 30:
        risk_rule += (t - 30) * 3
    if irrigation == "Non":
        risk_rule += 15

    # ---------------- FUSION ----------------
    risk = 0.7 * risk_ml + 0.3 * risk_rule
    risk = max(0, min(100, risk))

    # ---------------- PRIME ----------------
    prime = (risk * 4.2) + (sup * 12) + (prod * 1.1)

    # ==================================
    # RESULTATS
    # ==================================
    with col2:

        st.subheader("📊 Résultats")

        if model_charge:
            st.success("✔ Modèle chargé avec succès")
        else:
            st.warning("⚠ Modèle non trouvé (mode fallback)")

        st.metric("Risque ML", f"{risk_ml:.1f}%")
        st.metric("Risque Global", f"{risk:.1f}%")
        st.metric("Prime", f"{prime:.1f} DT")

        st.progress(int(risk))

        st.write("### 🌦️ Données météo")
        st.write(f"Température : {t:.1f} °C")
        st.write(f"Pluie : {pl:.1f} mm")
        st.write(f"Humidité : {hum:.1f} %")
        st.write(f"Vent : {vent:.1f} m/s")

        # Indemnité simple
        cap = sup * 200 + prod * 25
        indemnity = 0

        if pl < 35:
            indemnity = ((35 - pl) / 35) * cap

        st.write("### 💰 Indemnité")
        st.write(f"{indemnity:.1f} DT")
