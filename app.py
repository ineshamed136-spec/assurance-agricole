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
# 2. PREDICTION ML ROBUSTE (2026 FIX)
# ====================================
def predire_risque_ml(t, pl, hum, vent, mois, reg, sais):

    if not model_ok:
        return 20.0

    try:
        cols = model_rf.feature_names_in_
        X = pd.DataFrame(0, index=[0], columns=cols)

        # =========================
        # FEATURES NUMERIQUES
        # =========================
        features = {
            "temp": t,
            "temperature": t,
            "précipitations": pl,
            "precipitations": pl,
            "humidité": hum,
            "humidite": hum,
            "vent": vent,
            "mois": mois,
            "annee": 2026
        }

        for c in cols:
            if c in features:
                X[c] = features[c]

        # =========================
        # REGION (FIX IMPORTANT)
        # =========================
        region_col = f"region_{reg}"

        if region_col in cols:
            X[region_col] = 1
        else:
            # fallback intelligent (évite blocage 27%)
            region_cols = [c for c in cols if "region" in c]
            if region_cols:
                X[region_cols[0]] = 1

        # =========================
        # SAISON
        # =========================
        saison_col = f"saison_{sais}"

        if saison_col in cols:
            X[saison_col] = 1

        # =========================
        # PREDICTION
        # =========================
        proba = model_rf.predict_proba(X)[0][1]

        return float(proba * 100)

    except Exception as e:
        st.error(f"Erreur ML: {e}")
        return 20.0


# ====================================
# 3. REGLES METIER (EXPERT AGRICOLE)
# ====================================
def calcul_regles_metier(pl, t, irrigation):

    score = 10
    exp = ["Base 10%"]

    if pl < 15:
        score += 35
        exp.append("Stress hydrique (+35%)")

    if t > 38:
        score += 25
        exp.append("Stress thermique (+25%)")

    if irrigation == "Non":
        score += 15
        exp.append("Exploitation non irriguée (+15%)")

    return score, " + ".join(exp)


# ====================================
# 4. FUSION HYBRIDE
# ====================================
def calcul_risque_hybride(ml, metier):

    return (0.7 * ml) + (0.3 * metier)


# ====================================
# 5. DONNEES REGION
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
# 6. METEO SAFE
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
            "start": "2026",
            "end": "2026",
            "format": "JSON"
        }

        r = requests.get(url, params=params, timeout=8)

        if r.status_code != 200:
            return [25, 10, 60, 3], "Fallback"

        d = r.json()["properties"]["parameter"]
        k = f"2026{m:02d}"

        return [
            float(d["T2M"][k]),
            float(d["PRECTOTCORR"][k]),
            float(d["RH2M"][k]),
            float(d["WS2M"][k])
        ], "NASA POWER"

    except:
        return [25, 10, 60, 3], "Fallback"


# ====================================
# 7. INTERFACE
# ====================================
st.title("🌾 Assurance Agricole Paramétrique 2026 (Hybride ML + Métier)")

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

        # =========================
        # METEO
        # =========================
        w, source = get_weather(region, mois)

        if not isinstance(w, list) or len(w) != 4:
            w = [25, 10, 60, 3]

        t, pl, hum, vent = w
        saison = saisons_map[mois]

        # =========================
        # ML
        # =========================
        ml = predire_risque_ml(t, pl, hum, vent, mois, region, saison)

        # =========================
        # METIER
        # =========================
        metier, exp = calcul_regles_metier(pl, t, irrigation)

        # =========================
        # HYBRIDE
        # =========================
        risque = calcul_risque_hybride(ml, metier)

        # =========================
        # VALEUR ASSUREE
        # =========================
        valeur = (sup * 180) + (prod * 35)

        # =========================
        # PRIME
        # =========================
        prime_pure = (risque / 100) * valeur
        frais = (sup * 12) + (prod * 1.1)
        prime_totale = prime_pure + frais

        # =========================
        # INDEMNITE
        # =========================
        indemnité = 0
        if pl < 35:
            indemnité = (35 - pl) * sup * 2

        # =========================
        # AFFICHAGE
        # =========================
        st.subheader("📊 Résultats 2026")

        st.success(f"🔥 Risque ML : {ml:.2f}%")
        st.warning(f"🧠 Risque métier : {metier:.2f}%")
        st.info(f"⚖️ Risque hybride : {risque:.2f}%")

        st.success(f"💰 Prime totale : {prime_totale:.2f} DT")

        if indemnité > 0:
            st.error(f"🚨 Indemnité : {indemnité:.2f} DT")
        else:
            st.success("🍏 Aucun sinistre")

        # =========================
        # FORMULES EXPLICATIVES
        # =========================
        with st.expander("📌 Formules du modèle hybride"):

            st.markdown(f"""
### 🔹 1. Modèle ML
Prédit le risque basé sur les données climatiques historiques.

### 🔹 2. Modèle métier
{exp}

### 🔹 3. Fusion hybride
Risque = 70% ML + 30% Métier

### 🔹 4. Prime
Prime = Risque × Valeur assurée + frais

Valeur = {valeur:.2f} DT

### 🔹 5. Indemnité
Déclenchée si pluie < 35 mm
""")
