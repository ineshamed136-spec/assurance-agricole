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
    except:
        return None, False

model_rf, model_charge = load_model()

# ====================================
# 2. FONCTION DE PREDICTION ML SECURISEE
# ====================================
def predire_risque_ml(t, pl, hum, vent, mois, reg, sais):

    if not model_charge:
        return 20.0

    try:
        cm = model_rf.feature_names_in_

        X = pd.DataFrame(0, index=[0], columns=cm)

        X["temp"] = t
        X["précipitations"] = pl
        X["humidité"] = hum
        X["vent"] = vent
        X["mois"] = mois
        X["annee"] = 2025

        if f"region_{reg}" in X.columns:
            X[f"region_{reg}"] = 1

        if f"saison_{sais}" in X.columns:
            X[f"saison_{sais}"] = 1

        return float(model_rf.predict_proba(X)[0][1] * 100)

    except:
        return 20.0

# ====================================
# 3. COORDONNEES, SAISONS & METEO
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
    12: "Hiver",
    1: "Hiver",
    2: "Hiver",
    3: "Printemps",
    4: "Printemps",
    5: "Printemps",
    6: "Ete",
    7: "Ete",
    8: "Ete",
    9: "Automne",
    10: "Automne",
    11: "Automne"
}

normales_saisonnieres = {

    "Nabeul": {
        1: [11.8, 55.2, 74.0, 5.1],
        2: [12.2, 48.1, 72.0, 5.3],
        3: [14.1, 38.5, 70.0, 4.8],
        4: [16.5, 29.0, 68.0, 4.4],
        5: [20.8, 16.2, 65.0, 4.1],
        6: [25.2, 5.4, 61.0, 3.9],
        7: [28.5, 1.1, 59.0, 3.8],
        8: [29.1, 4.2, 62.0, 3.9],
        9: [25.8, 35.6, 67.0, 4.2],
        10: [21.7, 52.0, 71.0, 4.5],
        11: [16.9, 61.3, 73.0, 4.8],
        12: [13.1, 64.0, 75.0, 5.2]
    },

    "Tunis": {
        1: [11.5, 62.0, 76.0, 4.8],
        5: [21.2, 22.4, 66.0, 4.2],
        7: [29.1, 2.5, 57.0, 4.0],
        8: [29.5, 5.1, 59.0, 4.1]
    },

    "Beja": {
        1: [9.8, 95.0, 82.0, 4.5],
        5: [19.5, 38.0, 68.0, 3.9],
        7: [28.2, 2.0, 52.0, 3.7],
        8: [28.6, 4.0, 54.0, 3.8]
    },

    "Kebili": {
        1: [10.2, 12.0, 60.0, 3.8],
        5: [24.8, 6.0, 42.0, 4.9],
        7: [33.5, 0.5, 33.0, 4.6],
        8: [33.1, 1.2, 36.0, 4.4]
    }
}

# ====================================
# 4. RECUPERATION METEO NASA
# ====================================
@st.cache_data(ttl=3600)
def get_weather(reg, m):

    secours_local = normales_saisonnieres.get(
        reg,
        {}
    ).get(
        m,
        [24.5, 12.0, 60.0, 4.0]
    )

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
            return secours_local, "Historique (Fallback)"

        d = r.json()["properties"]["parameter"]

        k = f"2025{m:02d}"

        return [
            float(d["T2M"][k]),
            float(d["PRECTOTCORR"][k]),
            float(d["RH2M"][k]),
            float(d["WS2M"][k])
        ], "NASA POWER API"

    except:
        return secours_local, "Historique (Fallback)"

# ====================================
# 5. INTERFACE PRINCIPALE
# ====================================

st.title("🌾 Assurance Agricole Paramétrique")

if model_charge:
    st.sidebar.success("🔮 Système ML Initialisé")
else:
    st.sidebar.warning("⚙️ Mode Règles Métiers Actif")

col1, col2 = st.columns([1, 1.2], gap="medium")

# ====================================
# 6. PARAMETRES CONTRAT
# ====================================
with col1:

    st.subheader("📋 Paramètres du Contrat")

    uid = st.text_input(
        "ID Exploitant",
        value="TUN-01"
    )

    region = st.selectbox(
        "Région de l'exploitation",
        list(coords.keys()),
        index=1
    )

    culture = st.selectbox(
        "Type de Culture",
        ["Olives", "Cereales"]
    )

    irrigation = st.radio(
        "Système d'Irrigation",
        ["Oui", "Non"],
        horizontal=True
    )

    mois = st.selectbox(
        "Mois sous risque",
        list(range(1, 13)),
        index=7
    )

    sup = st.number_input(
        "Superficie Totale (Ha)",
        min_value=1,
        value=15
    )

    prod = st.number_input(
        "Rendement Estimé (Tonnes)",
        min_value=1,
        value=60
    )

    saison = saisons_map.get(mois, "Ete")

    btn = st.button(
        "🚀 LANCER L'ANALYSE ACTUARIELLE",
        use_container_width=True,
        type="primary"
    )

# ====================================
# 7. RESULTATS
# ====================================
with col2:

    w, source_data = get_weather(region, mois)

    t, pl, hum, vent = w[0], w[1], w[2], w[3]

    t1, t2, t3 = st.tabs([
        "🌦️ Indices Météo",
        "📉 Risque & Tarification",
        "🛡️ Indemnisation Paramétrique"
    ])

    # ====================================
    # ONGLET METEO
    # ====================================
    with t1:

        st.write(
            f"**📍 Région :** {region} | "
            f"**📅 Saison :** {saison}"
        )

        st.info(
            f"🌡️ Température : {t:.2f} °C | "
            f"🌧️ Pluviométrie : {pl:.2f} mm | "
            f"💧 Humidité : {hum:.2f} % | "
            f"💨 Vent : {vent:.2f} m/s"
        )

        if "Fallback" in source_data:

            st.warning(
                f"⚠️ Mode Simulation : "
                f"Données issues des "
                f"**{source_data}** "
                f"(Moyennes réelles 2014-2024)."
            )

        else:

            st.success(
                f"✅ Flux de données en provenance de : "
                f"**{source_data}**"
            )

    # ====================================
    # ANALYSE ACTUARIELLE
    # ====================================
    if btn:

        # ================================
        # SCORE ML
        # ================================
        risque_ml = predire_risque_ml(
            t,
            pl,
            hum,
            vent,
            mois,
            region,
            saison
        )

        # ================================
        # REGLES METIERS
        # ================================
        r_regle = 10

        txt_regle = "Base Standard (10%)"

        if pl < 15:
            r_regle += 35
            txt_regle += " + Stress Hydrique (<15mm : +35%)"

        if t > 38:
            r_regle += 25
            txt_regle += " + Stress Thermique (>38°C : +25%)"

        if irrigation == "Non":
            r_regle += 15
            txt_regle += " + Vulnérabilité Sol (Non irrigué : +15%)"

        # ================================
        # RISQUE HYBRIDE
        # ================================
        risque = max(
            0,
            min(
                100,
                (0.7 * risque_ml) +
                (0.3 * r_regle)
            )
        )

        # ================================
        # VALEUR ASSUREE
        # ================================
        valeur_assuree = (
            (sup * 180) +
            (prod * 35)
        )

        # ================================
        # PRIME PURE
        # ================================
        prime_pure = (
            (risque / 100) *
            valeur_assuree
        )

        # ================================
        # CHARGEMENT
        # ================================
        frais_ch = (
            (sup * 12) +
            (prod * 1.1)
        )

        # ================================
        # PRIME FINALE
        # ================================
        prime = prime_pure + frais_ch

        # ====================================
        # ONGLET TARIFICATION
        # ====================================
        with t2:

            st.subheader("📊 Résultats Actuariels")

            m1, m2 = st.columns(2)

            m1.metric(
                "🔥 Score de Risque Global",
                f"{risque:.2f} %"
            )

            m2.metric(
                "💳 Prime Totale Facturée",
                f"{prime:.2f} DT"
            )

            st.progress(int(risque))

            with st.expander(
                "🔍 Décomposition de la Formule de Tarification"
            ):

                st.markdown(f"""
                * **Modèle de Risque Hybride :**
                `70% Machine Learning + 30% Expertise Métier`

                * **Détail Calcul Métier :**
                {txt_regle} = **{r_regle}%**

                * **Valeur Assurée Agricole :**
                (Superficie × 180 DT)
                + (Rendement × 35 DT)
                = **{valeur_assuree:.2f} DT**

                * **Calcul de la Prime Pure :**
                Risque Global ({risque:.2f}%)
                × Valeur Assurée
                = **{prime_pure:.2f} DT**

                * **Chargement de Frais :**
                (Superficie × 12 DT)
                + (Rendement × 1.1 DT)
                = **{frais_ch:.2f} DT**

                * **Formule Finale :**
                `Prime Totale = Prime Pure + Chargement`

                * **Prime Totale Calculée :**
                **{prime:.2f} DT**
                """)

        # ====================================
        # ONGLET INDEMNISATION
        # ====================================
        with t3:

            st.subheader("🛡️ État du Déclencheur")

            cap_max = (
                (sup * 200) +
                (prod * 25)
            )

            ind = 0.0
            p_rate = 0.0
            peril = "Aucun"

            txt_form = "Aucune action"

            txt_expl = (
                "Les indices climatiques "
                "sont conformes aux normales."
            )

            # ================================
            # SECHERESSE
            # ================================
            if pl < 35.0:

                peril = "Sécheresse"

                if pl <= 8.0:

                    p_rate = 1.0

                    txt_form = (
                        "Forfait Catastrophe "
                        "Intégral (100%)"
                    )

                    txt_expl = (
                        f"Pluviométrie ({pl:.2f} mm) "
                        f"≤ Seuil critique (8 mm)."
                    )

                else:

                    p_rate = (
                        (35.0 - pl) /
                        (35.0 - 8.0)
                    )

                    txt_form = (
                        "Indemnisation "
                        "Linéaire Progressive"
                    )

                    txt_expl = (
                        f"Pluviométrie ({pl:.2f} mm) "
                        f"sous le seuil de confort."
                    )

                ind = p_rate * cap_max

            # ================================
            # CANICULE
            # ================================
            elif t > 39.0:

                peril = "Canicule"

                if t >= 47.0:

                    p_rate = 1.0

                    txt_form = (
                        "Forfait Catastrophe "
                        "Intégral (100%)"
                    )

                    txt_expl = (
                        f"Température ({t:.2f} °C) "
                        f"≥ Limite critique (47 °C)."
                    )

                else:

                    p_rate = (
                        (t - 39.0) /
                        (47.0 - 39.0)
                    )

                    txt_form = (
                        "Indemnisation "
                        "Stress Thermique"
                    )

                    txt_expl = (
                        f"Température ({t:.2f} °C) "
                        f"en zone de flétrissement."
                    )

                ind = p_rate * cap_max

            # ================================
            # AFFICHAGE INDEMNITE
            # ================================
            if ind > 0:

                st.error(
                    f"🚨 INDEMNITÉ DÉCLENCHÉE : "
                    f"{ind:.2f} DT "
                    f"(Événement : {peril})"
                )

            else:

                st.success(
                    "🍏 AUCUN SINISTRE DÉTECTÉ "
                    "(Indemnité : 0.00 DT)"
                )

            with st.expander(
                "🔍 Paramètres du Smart Contract"
            ):

                st.markdown(f"""
                * **Capitaux Maximums Exposés :**
                (Superficie × 200 DT)
                + (Rendement × 25 DT)
                = **{cap_max:.2f} DT**

                * **Règle de Calcul Indiciaire :**
                `{txt_form}`

                * **Justification Biologique :**
                {txt_expl}

                * *Note Académique :*
                L'indemnité est pilotée par
                les indices climatiques NASA,
                sans expertise physique terrain.
                """)

            # ====================================
            # TELEGRAM
            # ====================================
            tok = st.secrets.get("BOT_TOKEN", "")
            cid = st.secrets.get("CHAT_ID", "")

            if tok and cid:

                txt = (
                    f"🌾 ASSURANCE\n"
                    f"👤 ID: {uid}\n"
                    f"📈 Risque: {risque:.2f}%\n"
                    f"💰 Prime: {prime:.2f} DT\n"
                    f"🛡️ Indemnité: {ind:.2f} DT"
                )

                try:

                    requests.post(
                        f"https://api.telegram.org/bot{tok}/sendMessage",
                        data={
                            "chat_id": cid,
                            "text": txt
                        },
                        timeout=3
                    )

                except:
                    pass
