import streamlit as st
import joblib
import pandas as pd
import random
import os

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# STYLE POUR SUPPRIMER LES ÉLÉMENTS DE LIEN
st.markdown("""
<style>
h1 a, h2 a, h3 a {display: none !important;}
[data-testid="stHeaderActionElements"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# 1. CHARGEMENT SÉCURISÉ DU MODÈLE
@st.cache_resource
def load_model():
    # Construction du chemin dynamique
    file_path = os.path.join(os.path.dirname(__file__), 'modele_risque.joblib')
    if not os.path.exists(file_path):
        return None
    return joblib.load(file_path)

model = load_model()

# 2. CONFIGURATION RÉGIONALE
geo_conf = {
    "Tunis": {"facteur": 0.9, "seuil": 30.0, "type": "nord"},
    "Nabeul": {"facteur": 0.85, "seuil": 32.0, "type": "nord"},
    "Bizerte": {"facteur": 0.8, "seuil": 35.0, "type": "nord"},
    "Beja": {"facteur": 0.75, "seuil": 40.0, "type": "nord"},
    "Sousse": {"facteur": 0.95, "seuil": 28.0, "type": "centre"},
    "Monastir": {"facteur": 0.95, "seuil": 28.0, "type": "centre"},
    "Kairouan": {"facteur": 1.15, "seuil": 22.0, "type": "centre"},
    "Kebili": {"facteur": 1.4, "seuil": 10.0, "type": "sud"},
    "Gabes": {"facteur": 1.3, "seuil": 15.0, "type": "sud"},
    "Médenine": {"facteur": 1.5, "seuil": 8.0, "type": "sud"}
}

# 3. GÉNÉRATEUR CLIMATIQUE CORRIGÉ
def get_local_weather(reg, mois):
    random.seed(reg + str(mois))
    cfg = geo_conf[reg]
    base_t = 16 if cfg["type"] == "nord" else (22 if cfg["type"] == "centre" else 25)
    t = base_t + (10 * ((mois - 7) / 6)) + random.uniform(-2, 2)
    base_pl = {"nord": 50, "centre": 25, "sud": 8}
    saison_pl = 0.2 if 6 <= mois <= 8 else 1.2
    pl = max(0, (base_pl[cfg["type"]] * saison_pl) + random.uniform(-5, 10))
    h = random.uniform(40.0, 70.0)
    v = random.uniform(5.0, 15.0)
    return round(t, 1), round(pl, 1), round(h, 1), round(v, 1)

# 4. INTERFACE
st.markdown("<h1 style='font-size:38px;'>🌾 Système Intelligent d’Assurance Agricole</h1>", unsafe_allow_html=True)

if model is None:
    st.error("⚠️ Fichier 'modele_risque.joblib' introuvable à la racine. Veuillez l'ajouter à votre dépôt GitHub.")
else:
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
        st.markdown("<h2>📊 Données Climatiques (Normales Régionales)</h2>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Température", f"{t} °C")
        m2.metric("Précipitations", f"{pl} mm")
        m3.metric("Vent", f"{vent} km/h")
        m4.metric("Humidité", f"{hum} %")

        if btn:
            input_data = pd.DataFrame([[t, pl, hum, vent, sup, prod]], 
                                      columns=['Temp', 'Pluie', 'Humidite', 'Vent', 'Superficie', 'Rendement'])
            
            risque_final = model.predict(input_data)[0]
            prod_totale = sup * prod
            cap_max = (sup * 200) + (prod_totale * 25)
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
