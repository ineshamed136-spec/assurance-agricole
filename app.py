import streamlit as st
import joblib
import requests

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# 1. CHARGEMENT MODÈLE
@st.cache_resource
def load_model():
    try: return joblib.load("model.pkl"), True
    except: return None, False

model_rf, model_charge = load_model()

# 2. CONFIGURATION RÉGIONALE
geo_conf = {
    "Tunis": {"lat": 36.8065, "lon": 10.1815, "seuil": 30.0},
    "Nabeul": {"lat": 36.4510, "lon": 10.7360, "seuil": 32.0}
}

# 3. RÉCUPÉRATION DONNÉES
@st.cache_data(ttl=3600)
def get_weather(reg):
    try:
        c = geo_conf[reg]
        url = f"https://power.larc.nasa.gov/api/v2/temporal/climatology/point?latitude={c['lat']}&longitude={c['lon']}&community=ag&parameters=T2M,PRECTOTCORR&format=JSON"
        res = requests.get(url, timeout=5).json()
        p = res['properties']['parameter']
        return {"temp": p['T2M']['ANN'], "pluie": p['PRECTOTCORR']['ANN']}
    except: return {"temp": 20.0, "pluie": 30.0}

# 4. INTERFACE
st.title("🌾 Système d'Assurance Agricole")

region = st.selectbox("Région", list(geo_conf.keys()))
w = get_weather(region)

# Utilisation des colonnes natives de Streamlit
col1, col2 = st.columns(2)
col1.metric("Température annuelle", f"{w['temp']:.1f} °C")
col2.metric("Précipitations", f"{w['pluie']:.1f} mm")

st.info("Données provenant de NASA POWER.")
