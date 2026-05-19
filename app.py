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
# EMAIL ALERTE
# ======================
def envoyer_alerte(email_dest, user_id, region, risque):

    expediteur = "tonemail@gmail.com"
    mot_de_passe = "dgif waho jwui qbve"  # sans espaces

    sujet = "⚠️ Alerte Risque Agricole (30-70)"

    message = f"""
Bonjour,

Alerte de risque agricole détectée.

Utilisateur : {user_id}
Région : {region}
Score de risque : {risque:.2f} %

Niveau : ALERTE MODÉRÉE

Merci de surveiller les conditions climatiques.

Système Assurance Agricole
"""

    msg = MIMEText(message)
    msg["Subject"] = sujet
    msg["From"] = expediteur
    msg["To"] = email_dest

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(expediteur, mot_de_passe)
    server.send_message(msg)
    server.quit()

# ======================
# STREAMLIT UI
# ======================
st.title("🌾 Assurance Agricole Intelligente")

user_id = st.text_input("🆔 Identifiant utilisateur")
email = st.text_input("📧 Email utilisateur")

if user_id == "":
    st.warning("Veuillez entrer un identifiant")
    st.stop()

# ======================
# CLIMAT
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
    ["Tunis","Sousse","Nabeul","Monastir",
     "Kairouan","Kebili","Gabes","Beja"]
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

culture = st.selectbox("Culture", ["Olives", "Céréales"])
irrigation = st.radio("Irrigation", ["Oui", "Non"])

superficie = st.number_input("Superficie (ha)", 1, 1000, 10)
production = st.number_input("Production (tonnes)", 1, 10000, 50)

# ======================
# CALCUL
# ======================
if st.button("Calculer"):

    # ======================
    # INPUT MODELE
    # ======================
    X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)

    X["temp"] = temp
    X["précipitations"] = pluie
    X["humidité"] = humidite
    X["vent"] = vent
    X["mois"] = mois
    X["annee"] = annee

    # region encoding
    region_col = f"region_{region}"
    if region_col in X.columns:
        X[region_col] = 1

    # saison encoding
    saison_col = f"saison_{saison}"
    if saison_col in X.columns:
        X[saison_col] = 1

    # ======================
    # RISQUE IA
    # ======================
    risque_ml = model_rf.predict_proba(X)[0][1] * 100

    # ======================
    # REGLES METIER
    # ======================
    risque_regle = 0

    if pluie < 20:
        risque_regle += 20
    elif pluie < 40:
        risque_regle += 10

    if humidite < 30:
        risque_regle += 15

    if vent > 50:
        risque_regle += 10

    zones_chaudes = ["Kebili","Kairouan","Gabes"]

    if saison == "Été":

        if region in zones_chaudes:
            if temp > 48:
                risque_regle += 20
        else:
            if temp > 43:
                risque_regle += 25

    if irrigation == "Non":
        risque_regle += 15

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
        risque * 4 +
        superficie * 12 +
        production * 1.2
    )

    if culture == "Céréales":
        prime += 80
    else:
        prime += 40

    if irrigation == "Non":
        prime += 100

    if region in zones_chaudes:
        prime += 80

    prime = max(100, prime)

    # ======================
    # AFFICHAGE
    # ======================
    st.subheader("📊 Résultats")

    st.write("🆔 Client :", user_id)

    st.progress(int(risque))

    st.write(f"🌪 Score de risque : {risque:.2f} %")

    if risque < 30:
        st.success("🌿 Risque faible")

    elif 30 <= risque < 70:
        st.warning("⚠️ Alerte modérée")

        if email != "":
            envoyer_alerte(email, user_id, region, risque)
            st.info("📧 Email d’alerte envoyé")

    else:
        st.error("🔥 Risque élevé")

    st.subheader(f"💰 Prime estimée : {prime:.2f} DT")
