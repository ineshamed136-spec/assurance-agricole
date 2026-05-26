import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# CSS
st.markdown("<style>h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; } [data-testid='stHeaderActionElements'] { display: none !important; }</style>", unsafe_allow_html=True)

# 1. CONFIGURATION RÉGIONALE
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

# 2. RÉCUPÉRATION NASA (Cache indexé par la région et le mois)
@st.cache_data(show_spinner=False)
def get_nasa_data(lat, lon, mois):
    url = f"https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=T2M,PRECTOTCORR,RH2M,WS10M&community=AG&longitude={lon}&latitude={lat}&format=JSON"
    response = requests.get(url, timeout=15)
    data = response.json()['properties']['parameter']
    m = str(mois)
    return data['T2M'][m], data['PRECTOTCORR'][m], data['RH2M'][m], data['WS10M'][m]

# 3. INTERFACE
st.title("🌾 Système Intelligent d’Assurance Agricole")
col1, col2 = st.columns([1, 2])

with col1:
    region = st.selectbox("Région", list(geo_conf.keys()))
    mois = st.selectbox("Mois", list(range(1, 13)), index=datetime.now().month - 1)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement (T/Ha)", value=4.0)
    btn = st.button("🚀 LANCER L'ANALYSE", type="primary")

with col2:
    cfg = geo_conf[region]
    # APPEL DIRECT
    t, pl, hum, vent = get_nasa_data(cfg['lat'], cfg['lon'], mois)
    
    st.subheader(f"Données NASA pour {region} (Mois {mois})")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temp", f"{t:.1f}°C")
    m2.metric("Pluie", f"{pl:.1f}mm")
    m3.metric("Vent", f"{vent:.1f}m/s")
    m4.metric("Hum", f"{hum:.1f}%")

    if btn:
        st.success("Données NASA récupérées avec succès.")
        # ... votre logique de calcul ...
