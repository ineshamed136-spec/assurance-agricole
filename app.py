import streamlit as st
import joblib
import pandas as pd
import requests

st.set_page_config(page_title="Assurance Paramétrique", layout="wide")

# ====================================
# 1. CHARGEMENT DU MODELE ML
# ====================================
@st.cache_resource
def load_model():
    try: 
        return joblib.load("model_rf.pkl"), True
    except: 
        return None, False

model_rf, model_charge = load_model()

coords = {
    "Tunis": (36.80, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87),
    "Beja": (36.72, 9.18), "Sousse": (35.82, 10.60), "Monastir": (35.76, 10.81),
    "Kairouan": (35.67, 10.09), "Kebili": (33.70, 8.97), "Gabes": (33.88, 10.09)
}

# ====================================
# 2. COLLECTE DES DONNÉES SATELLITES
# ====================================
@st.cache_data(ttl=3600)
def get_weather(reg, m):
    lat, lon = coords[reg]
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    p = {
        "parameters": "T2M,PRECTOTCORR,RH2M,WS2M", 
        "community": "AG", 
        "longitude": lon, "latitude": lat, 
        "start": "2025", "end": "2025", 
        "format": "JSON"
    }
    try:
        r = requests.get(url, params=p, timeout=8)
        if r.status_code != 200: return [24.5, 12.0, 60.0, 4.0]
        d = r.json()["properties"]["parameter"]
        k = f"2025{m:02d}"
        return [
            float(d["T2M"][k]), 
            float(d["PRECTOTCORR"][k]), 
            float(d["RH2M"][k]), 
            float(d["WS2M"][k])
        ]
    except: 
        return [24.5, 12.0, 60.0, 4.0]

# ====================================
# 3. INTERFACE UTILISATEUR COMPACTE
# ====================================
st.title("🌾 Assurance Agricole Paramétrique")

col1, col2 = st.columns([1, 1.2], gap="medium")

with col1:
    st.subheader("Contrat")
    uid = st.text_input("ID Exploitant", value="TUN-01")
    region = st.selectbox("Region", list(coords.keys()), index=1)
    culture = st.selectbox("Culture", ["Olives", "Cereales"])
    irrigation = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    mois = st.selectbox("Mois (1-12)", list(range(1, 13)), index=4)
    sup = st.number_input("Superficie (Ha)", min_value=1, value=15)
    prod = st.number_input("Rendement (T)", min_value=1, value=60)
    
    # Détermination de la saison
    if mois in [12, 1, 2]: saison = "Hiver"
    elif mois in [3, 4, 5]: saison = "Printemps"
    elif mois in [6, 7, 8]: saison = "Ete"
    else: saison = "Automne"
    
    btn = st.button("🚀 ANALYSER", use_container_width=True, type="primary")

with col2:
    w = get_weather(region, mois)
    t, pl, hum, vent = w[0], w[1], w[2], w[3]
    t1, t2, t3 = st.tabs(["🌦️ Météo", "📉 Risque", "🛡️ Indemnité"])
    
    with t1:
        st.write(f"**Région :** {region} | **Saison :** {saison}")
        st.info(f"🌡️ Temp: {t:.2f}°C | 🌧️ Pluie: {pl:.2f}mm | 💧 Hum: {hum:.2f}%")
    
    if btn:
        # --- 1. SCORE MACHINE LEARNING ---
        risque_ml = 20.0
        if model_charge:
            try:
                X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)
                X["temp"] = t
                X["précipitations"] = pl
                X["humidité"] = hum
                X["vent"] = vent
                X["mois"] = mois
                X["annee"] = 2025
                
                col_reg = f"region_{region}"
                col_sais = f"saison_{saison}"
                if col_reg in X.columns: X[col_reg] = 1
                if col_sais in X.columns: X[col_sais] = 1
                
                risque_ml = model_rf.predict_proba(X)[0][1] * 100
            except: 
                risque_ml = max(10.0, min(90.0, t * 2.2))
        else:
            # Mode secours indexé sur la température locale
            risque_ml = max(10.0, min(90.0, t * 2.2))

        # --- 2. RÈGLES MÉTIER AGRONOMIQUES ---
        r_regle = 10
        if pl < 35: 
            r_regle += max(0, int((35 - pl) * 2.0))
        if t > 30: 
            r_regle += max(0, int((t - 30) * 3.5))
        if irrigation == "Non": 
            r_regle += 15
        
        # --- 3. CALCUL GLOBAL SANS LIGNES LONGUES ---
        risque = max(0, min(100, (0.7 * risque_ml) + (0.3 * r_regle)))
        prime = (risque * 4.2) + (sup * 12) + (prod * 1.1)
        
        with t2:
            st.markdown("### Tarification Actuarielle")
            st.metric("🔥 Taux de Risque Global", f"{risque:.2f} %")
            st.metric("💳 Prime Pure Calculée", f"{prime:.2f} DT")
            st.progress(int(risque))
            
            with st.expander("📝 Note Explicative"):
                st.write("Le risque fusionne les statistiques historiques (70%) et les règles agronomiques (30%).")
                st.markdown("**Formule de la Prime :**")
                st.latex(r"Prime = (Risque \times 4.2) + (Sup \times 12) + (Prod \times 1.1)")
                
        with t3:
            st.markdown("### Déclenchement Automatique")
            cap_max = (sup * 200) + (prod * 25)
            ind, peril = 0.0, "Normal"
            
            if pl < 35.0:
                peril = "Sécheresse"
                p_rate = 1.0 if pl <= 8.0 else (35.0 - pl) / (35.0 - 8.0)
                ind = p_rate * cap_max
            elif t > 39.0:
                peril = "Canicule"
                p_rate = 1.0 if t >= 47.0 else (t - 39.0) / (47.0 - 39.0)
                ind = p_rate * cap_max
            
            if ind > 0: 
                st.error(f"💰 Indemnité Déclenchée : {ind:.2f} DT ({peril})")
            else: 
                st.success("Indemnité Calculée : 0.00 DT")
                
            with st.expander("📊 Seuils Physiques (Triggers)"):
                st.latex(r"Cap_{Max} = (Sup \times 200) + (Prod \times 25)")
                st.write("- **Sécheresse :** Déclenché sous 35 mm.")
                st.write("- **Canicule :** Déclenché au-dessus de 39°C.")

            # Notification optionnelle
            tok, cid = st.secrets.get("BOT_TOKEN", ""), st.secrets.get("CHAT_ID", "")
            if tok and cid:
                txt = f"🌾 ID: {uid}\n📈 Risque: {risque:.2f}%\n💰 Ind: {ind:.2f} DT"
                try: requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat
