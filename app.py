import streamlit as st
import joblib
import pandas as pd
import requests

# ==========================================
# 1. CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(page_title="Assurance Agricole Intelligente", page_icon="🌾", layout="wide")

# Style CSS pour l'interface
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
    message = f"🌾 *ASSURANCE PARAMÉTRIQUE*\n👤 *Exploitant :* {user_id}\n📍 *Région :* {region}\n📅 *Saison :* {saison}\n📈 *Risque :* {risque:.2f} %\n💰 *Résultat :* {statut_indemnite}"
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=5)
    except:
        pass

# Coordonnées géographiques de la Tunisie
coords = {
    "Tunis": (36.8065, 10.1815), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.60), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.70, 8.97), "Gabes": (33.88, 10.09),
    "Medenine": (33.35, 10.50)
}

# ==========================================
# 4. COLLECTE DES DONNÉES CLIMATIQUES (NASA)
# ==========================================
@st.cache_data(ttl=3600)
def get_weather(region, mois, annee=2025):
    lat, lon = coords[region]
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    params = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": str(annee), "end": str(annee), "format": "JSON"}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200: return None
        p = r.json()["properties"]["parameter"]
        key = f"{annee}{mois:02d}"
        return float(p["T2M"][key]), float(p["PRECTOTCORR"][key]), float(p["RH2M"][key]), float(p["WS2M"][key])
    except:
        return None

# ==========================================
# 5. STRUCTURE DE L'INTERFACE UTILISATEUR
# ==========================================
st.title("🌾 Système Décisionnel d'Assurance Agricole Paramétrique")
st.markdown("---")

col_formulaire, col_dashboard = st.columns([1, 1.3], gap="medium")

# --- BLOC DE GAUCHE : FORMULAIRE ---
with col_formulaire:
    st.subheader("📋 Paramètres du Contrat")
    c1, c2 = st.columns(2)
    user_id = c1.text_input("🆔 ID Exploitant", placeholder="Ex: TUN-852")
    region = c2.selectbox("📍 Région d'analyse", list(coords.keys()))
    
    c3, c4 = st.columns(2)
    culture = c3.selectbox("🌱 Culture", ["Olives", "Céréales"])
    irrigation = c4.radio("💧 Irrigation artificielle", ["Oui", "Non"], horizontal=True)

    c5, c6, c7 = st.columns(3)
    mois = c5.selectbox("📅 Mois", list(range(1, 13)), index=4)
    superficie = c6.number_input("📏 Superficie (Ha)", min_value=1, value=15)
    production = c7.number_input("🚜 Rendement attendu (T)", min_value=1, value=60)

    if mois in [12, 1, 2]: saison = "Hiver"
    elif mois in [3, 4, 5]: saison = "Printemps"
    elif mois in [6, 7, 8]: saison = "Été"
    else: saison = "Automne"
    
    st.write(f"🍂 *Période rattachée : Période de l'{saison}*")
    btn_analyser = st.button("🚀 EXÉCUTER L'ANALYSE DES SEUILS", use_container_width=True, type="primary")

# --- BLOC DE DROITE : DASHBOARD ---
with col_dashboard:
    if not user_id:
        st.warning("👈 Veuillez renseigner l'Identifiant Exploitant à gauche pour activer le Dashboard.")
        st.stop()
        
    weather = get_weather(region, mois)
    if weather is None:
        st.error("❌ Données climatiques de la NASA temporairement indisponibles ou invalides pour cette date.")
        st.stop()
        
    temp, pluie, humidite, vent = weather
    tab1, tab2, tab3 = st.tabs(["🌦️ Données Météo Validées", "📉 Analyse Actuarielle du Risque", "🛡️ Calcul détaillé de l'Indemnité"])
    
    with tab1:
        st.markdown(f"#### Mesures certifiées pour la région de **{region}**")
        m_c1, m_c2 = st.columns(2)
        m_c1.markdown(f"<div class='metric-box'>🌡️ <b>Température Moyenne :</b> {temp:.2f} °C</div>", unsafe_allow_html=True)
        m_c1.markdown(f"<div class='metric-box'>🌧️ <b>Cumul des Pluies :</b> {pluie:.2f} mm</div>", unsafe_allow_html=True)
        m_c2.markdown(f"<div class='metric-box'>💧 <b>Taux d'Humidité :</b> {humidite:.2f} %</div>", unsafe_allow_html=True)
        m_c2.markdown(f"<div class='metric-box'>💨 <b>Vitesse Maximale Vent :</b> {vent:.2f} m/s</div>", unsafe_allow_html=True)
        st.caption("📍 *Source : Modèles satellitaires NASA POWER.*")

    if btn_analyser:
        X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_
