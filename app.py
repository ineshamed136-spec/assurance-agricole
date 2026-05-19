import streamlit as st
import joblib
import pandas as pd
import requests

# ======================
# MODELE IA
# ======================
model_rf = joblib.load("model_rf.pkl")

# ======================
# TELEGRAM
# ======================
BOT_TOKEN = "TON_BOT_TOKEN"
CHAT_ID = "TON_CHAT_ID"

def envoyer_alerte_telegram(user_id, region, risque):

    message = f"""
⚠️ ALERTE AGRICOLE

👤 User: {user_id}
📍 Région: {region}
🌪 Risque: {risque:.2f} %
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

# ======================
# INTERFACE
# ======================
st.title("🌾 Assurance Agricole Intelligente")

user_id = st.text_input("🆔 Identifiant")
if user_id == "":
    st.stop()

# ======================
# CLIMAT
# ======================
temp = st.slider("Température", 0, 50, 30)
pluie = st.slider("Pluie", 0, 200, 20)
humidite = st.slider("Humidité", 0, 100, 50)
vent = st.slider("Vent", 0, 100, 20)

mois = st.selectbox("Mois", list(range(1, 13)))

region = st.selectbox(
    "Région",
    ["Tunis","Nabeul","Bizerte","Beja",
     "Sousse","Monastir",
     "Kairouan","Kebili","Gabes","Medenine"]
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

st.write("📅 Saison:", saison)

# ======================
# AGRICULTURE
# ======================
culture = st.selectbox("Culture", ["Olives", "Céréales"])
irrigation = st.radio("Irrigation", ["Oui", "Non"])

# ======================
# CALCUL
# ======================
if st.button("Calculer"):

    # ======================
    # ML INPUT
    # ======================
    X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)

    X["temp"] = temp
    X["précipitations"] = pluie
    X["humidité"] = humidite
    X["vent"] = vent
    X["mois"] = mois

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
    # REGLES METIER LOGIQUES
    # ======================
    risque_regle = 0

    # 🌍 REGIONS
    zones_desertiques = ["Kebili", "Gabes", "Medenine"]
    zones_centrales = ["Kairouan"]
    zones_cotieres = ["Tunis", "Nabeul", "Bizerte", "Beja"]

    # ======================
    # 🌡 TEMPÉRATURE (INCENDIE)
    # ======================

    if region in zones_desertiques:
        if temp > 48:
            risque_regle += 25
        elif temp > 45:
            risque_regle += 10

    elif region in zones_centrales:
        if temp > 45:
            risque_regle += 25
        elif temp > 42:
            risque_regle += 15

    elif region in zones_cotieres:
        if temp > 38:
            risque_regle += 30
        elif temp > 35:
            risque_regle += 20

    # ======================
    # 🌵 PLUIE (SÉCHERESSE)
    # ======================

    if region in zones_cotieres:
        if pluie < 20:
            risque_regle += 35
        elif pluie < 40:
            risque_regle += 20
    else:
        if pluie < 15:
            risque_regle += 30
        elif pluie < 30:
            risque_regle += 15

    # ======================
    # 💨 VENT (INCENDIE)
    # ======================
    if vent > 60:
        risque_regle += 25
    elif vent > 40:
        risque_regle += 10

    # ======================
    # 🌦 SAISON
    # ======================
    if saison == "Été":
        risque_regle += 25
    elif saison == "Printemps":
        risque_regle += 10
    elif saison == "Automne":
        risque_regle += 5

    # interaction critique
    if saison == "Été" and region in zones_desertiques:
        risque_regle += 20

    # ======================
    # 🚜 AGRICULTURE
    # ======================
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
    prime = risque * 4 + 200

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
        st.warning("⚠️ ALERTE")

        envoyer_alerte_telegram(user_id, region, risque)
        st.info("📩 Alerte envoyée")

    else:
        st.error("🔥 RISQUE ÉLEVÉ")
