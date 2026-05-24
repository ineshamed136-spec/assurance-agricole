import streamlit as st
import joblib
import pandas as pd
import requests

# ==========================================
# 1. CONFIGURATION DE LA PAGE (Dashboard Wide)
# ==========================================
st.set_page_config(
    page_title="Assurance Agricole Intelligente",
    page_icon="🌾",
    layout="wide"  # Maximise l'espace horizontal pour éviter le défilement vers le bas
)

# Style CSS personnalisé pour embellir l'interface
st.markdown("""
    <style>
    .metric-box {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        border-left: 5px solid #1ba345;
        margin-bottom: 8px;
    }
    .explanation-box {
        background-color: #eef2f7;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #d0d7de;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CHARGEMENT DU MODELE ML
# ==========================================
@st.cache_resource
def load_model():
    return joblib.load("model_rf.pkl")

try:
    model_rf = load_model()
except:
    st.error("⚠️ Fichier 'model_rf.pkl' introuvable. Veuillez vérifier son emplacement.")
    st.stop()

# ==========================================
# 3. NOTIFICATION TELEGRAM
# ==========================================
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def envoyer_alerte(user_id, region, risque, saison, statut_indemnite):
    if not BOT_TOKEN or not CHAT_ID:
        return
    message = f"""
🌾 *NOTIFICATION ASSURANCE PARAMÉTRIQUE*
👤 *Exploitant :* {user_id}
📍 *Région :* {region}
📅 *Saison :* {saison}
📈 *Risque :* {risque:.2f} %
💰 *Résultat :* {statut_indemnite}
"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"},
            timeout=5
        )
    except:
        pass

# Coordonnées géographiques des gouvernorats de la Tunisie
coords = {
    "Tunis": (36.8065, 10.1815), 
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

# ==========================================
# 4. COLLECTE DES DONNÉES CLIMATIQUES (NASA)
# ==========================================
@st.cache_data(ttl=3600)
def get_weather(region, mois, annee=2025):
