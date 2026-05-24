import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# ====================================
# 1. MODELE ML
# ====================================
@st.cache_resource
def load_model():
    try:
        return joblib.load("model_rf.pkl"), True
    except:
        return None, False

model_rf, model_ok = load_model()


# ====================================
# 2. PREDICTION ML (ROBUSTE)
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
            "humidite": hum,
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
# 3. DONNEES REGION
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
# 4. METEO SAFE (ANTI CRASH)
# ====================================
def get_weather(reg, m):

    try:
        lat, lon = coords[reg]

        url = "https://power.larc.nasa.gov/api/temporal/monthly/point"

        params = {
            "parameters": "T2M,PRECTOTCORR,RH2M,WS2M",
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": "2025",
            "end": "2025",
            "format": "JSON"
        }

        r = requests.get(url, params=params, timeout=8)

        if r.status_code != 200:
            return [25, 10, 60, 3], "Fallback"

        d = r.json()["properties"]["parameter"]
        k = f"2025{m:02d}"

        return [
            float(d["T2M"][k]),
            float(d["PRECTOTCORR"][k]),
            float(d["RH2M"][k]),
            float(d["WS2M"][k])
        ], "NASA API"

    except:
        return [25, 10, 60, 3], "Fallback"


# ====================================
# 5. INTERFACE
# ====================================
st.title("🌾 Assurance Agricole Paramétrique")

if model_ok:
    st.sidebar.success("ML actif")
else:
    st.sidebar.warning("Mode règles")


col1, col2 = st.columns(2)

with col1:

    region = st.selectbox("Région", list(coords.keys()))
    mois = st.selectbox("Mois", list(range(1, 13)))
    sup = st.number_input("Superficie (Ha)", 1, 100, 15)
    prod = st.number_input("Rendement (T)", 1, 100, 60)
    irrigation = st.radio("Irrigation", ["Oui", "Non"])

    btn = st.button("Calculer")


with col2:

    if btn:

        # ====================================
        # METEO
        # ====================================
        w, source = get_weather(region, mois)

        if not isinstance(w, list) or len(w) != 4:
            w = [25, 10, 60, 3]

        t, pl, hum, vent = w

        saison = saisons_map[mois]

        # ====================================
        # RISQUE
        # ====================================
        ml = predire_risque_ml(t, pl, hum, vent, mois, region, saison)

        metier = 10

        exp = "Base 10%"

        if pl < 15:
            metier += 35
            exp += " + sécheresse"

        if t > 38:
            metier += 25
            exp += " + chaleur"

        if irrigation == "Non":
            metier += 15
            exp += " + non irrigué"

        risque = (0.7 * ml) + (0.3 * metier)

        # ====================================
        # PRIME
        # ====================================
        valeur = (sup * 180) + (prod * 35)

        prime_pure = (risque / 100) * valeur

        frais = (sup * 12) + (prod * 1.1)

        prime = prime_pure + frais

        # ====================================
        # INDEMNITE
        # ====================================
        seuil = 35
        indemnité = 0

        if pl < seuil:
            indemnité = (seuil - pl) * sup * 2

        # ====================================
        # AFFICHAGE
        # ====================================
        st.subheader("📊 Résultats")

        st.success(f"Risque global : {risque:.2f}%")
        st.info(f"Prime totale : {prime:.2f} DT")

        if indemnité > 0:
            st.error(f"🚨 Indemnité : {indemnité:.2f} DT")
        else:
            st.success("🍏 Aucun sinistre")

        # ====================================
        # FORMULES
        # ====================================
        with st.expander("📌 Formules utilisées"):

            st.markdown(f"""
### Risque global
70% ML + 30% métier

### Valeur assurée
{sup} × 180 + {prod} × 35 = {valeur:.2f} DT

### Prime pure
Risque × Valeur assurée

### Frais
{sup} × 12 + {prod} × 1.1

### Indemnité
Basée sur la sécheresse (pluie < 35 mm)
""")
