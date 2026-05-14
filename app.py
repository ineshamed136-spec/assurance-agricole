import streamlit as st
import joblib
import pandas as pd

# ======================
# Charger modèle IA
# ======================
model_rf = joblib.load("model_rf.pkl")

st.title("🌾 Simulateur Assurance Agricole (Sécheresse & Incendie)")

# ======================
# IDENTIFIANT CLIENT
# ======================
user_id = st.text_input("🆔 Identifiant utilisateur")

if user_id == "":
    st.warning("Veuillez entrer un identifiant")
    st.stop()

# ======================
# DONNÉES CLIMATIQUES
# ======================
st.subheader("🌦 Données climatiques")

temp = st.slider("Température (°C)", 0, 45, 30)
pluie = st.slider("Pluie (mm)", 0, 120, 20)
humidite = st.slider("Humidité (%)", 10, 100, 50)
vent = st.slider("Vent (km/h)", 0, 60, 20)

mois = st.selectbox("Mois", list(range(1, 13)))
annee = st.number_input("Année", 2020, 2030, 2026)

region = st.selectbox(
    "Région",
    ["Tunis","Sousse","Nabeul","Monastir",
     "Kairouan","Kebili","Gabes","Beja"]
)

# ======================
# SAISON AUTOMATIQUE
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
st.subheader("🚜 Culture")

culture = st.selectbox(
    "Type de culture",
    ["Olives", "Céréales"]
)

superficie = st.number_input("Superficie (ha)", 1, 1000, 10)
irrigation = st.radio("Irrigation", ["Oui", "Non"])

# ======================
# PRÉDICTION IA
# ======================
if st.button("Calculer le risque"):

    # ===== DATA ML =====
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
    risque_base = model_rf.predict_proba(X)[0][1] * 100

    # ======================
    # RISQUE SÉCHERESSE
    # ======================
    risque_secheresse = 0

    if pluie < 20:
        risque_secheresse += 30
    elif pluie < 40:
        risque_secheresse += 15

    if temp > 40:
        risque_secheresse += 20
    elif temp > 35:
        risque_secheresse += 10

    if irrigation == "Non":
        risque_secheresse += 20
    else:
        risque_secheresse -= 10

    # régions arides
    if region in ["Kebili", "Kairouan", "Gabes"]:
        risque_secheresse += 10

    # ======================
    # RISQUE INCENDIE
    # ======================
    risque_incendie = 0

    if temp > 40:
        risque_incendie += 25

    if vent > 50:
        risque_incendie += 20

    if humidite < 30:
        risque_incendie += 15

    if region in ["Kebili", "Kairouan", "Gabes"]:
        risque_incendie += 5

    # ======================
    # COMBINAISON
    # ======================
    risque_final = (0.6 * risque_secheresse) + (0.4 * risque_incendie)

    # intégrer IA
    risque_final = (0.7 * risque_base) + (0.3 * risque_final)

    # limiter
    risque_final = max(0, min(100, risque_final))

    # ======================
    # PRÉSENTATION
    # ======================
    st.subheader("📊 Résultats")

    st.write("🆔 Client :", user_id)

    st.write(f"🌪 Risque final : {round(risque_final,2)} %")

    st.progress(int(risque_final))

    if risque_final < 30:
        st.success("🌿 Risque faible")

    elif risque_final < 70:
        st.warning("⚠️ Alerte")

    else:
        st.error("🔥 Risque élevé")

    # détails
    st.write("🔥 Sécheresse :", round(risque_secheresse,2))
    st.write("🔥 Incendie :", round(risque_incendie,2))
    st.write("🤖 IA brute :", round(risque_base,2))
