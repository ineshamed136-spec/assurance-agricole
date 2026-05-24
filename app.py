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

# 2. CONFIGURATION GÉOGRAPHIQUE
coords = {
    "Tunis": (36.8, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.6), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.7, 8.97), "Gabes": (33.88, 10.09)
}

# 3. FONCTION MÉTÉO
@st.cache_data(ttl=3600)
def get_weather(reg, m):
    lat, lon = coords[reg]
    p = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2025", "end": "2025", "format": "JSON"}
    try:
        r = requests.get("https://power.larc.nasa.gov/api/temporal/monthly/point", params=p, timeout=8)
        d = r.json()["properties"]["parameter"]
        k = f"2025{m:02d}"
        return [float(d["T2M"][k]), float(d["PRECTOTCORR"][k]), float(d["RH2M"][k]), float(d["WS2M"][k])]
    except:
        return [24.5, 12.0, 60.0, 4.0]

# 4. INTERFACE
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
        risque = 20.0
        if model_charge:
            try:
                # Préparation du dataframe avec les features attendues par le modèle
                X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)
                
                # Remplissage des données
                mapping = {"temp": t, "précipitations": pl, "humidité": hum, "vent": vent, "mois": mois}
                for col in X.columns:
                    if col in mapping: X[col] = mapping[col]
                    # Tentative d'activation de la région si la colonne existe dans le modèle
                    if col == f"region_{region}": X[col] = 1
                
                risque = model_rf.predict_proba(X)[0][1] * 100
            except Exception as e:
                st.warning("Note : Le modèle n'a pas pu traiter toutes les données régionales.")

        # Calculs financiers
        prod_totale = sup * prod
        prime = (risque * 4.2) + (sup * 12) + (prod_totale * 1.1)
        cap_max = (sup * 200) + (prod_totale * 25)
        ind = max(0, ((35.0 - pl) / 27.0) * cap_max) if pl < 35 else 0

        st.metric("🔥 Risque Global", f"{risque:.1f} %")
        st.metric("💳 Prime à payer", f"{prime:.2f} DT")
        st.error(f"💰 Indemnité estimée : {ind:.2f} DT")
