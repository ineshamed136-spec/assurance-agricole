import streamlit as st
import joblib
import pandas as pd
import numpy as np

model_rf = joblib.load("model_rf.pkl")

st.title("🌾 Simulateur Assurance Agricole")

temp = st.slider("Température", 0, 50, 30)
pluie = st.slider("Pluie", 0, 200, 20)
humidite = st.slider("Humidité", 0, 100, 50)
vent = st.slider("Vent", 0, 100, 20)

mois = st.selectbox("Mois", list(range(1,13)))
annee = st.number_input("Année", 2020, 2030, 2026)

region = st.selectbox("Région", [
    "Tunis","Sousse","Nabeul","Monastir","Kairouan",
    "Bizerte","Beja","Gabes","Kebili","Medenine"
])

saison = st.selectbox("Saison", ["Automne","Hiver","Printemps","Été"])

if st.button("Prédire"):

    # construire toutes les features attendues
    X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)

    # variables de base
    X["temp"] = temp
    X["précipitations"] = pluie
    X["humidité"] = humidite
    X["vent"] = vent
    X["mois"] = mois
    X["annee"] = annee

    # région (one-hot)
    region_col = f"region_{region}"
    if region_col in X.columns:
        X[region_col] = 1

    # saison (one-hot)
    saison_col = f"saison_{saison}"
    if saison_col in X.columns:
        X[saison_col] = 1

    # prédiction
    prediction = model_rf.predict(X)[0]
    proba = model_rf.predict_proba(X)[0][1]

    st.write("### Résultat :", "🌧️ Sinistre" if prediction==1 else "🌿 Pas de sinistre")
    st.write("### Score de risque :", round(proba*100,2))
