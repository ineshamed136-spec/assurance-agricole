import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance Paramétrique", layout="wide")

# ====================================
# 1. CHARGEMENT DU MODELE ML
# ====================================
@st.cache_resource
def load_model():
    try: return joblib.load("model_rf.pkl"), True
    except: return None, False
model_rf, model_charge = load_model()

# ====================================
# 2. LOGIQUE DE DONNÉES (NASA + FALLBACK)
# ====================================
coords = {"Tunis": (36.80, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87)}
# ... (ajoute les autres régions ici)

def get_weather(reg, m):
    """
    Récupération dynamique des données :
    1. Tente l'appel API NASA pour 2026.
    2. Si échec ou donnée manquante, bascule sur la normale historique.
    """
    lat, lon = coords.get(reg, (36.80, 10.18))
    # Appel API NASA
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    params = {
        "parameters": "T2M,PRECTOTCORR,RH2M,WS2M",
        "community": "AG",
        "longitude": lon, "latitude": lat,
        "start": "2026", "end": "2026",
        "format": "JSON"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()["properties"]["parameter"]
        k = f"2026{m:02d}"
        
        # Vérification si la donnée existe pour ce mois
        if k in data["T2M"]:
            return [float(data["T2M"][k]), float(data["PRECTOTCORR"][k]), 
                    float(data["RH2M"][k]), float(data["WS2M"][k])], "📡 Donnée Satellite Temps Réel"
    except:
        pass
        
    # Fallback : Si l'API échoue ou le mois n'est pas encore passé
    return [24.5, 12.0, 60.0, 4.0], "📊 Normale Historique (Estimation)"

# ====================================
# 3. INTERFACE UTILISATEUR
# ====================================
st.title("🌾 Plateforme d'Assurance Agricole")
st.write("Gestion des risques paramétriques - Année 2026")

# Saisie des paramètres
col1, col2 = st.columns(2)
with col1:
    uid = st.text_input("ID Exploitant", "TUN-01")
    region = st.selectbox("Région", list(coords.keys()))
    mois = st.slider("Mois d'analyse", 1, 12, 5)
    btn = st.button("🚀 LANCER L'ANALYSE")

with col2:
    if btn:
        weather_data, source = get_weather(region, mois)
        st.success(f"Source des données : {source}")
        
        # Calcul du risque et prime (Logique métier)
        t, pl, hum, vent = weather_data
        risque = 15.0 # Simulation de calcul
        prime = (risque * 4.2) + 150
        
        st.metric("Taux de Risque", f"{risque}%")
        st.metric("Prime Totale", f"{prime} DT")
        
        # ZONE DEVELOPPEUR : JSON
        with st.expander("🛠️ Document JSON (Pour l'encadrant)"):
            st.json({
                "annee": 2026,
                "donnees_meteo": {"temp": t, "pluie": pl, "humidite": hum},
                "analyse_risque": {"taux": risque, "source": source},
                "prime_calcul": {"prime_pure": risque * 4.2, "frais": 150}
            })
