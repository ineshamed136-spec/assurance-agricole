import streamlit as st
import joblib
import pandas as pd
import random

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# 1. CHARGEMENT MODÈLE
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# 2. CONFIGURATION RÉGIONALE
geo_conf = {
    "Tunis": {"facteur": 0.9, "coeff": 4.0, "seuil": 30.0},
    "Nabeul": {"facteur": 0.85, "coeff": 4.5, "seuil": 32.0},
    "Bizerte": {"facteur": 0.8, "coeff": 3.5, "seuil": 35.0},
    "Beja": {"facteur": 0.75, "coeff": 3.0, "seuil": 40.0},
    "Sousse": {"facteur": 0.95, "coeff": 4.2, "seuil": 28.0},
    "Monastir": {"facteur": 0.95, "coeff": 4.2, "seuil": 28.0},
    "Kairouan": {"facteur": 1.15, "coeff": 5.5, "seuil": 22.0},
    "Kebili": {"facteur": 1.4, "coeff": 7.0, "seuil": 10.0},
    "Gabes": {"facteur": 1.3, "coeff": 6.5, "seuil": 15.0}
}

# 3. GÉNÉRATEUR DE DONNÉES LOCALES (Sensible au mois)
def get_local_weather(reg, mois):
    # La pluviométrie diminue en été (mois 6, 7, 8)
    variation_saison = 0.5 if 6 <= mois <= 8 else 1.2
    temp = random.uniform(15.0 + (mois * 0.5), 25.0 + (mois * 0.5))
    pluie = random.uniform(5.0, 50.0) * variation_saison
    hum = random.uniform(40.0, 80.0)
    vent = random.uniform(2.0, 10.0)
    return temp, pluie, hum, vent

# 4. INTERFACE
st.title("🌾 Système d'Assurance Agricole (Mode Local)")
col1, col2 = st.columns([1, 2])

with col1:
    region = st.selectbox("Région", list(geo_conf.keys()))
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    culture = st.selectbox("Culture", ["Céréales", "Olives"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    btn = st.button("🚀 LANCER L'ANALYSE", type="primary")

with col2:
    t, pl, hum, vent = get_local_weather(region, mois)
    st.subheader(f"📊 Données Climatiques Simulées (Mois {mois})")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f}°C")
    m2.metric("Précipitations", f"{pl:.1f} mm")
    m3.metric("Humidité", f"{hum:.1f}%")
    m4.metric("Vent", f"{vent:.1f} m/s")

    if btn:
        cfg = geo_conf[region]
        
        # Calcul du risque (impacté par le mois et l'irrigation)
        risque_final = (25.0 * cfg["facteur"]) + (mois * 0.5)
        if irrigation == "Non": risque_final += 15
        risque_final = min(max(risque_final, 5.0), 95.0)
        
        prod_totale = sup * prod
        prime = (risque_final * cfg["coeff"]) + (sup * 12) + (prod_totale * 1.1)
        cap_max = (sup * 200) + (prod_totale * 25)

        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("🔥 Risque Global", f"{risque_final:.1f} %")
        c2.metric("💳 Prime à payer", f"{prime:.2f} DT")
        
        st.divider()
        if pl < cfg["seuil"]:
            ind = ((cfg["seuil"] - pl) / cfg["seuil"]) * cap_max
            st.error(f"💰 Indemnité de sinistre : {ind:.2f} DT")
        else:
            st.success("✅ Conditions favorables.")
            st.info("💰 Aide de soutien : 50.00 DT")
