import streamlit as st
import joblib
import pandas as pd
import requests

# Configuration de la page
st.set_page_config(page_title="Assurance Agricole", layout="wide")

# 1. CHARGEMENT MODÈLE
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# 2. CONFIGURATION GÉOGRAPHIQUE
seuils_regionaux = {
    "Tunis": 30.0, "Nabeul": 32.0, "Bizerte": 35.0, 
    "Beja": 40.0, "Sousse": 28.0, "Monastir": 28.0, 
    "Kairouan": 22.0, "Kebili": 10.0, "Gabes": 15.0
}

coeff_actuariel_map = {
    "Tunis": 4.0, "Nabeul": 4.5, "Bizerte": 3.5, 
    "Beja": 3.0, "Sousse": 4.2, "Monastir": 4.2, 
    "Kairouan": 5.5, "Kebili": 7.0, "Gabes": 6.5
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
        return r.json(), r.json()["properties"]["parameter"]
    except: 
        return {}, {"T2M": {"202605": 24.5}, "PRECTOTCORR": {"202605": 12.0}, "RH2M": {"202605": 60.0}, "WS2M": {"202605": 4.0}}

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
    btn = st.button("🚀 LANCER L'ANALYSE", type="primary")

with col2:
    json_data, data = get_weather(region, mois)
    k = f"2026{mois:02d}"
    t, pl, hum, vent = float(data["T2M"][k]), float(data["PRECTOTCORR"][k]), float(data["RH2M"][k]), float(data["WS2M"][k])
    
    st.subheader("📊 Données Climatiques (NASA Power)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f}°C")
    m2.metric("Précipitations", f"{pl:.1f} mm")
    m3.metric("Humidité", f"{hum:.1f}%")
    m4.metric("Vent", f"{vent:.1f} m/s")

    if btn:
        st.subheader("🔍 Rapport d'Analyse Agronomique")
        
        risque_base = 20.0
        if model_charge:
            try:
                X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)
                mapping = {"temp": t, "précipitations": pl, "humidité": hum, "vent": vent, "mois": mois}
                for col in X.columns:
                    if col in mapping: X[col] = mapping[col]
                risque_base = model_rf.predict_proba(X)[0][1] * 100
            except: 
                pass

        risque_final = min(max(risque_base, 5.0), 95.0)
        
        # Diagnostic
        seuil = seuils_regionaux.get(region, 30.0)
        if pl < seuil:
            deficit_pct = ((seuil - pl) / seuil) * 100
            st.error(f"**Diagnostic :** Stress hydrique détecté (Déficit de {deficit_pct:.1f}%).")
        else:
            st.success("**Diagnostic :** Niveau hydrique optimal.")

        # Calculs Financiers
        prod_totale = sup * prod
        cap_max = (sup * 200) + (prod_totale * 25)
        coeff_act = coeff_actuariel_map.get(region, 4.2)
        prime = (risque_final * coeff_act) + (sup * 12) + (prod_totale * 1.1)

        st.divider()
        st.subheader("💰 Impact Financier")
        c1, c2 = st.columns(2)
        c1.metric("🔥 Risque Global", f"{risque_final:.1f} %")
        c2.metric("💳 Prime à payer", f"{prime:.2f} DT")
        
        if pl < seuil:
            facteur_irrigation = 0.5 if irrigation == "Oui" else 1.0
            ind = ((seuil - pl) / seuil) * cap_max * facteur_irrigation
            st.metric("💰 Indemnité de sinistre estimée", f"{ind:.2f} DT")
        else:
            st.info("💰 Aide de soutien prévue : 50.00 DT")

        with st.expander("ℹ️ Méthodologie et Transparence"):
            st.markdown("""
            ### 1. Formules utilisées
            $$Prime = (Risque \\times Coeff_{Actuariel}) + (Superficie \\times 12) + (Prod_{Totale} \\times 1.1)$$
            $$Indemnité = \\left( \\frac{Seuil - Pluviométrie}{Seuil} \\right) \\times Cap_{Max} \\times Facteur_{Irrigation}$$
            """)
            st.write("### 2. Données brutes (Source NASA)")
            st.json(json_data)
