import streamlit as st
import joblib
import pandas as pd
import requests
import os

st.set_page_config(page_title="Assurance", layout="wide")

@st.cache_resource
def load_model():
    try:
        path = os.path.join(os.path.dirname(__file__), "model.pkl")
        return joblib.load(path), True
    except:
        return None, False

model_rf, model_charge = load_model()

coords = {
    "Tunis": (36.80, 10.18), "Nabeul": (36.45, 10.73),
    "Bizerte": (37.27, 9.87), "Beja": (36.72, 9.18),
    "Sousse": (35.82, 10.60), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.70, 8.97),
    "Gabes": (33.88, 10.09)
}

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

st.title("🌾 Assurance Agricole")
col1, col2 = st.columns([1, 1.2])

with col1:
    region = st.selectbox("Region", list(coords.keys()))
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", value=15)
    prod = st.number_input("Rendement (T)", value=60)
    btn = st.button("🚀 ANALYSER")

with col2:
    w = get_weather(region, mois)
    t, pl, hum, vent = w[0], w[1], w[2], w[3]
    
    if btn:
        risque_ml = 20.0
        if model_charge:
            try:
                X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)
                for col in X.columns:
                    if "temp" in col: X[col] = t
                    if "precip" in col: X[col] = pl
                risque_ml = model_rf.predict_proba(X)[0][1] * 100
            except:
                risque_ml = min(90, t * 2.2)
        
        r_regle = 10 + (max(0, 35-pl) * 2) + (max(0, t-30) * 3.5) + (15 if irrigation == "Non" else 0)
        risque = (0.7 * risque_ml) + (0.3 * r_regle)
        
        st.metric("🔥 Risque Global", f"{risque:.1f} %")
        st.progress(int(min(100, risque)))
        
        if pl < 35:
            st.error(f"💰 Indemnité : {((35-pl)/27)*5000:.0f} DT")
        else:
            st.success("💰 Aucune indemnité")
            
