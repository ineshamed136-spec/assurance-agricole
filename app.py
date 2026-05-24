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

# Base de données des normales saisonnières historiques (2014-2024) par Région et par Mois
# Structure : [Température Moyenne (°C), Précipitations (mm), Humidité (%), Vent (m/s)]
normales_saisonnieres = {
    "Nabeul": {
        1: [11.8, 55.2, 74.0, 5.1], 2: [12.2, 48.1, 72.0, 5.3], 3: [14.1, 38.5, 70.0, 4.8],
        4: [16.5, 29.0, 68.0, 4.4], 5: [20.8, 16.2, 65.0, 4.1], 6: [25.2, 5.4, 61.0, 3.9],
        7: [28.5, 1.1, 59.0, 3.8],  8: [29.1, 4.2, 62.0, 3.9],  9: [25.8, 35.6, 67.0, 4.2],
        10: [21.7, 52.0, 71.0, 4.5], 11: [16.9, 61.3, 73.0, 4.8], 12: [13.1, 64.0, 75.0, 5.2]
    },
    "Tunis": {
        1: [11.5, 62.0, 76.0, 4.8], 5: [21.2, 22.4, 66.0, 4.2], 7: [29.1, 2.5, 57.0, 4.0],
        8: [29.5, 5.1, 59.0, 4.1]
    },
    "Beja": {
        1: [9.8, 95.0, 82.0, 4.5], 5: [19.5, 38.0, 68.0, 3.9], 7: [28.2, 2.0, 52.0, 3.7],
        8: [28.6, 4.0, 54.0, 3.8]
    },
    "Kebili": {
        1: [10.2, 12.0, 60.0, 3.8], 5: [24.8, 6.0, 42.0, 4.9], 7: [33.5, 0.5, 33.0, 4.6],
        8: [33.1, 1.2, 36.0, 4.4]
    }
}

@st.cache_data(ttl=3600)
def get_weather(reg, m):
    # Récupération du secours localisé (Fallback historique) spécifique à la région et au mois
    # Si la combinaison n'est pas encore saisie dans le dictionnaire, une moyenne globale tunisienne est appliquée
    secours_local = normales_saisonnieres.get(reg, {}).get(m, [24.5, 12.0, 60.0, 4.0])
    
    lat, lon = coords[reg]
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    p = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2025", "end": "2025", "format": "JSON"}
    try:
        r = requests.get(url, params=p, timeout=8)
        if r.status_code != 200: 
            return secours_local
        d = r.json()["properties"]["parameter"]
        k = f"2025{m:02d}"
        return [float(d["T2M"][k]), float(d["PRECTOTCORR"][k]), float(d["RH2M"][k]), float(d["WS2M"][k])]
    except: 
        return secours_local

# ====================================
# 4. INTERFACE GRAPHIQUE
# ====================================
st.title("🌾 Assurance Agricole Paramétrique")
if model_charge: st.sidebar.success("ML Actif")
else: st.sidebar.warning("Mode Regles Metiers")

col1, col2 = st.columns([1, 1.2], gap="medium")
with col1:
    st.subheader("Contrat")
    uid = st.text_input("ID Exploitant", value="TUN-01")
    region = st.selectbox("Region", list(coords.keys()), index=1)
    culture = st.selectbox("Culture", ["Olives", "Cereales"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=7)
    sup = st.number_input("Superficie (Ha)", min_value=1, value=15)
    prod = st.number_input("Rendement (T)", min_value=1, value=60)
    
    saison = saisons_map.get(mois, "Ete")
    btn = st.button("🚀 ANALYSER", use_container_width=True, type="primary")

with col2:
    w = get_weather(region, mois)
    t, pl, hum, vent = w[0], w[1], w[2], w[3]
    t1, t2, t3 = st.tabs(["🌦️ Meteo", "📉 Risque & Prime", "🛡️ Indemnite"])
    
    with t1:
        st.write(f"**Region :** {region} | **Saison :** {saison}")
        st.info(f"🌡️ Temp: {t:.2f} °C | 🌧️ Pluie: {pl:.2f} mm | 💧 Hum: {hum:.2f} % | 💨 Vent: {vent:.2f} m/s")
    
    if btn:
        risque_ml = predire_risque_ml(t, pl, hum, vent, mois, region, saison)

        r_regle = 10
        txt_regle = "Base 10%"
        if pl < 15: 
            r_regle += 35
            txt_regle += " + 35% (Pluie < 15mm)"
        if t > 38: 
            r_regle += 25
            txt_regle += " + 25% (Temp > 38C)"
        if irrigation == "Non": 
            r_regle += 15
            txt_regle += " + 15% (Pas d'irrigation)"
        
        risque = max(0, min(100, (0.7 * risque_ml) + (0.3 * r_regle)))
        prime_pure = risque * 4.2
        frais_ch = (sup * 12) + (prod * 1.1)
        prime = prime_pure + frais_ch
        
        with t2:
            st.write("### Evaluation Actuarielle")
            st.metric("🔥 Taux de Risque Global", f"{risque:.2f} %")
            st.metric("💳 Prime Totale Facturee", f"{prime:.2f} DT")
            st.progress(int(risque))
            st.write(f"**Formule du Risque :** 70% ML + 30% Regles Metiers (Calcul métier : {txt_regle} = {r_regle}%)")
            st.write(f"**Detail Prime Pure :** Risque ({risque:.2f}%) x Coeff 4.2 = {prime_pure:.2f} DT")
            st.write(f"**Detail Chargement (Frais) :** (Sup x 12) + (Prod x 1.1) = {frais_ch:.2f} DT")
            st.write("**Formule Prime Finale :** Prime Pure + Chargement")
            
        with t3:
            st.write("### Calcul Parametrique de l'Indemnite")
            cap_max = (sup * 200) + (prod * 25)
            ind, p_rate, peril = 0.0, 0.0, "Normal"
            txt_form, txt_expl = "Aucune", "Indices climatiques normaux."
            
            if pl < 35.0:
                peril = "Secheresse"
                if pl <= 8.0:
                    p_rate, txt_form, txt_expl = 1.0, "Forfait 100%", f"Pluie ({pl:.2f} mm) <= Seuil Critique Catastrophe (8 mm)."
                else:
                    p_rate = (35.0 - pl) / (35.0 - 8.0)
                    txt_form = "Taux = (Seuil Activation 35mm - Pluie) / (Seuil Activation 35mm - Seuil Critique 8mm)"
                    txt_expl = f"Pluie ({pl:.2f} mm) en zone de perte progressive."
                ind = p_rate * cap_max
            elif t > 39.0:
                peril = "Canicule"
                if t >= 47.0:
                    p_rate, txt_form, txt_expl = 1.0, "Forfait 100%", f"Temp ({t:.2f} C) >= Seuil Extreme (47 C)."
                else:
                    p_rate = (t - 39.0) / (47.0 - 39.0)
                    txt_form = "Taux = (Temp - Seuil Activation 39C) / (Seuil Critique 47C - Seuil Activation 39C)"
                    txt_expl = f"Temp ({t:.2f} C) en zone de stress thermique lineaire."
                ind = p_rate * cap_max
            
            if ind > 0: st.error(f"💰 Indemnite Declenchee : {ind:.2f} DT (Peril : {peril})")
            else: st.success("🍏 Indemnite Calculee : 0.00 DT (Aucun seuil franchi)")
            
            st.write(f"**Capital Maximum Garanti :** (Sup x 200 DT) + (Prod x 25 DT) = {cap_max:.2f} DT")
            st.write(f"**Formule Appliquee :** {txt_form}")
            st.write(f"**Analyse Metier :** {txt_expl}")
            st.write("*Note PFE : Indemnisation instantanee via donnees satellites sans expertise terrain.*")
            
            tok, cid = st.secrets.get("BOT_TOKEN", ""), st.secrets.get("CHAT_ID", "")
            if tok and cid:
                txt = f"🌾 ASSURANCE\n👤 ID: {uid}\n📈 Risque: {risque:.2f}%\n💰 Indemnite: {ind:.2f} DT"
                try: requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": cid, "text": txt}, timeout=3)
                except: pass
