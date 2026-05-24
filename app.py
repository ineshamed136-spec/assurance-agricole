import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance Agricole 2026", layout="wide")

# ====================================
# 1. CHARGEMENT MODELE
# ====================================
@st.cache_resource
def load_model():
    try:
        return joblib.load("model_rf.pkl"), True
    except:
        return None, False

model_rf, model_ok = load_model()


# ====================================
# 2. NASA POWER (OPTIONNEL + SAFE)
# ====================================
def get_weather(region, mois):

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

    fallback = [25, 10, 60, 3]

    try:
        lat, lon = coords[region]

        url = "https://power.larc.nasa.gov/api/temporal/monthly/point"

        params = {
            "parameters": "T2M,PRECTOTCORR,RH2M,WS2M",
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": "2026",
            "end": "2026",
            "format": "JSON"
        }

        r = requests.get(url, params=params, timeout=5)

        if r.status_code != 200:
            return fallback, "Fallback"

        d = r.json()["properties"]["parameter"]
        k = f"2026{mois:02d}"

        return [
            float(d["T2M"].get(k, 25)),
            float(d["PRECTOTCORR"].get(k, 10)),
            float(d["RH2M"].get(k, 60)),
            float(d["WS2M"].get(k, 3))
        ], "NASA POWER"

    except:
        return fallback, "Fallback"


# ====================================
# 3. RISQUE UNIQUE (ML + METIER + REGION)
# ====================================
def calcul_risque(region, mois, irrigation, t, pl):

    # =========================
    # ML
    # =========================
    if model_ok:
        try:
            cols = model_rf.feature_names_in_
            X = pd.DataFrame(0, index=[0], columns=cols)

            if "mois" in cols:
                X["mois"] = mois

            region_cols = [c for c in cols if "region_" in c]

            for c in region_cols:
                if region in c:
                    X[c] = 1

            if len(region_cols) > 0 and X[region_cols].sum().sum() == 0:
                X[region_cols[0]] = 1

            ml = model_rf.predict_proba(X)[0][1] * 100

        except:
            ml = 40
    else:
        ml = 40

    # =========================
    # METIER
    # =========================
    region_risk = {
        "Tunis": 5,
        "Nabeul": 10,
        "Bizerte": 8,
        "Beja": 12,
        "Sousse": 6,
        "Monastir": 7,
        "Kairouan": 15,
        "Kebili": 20,
        "Gabes": 18
    }

    metier = 10 + region_risk.get(region, 10)

    if irrigation == "Non":
        metier += 15

    # stress climatique simple (même avec NASA ou fallback)
    if pl < 15:
        metier += 20
    if t > 38:
        metier += 15

    # =========================
    # SCORE UNIQUE
    # =========================
    risk = (0.6 * ml) + (0.4 * metier)

    return max(5, min(95, risk))


# ====================================
# 4. PRIME
# ====================================
def calcul_prime(risk, sup, prod):

    valeur = (sup * 180) + (prod * 35)
    frais = (sup * 12) + (prod * 1.1)

    prime = (risk / 100) * valeur + frais

    return prime, valeur


# ====================================
# 5. UI
# ====================================
st.title("🌾 Assurance Agricole Paramétrique 2026")

col1, col2 = st.columns(2)

with col1:

    region = st.selectbox("Région", [
        "Tunis", "Nabeul", "Bizerte", "Beja",
        "Sousse", "Monastir", "Kairouan", "Kebili", "Gabes"
    ])

    mois = st.selectbox("Mois", list(range(1, 13)))
    sup = st.number_input("Superficie (Ha)", 1, 100, 15)
    prod = st.number_input("Rendement (T)", 1, 100, 60)
    irrigation = st.radio("Irrigation", ["Oui", "Non"])

    btn = st.button("Calculer")


with col2:

    if btn:

        # météo
        (t, pl, hum, vent), source = get_weather(region, mois)

        # risque unique
        risk = calcul_risque(region, mois, irrigation, t, pl)

        # prime
        prime, valeur = calcul_prime(risk, sup, prod)

        # indemnité simple
        indemnité = 0
        if risk > 70:
            indemnité = sup * 8

        # affichage
        st.subheader("📊 Résultat final")

        st.info(f"🌍 Source météo : {source}")
        st.metric("🔥 Score de risque", f"{risk:.2f} %")
        st.success(f"💰 Prime totale : {prime:.2f} DT")

        if indemnité > 0:
            st.error(f"🚨 Indemnité : {indemnité:.2f} DT")
        else:
            st.success("🍏 Aucun sinistre")

        # explication
        with st.expander("📌 Formule"):

            st.markdown(f"""
### 🔹 Risque unique
Risque = 60% ML + 40% expertise métier + climat

### 🔹 Prime
Prime = Risque × Valeur + frais

Valeur = {valeur:.2f} DT

### 🔹 Données météo
Source : {source} (NASA POWER ou fallback local)
""")
