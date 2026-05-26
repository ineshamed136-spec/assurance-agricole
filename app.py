import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# =========================
# STYLE
# =========================
st.markdown("""
<style>
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
    display: none !important;
}
[data-testid="stHeaderActionElements"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# CHARGEMENT MODÈLE
# =========================
@st.cache_resource
def load_model():
    try:
        return joblib.load("model.pkl"), True
    except:
        return None, False

model_rf, model_charge = load_model()

# =========================
# RÉGIONS (coordonnées)
# =========================
regions = {
    "Tunis": (36.8065, 10.1815),
    "Nabeul": (36.4561, 10.7376),
    "Bizerte": (37.2744, 9.8739),
    "Beja": (36.7256, 9.1817),
    "Sousse": (35.8256, 10.6411),
    "Monastir": (35.7643, 10.8113),
    "Kairouan": (35.6781, 10.0963),
    "Gabes": (33.8815, 10.0982),
    "Kebili": (33.7044, 8.9690),
    "Médenine": (33.3547, 10.5055)
}

# =========================
# CONFIGURATION RÉGIONALE
# =========================
geo_conf = {
    "Tunis": {"facteur": 0.9, "coeff": 4.0, "seuil": 30.0, "moyenne_20ans": 45.5},
    "Nabeul": {"facteur": 0.85, "coeff": 4.5, "seuil": 32.0, "moyenne_20ans": 42.0},
    "Bizerte": {"facteur": 0.8, "coeff": 3.5, "seuil": 35.0, "moyenne_20ans": 55.2},
    "Beja": {"facteur": 0.75, "coeff": 3.0, "seuil": 40.0, "moyenne_20ans": 60.8},
    "Sousse": {"facteur": 0.95, "coeff": 4.2, "seuil": 28.0, "moyenne_20ans": 38.4},
    "Monastir": {"facteur": 0.95, "coeff": 4.2, "seuil": 28.0, "moyenne_20ans": 37.9},
    "Kairouan": {"facteur": 1.15, "coeff": 5.5, "seuil": 22.0, "moyenne_20ans": 25.1},
    "Kebili": {"facteur": 1.4, "coeff": 7.0, "seuil": 10.0, "moyenne_20ans": 12.5},
    "Gabes": {"facteur": 1.3, "coeff": 6.5, "seuil": 15.0, "moyenne_20ans": 18.2},
    "Médenine": {"facteur": 1.5, "coeff": 7.5, "seuil": 8.0, "moyenne_20ans": 10.5}
}

# =========================
# NASA POWER API
# =========================
@st.cache_data(show_spinner=False)
def get_nasa_weather(region, mois):

    lat, lon = regions[region]
    year = 2024

    start = f"{year}{mois:02d}01"
    end = f"{year}{mois:02d}28"

    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters=T2M,PRECTOTCORR,RH2M,WS2M"
        f"&community=AG"
        f"&longitude={lon}"
        f"&latitude={lat}"
        f"&start={start}"
        f"&end={end}"
        f"&format=JSON"
    )

    data = requests.get(url, timeout=30).json()
    params = data["properties"]["parameter"]

    temp = pd.Series(params["T2M"]).mean()
    pluie = pd.Series(params["PRECTOTCORR"]).sum()
    humidite = pd.Series(params["RH2M"]).mean()
    vent = pd.Series(params["WS2M"]).mean()

    return temp, pluie, humidite, vent

# =========================
# INTERFACE
# =========================
st.markdown("<h1>🌾 Système Intelligent d’Assurance Agricole</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

# =========================
# INPUTS
# =========================
with col1:

    st.markdown("### ⚙️ Paramètres")

    region = st.selectbox("Région", list(regions.keys()))
    mois = st.selectbox("Mois", list(range(1, 13)), index=4)
    culture = st.selectbox("Culture", ["Céréales", "Olives"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)

    sup = st.number_input("Superficie (Ha)", value=15.0, min_value=1.0)
    prod = st.number_input("Rendement (T/Ha)", value=4.0, min_value=0.1)

    btn = st.button("🚀 Analyser", type="primary")

# =========================
# OUTPUT
# =========================
with col2:

    try:
        t, pl, hum, vent = get_nasa_weather(region, mois)
    except:
        st.error("Erreur NASA POWER")
        st.stop()

    cfg = geo_conf[region]

    st.markdown("### 📊 Données NASA POWER")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Température", f"{t:.1f} °C")
    c2.metric("Pluie", f"{pl:.1f} mm")
    c3.metric("Vent", f"{vent:.1f} m/s")
    c4.metric("Humidité", f"{hum:.1f} %")

    # =========================
    # ANALYSE
    # =========================
    if btn:

        # 🔥 RISQUE
        risque_final = min(
            max(
                (25.0 * cfg["facteur"])
                + (mois * 0.5)
                + (15 if irrigation == "Non" else 0),
                5.0
            ),
            95.0
        )

        risque_norm = risque_final / 100

        prod_totale = sup * prod
        cap_max = (sup * 200) + (prod_totale * 25)

        # 💳 PRIME (corrélée au risque)
        beta = 20

        prime = (
            beta * risque_final
            + sup * 12
            + prod_totale * 1.1
        )

        st.divider()

        colA, colB = st.columns(2)
        colA.metric("🔥 Risque", f"{risque_final:.1f} %")
        colB.metric("💳 Prime", f"{prime:.2f} DT")

        st.divider()

        # =========================
        # INDEMNITÉ (corrélée risque)
        # =========================
        if pl < cfg["seuil"]:

            deficit = (cfg["seuil"] - pl) / cfg["seuil"]

            alpha = 0.8

            indemn = cap_max * deficit * (1 + alpha * risque_norm)

            st.error(f"💰 Indemnité : {indemn:.2f} DT")

        elif cfg["seuil"] <= pl < (cfg["seuil"] + 10):

            st.warning(f"⚠️ Stress hydrique")

        else:
            st.success("✅ Conditions normales")

        # =========================
        # INTERPRÉTATION
        # =========================
        st.markdown("### 📌 Interprétation")

        if pl < cfg["seuil"]:
            st.write("Sécheresse détectée → risque élevé.")
        else:
            st.write("Conditions normales ou acceptables.")

        # =========================
        # NASA POWER SOURCE
        # =========================
        st.markdown("### 🌍 Source des données")

        st.write("NASA POWER API : https://power.larc.nasa.gov/docs/services/api/")
