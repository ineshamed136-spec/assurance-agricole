import streamlit as st
import joblib
import pandas as pd
import requests

# ====================================
# 1. PAGE CONFIG
# ====================================
st.set_page_config(
    page_title="Assurance",
    page_icon="🌾",
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
        f"🌾 *ASSURANCE*\n"
        f"👤 *ID :* {uid}\n"
        f"📍 *Région :* {reg}\n"
        f"📈 *Risque :* {risq:.2f} %\n"
        f"💰 *Résultat :* {stat}"
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
                "text": msg,
                "parse_mode": "Markdown"
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
liste_cultures = ["Olives", "Céréales"]
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
            float(p["T2M"][k]),
            float(p["PRECTOTCORR"][k]),
            float(p["RH2M"][k]),
            float(p["WS2M"][k])
        )
    except:
        return 24.5, 12.0, 60.0, 4.0

# ====================================
# 4. INTERFACE
# ====================================
st.title("🌾 Système Décisionnel")

if model_charge:
    st.sidebar.success("✅ ML Actif")
else:
    st.sidebar.warning("⚠️ Mode Règles")

st.markdown("---")
col_f, col_d = st.columns(
    [1, 1.3],
    gap="medium"
)

with col_f:
    st.subheader("📋 Contrat")
    c1, c2 = st.columns(2)
    user_id = c1.text_input(
        "🆔 ID Exploitant",
        value="TUN-NABEUL-01"
    )
    region = c2.selectbox(
        "📍 Région",
        liste_regions,
        index=1
    )
    
    c3, c4 = st.columns(2)
    culture = c3.selectbox(
        "🌱 Culture",
        liste_cultures
    )
    irrigation = c4.radio(
        "💧 Irrigation",
        liste_irrigation,
        horizontal=True
    )

    c5, c6, c7 = st.columns(3)
    mois = c5.selectbox(
        "📅 Mois
