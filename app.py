import streamlit as st
import joblib
import pandas as pd

# ======================
# MODELE IA
# ======================
model_rf = joblib.load("model_rf.pkl")

st.title("🌾 Simulateur Assurance Agricole")

# ======================
# ID CLIENT
# ======================
user_id = st.text_input("🆔 Identifiant utilisateur")

if user_id == "":
    st.warning("Veuillez entrer un identifiant")
    st.stop()

# ======================
# CLIMAT
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

# saison automatique
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
# PRÉDICTION IA
# ======================
if st.button("Calculer"):

    # --------- DATA ML ----------
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

    # --------- RISQUE IA ----------
    risque = model_rf.predict_proba(X)[0][1] * 100

    # ======================
    # PRIME ASSURANCE
    # ======================
    prime = 0

    # base risque IA
    prime += risque * 5

    # superficie
    prime += superficie * 15

    # production (IMPORTANT)
    prime += production * 1.5

    # culture
    if culture == "Céréales":
        prime += 80
    else:
        prime += 30

    # irrigation
    if irrigation == "Non":
        prime += 120
    else:
        prime -= 40

    # région
    if region in ["Kebili", "Kairouan", "Gabes"]:
        prime += 100

    # ======================
    # LIMITATION RISQUE
    # ======================
    risque = max(0, min(100, risque))

    # ======================
    # AFFICHAGE
    # ======================
    st.subheader("📊 Résultats")

    st.write("🆔 Client :", user_id)

    st.write(f"🌪 Score de risque : {round(risque,2)} %")
    st.progress(int(risque))

    if risque < 30:
        st.success("🌿 Risque faible")
    elif risque < 70:
        st.warning("⚠️ Alerte")
    else:
        st.error("🔥 Risque élevé")

    st.subheader(f"💰 Prime estimée : {round(prime,2)} DT")
