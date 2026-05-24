import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance Agricole 2026", layout="wide")

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
# 2. ML CORRIGÉ (IMPORTANT FIX)
# ====================================
def predire_risque_ml(t, pl, hum, vent, mois, reg, sais):

    if not model_ok:
        return 40.0

    try:
        cols = model_rf.feature_names_in_
        X = pd.DataFrame(0, index=[0], columns=cols)

        # =========================
        # VARIABLES NUMERIQUES
        # =========================
        if "temp" in cols:
            X["temp"] = t
        if "précipitations" in cols:
            X["précipitations"] = pl
        if "humidité" in cols:
            X["humidité"] = hum
        if "vent" in cols:
            X["vent"] = vent
        if "mois" in cols:
            X["mois"] = mois

        # =========================
        # REGION (FIX CRITIQUE)
        # =========================
        region_cols = [c for c in cols if "region_" in c]
        for c in region_cols:
            if reg in c:
                X[c] = 1

        # fallback si match absent
        if len(region_cols) > 0 and X[region_cols].sum().sum() == 0:
            X[region_cols[0]] = 1

        # =========================
        # SAISON
        # =========================
        saison_cols = [c for c in cols if "saison_" in c]
        for c in saison_cols:
            if sais in c:
                X[c] = 1

        # =========================
        # PREDICTION
        # =========================
        proba = model_rf.predict_proba(X)[0][1]

        return float(proba * 100)

    except Exception:
        return 40.0


# ====================================
# 3. REGLES METIER
# ====================================
def calcul_regles_metier(pl, t, irrigation):

    score = 10
    exp = ["Base 10%"]

    if pl < 15:
        score += 35
        exp.append("Sécheresse (+35%)")

    if t > 38:
        score += 25
        exp.append("Chaleur extrême (+25%)")

    if irrigation == "Non":
        score += 20
        exp.append("Non irrigué (+20%)")

    return score, " + ".join(exp)


# ====================================
# 4. HYBRIDE
# ====================================
def calcul_risque_hybride(ml, metier):

    # équilibré pour éviter blocage
    return (0.65 * ml) + (0.35 * metier)


# ====================================
# 5. DONNEES
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
        ], "NASA"

    except:
        return [25, 10, 60, 3], "Fallback"


# ====================================
# 7. UI
# ====================================
st.title("🌾 Assurance Agricole Paramétrique 2026")

col1, col2 = st.columns(2)

with col1:
    region = st.selectbox("Région", list(coords.keys()))
    mois = st.selectbox("Mois", list(range(1, 13)))
    sup = st.number_input("Superficie", 1, 100, 15)
    prod = st.number_input("Rendement", 1, 100, 60)
    irrigation = st.radio("Irrigation", ["Oui", "Non"])

    btn = st.button("Calculer")


with col2:

    if btn:

        # météo
        w, source = get_weather(region, mois)

        t, pl, hum, vent = w
        saison = saisons_map[mois]

        # ML
        ml = predire_risque_ml(t, pl, hum, vent, mois, region, saison)

        # métier
        metier, exp = calcul_regles_metier(pl, t, irrigation)

        # hybride
        risque = calcul_risque_hybride(ml, metier)

        # clamp sécurité
        risque = max(5, min(95, risque))

        # valeur assurée
        valeur = (sup * 180) + (prod * 35)

        prime_pure = (risque / 100) * valeur
        frais = (sup * 12) + (prod * 1.1)

        prime = prime_pure + frais

        # indemnité
        indemnité = 0
        if pl < 35:
            indemnité = (35 - pl) * sup * 2

        # affichage
        st.subheader("📊 Résultats")

        st.success(f"🔥 ML : {ml:.2f}%")
        st.warning(f"🧠 Métier : {metier:.2f}%")
        st.info(f"⚖️ Hybride : {risque:.2f}%")

        st.success(f"💰 Prime : {prime:.2f} DT")

        if indemnité > 0:
            st.error(f"🚨 Indemnité : {indemnité:.2f} DT")
        else:
            st.success("🍏 Aucun sinistre")

        # explication
        with st.expander("📌 Formules"):

            st.markdown(f"""
### ML
Score basé sur Random Forest

### Métier
{exp}

### Hybride
65% ML + 35% métier

### Prime
Prime = Risque × Valeur + frais

Valeur = {valeur:.2f} DT
""")
