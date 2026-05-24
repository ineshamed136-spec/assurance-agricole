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
    p = {"parameters": "T2M,PRECTOTCORR,RH2M,WS2M", "community": "AG", "longitude": lon, "latitude": lat, "start": "2025", "end": "2025", "format": "JSON"}
    try:
        r = requests.get(url, params=p, timeout=8)
        if r.status_code != 200: return [24.5, 12.0, 60.0, 4.0]
        d = r.json()["properties"]["parameter"]
        k = f"2025{m:02d}"
        return [float(d["T2M"][k]), float(d["PRECTOTCORR"][k]), float(d["RH2M"][k]), float(d["WS2M"][k])]
    except: 
        return [24.5, 12.0, 60.0, 4.0]

# ====================================
# 3. INTERFACE DE CONTROLE COMPACTE
# ====================================
st.title("🌾 Plateforme d'Assurance Agricole Paramétrique")

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
    saison = "Hiver" if mois in [12,1,2] else "Printemps" if mois in [3,4,5] else "Ete" if mois in [6,7,8] else "Automne"
    btn = st.button("🚀 ANALYSER", use_container_width=True, type="primary")

with col2:
    w = get_weather(region, mois)
    t, pl, hum, vent = w[0], w[1], w[2], w[3]
    t1, t2, t3 = st.tabs(["🌦️ Données Météo", "📉 Évaluation du Risque", "🛡️ Indemnisation"])
    
    with t1:
        st.write(f"**Région :** {region} | **Saison :** {saison}")
        st.info(f"🌡️ Temp: {t:.2f} °C | 🌧️ Pluie: {pl:.2f} mm | 💧 Hum: {hum:.2f} % | 💨 Vent: {vent:.2f} m/s")
    
    if btn:
        # --- Calcul du score Machine Learning ---
        risque_ml = 20.0
        if model_charge:
            try:
                X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)
                X["temp"], X["précipitations"], X["humidité"], X["vent"], X["mois"], X["annee"] = t, pl, hum, vent, mois, 2025
                if f"region_{region}" in X.columns: X[f"region_{region}"] = 1
                if f"saison_{saison}" in X.columns: X[f"saison_{saison}"] = 1
                risque_ml = model_rf.predict_proba(X)[0][1] * 100
            except: 
                risque_ml = 20.0

        # --- Calcul des Règles Métier Agronomiques (Syntaxe Corrigée avec ':') ---
        r_regle = 10
        if pl < 15: 
            r_regle += 35
        if t > 38: 
            r_regle += 25
        if irrigation == "Non": 
            r_regle += 15
        
        # --- Indice de Risque Global Combiné ---
        risque = max(0, min(100, (0.7 * risque_ml) + (0.3 * r_regle)))
        prime = (risque * 4.2) + (sup * 12) + (prod * 1.1)
        
        with t2:
            st.markdown("### Analyse & Tarification Actuarielle")
            st.metric("🔥 Taux de Risque Global", f"{risque:.2f} %")
            st.metric("💳 Prime Pure Calculée", f"{prime:.2f} DT")
            st.progress(int(risque))
            
            with st.expander("📝 Modèle de Tarification (Explication)"):
                st.markdown("**Méthodologie de Calcul :**")
                st.write("Le taux de risque intègre les probabilités statistiques historiques calculées par le modèle prédictif ainsi que les facteurs de vulnérabilité agronomiques aux champs (stress hydrique, absence d'irrigation).")
                st.markdown("**Formule de la Prime Globale :**")
                st.latex(r"Prime = \left( \text{Risque} \times 4.2 \right) + \left( \text{Superficie} \times 12 \right) + \left( \text{Rendement} \times 1.1 \right)")
                st.caption("Le coefficient de chargement (4.2) assure la marge de sécurité face à l'incertitude climatique.")
                
        with t3:
            st.markdown("### Déclenchement Paramétrique Automatique")
            cap_max = (sup * 200) + (prod * 25)
            ind, peril = 0.0, "Conditions Normales"
            
            # Application des index physiques linéaires
            if pl < 35.0:
                peril = "Sécheresse"
                p_rate = 1.0 if pl <= 8.0 else (35.0 - pl) / (35.0 - 8.0)
                ind = p_rate * cap_max
            elif t > 39.0:
                peril = "Canicule"
                p_rate = 1.0 if t >= 47.0 else (t - 39.0) / (47.0 - 39.0)
                ind = p_rate * cap_max
            
            if ind > 0: 
                st.error(f"💰 Indemnité Déclenchée : {ind:.2f} DT")
            else: 
                st.success("Indemnité Calculée : 0.00 DT")
                
            with st.expander("📊 Index Géophysiques Limites"):
                st.markdown("**1. Plafond des Capitaux Assurés :**")
                st.latex(r"Capital_{Max} = (\text{Superficie} \times 200) + (\text{Rendement} \times 25)")
                
                st.markdown("**2. Règle de calcul de l'Indemnité Proportionnelle :**")
                st.latex(r"Indemnité = \text{Taux de Perte} \times Capital_{Max}")
                
                st.markdown("**Seuils de déclenchement (Triggers) :**")
                st.write("- **Sécheresse :** Déclenchement sous **35 mm** mensuels. Sinistre total (100%) atteint à **8 mm**.")
                st.write("- **Canicule :** Déclenchement au-delà de **39°C**. Sinistre total (100%) atteint à **47°C**.")

            # Notification Système (Optionnelle)
            tok, cid = st.secrets.get("BOT_TOKEN", ""), st.secrets.get("CHAT_ID", "")
            if tok and cid:
                txt = f"🌾 ASSURANCE\n👤 ID: {uid}\n📈 Risque: {risque:.2f}%\n💰 Indemnite: {ind:.2f} DT"
                try: requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": cid, "text": txt}, timeout=3)
                except: pass
