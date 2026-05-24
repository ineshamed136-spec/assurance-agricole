import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance Agricole Hybride", layout="wide")

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
# 2. MODELE MACHINE LEARNING
# ====================================
def predire_risque_ml(t, pl, hum, vent, mois, reg, sais):

    if not model_ok:
        return 20.0

    try:
        cols = model_rf.feature_names_in_
        X = pd.DataFrame(0, index=[0], columns=cols)

        data = {
            "temp": t,
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
# 3. REGLES METIER (EXPERTISE HUMAIN)
# ====================================
def calcul_regles_metier(pl, t, irrigation):

    score = 10
    exp = ["Base 10%"]

    # sécheresse
    if pl < 15:
        score += 35
        exp.append("Stress hydrique (+35%)")

    # chaleur extrême
    if t > 38:
        score += 25
        exp.append("Stress thermique (+25%)")

    # vulnérabilité exploitation
    if irrigation == "Non":
        score += 15
        exp.append("Non irrigué (+15%)")

    return score, " + ".join(exp)


# ====================================
# 4. COMBINAISON HYBRIDE
# ====================================
def calcul_risque_hybride(ml, metier):

    # 70% data science + 30% expertise métier
    return (0.7 * ml) + (0.3 * metier)


# ====================================
# 5. INTERFACE
# ====================================
st.title("🌾 Assurance Agricole Paramétrique (Modèle Hybride ML + Métier)")

col1, col2 = st.columns(2)

with col1:

    region = st.selectbox("Région", ["Tunis", "Nabeul", "Bizerte", "Beja"])
    mois = st.selectbox("Mois", list(range(1, 13)))
    sup = st.number_input("Superficie (Ha)", 1, 100, 15)
    prod = st.number_input("Rendement (T)", 1, 100, 60)
    irrigation = st.radio("Irrigation", ["Oui", "Non"])

    btn = st.button("Calculer")


# ====================================
# 6. RESULTATS
# ====================================
with col2:

    if btn:

        # météo simulée (simple pour stabilité)
        t, pl, hum, vent = 25, 12, 60, 3

        # saison simple
        saison = "Ete"

        # ============================
        # ML MODEL
        # ============================
        ml = predire_risque_ml(t, pl, hum, vent, mois, region, saison)

        # ============================
        # RULES MODEL
        # ============================
        metier, exp = calcul_regles_metier(pl, t, irrigation)

        # ============================
        # HYBRID RISK
        # ============================
        risque = calcul_risque_hybride(ml, metier)

        # ============================
        # VALUE ASSURED
        # ============================
        valeur_assuree = (sup * 180) + (prod * 35)

        # ============================
        # PURE PREMIUM
        # ============================
        prime_pure = (risque / 100) * valeur_assuree

        # ============================
        # COSTS
        # ============================
        frais = (sup * 12) + (prod * 1.1)

        prime_totale = prime_pure + frais

        # ============================
        # INDICATIVE CLAIM
        # ============================
        indemnité = 0
        if pl < 35:
            indemnité = (35 - pl) * sup * 2

        # ============================
        # DISPLAY
        # ============================
        st.subheader("📊 Résultats du modèle hybride")

        st.success(f"🔥 Risque ML : {ml:.2f}%")
        st.warning(f"🧠 Risque métier : {metier:.2f}%")
        st.info(f"⚖️ Risque hybride : {risque:.2f}%")

        st.success(f"💰 Prime totale : {prime_totale:.2f} DT")

        # indemnité
        if indemnité > 0:
            st.error(f"🚨 Indemnité déclenchée : {indemnité:.2f} DT")
        else:
            st.success("🍏 Aucun sinistre")

        # ============================
        # EXPLICATION JURY
        # ============================
        with st.expander("📌 Explication du modèle hybride"):

            st.markdown(f"""
### 🔹 1. Modèle Machine Learning
Le modèle Random Forest estime la probabilité de sinistre :
→ {ml:.2f}%

---

### 🔹 2. Règles métier (expertise agricole)
{exp}
→ Score métier = {metier:.2f}%

---

### 🔹 3. Fusion hybride
Risque final = 70% ML + 30% métier

---

### 🔹 4. Prime
Prime = Risque × Valeur assurée + frais

Valeur assurée = {valeur_assuree:.2f} DT

---

### 🔹 5. Indemnité paramétrique
Déclenchée si pluie < 35 mm
""")
