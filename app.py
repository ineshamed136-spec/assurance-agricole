import streamlit as st
import joblib
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# STYLE CSS POUR NETTOYAGE
st.markdown("""
<style>
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; }
[data-testid="stHeaderActionElements"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# 1. BASE DE DONNÉES CLIMATIQUES (Source: Normales NASA POWER pour la Tunisie)
# Format: {Mois: (Temp, Pluie, Humidité, Vent)}
def get_nasa_climate(mois):
    data = {
        1: (12.0, 60.0, 75.0, 18.0), 2: (13.5, 50.0, 70.0, 19.0),
        3: (15.5, 45.0, 65.0, 20.0), 4: (18.0, 40.0, 60.0, 18.0),
        5: (22.0, 25.0, 55.0, 16.0), 6: (26.0, 15.0, 50.0, 15.0),
        7: (29.0, 5.0, 45.0, 14.0), 8: (30.0, 10.0, 45.0, 14.0),
        9: (27.0, 30.0, 55.0, 15.0), 10: (22.0, 40.0, 60.0, 16.0),
        11: (17.0, 55.0, 70.0, 17.0), 12: (13.0, 65.0, 75.0, 18.0)
    }
    return data.get(mois, (20.0, 30.0, 50.0, 15.0))

# 2. CONFIGURATION RÉGIONALE
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

# 3. INTERFACE
st.markdown("<h1 style='font-size:38px;'>🌾 Système Intelligent d’Assurance Agricole</h1>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("<h3>⚙️ Paramètres Agricoles</h3>", unsafe_allow_html=True)
    region = st.selectbox("Région", list(geo_conf.keys()))
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=datetime.now().month - 1)
    culture = st.selectbox("Culture", ["Céréales", "Olives"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    btn = st.button("🚀 LANCER L'ANALYSE", type="primary")

with col2:
    t, pl, hum, vent = get_nasa_climate(mois)
    cfg = geo_conf[region]

    st.markdown("<h2>📊 Données Climatiques</h2>", unsafe_allow_html=True)
    st.markdown("Sources : NASA POWER (Normales Climatologiques)")

    # Affichage corrigé sans coupure de chaîne
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f} °C")
    m2.metric("Précipitations", f"{pl:.1f} mm")
    m3.metric("Vent", f"{vent:.1f} km/h")
    m4.metric("Humidité", f"{hum:.1f} %")

    if btn:
        val_irrigation = 15 if irrigation == "Non" else 0
        risque_base = (25.0 * cfg["facteur"]) + (mois * 0.5) + val_irrigation
        risque_final = min(max(risque_base, 5.0), 95.0)
        
        prod_totale = sup * prod
        prime = (risque_final * cfg["coeff"]) + (sup * 12) + (prod_totale * 1.1)
        cap_max = (sup * 200) + (prod_totale * 25)

        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("🔥 Risque Global", f"{risque_final:.1f} %")
        c2.metric("💳 Prime à payer", f"{prime:.2f} DT")
        
        st.divider()
        if pl < cfg["seuil"]:
            indemnite = ((cfg['seuil'] - pl) / cfg['seuil']) * cap_max
            st.error(f"💰 Indemnité de sinistre : {indemnite:.2f} DT")
        else:
            st.success("✅ Conditions climatiques favorables.")

        with st.expander("ℹ️ Méthodologie"):
            st.latex(r"Prime = (Risque \times Coeff) + (Sup \times 12) + (Prod \times 1.1)")
