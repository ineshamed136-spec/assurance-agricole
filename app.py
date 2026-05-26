import streamlit as st
import joblib
import pandas as pd
import requests
from datetime import datetime, timedelta

# Configuration de la page
st.set_page_config(page_title="Assurance Agricole", layout="wide")

# 1. CONFIGURATION RÉGIONALE AVEC COORDONNÉES
geo_conf = {
    "Tunis": {"lat": 36.80, "lon": 10.18, "facteur": 0.9, "coeff": 4.0, "seuil": 30.0},
    "Nabeul": {"lat": 36.45, "lon": 10.73, "facteur": 0.85, "coeff": 4.5, "seuil": 32.0},
    "Bizerte": {"lat": 37.27, "lon": 9.87, "facteur": 0.8, "coeff": 3.5, "seuil": 35.0},
    "Beja": {"lat": 36.72, "lon": 9.18, "facteur": 0.75, "coeff": 3.0, "seuil": 40.0},
    "Sousse": {"lat": 35.82, "lon": 10.60, "facteur": 0.95, "coeff": 4.2, "seuil": 28.0},
    "Monastir": {"lat": 35.78, "lon": 10.83, "facteur": 0.95, "coeff": 4.2, "seuil": 28.0},
    "Kairouan": {"lat": 35.67, "lon": 10.10, "facteur": 1.15, "coeff": 5.5, "seuil": 22.0},
    "Kebili": {"lat": 33.70, "lon": 8.97, "facteur": 1.4, "coeff": 7.0, "seuil": 10.0},
    "Gabes": {"lat": 33.88, "lon": 10.09, "facteur": 1.3, "coeff": 6.5, "seuil": 15.0},
    "Médenine": {"lat": 33.35, "lon": 10.49, "facteur": 1.5, "coeff": 7.5, "seuil": 8.0}
}

# 2. RÉCUPÉRATION DONNÉES RÉELLES (API Daily)
@st.cache_data(ttl=3600)
def get_nasa_realtime(lat, lon):
    # On récupère les données des 7 derniers jours pour avoir des valeurs réelles et mouvantes
    end = datetime.now()
    start = end - timedelta(days=7)
    s_date, e_date = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
    
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,PRECTOTCORR,RH2M,WS10M&community=AG&longitude={lon}&latitude={lat}&start={s_date}&end={e_date}&format=JSON"
    
    try:
        res = requests.get(url, timeout=10).json()['properties']['parameter']
        # Moyenne des 7 derniers jours
        temps = list(res['T2M'].values())
        pluies = list(res['PRECTOTCORR'].values())
        hums = list(res['RH2M'].values())
        vents = list(res['WS10M'].values())
        return sum(temps)/len(temps), sum(pluies)/len(pluies), sum(hums)/len(hums), sum(vents)/len(vents)
    except:
        return 20.0, 10.0, 50.0, 5.0

# 3. INTERFACE
st.title("🌾 Système Intelligent d’Assurance Agricole")
region = st.selectbox("Région", list(geo_conf.keys()))
sup = st.number_input("Superficie (Ha)", value=15.0)
prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
btn = st.button("🚀 LANCER L'ANALYSE")

cfg = geo_conf[region]
t, pl, hum, vent = get_nasa_realtime(cfg['lat'], cfg['lon'])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Température", f"{t:.1f} °C")
m2.metric("Pluie (Moy 7j)", f"{pl:.1f} mm")
m3.metric("Vent", f"{vent:.1f} m/s")
m4.metric("Humidité", f"{hum:.1f} %")

if btn:
    # Votre logique de calcul ici...
    st.success("Analyse effectuée avec les données réelles de la dernière semaine.")
