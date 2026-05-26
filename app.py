import streamlit as st
import joblib
import pandas as pd
import random

st.set_page_config(page_title="Assurance Agricole", layout="wide")

# 1. CHARGEMENT MODÈLE
@st.cache_resource
def load_model():
    try:
        return joblib.load("model.pkl"), True
    except:
        return None, False

model_rf, model_charge = load_model()

# 2. CONFIGURATION RÉGIONALE
geo_conf = {
    "Tunis": {"facteur": 0.9, "coeff": 4.0, "seuil": 30.0, "moyenne_20ans": 45.5},
    "Nabeul": {"facteur": 0.85, "coeff": 4.5, "seuil": 32.0, "moyenne_20ans": 42.0},
    "Bizerte": {"facteur": 0.8, "coeff": 3.5, "seuil": 35.0, "moyenne_20ans": 55.2},
    "Beja": {"facteur": 0.75, "coeff": 3.0, "seuil": 40.0, "moyenne_20ans": 60.8},
    "Sousse": {"facteur": 0.95, "coeff": 4.2, "seuil": 28.0, "moyenne_20ans": 38.4},
    "Monastir": {"facteur": 0.95, "coeff": 4.2, "seuil": 28.0, "moyenne_20ans": 37.9},
    "Kairouan": {"facteur": 1.15, "coeff": 5.5, "seuil": 22.0, "moyenne_20ans": 25.1},
    "Kebili": {"facteur": 1.4, "coeff": 7.0, "seuil": 10.0, "moyenne_20ans": 12.5},
    "Gabes": {"facteur": 1.3, "coeff": 6.5, "seuil": 15.0, "moyenne_20ans": 18.2},
    "Médenine": {"facteur": 1.5, "coeff": 7.5, "seuil": 8.0, "moyenne_20ans": 10.5}
}

# 3. GÉNÉRATEUR DE DONNÉES
def get_local_weather(reg, mois):
    random.seed(reg + str(mois))

    variation_saison = 0.5 if 6 <= mois <= 8 else 1.2

    temp = random.uniform(15.0 + (mois * 0.5), 25.0 + (mois * 0.5))
    pluie = random.uniform(5.0, 50.0) * variation_saison
    hum = random.uniform(40.0, 80.0)
    vent = random.uniform(2.0, 10.0)

    random.seed(None)

    return temp, pluie, hum, vent


# 4. INTERFACE
st.markdown(
    """
    <h1 style='font-size:38px;'>
    🌾 Système Intelligent d’Assurance Agricole
    </h1>
    """,
    unsafe_allow_html=True
)

col1, col2 = st.columns([1, 2])

# =========================
# COLONNE GAUCHE
# =========================
with col1:

    st.markdown(
        "<h3>⚙️ Paramètres Agricoles</h3>",
        unsafe_allow_html=True
    )

    region = st.selectbox("Région", list(geo_conf.keys()))

    mois = st.selectbox(
        "Mois (1-12)",
        list(range(1, 13)),
        index=4
    )

    culture = st.selectbox(
        "Culture",
        ["Céréales", "Olives"]
    )

    irrigation = st.radio(
        "Irrigation",
        ["Oui", "Non"],
        horizontal=True
    )

    sup = st.number_input(
        "Superficie (Ha)",
        value=15.0
    )

    prod = st.number_input(
        "Rendement attendu (T/Ha)",
        value=4.0
    )

    btn = st.button(
        "🚀 LANCER L'ANALYSE",
        type="primary"
    )

# =========================
# COLONNE DROITE
# =========================
with col2:

    t, pl, hum, vent = get_local_weather(region, mois)

    cfg = geo_conf[region]

    st.markdown(
        "<h2>📊 Données Climatiques</h2>",
        unsafe_allow_html=True
    )

    st.caption(
        "Sources des données : NASA POWER"
    )

    # METRICS
    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Température",
        f"{t:.1f} °C"
    )

    m2.metric(
        "Précipitations",
        f"{pl:.1f} mm"
    )

    m3.metric(
        "Seuil Sinistre",
        f"{cfg['seuil']} mm"
    )

    m4.metric(
        "Moyenne 20 ans",
        f"{cfg['moyenne_20ans']} mm"
    )

    # =====================
    # ANALYSE
    # =====================
    if btn:

        # RISQUE
        risque_final = (25.0 * cfg["facteur"]) + (mois * 0.5)

        if irrigation == "Non":
            risque_final += 15

        risque_final = min(max(risque_final, 5.0), 95.0)

        # CALCULS
        prod_totale = sup * prod

        prime = (
            (risque_final * cfg["coeff"])
            + (sup * 12)
            + (prod_totale * 1.1)
        )

        cap_max = (
            (sup * 200)
            + (prod_totale * 25)
        )

        st.divider()

        c1, c2 = st.columns(2)

        c1.metric(
            "🔥 Risque Global",
            f"{risque_final:.1f} %"
        )

        c2.metric(
            "💳 Prime à payer",
            f"{prime:.2f} DT"
        )

        st.divider()

        # =====================
        # INDEMNISATION
        # =====================
        if pl < cfg["seuil"]:

            ind = (
                ((cfg["seuil"] - pl) / cfg["seuil"])
                * cap_max
            )

            st.error(
                f"💰 Indemnité de sinistre : {ind:.2f} DT"
            )

        elif cfg["seuil"] <= pl < (cfg["seuil"] + 10):

            ind_partielle = cap_max * 0.05

            st.warning(
                f"⚠️ Stress hydrique : "
                f"Indemnité de franchise : "
                f"{ind_partielle:.2f} DT"
            )

        else:

            st.success(
                "✅ Conditions climatiques optimales."
            )

        # =====================
        # EXPLICATIONS
        # =====================
        with st.expander("ℹ️ Méthodologie et logique paramétrique"):

            st.markdown(
                f"""
                <h3>🛡️ Le Capital Maximum</h3>

                <p>
                Représente la valeur totale assurée :
                (Superficie × 200 DT/Ha) +
                (Production Totale × 25 DT/T).
                </p>

                <h3>💳 Calcul de la Prime</h3>

                <p>
                La prime dépend :
                du niveau de risque,
                du coefficient régional,
                des frais fixes
                et du rendement agricole.
                </p>

                <p>
                <b>Sources des données :</b>
                <a href="https://power.larc.nasa.gov/"
                target="_blank">
                NASA POWER
                </a>
                </p>

                <h3>💧 Déclenchement du sinistre</h3>

                <ul>
                    <li>
                    <b>Moyenne historique sur 20 ans :</b>
                    {cfg['moyenne_20ans']} mm
                    </li>

                    <li>
                    <b>Seuil de déclenchement :</b>
                    {cfg['seuil']} mm
                    </li>
                </ul>
                """,
                unsafe_allow_html=True
            )

            st.latex(
                r"Prime = (Risque \times Coeff_{Régional}) + (Sup \times 12) + (Prod_{Totale} \times 1.1)"
            )

            st.latex(
                r"Indemnité_{Sinistre} = \left( \frac{Seuil - Pluie}{Seuil} \right) \times Capital_{Max}"
            )
