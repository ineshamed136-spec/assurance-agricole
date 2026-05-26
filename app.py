import streamlit as st
import requests
import datetime
import random

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# 1. CONFIGURATION
geo_conf = {
    "Tunis": {"lat": 36.8, "lon": 10.1, "facteur": 0.9, "coeff": 4.0, "seuil": 30.0},
    "Nabeul": {"lat": 36.4, "lon": 10.7, "facteur": 0.85, "coeff": 4.5, "seuil": 32.0},
    "Bizerte": {"lat": 37.2, "lon": 9.8, "facteur": 0.8, "coeff": 3.5, "seuil": 35.0}
}

@st.cache_data(ttl=3600)
def get_nasa_data(lat, lon):
    # On récupère les données climatologiques
    url = f"https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=T2M,PRECTOTCORR,RH2M,WS10M&community=AG&longitude={lon}&latitude={lat}&format=JSON"
    try:
        res = requests.get(url, timeout=5).json()
        return res['properties']['parameter']
    except:
        return None

# 2. INTERFACE
st.title("🌾 Système Intelligent d’Assurance Agricole")
region = st.selectbox("Région", list(geo_conf.keys()))
mois = st.selectbox("Mois", list(range(1, 13)), index=datetime.datetime.now().month - 1)
btn = st.button("🚀 LANCER L'ANALYSE")

cfg = geo_conf[region]
data = get_nasa_data(cfg['lat'], cfg['lon'])

# LOGIQUE DYNAMIQUE : NASA + Aléa pour simuler la variabilité météo
def get_varied_data(base_data, mois):
    m_str = str(mois)
    # On prend la base NASA, et on ajoute un facteur aléatoire (ex: +/- 10%)
    t = base_data['T2M'].get(m_str, 20.0) * random.uniform(0.95, 1.05)
    pl = base_data['PRECTOTCORR'].get(m_str, 30.0) * random.uniform(0.8, 1.2)
    hum = base_data['RH2M'].get(m_str, 50.0) * random.uniform(0.9, 1.1)
    vent = base_data['WS10M'].get(m_str, 5.0) * random.uniform(0.9, 1.1)
    return t, pl, hum, vent

t, pl, hum, vent = get_varied_data(data, mois) if data else (20.0, 30.0, 50.0, 5.0)

# AFFICHAGE
cols = st.columns(4)
cols[0].metric("Température", f"{t:.1f} °C")
cols[1].metric("Pluie", f"{pl:.1f} mm")
cols[2].metric("Humidité", f"{hum:.1f} %")
cols[3].metric("Vent", f"{vent:.1f} m/s")

if btn:
    st.success(f"Analyse effectuée pour {region} avec les données climatiques du mois {mois}.")
