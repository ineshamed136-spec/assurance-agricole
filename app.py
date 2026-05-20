import streamlit as st
import joblib
import pandas as pd
import requests

# ======================
# MODELE ML
# ======================
model_rf = joblib.load("model_rf.pkl")

# ======================
# TELEGRAM
# ======================
BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

# ======================
# FONCTION TELEGRAM
# ======================
def envoyer_alerte(user_id, region, risque, saison):

    message = f"""
🌾 ALERTE AGRICOLE

👤 Utilisateur : {user_id}
📍 Région : {region}
📅 Saison : {saison}

🌪 Risque détecté : {risque:.2f} %
"""

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message
        }
    )

# ======================
# COORDONNEES REGIONS
# ======================
coords = {
    "Tunis": (36.8065, 10.1815),
    "Nabeul": (36.45, 10.73),
    "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18),
    "Sousse": (35.82, 10.60),
    "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09),
    "Kebili": (33.70, 8.97),
    "Gabes": (33.88, 10.09),
    "Medenine": (33.35, 10.50)
}

# ======================
# ZONES DESERTIQUES
# ======================
zones_desertiques = [
    "Kebili",
    "Gabes",
    "Medenine"
]

# ======================
# NASA POWER
# ======================
def get_weather(region, mois, annee, coords):

    # NASA disponible jusqu'à 2025
    if annee > 2025:
        annee = 2025

    lat, lon = coords[region]

    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"

    params = {
        "parameters": "T2M,PRECTOTCORR,RH2M,WS2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": str(annee),
        "end": str(annee),
        "format": "JSON"
    }

    try:

        r = requests.get(
            url,
            params=params,
            timeout=30
        )

        if r.status_code != 200:
            st.error(f"NASA ERROR HTTP : {r.status_code}")
            return None

        data = r.json()

        if "properties" not in data:
            st.error("NASA DATA FORMAT ERROR")
            return None

        p = data["properties"]["parameter"]

        # ======================
        # EXTRACTION PAR MOIS
        # ======================
        def extract(param):

            if not param:
                return None

            # format YYYYMM
            key1 = f"{annee}{mois:02d}"

            if key1 in param:
                return param[key1]

            # format JAN-DEC
            months = [
                "JAN", "FEB", "MAR",
                "APR", "MAY", "JUN",
                "JUL", "AUG", "SEP",
                "OCT", "NOV", "DEC"
            ]

            key2 = months[mois - 1]

            if key2 in param:
                return param[key2]

            return None

        temp = extract(p.get("T2M"))
        pluie = extract(p.get("PRECTOTCORR"))
        humidite = extract(p.get("RH2M"))
        vent = extract(p.get("WS2M"))

        if None in [temp, pluie, humidite, vent]:
            return None

        return (
            float(temp),
            float(pluie),
            float(humidite),
            float(vent)
        )

    except Exception as e:

        st.error(f"NASA EXCEPTION : {e}")

        return None

# ======================
# INTERFACE
# ======================
st.title("🌾 Assurance Agricole Intelligente")

# ======================
# IDENTIFIANT
# ======================
user_id = st.text_input(
    "🆔 Identifiant utilisateur"
)

if not user_id:
    st.stop()

# ======================
# REGION
# ======================
region = st.selectbox(
    "📍 Région",
    list(coords.keys())
)

# ======================
# MOIS
# ======================
mois = st.selectbox(
    "📅 Mois",
    list(range(1, 13))
)

# ======================
# ANNEE
# ======================
annee = 2025

# ======================
# CULTURE
# ======================
culture = st.selectbox(
    "🌱 Culture",
    [
        "Olives",
        "Céréales"
    ]
)

# ======================
# IRRIGATION
# ======================
irrigation = st.radio(
    "💧 Irrigation",
    [
        "Oui",
        "Non"
    ]
)

# ======================
# SUPERFICIE
# ======================
superficie = st.number_input(
    "📏 Superficie (ha)",
    min_value=1,
    max_value=1000,
    value=10
)

# ======================
# PRODUCTION
# ======================
production = st.number_input(
    "🌾 Production (tonnes)",
    min_value=1,
    max_value=10000,
    value=50
)

# ======================
# SAISON
# ======================
if mois in [12, 1, 2]:
    saison = "Hiver"

elif mois in [3, 4, 5]:
    saison = "Printemps"

elif mois in [6, 7, 8]:
    saison = "Été"

else:
    saison = "Automne"

st.write(f"📅 Saison : {saison}")

# ======================
# METEO NASA
# ======================
weather = get_weather(
    region,
    mois,
    annee,
    coords
)

if weather is None:

    st.error(
        "❌ Données NASA indisponibles"
    )

    st.stop()

temp, pluie, humidite, vent = weather

# ======================
# AFFICHAGE METEO
# ======================
st.subheader(
    "🌦 Données climatiques (NASA POWER)"
)

st.write(f"🌡 Température : {temp:.2f} °C")
st.write(f"🌧 Pluie : {pluie:.2f} mm")
st.write(f"💧 Humidité : {humidite:.2f} %")
st.write(f"💨 Vent : {vent:.2f} m/s")

# ======================
# CALCUL RISQUE
# ======================
if st.button("📊 Calculer le risque"):

    # ======================
    # DATAFRAME INPUT ML
    # ======================
    X = pd.DataFrame(
        0,
        index=[0],
        columns=model_rf.feature_names_in_
    )

    X["temp"] = temp
    X["précipitations"] = pluie
    X["humidité"] = humidite
    X["vent"] = vent
    X["mois"] = mois
    X["annee"] = annee

    # REGION
    region_col = f"region_{region}"

    if region_col in X.columns:
        X[region_col] = 1

    # SAISON
    saison_col = f"saison_{saison}"

    if saison_col in X.columns:
        X[saison_col] = 1

    # ======================
    # PREDICTION ML
    # ======================
    risque_ml = (
        model_rf.predict_proba(X)[0][1] * 100
    )

    # ======================
    # REGLES METIER
    # ======================
    risque_regle = 0

    # sécheresse
    if pluie < 10:
        risque_regle += 30

    # chaleur
    if temp > 40:
        risque_regle += 25

    # irrigation
    if irrigation == "Non":
        risque_regle += 15

    # céréales sensibles
    if culture == "Céréales" and pluie < 25:
        risque_regle += 20

    # été
    if saison == "Été":
        risque_regle += 15

    # désert
    if region in zones_desertiques and temp > 42:
        risque_regle += 20

    # ======================
    # RISQUE FINAL
    # ======================
    risque = (
        0.7 * risque_ml
        + 0.3 * risque_regle
    )

    risque = max(
        0,
        min(100, risque)
    )

    # ======================
    # PRIME
    # ======================
    prime = (
        risque * 4
        + superficie * 12
        + production * 1.2
    )

    if irrigation == "Non":
        prime += 80

    if culture == "Céréales":
        prime += 60

    else:
        prime += 40

    # ======================
    # RESULTATS
    # ======================
    st.subheader("📊 Résultats")

    st.progress(int(risque))

    st.write(f"🌪 Risque : {risque:.2f} %")

    st.write(f"💰 Prime : {prime:.2f} DT")

    # ======================
    # ASSURANCE PARAMETRIQUE
    # ======================
    st.subheader(
        "🛡 Assurance Paramétrique"
    )

    evenement = None
    indemnite = 0

    # ======================
    # SECHERESSE
    # ======================
    if pluie < 10:

        evenement = "Sécheresse"

        indemnite = (
            superficie * 120
            + production * 15
        )

    # ======================
    # CANICULE
    # ======================
    elif temp > 42:

        evenement = "Canicule"

        indemnite = (
            superficie * 100
            + production * 12
        )

    # ======================
    # VENT VIOLENT
    # ======================
    elif vent > 20:

        evenement = "Vent violent"

        indemnite = (
            superficie * 80
            + production * 10
        )

    # ======================
    # HUMIDITE ELEVEE
    # ======================
    elif humidite > 85:

        evenement = "Humidité excessive"

        indemnite = (
            superficie * 70
            + production * 8
        )

    # ======================
    # RESULTATS PARAMETRIQUES
    # ======================
    if evenement is not None:

        st.error(
            f"⚠️ Événement détecté : {evenement}"
        )

        st.success(
            f"💰 Indemnisation automatique : {indemnite:.2f} DT"
        )

        st.info(
            "📌 Déclenchement automatique basé sur les seuils climatiques"
        )

    else:

        st.success(
            "✅ Aucun seuil paramétrique déclenché"
        )

    # ======================
    # ALERTES
    # ======================
    if risque < 30:

        st.success(
            "🌿 Risque faible"
        )

    elif risque < 70:

        st.warning(
            "⚠️ ALERTE MODÉRÉE"
        )

        envoyer_alerte(
            user_id,
            region,
            risque,
            saison
        )

        st.info(
            "📩 Notification envoyée"
        )

    else:

        st.error(
            "🔥 RISQUE ÉLEVÉ"
        )
