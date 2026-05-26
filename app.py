import streamlit as st
import joblib
import pandas as pd
import random

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# STYLE POUR SUPPRIMER LES ÉLÉMENTS DE LIEN
st.markdown("""
<style>
h1 a, h2 a, h3 a {display: none !important;}
[data-testid="stHeaderActionElements"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# 1. CONFIGURATION RÉGIONALE (Inchangée)
geo_conf = {
    "Tunis": {"facteur": 0.9, "coeff": 4.0, "seuil": 30.0, "moyenne_20ans": 45.5},
    "Nabeul": {"facteur": 0.85, "coeff": 4.5, "seuil": 32.0, "moyenne_20ans": 42.0},
    "Bizerte": {"facteur": 0.8, "coeff": 3.5, "seuil": 35.0, "moyenne_20ans": 55.2},
    "Beja": {"facteur": 0.75, "coeff": 3.0, "seuil": 40.0, "moyenne_20ans": 60.8},
    "Sousse": {"facteur": 0.95, "coeff": 4.2, "seuil": 28.0, "moyenne_20ans": 38.4},
    "Monastir": {"facteur": 0.95, "coeff": 4.2, "seuil": 28.0, "moyenne_20ans": 37.9},
    "Kairouan": {"facteur": 1.15, "coeff": 5.5, "seuil": 22.0, "moyenne_20ans": 25.1},
    "Kebili": {"facteur": 1.4, "coeff": 7.0, "seuil": 10.0, "moyenne_20ans": 12.5},
    "Gabes": {"facteur": 1.3, "coeff": 6.5, "seuil": 15.0, "moyenne_20ans": 18.2},
    "Médenine": {"facteur": 1.5, "coeff": 7.5, "seuil": 8.0, "moyenne_20ans": 10.5}
}

# 2. GÉNÉRATEUR DE DONNÉES (Inchangé)
def get_local_weather(reg, mois):
    random.seed(reg + str(mois))
    t = random.uniform(15.0, 30.0)
    pl = random.uniform(5.0, 60.0)
    h = random.uniform(40.0, 80.0)
    v = random.uniform(2.0, 10.0)
    return t, pl, h, v

# 3. INTERFACE
st.markdown("<h1 style='font-size:38px;'>🌾 Système Intelligent d’Assurance Agricole</h1>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("<h3>⚙️ Paramètres Agricoles</h3>", unsafe_allow_html=True)
    region = st.selectbox("Région", list(geo_conf.keys()))
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    btn = st.button("🚀 LANCER L'ANALYSE", type="primary")

with col2:
    t, pl, hum, vent = get_local_weather(region, mois)
    cfg = geo_conf[region]
    st.markdown("<h2>📊 Données Climatiques</h2>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f} °C")
    m2.metric("Précipitations", f"{pl:.1f} mm")
    m3.metric("Vent", f"{vent:.1f} km/h")
    m4.metric("Humidité", f"{hum:.1f} %")

    if btn:
        # LOGIQUE DE CORRÉLATION : Le risque intègre le stress hydrique (pluie vs seuil)
        stress_hydrique = max(0, (cfg["seuil"] - pl) / cfg["seuil"]) * 50
        risque_final = min(max((25.0 * cfg["facteur"]) + stress_hydrique, 5.0), 95.0)
        
        prod_totale = sup * prod
        cap_max = (sup * 200) + (prod_totale * 25)
        
        # Prime et Indemnité corrélées au risque
        prime = (risque_final / 100) * (cap_max * 0.15) + 50 
        ind = (cap_max * 0.6) * (risque_final / 100) if risque_final > 30 else 0

        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("🔥 Risque Global", f"{risque_final:.1f} %")
        c2.metric("💳 Prime à payer", f"{prime:.2f} DT")
        
        if ind > 0:
            st.error(f"💰 Indemnité de sinistre calculée : {ind:.2f} DT")
        else:
            st.success("✅ Risque maîtrisé : Aucune indemnité requise.")

        with st.expander("ℹ️ Méthodologie : Modèle Probabiliste"):
            st.markdown("""
            La prime et l'indemnité sont indexées sur la probabilité de risque prédite. 
            Plus le risque est élevé, plus la prime augmente pour couvrir l'espérance de perte.
            """)
            st.latex(r"Prime = \frac{Risque}{100} \times (Capital_{Max} \times 0.15) + Fixes")
            st.latex(r"Indemnité = (Capital_{Max} \times 0.6) \times \frac{Risque}{100}")
