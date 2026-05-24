import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance", layout="wide")

# ====================================
# 1. CHARGEMENT DU MODELE
# ====================================
@st.cache_resource
def load_model():
    try:
        return joblib.load("model_rf.pkl"), True
    except Exception as e:
        st.error(f"Erreur chargement modèle : {e}")
        return None, False

model_rf, model_charge = load_model()

# ====================================
# 2. FONCTION DE PREDICTION ML CORRIGEE
# ====================================
def predire_risque_ml(t, pl, hum, vent, mois, reg, sais):

    if not model_charge:
        return 20.0

    try:
        cm = model_rf.feature_names_in_

        X = pd.DataFrame(0, index=[0], columns=cm)

        # mapping robuste des variables
        valeurs = {
            "temp": t,
            "temperature": t,

            "précipitations": pl,
            "precipitations": pl,

            "humidité": hum,
            "humidite": hum,

            "vent": vent,
            "wind": vent,

            "mois": mois,
            "annee": 2025,
            "year": 2025
        }

        # remplissage automatique
        for col in cm:
            if col in valeurs:
                X[col] = valeurs[col]

        # régions / saisons
        if f"region_{reg}" in X.columns:
            X[f"region_{reg}"] = 1

        if f"saison_{sais}" in X.columns:
            X[f"saison_{sais}"] = 1

        proba = model_rf.predict_proba(X)[0][1]
        return float(proba * 100)

    except Exception as e:
        st.error(f"Erreur ML : {e}")
        return 20.0


# ====================================
# 3. COORDONNEES
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
    12: "Hiver", 1: "Hiver", 2: "Hiver",
    3: "Printemps", 4: "Printemps", 5: "Printemps",
    6: "Ete", 7: "Ete", 8: "Ete",
    9: "Automne", 10: "Automne", 11: "Automne"
}

normales_saisonnieres = {}

# ====================================
# 4. METEO
# ====================================
@st.cache_data(ttl=3600)
def get_weather(reg, m):

    lat, lon = coords[reg]

    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"

    p = {
        "parameters": "T2M,PRECTOTCORR,RH2M,WS2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": "2025",
        "end": "2025",
        "format": "JSON"
    }

    try:
        r = requests.get(url, params=p, timeout=8)

        if r.status_code != 200:
            return [24, 10, 60, 3], "Fallback"

        d = r.json()["properties"]["parameter"]
        k = f"2025{m:02d}"

        return [
            float(d["T2M"][k]),
            float(d["PRECTOTCORR"][k]),
            float(d["RH2M"][k]),
            float(d["WS2M"][k])
        ], "NASA POWER"

    except:
        return [24, 10, 60, 3], "Fallback"


# ====================================
# 5. INTERFACE
# ====================================
st.title("🌾 Assurance Agricole Paramétrique")

if model_charge:
    st.sidebar.success("🔮 Modèle ML chargé")
else:
    st.sidebar.warning("⚙️ Mode fallback actif")

col1, col2 = st.columns(2)

with col1:
    region = st.selectbox("Région", list(coords.keys()))
    mois = st.selectbox("Mois", list(range(1, 13)))
    sup = st.number_input("Superficie", 1, 100, 15)
    prod = st.number_input("Rendement", 1, 100, 60)
    irrigation = st.radio("Irrigation", ["Oui", "Non"])
    btn = st.button("Analyser")

with col2:
    w, source = get_weather(region, mois)
    t, pl, hum, vent = w

    st.write(f"Météo: {w} ({source})")

    if btn:

        # ================================
        # RISQUE ML + METIER
        # ================================
        risque_ml = predire_risque_ml(t, pl, hum, vent, mois, region, "Ete")

        r_regle = 10
        if pl < 15:
            r_regle += 35
        if t > 38:
            r_regle += 25
        if irrigation == "Non":
            r_regle += 15

        risque = (0.7 * risque_ml) + (0.3 * r_regle)

        # ================================
        # PRIME
        # ================================
        valeur_assuree = (sup * 180) + (prod * 35)

        prime_pure = (risque / 100) * valeur_assuree

        frais = (sup * 12) + (prod * 1.1)

        prime = prime_pure + frais

        st.subheader("Résultats")

        st.metric("Risque", f"{risque:.2f}%")
        st.metric("Prime", f"{prime:.2f} DT")

        st.progress(int(risque))
