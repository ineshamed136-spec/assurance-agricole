import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(
    page_title="Assurance",
    layout="wide"
)

# ==================================
# 1. CHARGEMENT DU MODELE ML
# ==================================
@st.cache_resource
def load_model():
    try:
        # Correction ici : chargement explicite de model.pkl
        m = joblib.load("model.pkl")
        return m, True
    except:
        return None, False

model_rf, model_charge = load_model()

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
# 2. COLLECTE DES DONNEES (NASA)
# ==================================
@st.cache_data(ttl=3600)
def get_weather(reg, m):
    lat, lon = coords[reg]
    url = (
        "https://power.larc.nasa.gov"
        "/api/temporal/monthly/point"
    )
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
        r = requests.get(
            url,
            params=p,
            timeout=8
        )
        if r.status_code != 200:
            return [24.5, 12.0, 60.0, 4.0]
        res = r.json()
        d = res["properties"]["parameter"]
        k = f"2025{m:02d}"
        v_t = float(d["T2M"][k])
        v_p = float(d["PRECTOTCORR"][k])
        v_h = float(d["RH2M"][k])
        v_w = float(d["WS2M"][k])
        return [v_t, v_p, v_h, v_w]
    except:
        return [24.5, 12.0, 60.0, 4.0]

# ==================================
# 3. INTERFACE UTILISATEUR
# ==================================
st.title("🌾 Assurance Agricole")

col1, col2 = st.columns(
    [1, 1.2],
    gap="medium"
)

with col1:
    st.subheader("Contrat")
    uid = st.text_input(
        "ID Exploitant",
        value="TUN-01"
    )
    region = st.selectbox(
        "Region",
        list(coords.keys()),
        index=1
    )
    culture = st.selectbox(
        "Culture",
        ["Olives", "Cereales"]
    )
    irrigation = st.radio(
        "Irrigation",
        ["Oui", "Non"],
        horizontal=True
    )
    mois = st.selectbox(
        "Mois (1-12)",
        list(range(1, 13)),
        index=4
    )
    sup = st.number_input(
        "Superficie (Ha)",
        min_value=1,
        value=15
    )
    prod = st.number_input(
        "Rendement (T)",
        min_value=1,
        value=60
    )

    if mois in [12, 1, 2]:
        saison = "Hiver"
    elif mois in [3, 4, 5]:
        saison = "Printemps"
    elif mois in [6, 7, 8]:
        saison = "Ete"
    else:
        saison = "Automne"

    btn = st.button(
        "🚀 ANALYSER",
        use_container_width=True,
        type="primary"
    )

with col2:
    w = get_weather(region, mois)
    t, pl, hum, vent = w[0], w[1], w[2], w[3]

    tabs = ["🌦️ Météo", "📉 Risque", "🛡️ Payout"]
    t1, t2, t3 = st.tabs(tabs)

    with t1:
        st.write(f"**Région :** {region}")
        st.write(f"**Saison :** {saison}")
        st.info(f"🌡️ Température : {t:.1f}°C")
        st.info(f"🌧️ Pluviométrie : {pl:.1f} mm")
        st.info(f"💧 Humidité : {hum:.1f} %")
        st.info(f"💨 Vitesse Vent : {vent:.1f} m/s")

    if btn:
        # --- MOTEUR 1 : MACHINE LEARNING ---
        risque_ml = 20.0
        if model_charge:
            try:
                f_in = model_rf.feature_names_in_
                X = pd.DataFrame(
                    0,
                    index=[0],
                    columns=f_in
                )
                X["temp"] = t
                X["précipitations"] = pl
                X["humidité"] = hum
                X["vent"] = vent
                X["mois"] = mois
                X["annee"] = 2025

                c_reg = f"region_{region}"
                c_sais = f"saison_{saison}"

                if c_reg in X.columns:
                    X[c_reg] = 1
                if c_sais in X.columns:
                    X[c_sais] = 1

                p = model_rf.predict_proba(X)
                risque_ml = p[0][1] * 100
            except:
                calc = t * 2.2
                risque_ml = max(10.0, min(90.0, calc))
        else:
            calc = t * 2.2
            risque_ml = max(10.0, min(90.0, calc))

        # --- MOTEUR 2 : REGLES DE METIER ---
        r_regle = 10
        if pl < 35:
            r_regle += int((35 - pl) * 2.0)
        if t > 30:
            r_regle += int((t - 30) * 3.5)
        if irrigation == "Non":
            r_regle += 15

        # --- FUSION DES DEUX MOTEURS (70% ML / 30% Métier) ---
        v1 = 0.7 * risque_ml
        v2 = 0.3 * r_regle
        risque = max(0, min(100, v1 + v2))
        
        # Tarification Actuarielle
        p1 = risque * 4.2
        p2 = sup * 12
        p3 = prod * 1.1
        prime = p1 + p2 + p3

        with t2:
            st.markdown("### Évaluation Hybride")
            if model_charge:
                st.success("🤖 Modèle model.pkl chargé !")
            else:
                st.warning("⚠️ Fichier model.pkl introuvable")
                
            st.write(f"📊 Risque ML pur : {risque_ml:.1f}%")
            st.write(f"📜 Risque Métier pur : {r_regle:.1f}%")
            st.divider()
            st.metric(
                "🔥 Taux Global Fusionné",
                f"{risque:.1f} %"
            )
            st.metric(
                "💳 Prime Finale",
                f"{prime:.1f} DT"
            )
            st.progress(int(risque))

        with t3:
            st.markdown("### Indemnité")
            c1 = sup * 200
            c2 = prod * 25
            cap_max = c1 + c2
            ind = 0.0
            peril = "Normal"

            if pl < 35.0:
                peril = "Sécheresse"
                if pl <= 8.0:
                    p_rate = 1.0
                else:
                    p_rate = (35.0 - pl) / 27.0
                ind = p_rate * cap_max
            elif t > 39.0:
                peril = "Canicule"
                if t >= 47.0:
                    p_rate = 1.0
                else:
                    p_rate = (t - 39.0) / 8.0
                ind = p_rate * cap_max

            if ind > 0:
                st.error(
                    f"💰 {ind:.1f} DT ({peril})"
                )
            else:
                st.success("💰 0.00 DT")

            # --- MODULE TELEGRAM ---
            tok = st.secrets.get("BOT_TOKEN", "")
            cid = st.secrets.get("CHAT_ID", "")
            if tok and cid:
                tg = (
                    f"https://api.telegram.org"
                    f"/bot{tok}/sendMessage"
                )
                txt = (
                    f"🌾 {uid} | "
                    f"Risque: {risque:.1f}%"
                )
                pay = {
                    "chat_id": cid,
                    "text": txt
                }
                try:
                    requests.post(
                        tg,
                        data=pay,
                        timeout=3
                    )
                except:
                    pass
