import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(
    page_title="Assurance", 
    layout="wide"
)

# ====================================
# 1. CHARGEMENT DU MODELE ML
# ====================================
@st.cache_resource
def load_model():
    try: 
        m = joblib.load("model_rf.pkl")
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

# ====================================
# 2. COLLECTE DES DONNÉES SATELLITES
# ====================================
@st.cache_data(ttl=3600)
def get_weather(reg, m):
    lat, lon = coords[reg]
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
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
        r = requests.get(url, params=p, timeout=8)
        if r.status_code != 200: 
            return [24.5, 12.0, 60.0, 4.0]
        d = r.json()["properties"]["parameter"]
        k = f"2025{m:02d}"
        return [
            float(d["T2M"][k]), 
            float(d["PRECTOTCORR"][k]), 
            float(d["RH2M"][k]), 
            float(d["WS2M"][k])
        ]
    except: 
        return [24.5, 12.0, 60.0, 4.0]

# ====================================
# 3. INTERFACE UTILISATEUR
# ====================================
st.title("🌾 Assurance Agricole Paramétrique")

col1, col2 = st.columns([1, 1.2], gap="medium")

with col1:
    st.subheader("Contrat")
    uid = st.text_input("ID Exploitant", value="TUN-01")
    region = st.selectbox("Region", list(coords.keys()), index=1)
    culture = st.selectbox("Culture", ["Olives", "Cereales"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", min_value=1, value=15)
    prod = st.number_input("Rendement (T)", min_value=1, value=60)
    
    if mois in [12, 1, 2]: 
        saison = "Hiver"
    elif mois in [3, 4, 5]: 
        saison = "Printemps"
    elif mois in [6, 7, 8]: 
        saison = "Ete"
    else: 
        saison = "Automne"
    
    btn = st.button(
        "🚀 ANALYSER", 
        use_container_width=True, 
        type="primary"
    )

with col2:
    w = get_weather(region, mois)
    t, pl, hum, vent = w[0], w[1], w[2], w[3]
    t1, t2, t3 = st.tabs(["🌦️ Météo", "📉 Risque", "🛡️ Indemnité"])
    
    with t1:
        st.write(f"**Région :** {region} | **Saison :** {saison}")
        st.info(f"Temp: {t:.2f}°C | Pluie: {pl:.2f}mm")
    
    if btn:
        # --- 1. CALCUL DU MACHINE LEARNING ---
        risque_ml = 20.0
        if model_charge:
            try:
                cols = model_rf.feature_names_in_
                X = pd.DataFrame(0, index=[0], columns=cols)
                X["temp"] = t
                X["précipitations"] = pl
                X["humidité"] = hum
                X["vent"] = vent
                X["mois"] = mois
                X["annee"] = 2025
                
                c_reg = f"region_{region}"
                c_sais = f"saison_{saison}"
                
                if c_reg in X.columns: 
                    X[c_reg] = 1
                if c_sais
