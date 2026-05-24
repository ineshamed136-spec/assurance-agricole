import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance", layout="wide")

# ==================================
# 1. CHARGEMENT DU MODELE
# ==================================
@st.cache_resource
def load_model():
    try:
        m = joblib.load("model.pkl")
        return m, True
    except:
        return None, False

model_rf, model_charge = load_model()

coords = {
    "Tunis": (36.80, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.60), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.70, 8.97), "Gabes": (33.88, 10.09)
}

# ==================================
# 2. COLLECTE DES DONNEES (NASA)
# ==================================
@st.cache_data(ttl=3600)
def get_weather(reg, m):
    lat, lon = coords[reg]
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    p = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2025", "end": "2025", "format": "JSON"}
    try:
        r = requests.get(url, params=p, timeout=8)
        d = r.json()["properties"]["parameter"]
        k = f"2025{m:02d}"
        return [float(d["T2M"][k]), float(d["PRECTOTCORR"][k]), float(d["RH2M"][k]), float(d["WS2M"][k])]
    except:
        return [24.5, 12.0, 60.0, 4.0]

# ==================================
# 3. INTERFACE UTILISATEUR
# ==================================
st.title("🌾 Assurance Agricole")
col1, col2 = st.columns([1, 1.2], gap="medium")

with col1:
    uid = st.text_input("ID Exploitant", value="TUN-01")
    region = st.selectbox("Region", list(coords.keys()), index=1)
    culture = st.selectbox("Culture", ["Olives", "Cereales"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", min_value=1, value=15)
    prod = st.number_input("Rendement (T)", min_value=1, value=60)
    btn = st.button("🚀 ANALYSER", use_container_width=True, type="primary")

with col2:
    w = get_weather(region, mois)
    t, pl, hum, vent = w[0], w[1], w[2], w[3]
    tabs = ["🌦️ Météo", "📉 Risque", "🛡️ Payout"]
    t1, t2, t3 = st.tabs(tabs)

    with t1:
        st.info(f"🌡️ Température : {t:.1f}°C")
        st.info(f"🌧️ Pluviométrie : {pl:.1f} mm")
        st.info(f"💧 Humidité : {hum:.1f} %")
        st.info(f"💨 Vent : {vent:.1f} m/s")

    if btn:
        # --- CALCUL RISQUE ML PUR ---
        risque = 20.0
        if model_charge:
            try:
                X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)
                mapping = {"temp": t, "précipitations": pl, "humidité": hum, "vent": vent, "mois": mois}
                for col in X.columns:
                    if col in mapping: X[col] = mapping[col]
                risque = model_rf.predict_proba(X)[0][1] * 100
            except: pass

        # Tarification basée sur le risque ML
        prime = (risque * 4.2) + (sup * 12) + (prod * 1.1)

        with t2:
            st.metric("🔥 Risque ML pur", f"{risque:.1f} %")
            st.metric("💳 Prime Finale", f"{prime:.1f} DT")
            st.progress(int(risque))

        with t3:
            # Indemnité basée sur la pluviométrie
            cap_max = (sup * 200) + (prod * 25)
            ind = 0.0
            if pl < 35.0:
                p_rate = (35.0 - pl) / 27.0 if pl > 8.0 else 1.0
                ind = p_rate * cap_max
            
            if ind > 0:
                st.error(f"💰 Indemnité estimée : {ind:.1f} DT")
            else:
                st.success("💰 Aucune indemnité (Conditions normales)")
