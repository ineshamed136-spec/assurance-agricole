import streamlit as st
import joblib
import pandas as pd
import requests

# ======================
# CHARGEMENT MODELE
# ======================
model_rf = joblib.load("model_rf.pkl")

# ======================
# TELEGRAM
# ======================
BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

# ======================
# FONCTION ALERTE
# ======================
def envoyer_alerte_telegram(user_id, region, risque, saison):

    message = f"""
🌾 ALERTE AGRICOLE

👤 Utilisateur : {user_id}
📍 Région : {region}
📅 Saison : {saison}

🌪 Risque détecté : {risque:.2f} %

⚠️ Niveau : ALERTE MODÉRÉE

📌 Recommandations :
- Vérifier les cultures
- Contrôler l'irrigation
- Surveiller les conditions climatiques
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })

# ======================
# INTERFACE
# ======================
st.title("🌾 Assurance Agricole Intelligente")

# ======================
# IDENTIFIANT
# ======================
user_id = st.text_input("🆔 Identifiant utilisateur")

if user_id == "":
    st.warning("Veuillez saisir votre identifiant")
    st.stop()

# ======================
# DONNÉES UTILISATEUR
# ======================
st.subheader("🚜 Informations agricoles")

region = st.selectbox(
    "Région",
    [
        "Tunis",
        "Nabeul",
        "Bizerte",
        "Beja",
        "Sousse",
        "Monastir",
        "Kairouan",
        "Kebili",
        "Gabes",
        "Medenine"
    ]
)

mois = st.selectbox("Mois", list(range(1, 13)))

annee = st.number_input(
    "Année",
    min_value=2020,
    max_value=2035,
    value=2026
)

culture = st.selectbox(
    "Culture",
    ["Olives", "Céréales"]
)

irrigation = st.radio(
    "Irrigation",
    ["Oui", "Non"]
)

superficie = st.number_input(
    "Superficie (ha)",
    min_value=1,
    max_value=1000,
    value=10
)

production = st.number_input(
    "Production (tonnes)",
    min_value=1,
    max_value=10000,
    value=50
)

# ======================
# SAISON AUTOMATIQUE
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
# DONNÉES CLIMATIQUES
# AUTOMATIQUES
# ======================

# Régions désertiques
zones_desertiques = ["Kebili", "Gabes", "Medenine"]

# Régions côtières
zones_cotieres = ["Tunis", "Nabeul", "Bizerte", "Sousse", "Monastir"]

# Régions agricoles
zones_agricoles = ["Beja", "Kairouan"]

# ======================
# MÉTÉO AUTOMATIQUE
# ======================

# ÉTÉ
if saison == "Été":

    if region in zones_desertiques:
        temp = 44
        pluie = 5
        humidite = 30
        vent = 35

    elif region in zones_cotieres:
        temp = 34
        pluie = 15
        humidite = 65
        vent = 25

    else:
        temp = 39
        pluie = 10
        humidite = 45
        vent = 30

# HIVER
elif saison == "Hiver":

    if region in zones_desertiques:
        temp = 16
        pluie = 20
        humidite = 45
        vent = 20

    elif region in zones_cotieres:
        temp = 12
        pluie = 80
        humidite = 75
        vent = 35

    else:
        temp = 10
        pluie = 60
        humidite = 70
        vent = 25

# PRINTEMPS
elif saison == "Printemps":

    if region in zones_desertiques:
        temp = 30
        pluie = 15
        humidite = 35
        vent = 30

    elif region in zones_cotieres:
        temp = 22
        pluie = 40
        humidite = 65
        vent = 25

    else:
        temp = 25
        pluie = 35
        humidite = 55
        vent = 28

# AUTOMNE
else:

    if region in zones_desertiques:
        temp = 28
        pluie = 20
        humidite = 40
        vent = 25

    elif region in zones_cotieres:
        temp = 24
        pluie = 50
        humidite = 70
        vent = 30

    else:
        temp = 22
        pluie = 45
        humidite = 60
        vent = 25

# ======================
# AFFICHAGE MÉTÉO
# ======================
st.subheader("🌦 Conditions climatiques estimées")

st.write(f"🌡 Température : {temp} °C")
st.write(f"🌧 Pluie : {pluie} mm")
st.write(f"💧 Humidité : {humidite} %")
st.write(f"💨 Vent : {vent} km/h")

# ======================
# CALCUL
# ======================
if st.button("Calculer le risque"):

    # ======================
    # INPUT ML
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

    # Région
    region_col = f"region_{region}"

    if region_col in X.columns:
        X[region_col] = 1

    # Saison
    saison_col = f"saison_{saison}"

    if saison_col in X.columns:
        X[saison_col] = 1

    # ======================
    # PRÉDICTION IA
    # ======================
    risque_ml = model_rf.predict_proba(X)[0][1] * 100

    # ======================
    # RÈGLES MÉTIER
    # ======================
    risque_regle = 0

    # sécheresse
    if pluie < 20:
        risque_regle += 25

    # chaleur dangereuse
    if region in zones_cotieres and temp > 35:
        risque_regle += 30

    elif region in zones_desertiques and temp > 45:
        risque_regle += 20

    # été
    if saison == "Été":
        risque_regle += 20

    # irrigation
    if irrigation == "Non":
        risque_regle += 15

    # céréales sensibles
    if culture == "Céréales" and pluie < 30:
        risque_regle += 15

    # ======================
    # RISQUE FINAL
    # ======================
    risque = (0.7 * risque_ml) + (0.3 * risque_regle)

    risque = max(0, min(100, risque))

    # ======================
    # PRIME
    # ======================
    prime = (
        risque * 4
        + superficie * 12
        + production * 1.2
    )

    if irrigation == "Non":
        prime += 100

    if culture == "Céréales":
        prime += 80

    else:
        prime += 40

    # ======================
    # RESULTATS
    # ======================
    st.subheader("📊 Résultats")

    st.progress(int(risque))

    st.write(f"🌪 Risque estimé : {risque:.2f} %")

    st.write(f"💰 Prime estimée : {prime:.2f} DT")

    # ======================
    # ALERTES
    # ======================
    if risque < 30:

        st.success("🌿 Risque faible")

    elif risque < 70:

        st.warning("⚠️ ALERTE MODÉRÉE")

        envoyer_alerte_telegram(
            user_id,
            region,
            risque,
            saison
        )

        st.info("📩 Notification envoyée")

    else:

        st.error("🔥 RISQUE ÉLEVÉ")

