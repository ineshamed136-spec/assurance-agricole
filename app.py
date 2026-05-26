import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Assurance Agricole Paramétrique", layout="wide")

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
# CONFIGURATION
# =========================
geo_conf = {
    "Tunis": {"facteur": 0.9, "seuil": 30.0, "historique": 45.5},
    "Nabeul": {"facteur": 0.85, "seuil": 32.0, "historique": 42.0},
    "Bizerte": {"facteur": 0.8, "seuil": 35.0, "historique": 55.2},
    "Beja": {"facteur": 0.75, "seuil": 40.0, "historique": 60.8},
    "Sousse": {"facteur": 0.95, "seuil": 28.0, "historique": 38.4},
    "Monastir": {"facteur": 0.95, "seuil": 28.0, "historique": 37.9},
    "Kairouan": {"facteur": 1.15, "seuil": 22.0, "historique": 25.1},
    "Kebili": {"facteur": 1.4, "seuil": 10.0, "historique": 12.5},
    "Gabes": {"facteur": 1.3, "seuil": 15.0, "historique": 18.2},
    "Médenine": {"facteur": 1.5, "seuil": 8.0, "historique": 10.5}
}

# =========================
# NASA POWER
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

    data = requests.get(url).json()
    params = data["properties"]["parameter"]

    return (
        pd.Series(params["T2M"]).mean(),
        pd.Series(params["PRECTOTCORR"]).sum(),
        pd.Series(params["RH2M"]).mean(),
        pd.Series(params["WS2M"]).mean()
    )

# =========================
# INTERFACE
# =========================
st.title("🌾 Assurance Agricole Paramétrique")

col1, col2 = st.columns([1, 2])

with col1:
    region = st.selectbox("Région", list(regions.keys()))
    mois = st.selectbox("Mois", list(range(1, 13)), index=4)

    culture = st.selectbox("Culture", ["Céréales", "Olives"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"])

    superficie = st.number_input("Superficie (Ha)", value=15.0)
    rendement = st.number_input("Rendement (T/Ha)", value=4.0)

    btn = st.button("🚀 Lancer analyse")

with col2:

    t, pl, hum, vent = get_nasa_weather(region, mois)
    cfg = geo_conf[region]

    valeur_ha = 180 if culture == "Céréales" else 300

    st.subheader("📊 Données climatiques")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temp", f"{t:.1f} °C")
    c2.metric("Pluie", f"{pl:.1f} mm")
    c3.metric("Vent", f"{vent:.1f}")
    c4.metric("Humidité", f"{hum:.1f}%")

    if btn:

        # =========================
        # RISQUE
        # =========================
        risque = min(
            max((25 * cfg["facteur"]) + (15 if irrigation == "Non" else 0), 5),
            95
        )

        risque_norm = risque / 100

        # =========================
        # CAPITAL
        # =========================
        production = superficie * rendement
        capital = (superficie * valeur_ha) + (production * 25)

        # =========================
        # PRIME
        # =========================
        prime = capital * (0.02 + 0.015 * risque_norm)

        # =========================
        # INDICE CLIMATIQUE
        # =========================
        seuil = cfg["seuil"]
        historique = cfg["historique"]

        deficit_seuil = max(0, (seuil - pl) / seuil)
        deficit_historique = max(0, (historique - pl) / historique)

        indice_climatique = 0.6 * deficit_seuil + 0.4 * deficit_historique

        # =========================
        # INDEMNITÉ
        # =========================
        indemn = capital * indice_climatique * (0.3 + 0.7 * risque_norm)

        # =========================
        # AFFICHAGE
        # =========================
        st.divider()

        c1, c2 = st.columns(2)
        c1.metric("Prime", f"{prime:.2f} DT")
        c2.metric("Capital", f"{capital:.2f} DT")

        st.divider()

        if indice_climatique > 0:
            st.error(f"💰 Indemnité : {indemn:.2f} DT")
        else:
            st.success("✅ Aucun sinistre")

        # =========================
        # INTERPRÉTATION (CORRIGÉE SELON TA DEMANDE)
        # =========================
        st.subheader("📌 Interprétation")

        st.write(f"""
- Pluie : {pl:.1f} mm
- Seuil : {seuil} mm
- Historique : {historique} mm
- Valeur/ha : {valeur_ha} DT
- Capital assuré : {capital:.2f} DT

👉 L’indemnité dépend uniquement du déficit climatique (seuil + historique)
et de la sensibilité du contrat (facteur de risque).
""")

        # =========================
        # FORMULES
        # =========================
        with st.expander("ℹ️ Formules"):

            st.markdown("""
### Capital
Capital = (Superficie × Valeur/ha) + (Superficie × Rendement × 25)

### Prime
Prime = Capital × (0.02 + 0.015 × Risque)

### Indemnité
Indice climatique = 0.6 × déficit seuil + 0.4 × déficit historique  
Indemnité = Capital × Indice climatique × (0.3 + 0.7 × Risque)
""")
