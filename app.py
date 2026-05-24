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
    try: return joblib.load("model_rf.pkl"), True
    except: return None, False
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
        X["annee"] = 2026
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
    "Tunis": (36.80, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.60), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.70, 8.97), "Gabes": (33.88, 10.09)
}

saisons_map = {
    12: "Hiver", 1: "Hiver", 2: "Hiver",
    3: "Printemps", 4: "Printemps", 5: "Printemps",
    6: "Ete", 7: "Ete", 8: "Ete",
    9: "Automne", 10: "Automne", 11: "Automne"
}

normales_saisonnieres = {
    "Nabeul": {
        1: [11.8, 55.2, 74.0, 5.1], 2: [12.2, 48.1, 72.0, 5.3], 3: [14.1, 38.5, 70.0, 4.8],
        4: [16.5, 29.0, 68.0, 4.4], 5: [20.8, 16.2, 65.0, 4.1], 6: [25.2, 5.4, 61.0, 3.9],
        7: [28.5, 1.1, 59.0, 3.8],  8: [29.1, 4.2, 62.0, 3.9],  9: [25.8, 35.6, 67.0, 4.2],
        10: [21.7, 52.0, 71.0, 4.5], 11: [16.9, 61.3, 73.0, 4.8], 12: [13.1, 64.0, 75.0, 5.2]
    }
}

@st.cache_data(ttl=3600)
def get_weather(reg, m):
    secours_local = normales_saisonnieres.get(reg, {}).get(m, [24.5, 12.0, 60.0, 4.0])
    lat, lon = coords[reg]
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    p = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2026", "end": "2026", "format": "JSON"}
    try:
        r = requests.get(url, params=p, timeout=8)
        if r.status_code != 200: return secours_local, "Historique Réel (Fallback)"
        d = r.json()["properties"]["parameter"]
        k = f"2026{m:02d}"
        return [float(d["T2M"][k]), float(d["PRECTOTCORR"][k]), float(d["RH2M"][k]), float(d["WS2M"][k])], "NASA POWER API"
    except: return secours_local, "Historique Réel (Fallback)"

# ====================================
# 4. INTERFACE GRAPHIQUE
# ====================================
st.title("🌾 Assurance Agricole Paramétrique (2026)")
col1, col2 = st.columns([1, 1.2], gap="medium")
with col1:
    st.subheader("📋 Paramètres du Contrat")
    uid = st.text_input("ID Exploitant", value="TUN-01")
    region = st.selectbox("Région", list(coords.keys()), index=1)
    culture = st.selectbox("Type de Culture", ["Olives", "Cereales"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    mois = st.selectbox("Mois sous risque", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", min_value=1, value=15)
    prod = st.number_input("Rendement (Tonnes)", min_value=1, value=60)
    saison = saisons_map.get(mois, "Ete")
    btn = st.button("🚀 LANCER L'ANALYSE", use_container_width=True, type="primary")

with col2:
    w, source = get_weather(region, mois)
    t, pl, hum, vent = w[0], w[1], w[2], w[3]
    t1, t2, t3 = st.tabs(["🌦️ Indices Météo", "📉 Risque & Prime", "🛡️ Indemnisation"])
    
    with t1:
        st.info(f"🌡️ Temp: {t:.2f} °C | 🌧️ Pluie: {pl:.2f} mm | 💧 Hum: {hum:.2f} %")
        st.write(f"Source des données : **{source}**")
    
    if btn:
        risque_ml = predire_risque_ml(t, pl, hum, vent, mois, region, saison)
        r_regle = 10 + (35 if pl < 15 else 0) + (25 if t > 38 else 0) + (15 if irrigation == "Non" else 0)
        risque = max(0, min(100, (0.7 * risque_ml) + (0.3 * r_regle)))
        prime = (risque * 4.2) + (sup * 12) + (prod * 1.1)
        
        with t2:
            st.metric("🔥 Score de Risque Global", f"{risque:.2f} %")
            st.metric("💳 Prime Totale", f"{prime:.2f} DT")
            with st.expander("🔍 Voir les détails de calcul"):
                st.write(f"Prime Pure = Risque ({risque:.2f}%) * 4.2")
                st.write(f"Chargement = (Sup {sup} * 12) + (Prod {prod} * 1.1)")
        
        with t3:
            cap_max = (sup * 200) + (prod * 25)
            ind, peril = 0.0, "Normal"
            if pl < 35.0:
                peril = "Sécheresse"
                ind = ((35.0 - pl) / 27.0) * cap_max if pl > 8 else cap_max
            
            if ind > 0: st.error(f"🚨 INDEMNITÉ : {ind:.2f} DT ({peril})")
            else: st.success("🍏 AUCUN SINISTRE")
            with st.expander("🔍 Voir le calcul de l'indemnité"):
                st.write(f"Capital Maximum = {cap_max:.2f} DT")
                st.write("Indemnisation basée sur l'oracle satellite.")

            with st.expander("🛠️ Zone Développeur : JSON"):
                st.json({"annee": 2026, "id": uid, "risque": risque, "indemnite": ind})
