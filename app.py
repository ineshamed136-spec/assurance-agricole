import streamlit as st
import joblib
import pandas as pd
import random
import requests  # Utilisation de la bibliothèque native

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# SUPPRESSION DES ICÔNES/LIENS DES TITRES
st.markdown("""
<style>
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; }
[data-testid="stHeaderActionElements"] { display: none !important; }
</style>
""", unsafe_html=True)

# 1. CHARGEMENT MODÈLE
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# 2. CONFIGURATION RÉGIONALE
geo_conf = {
    "Tunis": {"lat": 36.8065, "lon": 10.1815, "facteur": 0.9, "coeff": 4.0, "seuil": 30.0, "moyenne_20ans": 45.5},
    "Nabeul": {"lat": 36.4510, "lon": 10.7360, "facteur": 0.85, "coeff": 4.5, "seuil": 32.0, "moyenne_20ans": 42.0},
    "Bizerte": {"lat": 37.2744, "lon": 9.8739, "facteur": 0.8, "coeff": 3.5, "seuil": 35.0, "moyenne_20ans": 55.2},
    "Beja": {"lat": 36.7256, "lon": 9.1817, "facteur": 0.75, "coeff": 3.0, "seuil": 40.0, "moyenne_20ans": 60.8},
    "Sousse": {"lat": 35.8256, "lon": 10.6099, "facteur": 0.95, "coeff": 4.2, "seuil": 28.0, "moyenne_20ans": 38.4},
    "Monastir": {"lat": 35.7821, "lon": 10.8261, "facteur": 0.95, "coeff": 4.2, "seuil": 28.0, "moyenne_20ans": 37.9},
    "Kairouan": {"lat": 35.6784, "lon": 10.0963, "facteur": 1.15, "coeff": 5.5, "seuil": 22.0, "moyenne_20ans": 25.1},
    "Kebili": {"lat": 33.7042, "lon": 8.9723, "facteur": 1.4, "coeff": 7.0, "seuil": 10.0, "moyenne_20ans": 12.5},
    "Gabes": {"lat": 33.8815, "lon": 10.0982, "facteur": 1.3, "coeff": 6.5, "seuil": 15.0, "moyenne_20ans": 18.2},
    "Médenine": {"lat": 33.3517, "lon": 10.4859, "facteur": 1.5, "coeff": 7.5, "seuil": 8.0, "moyenne_20ans": 10.5}
}

# 3. RÉCUPÉRATION DONNÉES VIA API NASA (Requêtes directes)
@st.cache_data(ttl=86400)
def get_weather_data(reg):
    try:
        coords = geo_conf[reg]
        url = f"https://power.larc.nasa.gov/api/v2/temporal/climatology/point?latitude={coords['lat']}&longitude={coords['lon']}&community=ag&parameters=T2M,PRECTOTCORR,WS2M,RH2M&format=JSON"
        response = requests.get(url, timeout=10)
        data = response.json()
        params = data['properties']['parameter']
        return {
            "temp": params['T2M']['ANN'],
            "pluie": params['PRECTOTCORR']['ANN'],
            "vent": params['WS2M']['ANN'],
            "hum": params['RH2M']['ANN']
        }
    except:
        return None

def get_simulated_weather(reg, mois):
    random.seed(reg + str(mois))
    return (random.uniform(15, 25), random.uniform(5, 50), random.uniform(40, 80), random.uniform(2, 10))

# 4. INTERFACE
st.markdown("<h1 style='font-size:38px;'>🌾 Système Intelligent d’Assurance Agricole</h1>", unsafe_html=True)
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
    w_data = get_weather_data(region)
    if w_data:
        t, pl, vent, hum = w_data["temp"], w_data["pluie"], w_data["vent"], w_data["hum"]
        source_text = "NASA POWER (Données réelles)"
    else:
        t, pl, hum, vent = get_simulated_weather(region, mois)
        source_text = "Simulation (Mode hors-ligne)"

    cfg = geo_conf[region]
    st.markdown("<h2>📊 Données Climatiques</h2>", unsafe_html=True)
    st.caption(f"Source : {source_text}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f} °C")
    m2.metric("Précipitations", f"{pl:.1f} mm")
    m3.metric("Vent", f"{vent:.1f} km/h")
    m4.metric("Humidité", f"{hum:.1f} %")

    if btn:
        risque_final = min(max((25.0 * cfg["facteur"]) + (mois * 0.5) + (15 if irrigation == "Non" else 0), 5.0), 95.0)
        prod_totale = sup * prod
        prime = (risque_final * cfg["coeff"]) + (sup * 12) + (prod_totale * 1.1)
        cap_max = (sup * 200) + (prod_totale * 25)

        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("🔥 Risque Global", f"{risque_final:.1f} %")
        c2.metric("💳 Prime à payer", f"{prime:.2f} DT")
        
        st.divider()
        if pl < cfg["seuil"]:
            st.error(f"💰 Indemnité de sinistre : {(((cfg['seuil'] - pl) / cfg['seuil']) * cap_max):.2f} DT")
        elif cfg["seuil"] <= pl < (cfg["seuil"] + 10):
            st.warning(f"⚠️ Stress hydrique : Indemnité de franchise : {(cap_max * 0.05):.2f} DT")
        else:
            st.success("✅ Conditions climatiques optimales.")
