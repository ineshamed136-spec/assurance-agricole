import streamlit as st
import joblib
import pandas as pd

# =========================
# Charger modèle
# =========================

model_rf = joblib.load("model_rf.pkl")

# =========================
# Interface
# =========================

st.title("🌾 Simulateur Assurance Agricole")

st.subheader("🌦 Données climatiques")

temp = st.slider("Température (°C)", 0, 45, 30)

pluie = st.slider("Pluie (mm)", 0, 120, 20)

humidite = st.slider("Humidité (%)", 10, 100, 50)

vent = st.slider("Vent (km/h)", 0, 60, 20)

mois = st.selectbox("Mois", list(range(1, 13)))

annee = st.number_input("Année", 2020, 2030, 2026)

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

# =========================
# Saison automatique
# =========================

if mois in [12, 1, 2]:
    saison = "Hiver"

elif mois in [3, 4, 5]:
    saison = "Printemps"

elif mois in [6, 7, 8]:
    saison = "Été"

else:
    saison = "Automne"

st.write("📅 Saison :", saison)

# =========================
# Paramètres agricoles
# =========================

st.subheader("🚜 Paramètres agricoles")

culture = st.selectbox(
    "Type de culture",
    ["Olives", "Céréales", "Légumes"]
)

superficie = st.number_input(
    "Superficie (hectares)",
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

irrigation = st.radio(
    "Irrigation",
    ["Oui", "Non"]
)

# =========================
# Calcul
# =========================

if st.button("Calculer"):

    # dataframe pour ML
    X = pd.DataFrame(
        0,
        index=[0],
        columns=model_rf.feature_names_in_
    )

    # variables météo
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

    # =========================
    # Risque ML
    # =========================

    risque_ml = model_rf.predict_proba(X)[0][1] * 100

    # =========================
    # Ajustements métier
    # =========================

    # température élevée
    if temp > 40:
        risque_ml += 25

    elif temp > 35:
        risque_ml += 15

    # faible pluie
    if pluie < 20:
        risque_ml += 20

    elif pluie < 50:
        risque_ml += 10

    # humidité faible
    if humidite < 30:
        risque_ml += 10

    # vent fort
    if vent > 50:
        risque_ml += 10

    # été
    if saison == "Été":
        risque_ml += 10

    # régions risquées
    if region in ["Kebili", "Kairouan"]:
        risque_ml += 10

    # irrigation réduit risque
    if irrigation == "Oui":
        risque_ml -= 10

    # limiter entre 0 et 100
    risque_ml = max(0, min(100, risque_ml))

    # =========================
    # Calcul prime
    # =========================

    prime = 0

    # base superficie
    prime += superficie * 20

    # production
    prime += production * 2

    # risque
    prime += risque_ml * 5

    # irrigation
    if irrigation == "Non":
        prime += 100

    # culture sensible
    if culture == "Céréales":
        prime += 80

    # régions risquées
    if region in ["Kebili", "Kairouan"]:
        prime += 150

    # =========================
    # Résultats
    # =========================

    st.subheader("📊 Résultats")

    st.write(f"🌪 Risque de sinistre : {round(risque_ml,2)} %")

    st.progress(int(risque_ml))

    if risque_ml < 30:
        st.success("🌿 Risque faible")

    elif risque_ml < 70:
        st.warning("⚠️ Risque moyen")

    else:
        st.error("🔥 Risque élevé")

    st.subheader(f"💰 Prime estimée : {round(prime,2)} DT")
