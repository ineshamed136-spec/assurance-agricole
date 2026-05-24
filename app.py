import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# ====================================
# MODELE
# ====================================
@st.cache_resource
def load_model():
    try:
        return joblib.load("model_rf.pkl"), True
    except:
        return None, False

model_rf, model_ok = load_model()


# ====================================
# ML RISK
# ====================================
def predire_risque_ml(t, pl, hum, vent, mois, reg, sais):

    if not model_ok:
        return 20.0

    try:
        cols = model_rf.feature_names_in_
        X = pd.DataFrame(0, index=[0], columns=cols)

        data = {
            "temp": t,
            "temperature": t,
            "précipitations": pl,
            "humidité": hum,
            "vent": vent,
            "mois": mois,
            "annee": 2025
        }

        for c in cols:
            if c in data:
                X[c] = data[c]

        if f"region_{reg}" in X.columns:
            X[f"region_{reg}"] = 1

        if f"saison_{sais}" in X.columns:
            X[f"saison_{sais}"] = 1

        return float(model_rf.predict_proba(X)[0][1] * 100)

    except:
        return 20.0


# ====================================
# DATA REGION
# ====================================
coords = {
    "Tunis": (36.80, 10.18),
    "Nabeul": (36.45, 10.73),
    "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18),
    "Sousse": (35.82, 10.60),
    "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09),
    "Kebili": (33.70, 8.97),
    "Gabes": (33.88, 10.09)
}

saisons_map = {
    1: "Hiver", 2: "Hiver", 12: "Hiver",
    3: "Printemps", 4: "Printemps", 5: "Printemps",
    6: "Ete", 7: "Ete", 8: "Ete",
    9: "Automne", 10: "Automne", 11: "Automne"
}


# ====================================
# METEO (fallback simple)
# ====================================
def get_weather(region, mois):
    return [25, 10, 60, 3], "Simulation"


# ====================================
# UI
# ====================================
st.title("🌾 Assurance Agricole Paramétrique (Version Pro)")

col1, col2 = st.columns(2)

with col1:

    st.subheader("📋 Paramètres")

    region = st.selectbox("Région", list(coords.keys()))
    mois = st.selectbox("Mois", list(range(1, 13)))
    sup = st.number_input("Superficie (Ha)", 1, 100, 15)
    prod = st.number_input("Rendement (T)", 1, 100, 60)
    irrigation = st.radio("Irrigation", ["Oui", "Non"])

    btn = st.button("🔍 Calculer")


with col2:

    if btn:

        # ====================================
        # METEO
        # ====================================
        t, pl, hum, vent = get_weather(region, mois)

        saison = saisons_map[mois]

        # ====================================
        # RISQUE ML
        # ====================================
        ml = predire_risque_ml(t, pl, hum, vent, mois, region, saison)

        # ====================================
        # RISQUE METIER
        # ====================================
        r = 10
        exp = "Base 10%"

        if pl < 15:
            r += 35
            exp += " + Sécheresse"

        if t > 38:
            r += 25
            exp += " + Chaleur"

        if irrigation == "Non":
            r += 15
            exp += " + Non irrigué"

        # ====================================
        # RISQUE FINAL
        # ====================================
        risque = (0.7 * ml) + (0.3 * r)

        # ====================================
        # VALEUR ASSUREE
        # ====================================
        valeur = (sup * 180) + (prod * 35)

        # ====================================
        # PRIME PURE
        # ====================================
        prime_pure = (risque / 100) * valeur

        # ====================================
        # FRAIS
        # ====================================
        frais = (sup * 12) + (prod * 1.1)

        prime_totale = prime_pure + frais

        # ====================================
        # INDEMNITE
        # ====================================
        seuil_secheresse = 35
        indemnité = 0

        if pl < seuil_secheresse:
            indemnité = (seuil_secheresse - pl) * sup * 2

        # ====================================
        # RESULTATS
        # ====================================
        st.subheader("📊 Résultats")

        st.success(f"Risque global : {risque:.2f} %")
        st.info(f"Prime totale : {prime_totale:.2f} DT")

        if indemnité > 0:
            st.error(f"🚨 Indemnité déclenchée : {indemnité:.2f} DT")
        else:
            st.success("🍏 Aucun sinistre détecté")

        # ====================================
        # EXPLICATION PROPRE
        # ====================================
        with st.expander("📌 Formules utilisées"):

            st.markdown(f"""
### 🔹 Risque global
Risque = 70% ML + 30% métier

### 🔹 Valeur assurée
Valeur = Superficie × 180 + Rendement × 35 = **{valeur:.2f} DT**

### 🔹 Prime pure
Prime = Risque × Valeur

### 🔹 Frais
Frais = Superficie × 12 + Rendement × 1.1

### 🔹 Prime totale
Prime totale = Prime pure + Frais

### 🔹 Indemnité
Basée sur le déficit de pluie (stress hydrique)
""")
