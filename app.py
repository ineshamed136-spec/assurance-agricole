import streamlit as st
import joblib
import pandas as pd
import requests
import numpy as np
import os

st.set_page_config(
    page_title="Assurance Agricole",
    layout="wide"
)

# ==================================
# 1. CHARGEMENT DU MODELE (FIXÉ)
# ==================================
@st.cache_resource
def load_model():
    model_path = os.path.join(os.path.dirname(__file__), "model.pkl")

    if os.path.exists(model_path):
        model = joblib.load(model_path)
        return model, True
    else:
        return None, False

model_rf, model_charge = load_model()

# Debug (utile)
st.write("📂 Fichiers présents :", os.listdir())

# ==================================
# 2. COORDONNÉES
# ==================================
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

# ==================================
# 3. MÉTÉO NASA
# ==================================
@st.cache_data(ttl=3600)
def get_weather(reg, m):
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

    try:
        r = requests.get(url, params=params, timeout=8)

        if r.status_code != 200:
            return [24.5, 12.0, 60.0, 4.0]

        res = r.json()["properties"]["parameter"]
        key = f"2025{m:02d}"

        return [
            float(res["T2M"][key]),
            float(res["PRECTOTCORR"][key]),
            float(res["RH2M"][key]),
            float(res["WS2M"][key])
        ]

    except:
        return [24.5, 12.0, 60.0, 4.0]

# ==================================
# 4. INTERFACE
# ==================================
st.title("🌾 Assurance Agricole - Prédiction des Sinistres")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("Contrat")

    uid = st.text_input("ID Exploitant", "TUN-01")
    region = st.selectbox("Région", list(coords.keys()))
    culture = st.selectbox("Culture", ["Olives", "Céréales"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)

    mois = st.selectbox("Mois", list(range(1, 13)))
    sup = st.number_input("Superficie (Ha)", 1, value=15)
    prod = st.number_input("Rendement (T)", 1, value=60)

    saison = (
        "Hiver" if mois in [12,1,2] else
        "Printemps" if mois in [3,4,5] else
        "Été" if mois in [6,7,8] else
        "Automne"
    )

    btn = st.button("🚀 ANALYSER", type="primary", use_container_width=True)

with col2:
    t, pl, hum, vent = get_weather(region, mois)

    tab1, tab2, tab3 = st.tabs(["🌦️ Météo", "📉 Risque", "🛡️ Indemnité"])

    with tab1:
        st.info(f"Température: {t:.1f}°C")
        st.info(f"Pluie: {pl:.1f} mm")
        st.info(f"Humidité: {hum:.1f}%")
        st.info(f"Vent: {vent:.1f} m/s")

    # ==================================
    # 5. ANALYSE
    # ==================================
    if btn:

        # ---------------- ML ----------------
        if model_charge and model_rf is not None:
            try:
                f_in = model_rf.feature_names_in_

                X = pd.DataFrame(0, index=[0], columns=f_in)

                X["temp"] = t
                X["précipitations"] = pl
                X["humidité"] = hum
                X["vent"] = vent
                X["mois"] = mois
                X["annee"] = 2025

                col_reg = f"region_{region}"
                col_saison = f"saison_{saison}"

                if col_reg in X.columns:
                    X[col_reg] = 1
                if col_saison in X.columns:
                    X[col_saison] = 1

                proba = model_rf.predict_proba(X)[0][1]
                risque_ml = proba * 100

            except:
                risque_ml = min(90, max(10, t * 2))

        else:
            risque_ml = min(90, max(10, t * 2))

        # ---------------- RULES ----------------
        r_regle = 10
        if pl < 35:
            r_regle += int((35 - pl) * 2)
        if t > 30:
            r_regle += int((t - 30) * 3.5)
        if irrigation == "Non":
            r_regle += 15

        # ---------------- FUSION ----------------
        risque = 0.7 * risque_ml + 0.3 * r_regle
        risque = max(0, min(100, risque))

        prime = (risque * 4.2) + (sup * 12) + (prod * 1.1)

        # ==================================
        # 6. RESULTATS
        # ==================================
        with tab2:
            if model_charge:
                st.success("✔ modèle model.pkl chargé")
            else:
                st.warning("⚠ modèle non trouvé")

            st.metric("Risque ML", f"{risque_ml:.1f}%")
            st.metric("Risque global", f"{risque:.1f}%")
            st.metric("Prime", f"{prime:.1f} DT")
            st.progress(int(risque))

        # ==================================
        # 7. INDEMNITÉ
        # ==================================
        with tab3:
            cap = sup * 200 + prod * 25
            indemnité = 0

            if pl < 35:
                indemnité = ((35 - pl) / 35) * cap
            elif t > 39:
                indemnité = ((t - 39) / 10) * cap

            st.write(f"Indemnité: {indemnité:.1f} DT")

        # ==================================
        # 8. TELEGRAM
        # ==================================
        token = st.secrets.get("BOT_TOKEN", "")
        chat_id = st.secrets.get("CHAT_ID", "")

        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, data={
                "chat_id": chat_id,
                "text": f"{uid} | Risque: {risque:.1f}%"
            })
