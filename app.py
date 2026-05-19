import streamlit as st
import joblib
import pandas as pd
import requests

# ======================
# MODELE IA
# ======================
model_rf = joblib.load("model_rf.pkl")

# ======================
# TELEGRAM CONFIG
# ======================
BOT_TOKEN = "TON_BOT_TOKEN"
CHAT_ID = "TON_CHAT_ID"

def envoyer_alerte_telegram(user_id, region, risque):

    message = f"""
⚠️ ALERTE AGRICOLE

👤 Utilisateur: {user_id}
📍 Région: {region}
🌪 Risque: {risque:.2f} %

Niveau: ALERTE (30-70)
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

user_id = st.text_input("🆔 Identifiant utilisateur")
if user_id == "":
    st.stop()

email = st.text_input("📧 Email (optionnel)")

# ======================
# CLIMAT
# ======================
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
culture = st.selectbox("Culture", ["Olives", "Céréales"])
irrigation = st.radio("Irrigation", ["Oui", "Non"])
superficie = st.number_input("Superficie (ha)", 1, 1000, 10)
production = st.number_input("Production (tonnes)", 1, 10000, 50)

# ======================
# CALCUL
# ======================
if st.button("Calculer"):

    # ======================
    # INPUT MODELE IA
    # ======================
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
    # RISQUE IA
    # ======================
    risque_ml = model_rf.predict_proba(X)[0][1] * 100

    # ======================
    # REGLES METIER (CORRIGÉES)
    # ======================
    risque_regle = 0

    # --- SÉCHERESSE ---
    if pluie < 10:
        risque_regle += 35
    elif pluie < 20:
        risque_regle += 25
    elif pluie < 40:
        risque_regle += 10

    # --- TEMPÉRATURE (INCENDIE + SÉCHERESSE) ---
    if temp >= 45:
        risque_regle += 30
    elif temp >= 40:
        risque_regle += 20
    elif temp >= 35:
        risque_regle += 10

    # --- HUMIDITÉ ---
    if humidite < 25:
        risque_regle += 20
    elif humidite < 40:
        risque_regle += 10

    # --- VENT ---
    if vent > 60:
        risque_regle += 20
    elif vent > 40:
        risque_regle += 10

    # --- RÉGION ---
    zones_tres_risque = ["Kebili", "Kairouan", "Gabes"]
    zones_moyen = ["Sousse", "Nabeul", "Monastir"]

    if region in zones_tres_risque:
        risque_regle += 25
    elif region in zones_moyen:
        risque_regle += 10
    else:
        risque_regle += 5

    # --- SAISON ---
    if saison == "Été":
        risque_regle += 25
    elif saison == "Printemps":
        risque_regle += 10
    elif saison == "Automne":
        risque_regle += 5

    # --- INTERACTION SAISON + RÉGION (IMPORTANT) ---
    if saison == "Été" and region in zones_tres_risque:
        risque_regle += 20

    # --- AGRICULTURE ---
    if irrigation == "Non":
        risque_regle += 15
    else:
        risque_regle -= 10

    if culture == "Céréales" and pluie < 30:
        risque_regle += 15

    if culture == "Olives":
        risque_regle -= 5

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

    if region in zones_tres_risque:
        prime += 80

    # ======================
    # AFFICHAGE
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

    elif 30 <= risque < 70:
        st.warning("⚠️ ALERTE MODÉRÉE")

        envoyer_alerte_telegram(user_id, region, risque)

        st.info("📩 Alerte envoyée via Telegram")

    else:
        st.error("🔥 RISQUE ÉLEVÉ")
