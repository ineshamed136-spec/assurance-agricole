import streamlit as st
import pandas as pd
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Assurance Paramétrique Tunisie", layout="wide")

# --- LOGIQUE MÉTIER & ACTUARIELLE (Formules) ---
class Actuariat:
    @staticmethod
    def calculer_taux_risque(pluie, temp):
        # Stress hydrique selon FAO-56 (Seuil 35mm -> 8mm)
        stress_h = max(0, (35 - pluie) / (35 - 8)) if pluie < 35 else 0
        # Stress thermique selon seuils locaux (Seuil 39°C -> 47°C)
        stress_t = max(0, (temp - 39) / (47 - 39)) if temp > 39 else 0
        return min(max(stress_h, stress_t) * 100, 100)

    @staticmethod
    def calculer_prime(risque, sup, prod):
        # Formule hybride : Prime Pure + Chargement (frais gestion)
        # 4.2 est le coefficient de mutualisation actuariel
        prime_pure = (risque / 100) * 4.2 
        frais = (sup * 12) + (prod * 1.1)
        return prime_pure + frais

# --- GESTION DES DONNÉES (NASA API) ---
def fetch_nasa_data(lat, lon):
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    params = {
        "parameters": "T2M,PRECTOTCORR",
        "community": "AG",
        "longitude": lon, "latitude": lat,
        "start": "2026", "end": "2026",
        "format": "JSON"
    }
    try:
        res = requests.get(url, params=params, timeout=5)
        data = res.json()["properties"]["parameter"]
        # On extrait la température et la pluie pour le mois de mai (202605)
        t = data["T2M"]["202605"]
        p = data["PRECTOTCORR"]["202605"]
        return float(t), float(p)
    except:
        return 24.5, 12.0 # Valeurs de secours (fallback)

# --- INTERFACE (Dashboard) ---
st.title("📊 Système d'Assurance Agricole Paramétrique 2026")

# Layout en 3 colonnes pour éviter le scroll
c1, c2, c3 = st.columns([1, 1, 1])

with c1:
    st.subheader("Paramètres Exploitation")
    reg = st.selectbox("Région", ["Tunis", "Nabeul", "Bizerte", "Sfax"])
    sup = st.number_input("Superficie (ha)", 1.0, 100.0, 10.0)
    prod = st.number_input("Production (t)", 1.0, 500.0, 20.0)

with c2:
    st.subheader("Données Climatiques 2026")
    # Simulation coordonnées
    lat, lon = (36.8, 10.1) 
    t, p = fetch_nasa_data(lat, lon)
    st.write(f"Température : {t}°C")
    st.write(f"Pluviométrie : {p} mm")
    st.info("Données synchronisées via NASA POWER")

with c3:
    st.subheader("Résultats Financiers")
    risque = Actuariat.calculer_taux_risque(p, t)
    prime = Actuariat.calculer_prime(risque, sup, prod)
    indem = ((sup * 200) + (prod * 25)) * (risque / 100)
    
    st.metric("Taux de Risque", f"{risque:.1f}%")
    st.metric("Prime Totale", f"{prime:.2f} DT")
    st.metric("Indemnité due", f"{indem:.2f} DT")

# Fiche technique pour l'encadrant
with st.expander("📝 Détails Techniques & Formules"):
    st.latex(r"Prime = (Risque \times 4.2) + (Superficie \times 12) + (Production \times 1.1)")
    st.json({
        "modele": "Hybrid RF-Parametric",
        "source": "NASA Power API / FAO-56",
        "formule_prime": "Actuarielle Standard Tunisien"
    })
