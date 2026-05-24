import streamlit as st
import requests

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Assurance Paramétrique 2026", layout="wide")

# --- 1. RÉCUPÉRATION DONNÉES NASA POWER ---
def get_nasa_data(reg, mois):
    coords = {
        "Tunis": (36.80, 10.18), "Nabeul": (36.45, 10.73), 
        "Bizerte": (37.27, 9.87), "Sfax": (34.74, 10.76)
    }
    lat, lon = coords.get(reg, (36.80, 10.18))
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    params = {
        "parameters": "T2M,PRECTOTCORR", "community": "AG",
        "longitude": lon, "latitude": lat,
        "start": "2026", "end": "2026", "format": "JSON"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()["properties"]["parameter"]
        key = f"2026{mois:02d}"
        return float(data["T2M"][key]), float(data["PRECTOTCORR"][key])
    except:
        return 38.5, 12.0 # Fallback en cas d'erreur API

# --- 2. LOGIQUE ACTUARIELLE & AGRONOMIQUE ---
def calculer_indemnite_prime(sup, prod, irrigation, culture, t, pl):
    # Ajustement irrigation
    coef_irr = 0.5 if irrigation == "Oui" else 1.0
    seuil_p = 35 if culture == "Céréales" else 45
    
    # Stress Agronomique (FAO-56)
    stress_h = max(0, (seuil_p - pl) / seuil_p) * 100 * coef_irr
    stress_t = max(0, (t - 39) / (47 - 39)) * 100 if t > 39 else 0
    risque_agri = max(stress_h, stress_t)
    
    # Risque Hybride (70% ML, 30% FAO)
    risque_total = (0.7 * 27.5) + (0.3 * risque_agri)
    
    # Prime (Actuariat Tunisien)
    prime = ((risque_total / 100) * 4.2) + (sup * 12) + (prod * 1.1)
    indemnite = ((sup * 200) + (prod * 25)) * (risque_total / 100)
    
    return risque_total, prime, indemnite

# --- 3. INTERFACE UTILISATEUR ---
st.title("🌾 Système d'Assurance Agricole Paramétrique 2026")

c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("Entrées Exploitation")
    reg = st.selectbox("Région", ["Tunis", "Nabeul", "Bizerte", "Sfax"])
    mois = st.slider("Mois", 1, 12, 5)
    sup = st.number_input("Superficie (ha)", 1.0, 100.0, 10.0)
    prod = st.number_input("Production (t)", 1.0, 500.0, 20.0)
    irrig = st.radio("Irrigation", ["Oui", "Non"])
    cult = st.selectbox("Culture", ["Céréales", "Oléiculture"])

with c2:
    st.subheader("Résultats 2026")
    if st.button("🚀 LANCER L'ANALYSE"):
        t, pl = get_nasa_data(reg, mois)
        r, p, i = calculer_indemnite_prime(sup, prod, irrig, cult, t, pl)
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Risque", f"{r:.1f}%")
        col_m2.metric("Prime (DT)", f"{p:.2f}")
        col_m3.metric("Indemnité (DT)", f"{i:.2f}")
        
        st.info(f"Source NASA : {t}°C, {pl}mm")
        
        with st.expander("🛠️ Fiche Technique (JSON)"):
            st.json({
                "modele": "Hybride RF/FAO",
                "formule_prime": "Prime = (Risque * 4.2) + Charges",
                "resultat": {"taux": round(r, 2), "prime": round(p, 2), "indem": round(i, 2)}
            })
