import streamlit as st
import joblib
import pandas as pd
import requests

# Configuration de la page
st.set_page_config(page_title="Assurance Agricole", layout="wide")

# 1. CHARGEMENT DU MODÈLE
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# 2. CONFIGURATION : Poids géographiques pour forcer la différenciation des risques
geo_factors = {
    "Tunis": 0.9, "Nabeul": 0.85, "Bizerte": 0.8, 
    "Beja": 0.75, "Sousse": 0.95, "Monastir": 0.95, 
    "Kairouan": 1.15, "Kebili": 1.4, "Gabes": 1.3
}

coords = {
    "Tunis": (36.8, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.6), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.7, 8.97), "Gabes": (33.88, 10.09)
}

# 3. COLLECTE MÉTÉO (NASA POWER)
@st.cache_data(ttl=3600)
def get_weather(reg, m):
    lat, lon = coords[reg]
    p = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2025", "end": "2025", "format": "JSON"}
    try:
        r = requests.get("https://power.larc.nasa.gov/api/temporal/monthly/point", params=p, timeout=8)
        d = r.json()["properties"]["parameter"]
        k = f"2025{m:02d}"
        return [float(d["T2M"][k]), float(d["PRECTOTCORR"][k]), float(d["RH2M"][k]), float(d["WS2M"][k])]
    except: return [24.5, 12.0, 60.0, 4.0]

# 4. INTERFACE UTILISATEUR
st.title("🌾 Assurance Agricole")
col1, col2 = st.columns([1, 2])

with col1:
    region = st.selectbox("Région", list(coords.keys()))
    culture = st.selectbox("Culture", ["Céréales", "Olives"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    btn = st.button("🚀 CALCULER", type="primary")

with col2:
    t, pl, hum, vent = get_weather(region, mois)
    if btn:
        # A. Risque IA pur
        risque_base = 20.0
        if model_charge:
            try:
                X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)
                mapping = {"temp": t, "précipitations": pl, "humidité": hum, "vent": vent, "mois": mois}
                for col in X.columns:
                    if col in mapping: X[col] = mapping[col]
                risque_base = model_rf.predict_proba(X)[0][1] * 100
            except: pass

        # B. APPLICATION DU RISQUE HYBRIDE (IA + Poids Géographique)
        facteur = geo_factors.get(region, 1.0)
        risque_final = risque_base * facteur
        if irrigation == "Non": risque_final += 15
        risque_final = min(max(risque_final, 5.0), 95.0)
        
        # C. CALCULS FINANCIERS
        prod_totale = sup * prod
        prime = (risque_final * 4.2) + (sup * 12) + (prod_totale * 1.1)
        cap_max = (sup * 200) + (prod_totale * 25)
        ind = max(0, ((35.0 - pl) / 27.0) * cap_max) if pl < 35 else 0

        # D. AFFICHAGE
        m1, m2, m3 = st.columns(3)
        m1.metric("🔥 Risque Hybride", f"{risque_final:.1f} %")
        m2.metric("💳 Prime Finale", f"{prime:.2f} DT")
        m3.error(f"💰 Indemnité : {ind:.2f} DT")
        
        st.write("---")
        st.write(f"💡 *Ajustement géographique appliqué pour la région de **{region}**.*")
