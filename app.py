import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Assurance Agricole 2026", layout="wide")


# =========================================
# 1. NASA POWER (CORRIGÉ + ROBUSTE)
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

    lat, lon = coords[region]

    url = "https://power.larc.nasa.gov/api/temporal/climatology/point"

    params = {
        "parameters": "T2M,PRECTOTCORR,RH2M,WS2M",
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "format": "JSON"
    }

    r = requests.get(url, params=params, timeout=8)
    d = r.json()["properties"]["parameter"]

    # 🔥 valeurs par mois (TRÈS IMPORTANT)
    return {
        "temp": float(d["T2M"][str(mois)]),
        "pluie": float(d["PRECTOTCORR"][str(mois)]),
        "humidite": float(d["RH2M"][str(mois)]),
        "vent": float(d["WS2M"][str(mois)])
    }


# =========================================
# 2. RISQUE (RÉALISTE + NON LINÉAIRE)
# =========================================
def calcul_risque(data, region, irrigation, culture, mois):

    risk = 12

    # 🌧 pluie (impact fort)
    if data["pluie"] < 8:
        risk += 40
    elif data["pluie"] < 20:
        risk += 25
    else:
        risk += 10

    # 🌡 température
    if data["temp"] > 40:
        risk += 35
    elif data["temp"] > 33:
        risk += 18

    # 💨 vent
    risk += max(0, (data["vent"] - 3) * 5)

    # 🌍 région
    region_map = {
        "Tunis": 5,
        "Nabeul": 10,
        "Bizerte": 8,
        "Beja": 15,
        "Sousse": 7,
        "Monastir": 6,
        "Kairouan": 18,
        "Kebili": 25,
        "Gabes": 20
    }

    risk += region_map.get(region, 10)

    # 💧 irrigation
    if irrigation == "Non":
        risk += 15

    # 🌱 culture
    if culture == "Cereales":
        risk += 8
    else:
        risk += 5

    # 📅 saison été
    if mois in [6,7,8]:
        risk += 10

    return max(5, min(95, risk))


# =========================================
# 3. CAPITAL ASSURÉ
# =========================================
def capital(sup, prod):
    return (sup * 200) + (prod * 45)


# =========================================
# 4. PRIME (FORMULE ASSURANCE SIMPLE)
# =========================================
def prime(risk, cap):
    return (risk / 100) * cap + cap * 0.025


# =========================================
# 5. INDEMNITÉ (LOGIQUE CORRIGÉE)
# =========================================
def indemnité(risk, data, cap):

    # sécheresse
    if data["pluie"] < 7:
        return cap * 0.25

    # risque élevé
    if risk > 80:
        return cap * 0.5

    if risk > 60:
        return cap * 0.3

    return 0


# =========================================
# 6. UI
# =========================================
st.title("🌾 Assurance Agricole Paramétrique 2026")

col1, col2 = st.columns(2)

with col1:

    region = st.selectbox("Région", list({
        "Tunis":1,"Nabeul":1,"Bizerte":1,"Beja":1,
        "Sousse":1,"Monastir":1,"Kairouan":1,"Kebili":1,"Gabes":1
    }.keys()))

    mois = st.selectbox("Mois", list(range(1,13)))
    sup = st.number_input("Superficie", 1, 100, 15)
    prod = st.number_input("Production", 1, 100, 60)
    irrigation = st.radio("Irrigation", ["Oui","Non"])
    culture = st.selectbox("Culture", ["Olives","Cereales"])

    btn = st.button("Calculer")


with col2:

    if btn:

        data = get_weather(region, mois)

        risk = calcul_risque(data, region, irrigation, culture, mois)
        cap = capital(sup, prod)

        pr = prime(risk, cap)
        ind = indemnité(risk, data, cap)

        st.subheader("📊 Résultats")

        st.write("🌡 Température:", round(data["temp"],2))
        st.write("🌧 Pluie:", round(data["pluie"],2))
        st.write("💨 Vent:", round(data["vent"],2))
        st.write("💧 Humidité:", round(data["humidite"],2))

        st.metric("🔥 Risque", f"{risk:.2f}%")
        st.success(f"💰 Prime: {pr:.2f} DT")

        if ind > 0:
            st.error(f"🚨 Indemnité: {ind:.2f} DT")
        else:
            st.success("🍏 Aucun sinistre")

        with st.expander("📌 Formules"):

            st.markdown("""
### 🔹 Risque
Météo NASA POWER + région + culture + irrigation

### 🔹 Prime
Prime = (Risque × Capital) + frais 2.5%

### 🔹 Indemnité
Basée sur sécheresse et seuil de risque élevé
""")
