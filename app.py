import streamlit as st
import requests
import joblib
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Assurance Agricole", layout="wide")

# CSS pour masquer les éléments superflus
st.markdown("""
<style>
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; }
[data-testid="stHeaderActionElements"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# 1. CONFIGURATION RÉGIONALE COMPLÈTE
# Inclut toutes vos régions avec les coordonnées nécessaires à l'API NASA
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

# 2. RÉCUPÉRATION DONNÉES NASA POWER (Climatologie)
@st.cache_data(ttl=86400)
def get_nasa_data(lat, lon, mois):
    url = f"https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=T2M,PRECTOTCORR,RH2M,WS10M&community=AG&longitude={lon}&latitude={lat}&format=JSON"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()['properties']['parameter']
        m = str(mois)
        return data['T2M'][m], data['PRECTOTCORR'][m], data['RH2M'][m], data['WS10M'][m]
    except:
        return 20.0, 30.0, 50.0, 5.0

# 3. INTERFACE UTILISATEUR
st.markdown("<h1 style='font-size:38px;'>🌾 Système Intelligent d’Assurance Agricole</h1>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("<h3>⚙️ Paramètres</h3>", unsafe_allow_html=True)
    region = st.selectbox("Région", list(geo_conf.keys()))
    mois = st.selectbox("Mois", range(1, 13), index=datetime.now().month - 1)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement attendu (T/Ha)", value=4.0)
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    btn = st.button("🚀 LANCER L'ANALYSE", type="primary")

with col2:
    cfg = geo_conf[region]
    t, pl, hum, vent = get_nasa_data(cfg['lat'], cfg['lon'], mois)
    
    st.markdown("<h2>📊 Données NASA POWER</h2>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Température", f"{t:.1f} °C")
    m2.metric("Pluie", f"{pl:.1f} mm")
    m3.metric("Vent", f"{vent:.1f} m/s")
    m4.metric("Humidité", f"{hum:.1f} %")

    if btn:
        val_irrigation = 15 if irrigation == "Non" else 0
        risque_final = min(max((25.0 * cfg["facteur"]) + (mois * 0.5) + val_irrigation, 5.0), 95.0)
        prod_totale = sup * prod
        prime = (risque_final * cfg["coeff"]) + (sup * 12) + (prod_totale * 1.1)
        cap_max = (sup * 200) + (prod_totale * 25)

        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("🔥 Risque Global", f"{risque_final:.1f} %")
        c2.metric("💳 Prime à payer", f"{prime:.2f} DT")
        
        if pl < cfg["seuil"]:
            st.error(f"💰 Indemnité : {(((cfg['seuil'] - pl) / cfg['seuil']) * cap_max):.2f} DT")
        else:
            st.success("✅ Conditions favorables.")

        with st.expander("ℹ️ Méthodologie"):
            st.write("Calcul basé sur les normales climatologiques NASA (Community AG).")
            st.latex(r"Prime = (Risque \times Coeff) + (Sup \times 12) + (Prod \times 1.1)")
