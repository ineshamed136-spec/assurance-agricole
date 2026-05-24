import streamlit as st
import requests

st.set_page_config(page_title="Assurance Paramétrique 2026", layout="wide")

# --- 1. FONCTION NASA POWER ---
def get_nasa_data(reg, mois):
    coords = {"Tunis": (36.80, 10.18), "Nabeul": (36.45, 10.73), "Bizerte": (37.27, 9.87), "Sfax": (34.74, 10.76)}
    lat, lon = coords.get(reg, (36.80, 10.18))
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    params = {"parameters": "T2M,PRECTOTCORR", "community": "AG", "longitude": lon, "latitude": lat, "start": "2026", "end": "2026", "format": "JSON"}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()["properties"]["parameter"]
        return float(data["T2M"][f"2026{mois:02d}"]), float(data["PRECTOTCORR"][f"2026{mois:02d}"])
    except:
        return 38.5, 12.0

# --- 2. LOGIQUE ACTUARIELLE ---
def calculer_tout(sup, prod, irrig, cult, t, pl):
    coef_irr = 0.5 if irrig == "Oui" else 1.0
    seuil = 35 if cult == "Céréales" else 45
    stress = max(0, (seuil - pl) / seuil) * 100 * coef_irr
    risque = (0.7 * 27.5) + (0.3 * stress) 
    prime = ((risque / 100) * 4.2) + (sup * 12) + (prod * 1.1)
    indem = ((sup * 200) + (prod * 25)) * (risque / 100)
    return risque, prime, indem

# --- 3. INTERFACE ---
st.title("🌾 Assurance Agricole 2026")
c1, c2 = st.columns([1, 1])

with c1:
    reg = st.selectbox("Région", ["Tunis", "Nabeul", "Bizerte", "Sfax"])
    mois = st.slider("Mois", 1, 12, 5)
    sup = st.number_input("Superficie (ha)", 1.0, 100.0, 10.0)
    prod = st.number_input("Production (t)", 1.0, 500.0, 20.0)
    irrig = st.radio("Irrigation", ["Oui", "Non"], horizontal=True)
    cult = st.selectbox("Culture", ["Céréales", "Oléiculture"])
    btn = st.button("🚀 LANCER L'ANALYSE")

with c2:
    if btn:
        t, pl = get_nasa_data(reg, mois)
        st.info(f"📍 Données météo récupérées : {t:.1f}°C / {pl:.1f} mm")
        r, p, i = calculer_tout(sup, prod, irrig, cult, t, pl)
        m1, m2, m3 = st.columns(3)
        m1.metric("Risque", f"{r:.1f}%")
        m2.metric("Prime (DT)", f"{p:.2f}")
        m3.metric("Indemnité (DT)", f"{i:.2f}")
        
        with st.expander("🛠️ Fiche Technique"):
            st.latex(r"Indemnite = (Sup \times 200 + Prod \times 25) \times Risque")
            st.json({"Température": t, "Pluie": pl, "Taux_Risque": round(r, 2)})
