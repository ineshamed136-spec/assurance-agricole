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

def envoyer_alerte(user_id, region, risque, saison):

    message = f"""
🌾 ALERTE AGRICOLE

👤 Utilisateur : {user_id}
📍 Région : {region}
📅 Saison : {saison}

🌪 Risque : {risque:.2f} %
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })

# ======================
# NASA POWER (TA VERSION CORRIGÉE)
# ======================
def get_weather(region, mois, annee, coords):

    lat, lon = coords[region]

    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"

    params = {
        "parameters": "T2M,PRECTOTCORR,RH2M,WS2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": annee,
        "end": annee,
        "format": "JSON"
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()

        # DEBUG (optionnel)
        # st.write(data)

        if "properties" not in data:
            return None

        p = data["properties"]["parameter"]

        key = f"{annee}{mois:02d}"

        def safe_get(d):
            if not d:
                return None
            return d.get(key) or list(d.values())[0]

        temp = safe_get(p.get("T2M"))
        pluie = safe_get(p.get("PRECTOTCORR"))
        humidite = safe_get(p.get("RH2M"))
        vent = safe_get(p.get("WS2M"))

        if None in [temp, pluie, humidite, vent]:
            return None

        return temp, pluie, humidite, vent

    except Exception as e:
        print("NASA ERROR:", e)
        return None


# ======================
# COORDONNEES
# ======================
coords = {
    "Tunis": (36.8065, 10.1815),
    "Nabeul": (36.4513, 10.7357),
    "Bizerte": (37.2744, 9.8739),
    "Beja": (36.7256, 9.1817),
    "Sousse": (35.8256, 10.6084),
    "Monastir": (35.7643, 10.8113),
    "Kairouan": (35.6781, 10.0963),
    "Kebili": (33.7076, 8.9711),
    "Gabes": (33.8815, 10.0982),
    "Medenine": (33.3549, 10.5055)
}

zones_desertiques = ["Kebili", "Gabes", "Medenine"]

# ======================
# INTERFACE
# ======================
st.title("🌾 Assurance Agricole Intelligente")

user_id = st.text_input("🆔 Identifiant utilisateur")
if user_id == "":
    st.stop()

region = st.selectbox("📍 Région", list(coords.keys()))
mois = st.selectbox("📅 Mois", list(range(1, 13)))
annee = 2026

culture = st.selectbox("🌱 Culture", ["Olives", "Céréales"])
irrigation = st.radio("💧 Irrigation", ["Oui", "Non"])
superficie = st.number_input("📏 Superficie (ha)", 1, 1000, 10)
production = st.number_input("🌾 Production (tonnes)", 1, 10000, 50)

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

st.write("📅 Saison :", saison)

# ======================
# METEO
# ======================
weather = get_weather(region, mois, annee, coords)

# FALLBACK si NASA échoue
if weather is None:
    st.warning("⚠️ NASA POWER indisponible → données simulées utilisées")

    temp = 30
    pluie = 20
    humidite = 60
    vent = 15
else:
    temp, pluie, humidite, vent = weather

# ======================
# AFFICHAGE
# ======================
st.subheader("🌦 Données climatiques")

st.write(f"🌡 Température : {temp:.2f} °C")
st.write(f"🌧 Pluie : {pluie:.2f} mm")
st.write(f"💧 Humidité : {humidite:.2f} %")
st.write(f"💨 Vent : {vent:.2f} m/s")

# ======================
# CALCUL RISQUE
# ======================
if st.button("📊 Calculer le risque"):

    X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)

    X["temp"] = temp
    X["précipitations"] = pluie
    X["humidité"] = humidite
    X["vent"] = vent
    X["mois"] = mois
    X["annee"] = annee

    region_col = f"region_{region}"
    if region_col in X.columns:
        X[region_col] = 1

    saison_col = f"saison_{saison}"
    if saison_col in X.columns:
        X[saison_col] = 1

    # ======================
    # ML
    # ======================
    risque_ml = model_rf.predict_proba(X)[0][1] * 100

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

    if region in zones_desertiques and temp > 42:
        risque_regle += 20

    # ======================
    # RISQUE FINAL
    # ======================
    risque = (0.7 * risque_ml) + (0.3 * risque_regle)
    risque = max(0, min(100, risque))

    # ======================
    # PRIME
    # ======================
    prime = risque * 4 + superficie * 12 + production * 1.2

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
    # ALERTES
    # ======================
    if risque < 30:
        st.success("🌿 Risque faible")

    elif risque < 70:
        st.warning("⚠️ ALERTE MODÉRÉE")
        envoyer_alerte(user_id, region, risque, saison)
        st.info("📩 Notification envoyée")

    else:
        st.error("🔥 RISQUE ÉLEVÉ")
