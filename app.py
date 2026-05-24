import streamlit as st
import joblib
import pandas as pd
import requests

# ====================================
# 1. CONFIG
# ====================================
st.set_page_config(page_title="Assurance", layout="wide")

st.markdown("""
<style>
.m-box {background-color: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 5px solid #1ba345; margin-bottom: 8px;}
.e-box {background-color: #eef2f7; padding: 15px; border-radius: 8px; border: 1px solid #d0d7de; margin-top: 10px;}
</style>
""", unsafe_allow_html=True)

# ====================================
# 2. MODEL ML
# ====================================
@st.cache_resource
def load_model():
    try:
        return joblib.load("model_rf.pkl"), True
    except:
        return None, False

model_rf, model_charge = load_model()

# ====================================
# 3. TELEGRAM & DATA
# ====================================
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def envoyer_alerte(uid, reg, risq, stat):
    if not BOT_TOKEN or not CHAT_ID: return
    msg = f"ASSURANCE\nID: {uid}\nReg: {reg}\nRisque: {risq:.2f}%\nResultat: {stat}"
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except: pass

coords = {
    "Tunis": (36.80, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.60), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.70, 8.97), "Gabes": (33.88, 10.09), "Medenine": (33.35, 10.50)
}

liste_regions = list(coords.keys())
liste_cultures = ["Olives", "Cereales"]
liste_irrigation = ["Oui", "Non"]
liste_mois = list(range(1, 13))

@st.cache_data(ttl=3600)
def get_weather(region, mois):
    lat, lon = coords[region]
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    prms = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2025", "end": "2025", "format": "JSON"}
    try:
        r = requests.get(url, params=prms, timeout=10)
        if r.status_code != 200: return [24.5, 12.0, 60.0, 4.0]
        p = r.json()["properties"]["parameter"]
        k = f"2025{mois:02d}"
        return [float(p["T2M"][k]), float(p["PRECTOTCORR"][k]), float(p["RH2M"][k]), float(p["WS2M"][k])]
    except:
        return [24.5, 12.0, 60.0, 4.0]

# ====================================
# 4. INTERFACE
# ====================================
st.title("Assurance Agricole")

if model_charge: st.sidebar.success("ML Actif")
else: st.sidebar.warning("Mode Regles")

st.markdown("---")
col_f, col_d = st.columns([1, 1.3], gap="medium")

with col_f:
    st.subheader("Contrat")
    c1, c2 = st.columns(2)
    user_id = c1.text_input("ID Exploitant", value="TUN-01")
    region = c2.selectbox("Region", liste_regions, index=1)
    
    c3, c4 = st.columns(2)
    culture = c3.selectbox("Culture", liste_cultures)
    irrigation = c4.radio("Irrigation", liste_irrigation, horizontal=True)

    c5, c6, c7 = st.columns(3)
    mois = c5.selectbox("Mois", liste_mois, index=4)
    superficie = c6.number_input("Sup (Ha)", min_value=1, value=15)
    production = c7.number_input("Rendement", min_value=1, value=60)

    if mois in [12, 1, 2]: saison = "Hiver"
    elif mois in [3, 4, 5]: saison = "Printemps"
    elif mois in [6, 7, 8]: saison = "Ete"
    else: saison = "Automne"
    
    st.write(f"Saison: {saison}")
    btn_analyser = st.button("ANALYSER", use_container_width=True, type="primary")

with col_d:
    w = get_weather(region, mois)
    t, pl, hum, vent = w[0], w[1], w[2], w[3]
    t1, t2, t3 = st.tabs(["Meteo", "Risque", "Indemnite"])
    
    with t1:
        st.markdown(f"Region: {region}")
        m1, m2 = st.columns(2)
        m1.markdown(f"<div class='m-box'><b>Temp:</b> {t:.2f} C</div>", unsafe_allow_html=True)
        m1.markdown(f"<div class='m-box'><b>Pluie:</b> {pl:.2f} mm</div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='m-box'><b>Hum:</b> {hum:.2f} %</div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='m-box'><b>Vent:</b> {vent:.2f} m/s</div>", unsafe_allow_html=True)

    if btn_analyser:
        if model_charge:
            try:
                cm = model_rf.feature_names_in_
                X = pd.DataFrame(0, index=[0], columns=cm)
                X["temp"], X["précipitations"], X["humidité"], X["vent"], X["mois"], X["annee"] = t, pl, hum, vent, mois, 2025
                if f"region_{region}" in X.columns: X[f"region_{region}"] = 1
                if f"saison_{saison}" in X.columns: X[f"saison_{saison}"] = 1
                risque_ml = model_rf.predict_proba(X)[0][1] * 100
            except: risque_ml = 20.0
        else: risque_ml = 20.0

        risque_regle = 10
        if pl < 15: risque_regle += 35
        if t > 38: risque_regle += 25
        if irrigation == "Non": risque_regle += 15
        if culture == "Cereales" and pl < 25: risque_regle += 15
        
        risque = max(0, min(100, (0.7 * risque_ml) + (0.3 * risque_regle)))
        prime = (risque * 4.2) + (superficie * 12) + (production * 1.1)
        
        with t2:
            st.markdown("#### Actuariat")
            st.progress(int(risque))
            rc1, rc2 = st.columns(2)
            rc1.metric("Taux Risque", f"{risque:.2f} %")
            rc2.metric("Prime pure", f"{prime:.2f} DT")

        with t3:
            st.markdown("#### Index Trigger")
            cap_max = (superficie * 200) + (production * 25)
            ind, p_rate, t_sin = 0.0, 0.0, "Normal"
            form, expl = "Aucune", "Normal"
            
            if pl < 35.0:
                t_sin = "Secheresse"
                if pl <= 8.0:
                    p_rate, form, expl = 1.0, "Fixe 100%", "Seuil atteint"
                else:
                    p_rate, form, expl = (35.0-pl)/(35.0-8.0), "Lineaire", "Zone prog"
                ind = p_rate * cap_max
            elif t > 39.0:
                t_sin = "Canicule"
                if t >= 47.0:
                    p_rate, form, expl = 1.0, "Fixe 100%", "Seuil ext"
                else:
                    p_rate, form, expl = (t-39.0)/(47.0-39.0), "Lineaire", "Zone stress"
                ind = p_rate * cap_max

            st.markdown(f"**Peril :** `{t_sin}`")
            if ind > 0:
                st.error(f"Indemnite : {ind:.2f} DT")
                stat_tel = f"Emise: {ind:.2f} DT"
            else:
                st.
