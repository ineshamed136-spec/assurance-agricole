import streamlit as st
import requests
import joblib

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# CSS pour clean l'UI
st.markdown("<style>h1 a, h2 a {display: none !important;} [data-testid='stHeaderActionElements'] {display: none !important;}</style>", unsafe_allow_html=True)

# 1. CONFIGURATION
geo_conf = {
    "Tunis": {"lat": 36.8, "lon": 10.1, "facteur": 0.9, "coeff": 4.0, "seuil": 30.0},
    "Nabeul": {"lat": 36.4, "lon": 10.7, "facteur": 0.85, "coeff": 4.5, "seuil": 32.0},
    "Bizerte": {"lat": 37.2, "lon": 9.8, "facteur": 0.8, "coeff": 3.5, "seuil": 35.0},
    "Kairouan": {"lat": 35.6, "lon": 10.1, "facteur": 1.15, "coeff": 5.5, "seuil": 22.0}
}

@st.cache_data(ttl=3600)
def get_nasa_data(lat, lon):
    url = f"https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=T2M,PRECTOTCORR,RH2M,WS10M&community=AG&longitude={lon}&latitude={lat}&format=JSON"
    try:
        res = requests.get(url, timeout=5).json()
        return res['properties']['parameter']
    except:
        return None

# 2. INTERFACE
st.title("🌾 Système Intelligent d’Assurance Agricole")
col1, col2 = st.columns([1, 2])

with col1:
    region = st.selectbox("Région", list(geo_conf.keys()))
    mois = st.selectbox("Mois", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", value=15.0)
    prod = st.number_input("Rendement (T/Ha)", value=4.0)
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    btn = st.button("🚀 LANCER L'ANALYSE")

with col2:
    cfg = geo_conf[region]
    data = get_nasa_data(cfg['lat'], cfg['lon'])
    
    # Sécurité: Valeurs par défaut si API échoue ou clé manquante
    t, pl, hum, vent = 20.0, 30.0, 50.0, 5.0
    if data:
        try:
            m_str = str(mois)
            t = data['T2M'].get(m_str, t)
            pl = data['PRECTOTCORR'].get(m_str, pl)
            hum = data['RH2M'].get(m_str, hum)
            vent = data['WS10M'].get(m_str, vent)
        except: pass

    st.subheader("📊 Données Climatiques (NASA)")
    cols = st.columns(4)
    cols[0].metric("Température", f"{t:.1f} °C")
    cols[1].metric("Pluie", f"{pl:.1f} mm")
    cols[2].metric("Vent", f"{vent:.1f} m/s")
    cols[3].metric("Humidité", f"{hum:.1f} %")

    if btn:
        risque = min(max((25.0 * cfg["facteur"]) + (mois * 0.5) + (15 if irrigation == "Non" else 0), 5.0), 95.0)
        cap_max = (sup * 200) + ((sup * prod) * 25)
        prime = (risque * cfg["coeff"]) + (sup * 12) + ((sup * prod) * 1.1)
        
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("🔥 Risque Global", f"{risque:.1f} %")
        c2.metric("💳 Prime estimée", f"{prime:.2f} DT")
        
        if pl < cfg["seuil"]:
            st.error(f"💰 Indemnité estimée : {(((cfg['seuil'] - pl) / cfg['seuil']) * cap_max):.2f} DT")
        else:
            st.success("✅ Conditions climatiques favorables.")
