import streamlit as st
import joblib
import pandas as pd
import requests

# ====================================
# 1. CONFIG
# ====================================
st.set_page_config(
    page_title="Assurance",
    layout="wide"
)

st.markdown("""
<style>
.m-box {
    background-color: #f8f9fa;
    padding: 12px;
    border-radius: 8px;
    border-left: 5px solid #1ba345;
    margin-bottom: 8px;
}
.e-box {
    background-color: #eef2f7;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #d0d7de;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# ====================================
# 2. MODEL ML
# ====================================
@st.cache_resource
def load_model():
    try:
        m = joblib.load("model_rf.pkl")
        return m, True
    except:
        return None, False

model_rf, model_charge = load_model()

# ====================================
# 3. TELEGRAM & DATA
# ====================================
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def envoyer_alerte(uid, reg, risq, stat):
    if not BOT_TOKEN or not CHAT_ID:
        return
    msg = (
        f"ASSURANCE\n"
        f"ID: {uid}\n"
        f"Reg: {reg}\n"
        f"Risque: {risq:.2f}%\n"
        f"Resultat: {stat}"
    )
    try:
        u = (
            f"https://api.telegram.org/bot"
            f"{BOT_TOKEN}/sendMessage"
        )
        requests.post(
            u,
            data={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=5
        )
    except:
        pass

coords = {
    "Tunis": (36.80, 10.18),
    "Nabeul": (36.45, 10.73),
    "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18),
    "Sousse": (35.82, 10.60),
    "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09),
    "Kebili": (33.70, 8.97),
    "Gabes": (33.88, 10.09),
    "Medenine": (33.35, 10.50)
}

liste_regions = list(coords.keys())
liste_cultures = ["Olives", "Cereales"]
liste_irrigation = ["Oui", "Non"]
liste_mois = list(range(1, 13))

@st.cache_data(ttl=3600)
def get_weather(region, mois, annee=2025):
    lat, lon = coords[region]
    url = (
        f"https://power.larc.nasa.gov"
        f"/api/temporal/monthly/point"
    )
    prms = {
        "parameters": "T2M,PRECTOTCORR,RH2M,WS2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": str(annee),
        "end": str(annee),
        "format": "JSON"
    }
    try:
        r = requests.get(
            url,
            params=prms,
            timeout=10
        )
        if r.status_code != 200:
            return 24.5, 12.0, 60.0, 4.0
        p = r.json()["properties"]["parameter"]
        k = f"{annee}{mois:02d}"
        return (
