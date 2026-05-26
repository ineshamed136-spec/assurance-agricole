import streamlit as st
import joblib
import requests

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# BLOC CSS NETTOYÉ
# Note : Nous utilisons une chaîne de caractères simple sans caractères invisibles
css = """
<style>
h1, h2, h3 { color: #2E7D32; }
</style>
"""
st.markdown(css, unsafe_html=True)

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
    # Ajoutez vos autres régions ici...
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

st.metric("Température annuelle", f"{w['temp']:.1f} °C")
st.metric("Précipitations", f"{w['pluie']:.1f} mm")
