import streamlit as st
import requests

# Configuration de la page
st.set_page_config(page_title="Assurance Paramétrique 2026", layout="wide")

# --- 1. CONFIGURATION DES RÉGIONS (Coordonnées GPS) ---
COORDS = {
    "Tunis": (36.80, 10.18), "Nabeul": (36.45, 10.73), 
    "Bizerte": (37.27, 9.87), "Sfax": (34.74, 10.76)
}

# --- 2. FONCTIONS DE CALCUL (Le Cœur Actuariel) ---
def calculer_risques_et_primes(sup, prod, irrigation, culture, t, pl):
    """
    Formule Hybride : 
    - Risque = max(Stress Hydrique, Stress Thermique)
    - Prime = (Risque_ML * Coeff_Actu) + (Frais_Gestion)
    """
    # Facteur d'irrigation : réduit le risque de 50%
    coef_irr = 0.5 if irrigation == "Oui" else 1.0
    
    # Seuils FAO-56
    seuil_pluie = 35 if culture == "Céréales" else 45
    
    # Calcul du stress (0 à 100%)
    stress_h = max(0, (seuil_pluie - pl) / seuil_pluie) * 100 * coef_irr
    stress_t = max(0, (t - 39) / (47 - 39)) * 100 if t > 39 else 0
    risque_global = max(stress_h, stress_t)
    
    # Prime : Prime Pure (Risque * 4.2) + Chargement Fixe
    # 4.2 est le coefficient de sécurité actuariel standard
    prime_totale = ((risque_global / 100) * 4.2) + (sup * 12) + (prod * 1.1)
    
    # Indemnité (Progressive selon le risque)
    capital_assure = (sup * 200) + (prod * 25)
    indemnite = capital_assure * (risque_global / 100)
    
    return risque_global, prime_totale, indemnite

# --- 3. INTERFACE UTILISATEUR ---
st.title("🌾 Plateforme d'Assurance Agricole Paramétrique 2026")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Entrées Exploitation")
    reg = st.selectbox("Région", list(COORDS.keys()))
    mois = st.slider("Mois d'analyse", 1, 12, 5)
    sup = st.number_input("Superficie (ha)", 1.0, 100.0, 10.0)
    prod = st.number_input("Production (t)", 1.0, 500.0, 20.0)
    irrig = st.radio("Irrigation ?", ["Oui", "Non"])
    cult = st.selectbox("Type de Culture", ["Céréales", "Oléiculture"])

with col2:
    st.subheader("Résultats et Analyse")
    if st.button("🚀 Lancer l'analyse 2026"):
        # Données météo (Simulation NASA Power)
        t, pl = 3
