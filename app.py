import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance", layout="wide")

@st.cache_resource
def load_model():
    try: return joblib.load("model_rf.pkl"), True
    except: return None, False
model_rf, model_charge = load_model()

coords = {
    "Tunis": (36.80, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.60), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.70, 8.97), "Gabes": (33.88, 10.09)
}

@st.cache_data(ttl=3600)
def get_weather(reg, m):
    lat, lon = coords[reg]
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    p = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2025", "end": "2025", "format": "JSON"}
    try:
        r = requests.get(url, params=p, timeout=8)
        if r.status_code != 200: return [24.5, 12.0, 60.0, 4.0]
        d = r.json()["properties"]["parameter"]
        k = f"2025{m:02d}"
        return [float(d["T2M"][k]), float(d["PRECTOTCORR"][k]), float(d["RH2M"][k]), float(d["WS2M"][k])]
    except: return [24.5, 12.0, 60.0, 4.0]

st.title("🌾 Assurance Agricole Paramétrique")
if model_charge: st.sidebar.success("ML Actif")
else: st.sidebar.warning("Mode Regles Metiers")

col1, col2 = st.columns([1, 1.2], gap="medium")
with col1:
    st.subheader("Contrat")
    uid = st.text_input("ID Exploitant", value="TUN-01")
    region = st.selectbox("Region", list(coords.keys()), index=1)
    culture = st.selectbox("Culture", ["Olives", "Cereales"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=7)
    sup = st.number_input("Superficie (Ha)", min_value=1, value=15)
    prod = st.number_input("Rendement (T)", min_value=1, value=60)
    saison = "Hiver" if mois in [12,1,2] else "Printemps" if mois in [3,4,5] else "Ete" if mois in [6,7,8] else "Automne"
    btn = st.button("🚀 ANALYSER", use_container_width=True, type="primary")

with col2:
    w = get_weather(region, mois)
    t, pl, hum, vent = w[0], w[1], w[2], w[3]
    t1, t2, t3 = st.tabs(["🌦️ Meteo", "📉 Risque & Prime", "🛡️ Indemnite"])
    
    with t1:
        st.write(f"**Region :** {region} | **Saison :** {saison}")
        st.info(f"🌡️ Temp: {t:.2f} °C | 🌧️ Pluie: {pl:.2f} mm | 💧 Hum: {hum:.2f} % | 💨 Vent: {vent:.2f} m/s")
    
    if btn:
        risque_ml = 20.0
        if model_charge:
            try:
                X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)
                X["temp"], X["précipitations"], X["humidité"], X["vent"], X["mois"], X["annee"] = t, pl, hum, vent, mois, 2025
                if f"region_{region}" in X.columns: X[f"region_{region}"] = 1
                if f"saison_{saison}" in X.columns: X[f"saison_{saison}"] = 1
                risque_ml = model_rf.predict_proba(X)[0][1] * 100
            except: pass

        r_regle = 10
        explication_regle = "Score de base : 10%"
        if pl < 15: 
            r_regle += 35
            explication_regle += " + 35% (Pluie < 15mm)"
        if t > 38: 
            r_regle += 25
            explication_regle += " + 25% (Temp > 38°C)"
        if irrigation == "Non": 
            r_regle += 15
            explication_regle += " + 15% (Pas d'irrigation)"
        
        risque = max(0, min(100, (0.7 * risque_ml) + (0.3 * r_regle)))
        prime_pure = risque * 4.2
        frais_chargement = (sup * 12) + (prod * 1.1)
        prime = prime_pure + frais_chargement
        
        with t2:
            st.markdown("###
