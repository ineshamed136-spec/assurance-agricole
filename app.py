import streamlit as st
import joblib
import pandas as pd
import smtplib
from email.mime.text import MIMEText

# ======================
# MODELE IA
# ======================
model_rf = joblib.load("model_rf.pkl")

# ======================
# FONCTION EMAIL
# ======================
def envoyer_alerte(email_dest, risque):

    expediteur = "VOTRE_EMAIL@gmail.com"

    # mot de passe application Google
    mot_de_passe = "VOTRE_MDP_APPLICATION"

    sujet = "⚠️ Alerte Risque Agricole"

    message = f"""
Bonjour,

Une alerte climatique a été détectée.

Le score de risque est de : {risque:.2f} %

Veuillez prendre les précautions nécessaires.

Système Assurance Agricole
"""

    msg = MIMEText(message)

    msg["Subject"] = sujet
    msg["From"] = expediteur
    msg["To"] = email_dest

    serveur = smtplib.SMTP("smtp.gmail.com", 587)

    serveur.starttls()

    serveur.login(expediteur, mot_de_passe)

    serveur.send_message(msg)

    serveur.quit()

# ======================
# STREAMLIT
# ======================
st.title("🌾 Assurance Agricole Intelligente")

# ======================
# CLIENT
# ======================
user_id = st.text_input("🆔 Identifiant utilisateur")

email = st.text_input("📧 Email utilisateur")

if user_id == "":
    st.warning("Veuillez entrer un identifiant")
    st.stop()

# ======================
# DONNEES CLIMATIQUES
# ======================
st.subheader("🌦 Données climatiques")

temp = st.slider("Température (°C)", 0, 50, 30)

pluie = st.slider("Pluie (mm)", 0, 200, 20)

humidite = st.slider("Humidité (%)", 0, 100, 50)

vent = st.slider("Vent (km/h)", 0, 100, 20)

mois = st.selectbox("Mois", list(range(1, 13)))

annee = st.number_input("Année", 2020, 2035, 2026)

region = st.selectbox(
    "Région",
    [
        "Tunis",
        "Sousse",
        "Nabeul",
        "Monastir",
        "Kairouan",
        "Kebili",
        "Gabes",
        "Beja"
    ]
)

# ======================
# SAISON
# ======================
if mois in [12,1,2]:
    saison = "Hiver"

elif mois in [3,4,5]:
    saison = "Printemps"

elif mois in [6,7,8]:
    saison = "Été"

else:
    saison = "Automne"

st.write("📅 Saison :", saison)

# ======================
# AGRICULTURE
# ======================
st.subheader("🚜 Données agricoles")

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
    1,
    1000,
    10
)

production = st.number_input(
    "Production (tonnes)",
    1,
    10000,
    50
)

# ======================
# CALCUL
# ======================
if st.button("Calculer"):

    # ======================
    # INPUT IA
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
    # RISQUE IA
    # ======================
    risque_ml = model_rf.predict_proba(X)[0][1] * 100

    # ======================
    # REGLES PARAMETRIQUES
    # ======================
    risque_regle = 0

    # sécheresse
    if pluie < 20:
        risque_regle += 20

    elif pluie < 40:
        risque_regle += 10

    # humidité faible
    if humidite < 30:
        risque_regle += 15

    # vent fort
    if vent > 50:
        risque_regle += 10

    # régions chaudes
    zones_chaudes = [
        "Kebili",
        "Kairouan",
        "Gabes"
    ]

    # impact région + saison
    if saison == "Été":

        if region in zones_chaudes:

            if temp > 46:
                risque_regle += 10

            if temp > 48:
                risque_regle += 20

        else:

            if temp > 40:
                risque_regle += 20

            if temp > 43:
                risque_regle += 35

    elif saison == "Hiver":

        if temp > 30:
            risque_regle += 25

    elif saison == "Printemps":

        if temp > 38:
            risque_regle += 20

    elif saison == "Automne":

        if temp > 35:
            risque_regle += 15

    # irrigation
    if irrigation == "Non":
        risque_regle += 15

    # culture
    if culture == "Céréales":

        if pluie < 30:
            risque_regle += 15

    else:

        if temp > 45 and pluie < 15:
            risque_regle += 10

    # ======================
    # RISQUE FINAL
    # ======================
    risque = (
        0.7 * risque_ml
        + 0.3 * risque_regle
    )

    risque = max(0, min(100, risque))

    # ======================
    # PRIME
    # ======================
    prime = 0

    prime += risque * 4

    prime += superficie * 12

    prime += production * 1.2

    if culture == "Céréales":
        prime += 80

    else:
        prime += 40

    if irrigation == "Non":
        prime += 100

    else:
        prime -= 30

    if region in zones_chaudes:
        prime += 80

    prime = max(100, prime)

    # ======================
    # AFFICHAGE
    # ======================
    st.subheader("📊 Résultats")

    st.write("🆔 Client :", user_id)

    st.progress(int(risque))

    st.write(
        f"🌪 Score de risque : {round(risque,2)} %"
    )

    # ======================
    # ALERTES
    # ======================
    if risque < 30:

        st.success("🌿 Risque faible")

    elif risque < 70:

        st.warning("⚠️ Alerte")

        # EMAIL
        if email != "":

            envoyer_alerte(email, risque)

            st.info("📧 Email d'alerte envoyé")

    else:

        st.error("🔥 Risque élevé")

    # ======================
    # PRIME
    # ======================
    st.subheader(
        f"💰 Prime estimée : {round(prime,2)} DT"
    )
