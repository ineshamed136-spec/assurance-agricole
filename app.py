import streamlit as st
import joblib
import pandas as pd

# ======================
# Charger modèle ML
# ======================

model_rf = joblib.load("model_rf.pkl")

# ======================
# Interface
# ======================

st.title("🌾 Simulateur Assurance Agricole")

st.subheader("🌦 Données climatiques")

temp = st.slider("Température (°C)", 0, 45, 30)

pluie = st.slider("Pluie (mm)", 0, 120, 20)

humidite = st.slider("Humidité (%)", 10, 100, 50)

vent = st.slider("Vent (km/h)", 0, 60, 20)

mois = st.selectbox("Mois", list(range(1,13)))

annee = st.number_input("Année", 2020, 2030, 2026)

region = st.selectbox(
    "Région",
    ["Tunis","Sousse","Nabeul",
     "Monastir","Kairouan",
     "Kebili","Gabes","Beja"]
)

saison = st.selectbox(
    "Saison",
    ["Hiver","Printemps","Été","Automne"]
)

# ======================
# Paramètres agricoles
# ======================

st.subheader("🚜 Paramètres agricoles")

culture = st.selectbox(
    "Type de culture",
    ["Olives","Céréales","Légumes"]
)

superficie = st.number_input(
    "Superficie (hectares)",
    1,
    1000,
    10
)

production = st.number_input(
    "Quantité production (tonnes)",
    1,
    10000,
    50
)

irrigation = st.radio(
    "Irrigation",
    ["Oui","Non"]
)

# ======================
# Calcul
# ======================

if st.button("Calculer"):

    # dataframe ML
    X = pd.DataFrame(
        0,
        index=[0],
        columns=model_rf.feature_names_in_
    )

    # remplir données météo
    X["temp"] = temp
    X["précipitations"] = pluie
    X["humidité"] = humidite
    X["vent"] = vent
    X["mois"] = mois
    X["annee"] = annee

    # région
    region_col = f"region_{region}"
    if region_col in X.columns:
        X[region_col] = 1

    # saison
    saison_col = f"saison_{saison}"
    if saison_col in X.columns:
        X[saison_col] = 1

    # ======================
    # Risque ML
    # ======================

    risque_ml = model_rf.predict_proba(X)[0][1] * 100

    # ======================
    # Calcul prime
    # ======================

    prime = 0

    # base superficie
    prime += superficie * 20

    # production
    prime += production * 2

    # risque ML
    prime += risque_ml * 5

    # irrigation
    if irrigation == "Non":
        prime += 100

    # régions risquées
    if region in ["Kebili", "Kairouan"]:
        prime += 150

    # cultures plus sensibles
    if culture == "Céréales":
        prime += 80

    # ======================
    # Affichage
    # ======================

    st.subheader("📊 Résultats")

    st.write(f"🌪 Risque de sinistre : {round(risque_ml,2)} %")

    st.progress(int(risque_ml))

    # niveau risque
    if risque_ml < 30:
        st.success("🌿 Risque faible")

    elif risque_ml < 70:
        st.warning("⚠️ Risque moyen")

    else:
        st.error("🔥 Risque élevé")

    st.subheader(f"💰 Prime estimée : {round(prime,2)} DT")
