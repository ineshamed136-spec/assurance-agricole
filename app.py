import streamlit as st
import joblib
import pandas as pd
import requests

# Configuration de la page
st.set_page_config(page_title="Assurance Agricole", layout="wide")

# 1. CHARGEMENT MODÈLE
@st.cache_resource
def load_model():
    try: 
        return joblib.load("model.pkl"), True
    except: 
        return None, False

model_rf, model_charge = load_model()

# 2. CONFIGURATION GÉOGRAPHIQUE ET SEUILS
# Seuils de précipitations (mm) en dessous desquels le déficit est critique
seuils_regionaux = {
    "Tunis": 30.0, "Nabeul": 32.0, "Bizerte": 35.0, 
    "Beja": 40.0, "Sousse": 28.0, "Monastir": 28.0, 
    "Kairouan": 22.0, "Kebili": 10.0, "Gabes": 15.0
}

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

@st.cache_data(ttl=3600)
def get_weather(reg, m):
    lat, lon = coords[reg]
    p = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2026", "end": "2026", "format": "JSON"}
    try:
        r = requests.get("https://power.larc.nasa.gov/api/temporal/monthly/point", params=p, timeout=8)
        d = r.json()["properties"]["parameter"]
        k = f"2026{m:02d}"
        return [float(d["T2M"][k]), float(d["PRECTOTCORR"][k]), float(d["RH2M"][k]), float(d["WS2M"][k])]
    except: 
        return [24.5, 12.0, 60.0, 4.0]

# 3. INTERFACE UTILISATEUR
st.title("🌾 Système d'Assurance Agricole Paramétrique")
col1, col2 = st.columns([1, 2])

with col1:
    region = st.selectbox("Région", list(coords.keys()))
    culture = st.selectbox("Culture", ["Céréales", "Olives"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    btn = st.button("🚀 CALCULER L'INDEMNITÉ", type="primary")

with col2:
    t, pl, hum, vent = get_weather(region, mois)
    st.subheader("📊 Données Climatiques (NASA Power)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f}°C")
    m2.metric("Précipitations", f"{pl:.1f} mm")
    m3.metric("Humidité", f"{hum:.1f}%")
    m4.metric("Vent", f"{vent:.1f} m/s")

    if btn:
        # Calcul du risque
        risque_base = 20.0
        if model_charge:
            try:
                X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)
                mapping = {"temp": t, "précipitations": pl, "humidité": hum, "vent": vent, "mois": mois}
                for col in X.columns:
                    if col in mapping:
                        X[col] = mapping[col]
                risque_base = model_rf.predict_proba(X)[0][1] * 100
            except Exception as e:
                st.warning(f"Erreur modèle : {e}")

        risque_final = risque_base * geo_factors.get(region, 1.0)
        if irrigation == "Non": risque_final += 15
        risque_final = min(max(risque_final, 5.0), 95.0)
        
        prod_totale = sup * prod
        prime = (risque_final * 4.2) + (sup * 12) + (prod_totale * 1.1)
        cap_max = (sup * 200) + (prod_totale * 25)

        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("🔥 Risque Global", f"{risque_final:.1f} %")
        c2.metric("💳 Prime à payer", f"{prime:.2f} DT")
        
        # LOGIQUE D'INDEMNISATION DYNAMIQUE
        st.divider()
        seuil = seuils_regionaux.get(region, 30.0)
        
        if pl < seuil:
            deficit = (seuil - pl) / seuil
            # Si irrigué, indemnisation réduite par 2 car l'agriculteur limite ses pertes
            facteur_irrigation = 0.5 if irrigation == "Oui" else 1.0
            ind = deficit * cap_max * facteur_irrigation
            
            st.error(f"⚠️ Déficit hydrique détecté (Seuil {region} : {seuil}mm)")
            st.metric("💰 Indemnité de sinistre estimée", f"{ind:.2f} DT")
        else:
            st.success("✅ Conditions hydriques optimales.")
            st.info("💰 Aide de soutien symbolique : 50.00 DT")

        with st.expander("ℹ️ Méthodologie"):
            st.write(f"Le calcul est basé sur un seuil de précipitations régional de **{seuil} mm**.")
            st.write("Si les précipitations sont inférieures à ce seuil, l'indemnisation est proportionnelle au déficit constaté.")
            st.write("L'irrigation réduit l'indemnité finale car elle limite l'impact du déficit sur la culture.")
