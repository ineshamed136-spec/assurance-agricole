import streamlit as st
import joblib
import pandas as pd
import requests

# ==========================================
# 1. CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(page_title="Assurance Agricole Intelligente", page_icon="🌾", layout="wide")

st.markdown("""
    <style>
    .metric-box {background-color: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 5px solid #1ba345; margin-bottom: 8px;}
    .explanation-box {background-color: #eef2f7; padding: 15px; border-radius: 8px; border: 1px solid #d0d7de; margin-top: 10px;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CHARGEMENT DU MODELE ML
# ==========================================
@st.cache_resource
def load_model():
    try: return joblib.load("model_rf.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# ==========================================
# 3. CONFIGURATION DES DONNÉES & SÉCURITÉS
# ==========================================
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def envoyer_alerte(user_id, region, risque, saison, statut_indemnite):
    if not BOT_TOKEN or not CHAT_ID: return
    msg = f"🌾 *ASSURANCE PARAMÉTRIQUE*\n👤 *Exploitant :* {user_id}\n📍 *Région :* {region}\n📈 *Risque :* {risque:.2f} %\n💰 *Résultat :* {statut_indemnite}"
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

coords = {
    "Tunis": (36.8065, 10.1815), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.60), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.70, 8.97), "Gabes": (33.88, 10.09), "Medenine": (33.35, 10.50)
}

# Extraction des listes à plat pour éviter les fonctions imbriquées dans l'interface
liste_regions = list(coords.keys())
liste_cultures = ["Olives", "Céréales"]
liste_options_irrigation = ["Oui", "Non"]
liste_mois = list(range(1, 13))

@st.cache_data(ttl=3600)
def get_weather(region, mois, annee=2025):
    lat, lon = coords[region]
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    prms = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": str(annee), "end": str(annee), "format": "JSON"}
    try:
        r = requests.get(url, params=prms, timeout=10)
        if r.status_code != 200: return 24.5, 12.0, 60.0, 4.0
        p = r.json()["properties"]["parameter"]
        k = f"{annee}{mois:02d}"
        return float(p["T2M"][k]), float(p["PRECTOTCORR"][k]), float(p["RH2M"][k]), float(p["WS2M"][k])
    except: return 24.5, 12.0, 60.0, 4.0

# ==========================================
# 4. ARCHITECTURE DE L'INTERFACE
# ==========================================
st.title("🌾 Système Décisionnel d'Assurance Agricole Paramétrique")

if model_charge: st.sidebar.success("✅ Modèle Random Forest actif.")
else: st.sidebar.warning("⚠️ Mode Hybride Actif (Calcul basé sur les règles experts métiers).")

st.markdown("---")
col_formulaire, col_dashboard = st.columns([1, 1.3], gap="medium")

# --- BLOC DE GAUCHE : FORMULAIRE PROTÉGÉ ---
with col_formulaire:
    st.subheader("📋 Paramètres du Contrat")
    c1, c2 = st.columns(2)
    user_id = c1.text_input("🆔 ID Exploitant", value="TUN-NABEUL-01")
    region = c2.selectbox("📍 Région d'analyse", liste_regions, index=1)
    
    c3, c4 = st.columns(2)
    culture = c3.selectbox("🌱 Culture", liste_cultures)
    irrigation = c4.radio("💧 Irrigation artificielle", liste_options_irrigation, horizontal=True)

    c5, c6, c7 = st.columns(3)
    mois = c5.selectbox("📅 Mois d'analyse", liste_mois, index=4)
    superficie = c6.number_input("📏 Superficie (Ha)", min_value=1, value=15)
    production = c7.number_input("🚜 Rendement attendu (T)", min_value=1, value
