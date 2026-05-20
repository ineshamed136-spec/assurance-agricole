import streamlit as st
import joblib
import pandas as pd
import requests

# ======================
# CONFIG PAGE
# ======================
st.set_page_config(
    page_title="Assurance Agricole Intelligente",
    page_icon="🌾",
    layout="centered"
)

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
# TELEGRAM ALERT
# ======================
def envoyer_alerte(user_id, region, risque, saison):

    message = f"""
🌾 ALERTE AGRICOLE

👤 Utilisateur : {user_id}
📍 Région : {region}
📅 Saison : {saison}

🌪 Risque détecté : {risque:.2f} %
"""

    try:

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=10
        )

    except:
        pass

# ======================
# COORDONNEES
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
# NASA POWER
# ======================
def get_weather(region, mois, annee):

    lat, lon = coords[region]

    if annee > 2025:
        annee = 2025

    url = (
        "https://power.larc.nasa.gov/api/"
        "temporal/monthly/point"
    )

    params = {

        "parameters":
        "T2M,PRECTOTCORR,RH2M,WS2M",

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
            return None

        data = r.json()

        if "properties" not in data:
            return None

        p = data["properties"]["parameter"]

        # ======================
        # EXTRACTION MOIS
        # ======================
        def extract_value(param):

            if not param:
                return None

            key1 = f"{annee}{mois:02d}"

            if key1 in param:
                return param[key1]

            months = [
                "JAN", "FEB", "MAR",
                "APR", "MAY", "JUN",
                "JUL", "AUG", "SEP",
                "OCT", "NOV", "DEC"
            ]

            key2 = months[mois - 1]

            if key2 in param:
                return param[key2]

            values = list(param.values())

            if len(values) > 0:
                return values[0]

            return None

        temp = extract_value(
            p.get("T2M")
        )

        pluie = extract_value(
            p.get("PRECTOTCORR")
        )

        humidite = extract_value(
            p.get("RH2M")
        )

        vent = extract_value(
            p.get("WS2M")
        )

        if None in [
            temp,
            pluie,
            humidite,
            vent
        ]:
            return None

        return (

            float(temp),

            float(pluie),

            float(humidite),

            float(vent)
        )

    except:
        return None

# ======================
# INTERFACE
# ======================
st.title(
    "🌾 Assurance Agricole Intelligente"
)

# ======================
# USER
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
# NASA POWER
# ======================
weather = get_weather(
    region,
    mois,
    annee
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
    "🌦 Données climatiques NASA POWER"
)

st.write(
    f"🌡 Température : {temp:.2f} °C"
)

st.write(
    f"🌧 Pluie : {pluie:.2f} mm"
)

st.write(
    f"💧 Humidité : {humidite:.2f} %"
)

st.write(
    f"💨 Vent : {vent:.2f} m/s"
)

# ======================
# CALCUL RISQUE
# ======================
if st.button("📊 Calculer le risque"):

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
    # ML
    # ======================
    risque_ml = (
        model_rf.predict_proba(X)[0][1]
        * 100
    )

    # ======================
    # REGLES METIER
    # ======================
    risque_regle = 0

    if pluie < 10:
        risque_regle += 30

    if temp > 40:
        risque_regle += 25

    if irrigation == "Non":
        risque_regle += 15

    if culture == "Céréales" and pluie < 25:
        risque_regle += 20

    if saison == "Été":
        risque_regle += 15

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

    # ======================
    # RESULTATS
    # ======================
    st.subheader("📊 Résultats")

    st.progress(int(risque))

    st.write(
        f"🌪 Score de risque : {risque:.2f} %"
    )

    st.write(
        f"💰 Prime estimée : {prime:.2f} DT"
    )

    # ======================
    # DECISION
    # ======================
    if risque < 50:

        st.success(
            "✅ Risque faible"
        )

        st.info(
            "📌 Aucun déclenchement d'indemnité"
        )

    else:

        st.error(
            "⚠️ Risque élevé détecté"
        )

        # ======================
        # ASSURANCE PARAMETRIQUE
        # ======================
        evenement = None

        indemnite = 0

        # sécheresse sévère
        if pluie < 5 and temp > 35:

            evenement = (
                "Sécheresse sévère"
            )

            indemnite = (
                superficie * 180
                + production * 20
            )

        # canicule
        elif temp > 45:

            evenement = (
                "Canicule extrême"
            )

            indemnite = (
                superficie * 150
                + production * 18
            )

        # vent violent
        elif vent > 25:

            evenement = (
                "Vent violent"
            )

            indemnite = (
                superficie * 120
                + production * 14
            )

        # humidité excessive
        elif humidite > 90 and pluie > 40:

            evenement = (
                "Humidité excessive"
            )

            indemnite = (
                superficie * 100
                + production * 12
            )

        # risque global
        else:

            evenement = (
                "Risque climatique élevé"
            )

            indemnite = (
                superficie * 130
                + production * 16
            )

        # ======================
        # RESULTATS PARAMETRIQUES
        # ======================
        st.subheader(
            "🛡 Assurance Paramétrique"
        )

        st.warning(
            f"⚠️ Événement détecté : {evenement}"
        )

        st.success(
            f"💰 Indemnité déclenchée automatiquement : {indemnite:.2f} DT"
        )

        st.info(
            "📌 Déclenchement automatique basé sur les seuils climatiques"
        )

        # ======================
        # TELEGRAM
        # ======================
        envoyer_alerte(
            user_id,
            region,
            risque,
            saison
        )

        st.info(
            "📩 Notification envoyée"
        )
