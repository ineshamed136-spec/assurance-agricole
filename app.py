import streamlit as st
import joblib
import pandas as pd
import requests

# ==========================================
# 1. CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(page_title="Assurance Agricole Intelligente", page_icon="🌾", layout="wide")

# Injection de styles CSS personnalisés pour le Dashboard
st.markdown("""
    <style>
    .metric-box {
        background-color: #f8f9fa; padding: 12px; border-radius: 8px;
        border-left: 5px solid #1ba345; margin-bottom: 8px;
    }
    .explanation-box {
        background-color: #eef2f7; padding: 15px; border-radius: 8px;
        border: 1px solid #d0d7de; margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CHARGEMENT SÉCURISÉ DU MODÈLE ML
# ==========================================
@st.cache_resource
def load_model():
    try:
        return joblib.load("model_rf.pkl"), True
    except:
        return None, False

model_rf, model_charge = load_model()

# ==========================================
# 3. SYSTÈME DE NOTIFICATION TELEGRAM
# ==========================================
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def envoyer_alerte(user_id, region, risque, saison, statut_indemnite):
    if not BOT_TOKEN or not CHAT_ID: return
    msg = f"🌾 *ASSURANCE PARAMÉTRIQUE*\n👤 *Exploitant :* {user_id}\n📍 *Région :* {region}\n📈 *Risque :* {risque:.2f} %\n💰 *Résultat :* {statut_indemnite}"
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except:
        pass

# Coordonnées géographiques des gouvernorats de Tunisie
coords = {
    "Tunis": (36.8065, 10.1815), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.60), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.70, 8.97), "Gabes": (33.88, 10.09),
    "Medenine": (33.35, 10.50)
}

# ==========================================
# 4. COLLECTE DES DONNÉES CLIMATIQUES (NASA POWER)
# ==========================================
@st.cache_data(ttl=3600)
def get_weather(region, mois, annee=2025):
    lat, lon = coords[region]
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    prms = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": str(annee), "end": str(annee), "format": "JSON"}
    try:
        r = requests.get(url, params=prms, timeout=12)
        if r.status_code != 200: return 26.2, 14.5, 58.0, 3.8
        p = r.json()["properties"]["parameter"]
        k = f"{annee}{mois:02d}"
        return float(p["T2M"][k]), float(p["PRECTOTCORR"][k]), float(p["RH2M"][k]), float(p["WS2M"][k])
    except:
        # Valeurs par défaut de secours (Tunisie) en cas de coupure de l'API NASA
        return 26.2, 14.5, 58.0, 3.8

# ==========================================
# 5. ARCHITECTURE DE L'INTERFACE GRAPHIQUE
# ==========================================
st.title("🌾 Système Décisionnel d'Assurance Agricole Paramétrique")

# Alerte informative transparente sur l'état du modèle ML chargé
if model_charge:
    st.sidebar.success("✅ Modèle prédictif Random Forest actif.")
else:
    st.sidebar.warning("⚠️ Mode hybride / Règles métiers activé (Fichier model_rf.pkl non détecté).")

st.markdown("---")

col_formulaire, col_dashboard = st.columns([1, 1.3], gap="medium")

# --- BLOC DE GAUCHE : PARAMÈTRES DU CONTRAT ---
with col_formulaire:
    st.subheader("📋 Paramètres du Contrat")
    c1, c2 = st.columns(2)
    user_id = c1.text_input("🆔 ID Exploitant", placeholder="Ex: TUN-852")
    region = c2.selectbox("
