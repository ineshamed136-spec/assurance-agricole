import streamlit as st
import joblib
import pandas as pd
import requests
import os

st.set_page_config(
    page_title="Assurance",
    layout="wide"
)

# ==================================
# 1. CHARGEMENT DU MODELE ML
# ==================================
@st.cache_resource
def load_model():
    try:
        dossier_actuel = os.path.dirname(__file__)
        chemin_modele = os.path.join(dossier_actuel, "model.pkl")
        m = joblib.load(chemin_modele)
        return m, True
    except:
        return None, False

model_rf, model_charge = load_model()

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
# 2. COLLECTE DES DONNEES (NASA)
# ==================================
@st.cache_data(ttl=3600)
def get_weather(reg, m):
    lat, lon = coords[reg]
    url = (
        "https://power.larc.nasa.gov"
        "/api/temporal/monthly/point"
    )
    p = {
        "parameters": "T2M,PRECTOTCORR,RH2M,WS2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": "2025",
        "end": "2025",
        "format": "JSON"
    }
    try:
        r = requests.get(
            url,
            params=p,
            timeout=8
        )
        if r.status_code != 200:
            return [24.5, 12.0, 60.0, 4.0]
        res = r.json()
        d = res["properties"]["parameter"]
        k = f"2025{m:02d}"
        v_t = float(d["T2M"][k])
        v_p = float(d["PRECTOTCORR"][k])
        v_h = float(d["RH2M"][k])
        v_w = float(d["WS2M"][k])
        return [v_t, v_p, v_h, v_w]
    except:
        return
