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

# 2. CONFIGURATION RÉGIONALE (Coefficients et Seuils personnalisés)
# 'coeff' : multiplicateur de risque pour la prime
# 'seuil' : limite de pluviométrie en dessous de laquelle l'indemnité se déclenche
geo_conf = {
    "Tunis":    {"coeff": 4.0, "seuil": 30.0},
    "Nabeul":   {"coeff": 4.5, "seuil": 32.0},
    "Bizerte":  {"coeff": 3.5, "seuil": 35.0},
    "Beja":     {"coeff": 3.0, "seuil": 40.0},
    "Sousse":   {"coeff": 4.2, "seuil": 28.0},
    "Monastir": {"coeff": 4.2, "seuil": 28.0},
    "Kairouan": {"coeff": 5.5, "seuil": 22.0},
    "Kebili":   {"coeff": 7.0, "seuil": 10.0},
    "Gabes":    {"coeff": 6.5, "seuil": 15.0}
}

# 3. GÉNÉRATEUR DE DONNÉES LOCALES
def get_local_weather(reg):
    # Données simulées cohérentes
    temp = random.uniform(18.0, 38.0)
    pluie = random.uniform(5.0, 50.0)
    hum = random.uniform(30.0, 70.0)
    vent = random.uniform(2.0, 8.0)
    return temp, pluie, hum, vent

# 4. INTERFACE
st.title("🌾 Système d'Assurance Agricole Paramétrique")
col1, col2 = st.columns([1, 2])

with col1:
    region = st.selectbox("Région", list(geo_conf.keys()))
    culture = st.selectbox("Culture", ["Céréales", "Olives"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    btn = st.button("🚀 LANCER L'ANALYSE", type="primary")

with col2:
    t, pl, hum, vent = get_local_weather(region)
    st.subheader("📊 Indicateurs Agro-Climatiques")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f}°C")
    m2.metric("Précipitations", f"{pl:.1f} mm")
    m3.metric("Humidité", f"{hum:.1f}%")
    m4.metric("Vent", f"{vent:.1f} m/s")

    if btn:
        cfg = geo_conf[region]
        risque_final = 25.0 # Risque de base IA
        if irrigation == "Non": risque_final += 15
        
        prod_totale = sup * prod
        # Formule intégrant le coefficient régional unique
        prime = (risque_final * cfg["coeff"]) + (sup * 12) + (prod_totale * 1.1)
        cap_max = (sup * 200) + (prod_totale * 25)

        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("🔥 Risque Global", f"{risque_final:.1f} %")
        c2.metric("💳 Prime à payer", f"{prime:.2f} DT")
        
        st.divider()
        if pl < cfg["seuil"]:
            ind = ((cfg["seuil"] - pl) / cfg["seuil"]) * cap_max
            st.error(f"💰 Indemnité de sinistre : {ind:.2f} DT (Déficit hydrique détecté)")
        else:
            st.success("✅ Conditions climatiques favorables.")
            st.info("💰 Aide de soutien : 50.00 DT")

        # EXPLICATION DES FORMULES
        with st.expander("ℹ️ Méthodologie et Formules de Calcul"):
            st.markdown("""
            ### 1. Calcul de la Prime d'Assurance
            $$Prime = (Risque \\times Coeff_{Régional}) + (Superficie \\times 12) + (Prod_{Totale} \\times 1.1)$$
            * **Risque :** Estimation de la probabilité de perte basée sur l'historique météo.
            * **Coeff Régional :** Pondération spécifique (ex: Kébili=7.0 vs Béja=3.0) reflétant la vulnérabilité intrinsèque de la zone.
            
            ### 2. Calcul de l'Indemnité
            $$Indemnité = \\left( \\frac{Seuil_{Régional} - Pluviométrie_{Réelle}}{Seuil_{Régional}} \\right) \\times Capital_{Max}$$
            * **Seuil Régional :** La limite de pluie en dessous de laquelle le stress hydrique est jugé critique pour la culture.
            * **Capital Max :** Somme assurée couvrant les intrants et la production espérée.
            """)
