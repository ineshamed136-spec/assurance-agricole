import streamlit as st
import joblib
import pandas as pd

# charger modèle
model_rf = joblib.load("model_rf.pkl")

st.title("🌾 Simulateur Assurance Agricole")

temperature = st.slider("Température", 0, 50, 30)
pluie = st.slider("Pluie", 0, 100, 20)
humidite = st.slider("Humidité", 0, 100, 50)
vent = st.slider("Vent", 0, 100, 20)

if st.button("Prédire"):

    X = pd.DataFrame([{
        "temperature": temperature,
        "pluie": pluie,
        "humidite": humidite,
        "vent": vent
    }])

    prediction = model_rf.predict(X)[0]
    proba = model_rf.predict_proba(X)[0][1]

    st.write("Sinistre :", prediction)
    st.write("Score :", proba * 100)