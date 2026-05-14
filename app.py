import streamlit as st
import joblib
import pandas as pd
import numpy as np

# Charger modèle
model_rf = joblib.load("model_rf.pkl")

# Interface
st.title("🌾 Simulateur Assurance Agricole")

temp = st.slider("Température (°C)", 0, 50, 30)
pluie = st.slider("Pluie (mm)", 0, 200, 20)
humidite = st.slider("Humidité (%)", 0, 100, 50)
vent = st.slider("Vent (km/h)", 0, 100, 20)

mois = st.selectbox("Mois", list(range(1, 13)))
annee = st.number_input("Année", 2020, 2030, 2026)

region = st.selectbox(
    "Région",
    ["Tunis", "Sousse", "Nabeul", "Monastir",
     "Kairouan", "Kebili", "Gabes", "Beja"]
)

saison = st.selectbox(
    "Saison",
    ["Automne", "Hiver", "Printemps", "Été"]
)

# Bouton prédiction
if st.button("Calculer le risque"):

    # Construire dataframe complet
    X = pd.DataFrame(
        0,
        index=[0],
        columns=model_rf.feature_names_in_
    )

    # Variables utilisateur
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

    # Probabilité ML
    proba = model_rf.predict_proba(X)[0][1] * 100

    # ===== AJUSTEMENTS MÉTIER =====

    score = proba

    # Régions plus risquées
    if region in ["Kebili", "Kairouan"]:
        score += 10

    # Été plus risqué
    if saison == "Été":
        score += 5

    # Forte pluie réduit sécheresse
    if pluie > 100:
        score -= 10

    # Limiter entre 0 et 100
    score = max(0, min(100, score))

    # ===== AFFICHAGE =====

    st.subheader(f"🌾 Score de risque : {round(score,2)} / 100")

    st.progress(int(score))

    if score < 30:
        st.success("🌿 Risque faible")

    elif score < 70:
        st.warning("⚠️ Risque moyen")

    else:
        st.error("🔥 Risque élevé")
