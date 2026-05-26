import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="Assurance Agricole Paramétrique",
    layout="wide"
)

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

.block-container {
    padding-top: 2rem;
}

</style>
""", unsafe_allow_html=True)

# =========================
# RÉGIONS
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
# CONFIGURATION CLIMATIQUE
# =========================
geo_conf = {

    "Tunis": {
        "facteur": 0.9,
        "seuil": 30.0,
        "historique": 45.5
    },

    "Nabeul": {
        "facteur": 0.85,
        "seuil": 32.0,
        "historique": 42.0
    },

    "Bizerte": {
        "facteur": 0.8,
        "seuil": 35.0,
        "historique": 55.2
    },

    "Beja": {
        "facteur": 0.75,
        "seuil": 40.0,
        "historique": 60.8
    },

    "Sousse": {
        "facteur": 0.95,
        "seuil": 28.0,
        "historique": 38.4
    },

    "Monastir": {
        "facteur": 0.95,
        "seuil": 28.0,
        "historique": 37.9
    },

    "Kairouan": {
        "facteur": 1.15,
        "seuil": 22.0,
        "historique": 25.1
    },

    "Gabes": {
        "facteur": 1.3,
        "seuil": 15.0,
        "historique": 18.2
    },

    "Kebili": {
        "facteur": 1.4,
        "seuil": 10.0,
        "historique": 12.5
    },

    "Médenine": {
        "facteur": 1.5,
        "seuil": 8.0,
        "historique": 10.5
    }
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

    response = requests.get(url, timeout=30)
    data = response.json()

    params = data["properties"]["parameter"]

    temperature = pd.Series(params["T2M"]).mean()
    pluie = pd.Series(params["PRECTOTCORR"]).sum()
    humidite = pd.Series(params["RH2M"]).mean()
    vent = pd.Series(params["WS2M"]).mean()

    return (
        round(temperature, 1),
        round(pluie, 1),
        round(humidite, 1),
        round(vent, 1)
    )

# =========================
# TITRE
# =========================
st.title("🌾 Assurance Agricole Paramétrique")

col1, col2 = st.columns([1, 2])

# =========================
# PARAMÈTRES
# =========================
with col1:

    st.subheader("⚙️ Paramètres")

    region = st.selectbox(
        "Région",
        list(regions.keys())
    )

    mois = st.selectbox(
        "Mois",
        list(range(1, 13)),
        index=4
    )

    culture = st.selectbox(
        "Culture",
        ["Céréales", "Olives"]
    )

    irrigation = st.radio(
        "Irrigation",
        ["Oui", "Non"],
        horizontal=True
    )

    superficie = st.number_input(
        "Superficie (Ha)",
        min_value=1.0,
        value=15.0
    )

    rendement = st.number_input(
        "Rendement (T/Ha)",
        min_value=0.1,
        value=4.0
    )

    btn = st.button(
        "🚀 Lancer analyse",
        type="primary"
    )

# =========================
# ANALYSE
# =========================
with col2:

    try:
        t, pl, hum, vent = get_nasa_weather(region, mois)

    except:
        st.error("Erreur lors de la récupération des données NASA POWER")
        st.stop()

    cfg = geo_conf[region]

    # =========================
    # VALEUR PAR HECTARE
    # =========================
    valeur_ha = 180 if culture == "Céréales" else 300

    # =========================
    # AFFICHAGE MÉTÉO
    # =========================
    st.subheader("📊 Données climatiques")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("🌡️ Température", f"{t} °C")
    c2.metric("🌧️ Pluie", f"{pl} mm")
    c3.metric("💨 Vent", f"{vent}")
    c4.metric("💧 Humidité", f"{hum}%")

    # =========================
    # CALCULS
    # =========================
    if btn:

        seuil = cfg["seuil"]
        historique = cfg["historique"]

        # =========================
        # DÉFICITS CLIMATIQUES
        # =========================
        deficit_seuil = max(
            0,
            (seuil - pl) / seuil
        )

        deficit_historique = max(
            0,
            (historique - pl) / historique
        )

        # =========================
        # STRESS CLIMATIQUE
        # =========================
        stress_climatique = (
            0.6 * deficit_seuil
            + 0.4 * deficit_historique
        )

        # =========================
        # RISQUE COHÉRENT
        # =========================
        risque = (
            (15 * cfg["facteur"])
            + (stress_climatique * 60)
            + (12 if irrigation == "Non" else 0)
        )

        risque = min(max(risque, 5), 95)

        risque_norm = risque / 100

        # =========================
        # CAPITAL
        # =========================
        production = superficie * rendement

        capital = (
            (superficie * valeur_ha)
            + (production * 25)
        )

        # =========================
        # PRIME
        # =========================
        prime = capital * (
            0.02 + (0.015 * risque_norm)
        )

        # =========================
        # INDEMNITÉ
        # =========================
        indemn = (
            capital
            * stress_climatique
            * (0.4 + 0.6 * risque_norm)
        )

        # =========================
        # AFFICHAGE RÉSULTATS
        # =========================
        st.divider()

        r1, r2 = st.columns(2)

        r1.metric(
            "🔥 Risque",
            f"{risque:.1f}%"
        )

        r2.metric(
            "💳 Prime",
            f"{prime:.2f} DT"
        )

        st.metric(
            "💰 Capital assuré",
            f"{capital:.2f} DT"
        )

        st.divider()

        # =========================
        # DÉCISION SINISTRE
        # =========================
        if stress_climatique > 0:

            st.error(
                f"💰 Indemnité : {indemn:.2f} DT"
            )

        else:

            st.success(
                "✅ Aucun sinistre déclenché"
            )

        # =========================
        # INTERPRÉTATION
        # =========================
        st.subheader("📌 Interprétation")

        st.write(f"""
- Pluie observée : {pl:.1f} mm
- Seuil régional : {seuil} mm
- Historique régional : {historique} mm
- Valeur par hectare : {valeur_ha} DT
- Capital assuré : {capital:.2f} DT

👉 Le risque augmente lorsque les précipitations deviennent
inférieures aux normales climatiques régionales.

👉 L’indemnité est déclenchée uniquement en présence
d’un déficit climatique réel.
""")

        # =========================
        # FORMULES
        # =========================
        with st.expander("ℹ️ Formules du modèle"):

            st.markdown("""
### 💰 Capital assuré
Capital = (Superficie × Valeur/ha)
+ (Production × 25)

### 💳 Prime d’assurance
Prime = Capital × (0.02 + 0.015 × Risque)

### 🌧️ Stress climatique
Stress climatique =
0.6 × déficit seuil
+ 0.4 × déficit historique

### 💰 Indemnité
Indemnité =
Capital × Stress climatique
× (0.4 + 0.6 × Risque)
""")
