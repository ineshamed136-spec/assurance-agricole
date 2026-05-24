import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# 1. CHARGEMENT DU MODÈLE
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# Liste des régions pour correspondance numérique
regions_list = ["Tunis", "Nabeul", "Bizerte", "Beja", "Sousse", "Monastir", "Kairouan", "Kebili", "Gabes"]

@st.cache_data(ttl=3600)
def get_weather(reg, m):
    # Coordonnées NASA
    coords = {
        "Tunis": (36.8, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
        "Beja": (36.72, 9.18), "Sousse": (35.82, 10.6), "Monastir": (35.76, 10.81),
        "Kairouan": (35.67, 10.09), "Kebili": (33.7, 8.97), "Gabes": (33.88, 10.09)
    }
    lat, lon = coords[reg]
    p = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2025", "end": "2025", "format": "JSON"}
    try:
        r = requests.get("https://power.larc.nasa.gov/api/temporal/monthly/point", params=p, timeout=8)
        d = r.json()["properties"]["parameter"]
        k = f"2025{m:02d}"
        return [float(d["T2M"][k]), float(d["PRECTOTCORR"][k]), float(d["RH2M"][k]), float(d["WS2M"][k])]
    except: return [24.5, 12.0, 60.0, 4.0]

# 2. INTERFACE
st.title("🌾 Assurance Agricole")
col1, col2 = st.columns([1, 2])

with col1:
    region = st.selectbox("Région", regions_list)
    culture = st.selectbox("Culture", ["Céréales", "Olives"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    btn = st.button("🚀 CALCULER", type="primary")

with col2:
    t, pl, hum, vent = get_weather(region, mois)
    if btn:
        risque = 20.0
        if model_charge:
            try:
                X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)
                
                # Conversion de la région en index numérique (0, 1, 2...)
                region_idx = regions_list.index(region)
                
                for col in X.columns:
                    if col == "temp": X[col] = t
                    elif col == "précipitations": X[col] = pl
                    elif col == "humidité": X[col] = hum
                    elif col == "vent": X[col] = vent
                    elif col == "mois": X[col] = mois
                    # Si une colonne s'appelle "region" ou "Region", on y met le chiffre
                    elif col.lower() == "region": X[col] = region_idx
                
                risque = model_rf.predict_proba(X)[0][1] * 100
            except Exception as e:
                st.warning("Le modèle ne reconnaît pas la structure des données.")

        if irrigation == "Non": risque += 10
        risque = min(max(risque, 0.0), 100.0)
        
        prime = (risque * 4.2) + (sup * 12) + (prod * 1.1)
        ind = max(0, ((35.0 - pl) / 27.0) * ((sup * 200) + (prod * 25))) if pl < 35 else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("🔥 Risque", f"{risque:.1f} %")
        m2.metric("💳 Prime", f"{prime:.2f} DT")
        m3.error(f"💰 Indemnité : {ind:.2f} DT")

        st.write("---")
        st.write("Si le risque est toujours le même, ton fichier `model.pkl` a été entraîné avec des données qui ne prennent pas en compte la localisation géographique.")
