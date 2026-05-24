import streamlit as st
import requests
import pandas as pd
import json

st.set_page_config(page_title="Assurance Agricole 2026", layout="wide")


# =========================================
# 1. NASA POWER DATA
# =========================================
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

        r = requests.get(url, params=params, timeout=6)
        d = r.json()["properties"]["parameter"]

        key = f"2026{mois:02d}"

        return {
            "temp": float(d["T2M"].get(key, 25)),
            "pluie": float(d["PRECTOTCORR"].get(key, 10)),
            "humidite": float(d["RH2M"].get(key, 60)),
            "vent": float(d["WS2M"].get(key, 3))
        }

    except:
        return {"temp": 25, "pluie": 10, "humidite": 60, "vent": 3}


# =========================================
# 2. RISQUE (ML + METEO + REGION)
# =========================================
def calcul_risque(data, region, irrigation, culture):

    base = 10

    # 🌧️ météo (NASA)
    if data["pluie"] < 15:
        base += 30
    if data["temp"] > 38:
        base += 25
    if data["vent"] > 6:
        base += 10

    # 🌍 région
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

    base += region_risk.get(region, 10)

    # 💧 irrigation
    if irrigation == "Non":
        base += 15

    # 🌱 culture
    if culture == "Cereales":
        base += 5
    else:
        base += 3

    return max(5, min(95, base))


# =========================================
# 3. CAPITAL ASSURE
# =========================================
def capital_assure(superficie, production):

    return (superficie * 200) + (production * 50)


# =========================================
# 4. PRIME ACTUARIELLE (FORMULE REALISTE)
# =========================================
def calcul_prime(risque, capital):

    # ✔ formule assurance réelle simplifiée
    pure_premium = (risque / 100) * capital

    frais = capital * 0.02   # 2% frais admin

    return pure_premium + frais


# =========================================
# 5. INDEMNITE PARAMETRIQUE
# =========================================
def calcul_indemnité(risque, data, capital):

    trigger = 35

    if data["pluie"] < trigger:
        return capital * (trigger - data["pluie"]) / trigger

    if risque > 75:
        return capital * 0.4

    return 0


# =========================================
# 6. INTERFACE (COMPACTE SANS SCROLL)
# =========================================
st.title("🌾 Assurance Agricole Paramétrique 2026")

col1, col2 = st.columns(2)

with col1:

    region = st.selectbox("Région", ["Tunis","Nabeul","Bizerte","Beja","Sousse","Monastir","Kairouan","Kebili","Gabes"])
    mois = st.selectbox("Mois", list(range(1,13)))

    superficie = st.number_input("Superficie (Ha)", 1, 100, 15)
    production = st.number_input("Production (T)", 1, 100, 60)

    irrigation = st.radio("Irrigation", ["Oui","Non"])
    culture = st.selectbox("Culture", ["Olives","Cereales"])

    btn = st.button("Calculer")


with col2:

    if btn:

        # météo NASA
        data = get_weather(region, mois)

        # risque
        risque = calcul_risque(data, region, irrigation, culture)

        # capital
        capital = capital_assure(superficie, production)

        # prime
        prime = calcul_prime(risque, capital)

        # indemnité
        indemnité = calcul_indemnité(risque, data, capital)

        # =========================================
        # RESULTAT
        # =========================================
        st.subheader("📊 Résultats")

        st.success(f"🌡 Température: {data['temp']:.1f} °C")
        st.success(f"🌧 Pluie: {data['pluie']:.1f} mm")
        st.success(f"💧 Humidité: {data['humidite']:.1f}%")
        st.success(f"💨 Vent: {data['vent']:.1f} m/s")

        st.metric("🔥 Risque global", f"{risque:.2f} %")
        st.success(f"💰 Prime totale: {prime:.2f} DT")

        if indemnité > 0:
            st.error(f"🚨 Indemnité: {indemnité:.2f} DT")
        else:
            st.success("🍏 Aucun sinistre")

        # =========================================
        # EXPLICATION FORMULE
        # =========================================
        with st.expander("📌 Formules utilisées"):

            st.markdown("""
### 🔹 1. Risque
Risque = météo (NASA POWER) + région + culture + irrigation

### 🔹 2. Capital assuré
Capital = (Superficie × 200) + (Production × 50)

### 🔹 3. Prime (formule assurance réelle)
Prime = (Risque × Capital) + 2% frais

### 🔹 4. Indemnité
Indemnité = fonction de la sécheresse ou du risque élevé

✔ logique paramétrique agricole
✔ basée sur indices climatiques
""")

        # =========================================
        # EXPORT JSON
        # =========================================
        result = {
            "region": region,
            "mois": mois,
            "climat": data,
            "risque": risque,
            "capital": capital,
            "prime": prime,
            "indemnité": indemnité
        }

        st.download_button(
            "📥 Télécharger JSON",
            data=json.dumps(result, indent=4),
            file_name="resultat_assurance_2026.json"
        )
