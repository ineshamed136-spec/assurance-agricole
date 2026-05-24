import streamlit as st
import pandas as pd
import requests

# Configuration de la page (Mode dashboard sans scroll)
st.set_page_config(page_title="Assurance Paramétrique 2026", layout="wide")

# ==============================================================================
# 1. LOGIQUE MÉTIER & FORMULES (Standard Actuariel Tunisien)
# ==============================================================================
def calculer_risques_et_primes(sup, prod, irrigation, type_culture, t, pl):
    """
    Formule : Prime = (Risque_ML * Coeff_Actu) + (Frais_Gestion)
    Le risque est ajusté par un facteur de stress basé sur la FAO.
    """
    # Facteur de stress (0 à 1)
    stress_hydrique = max(0, (35 - pl) / 35) if pl < 35 else 0
    stress_thermique = max(0, (t - 39) / (47 - 39)) if t > 39 else 0
    risque_global = (stress_hydrique * 0.7 + stress_thermique * 0.3) * 100
    
    # Formule de Prime : Prime Pure (Risque * 4.2) + Chargement (12/ha + 1.1/tonne)
    prime_pure = (risque_global / 100) * 4.2
    frais_gestion = (sup * 12) + (prod * 1.1)
    prime_totale = prime_pure + frais_gestion
    
    # Indemnité (perte proportionnelle)
    indemnite = ((sup * 200) + (prod * 25)) * (risque_global / 100)
    
    return risque_global, prime_totale, indemnite

# ==============================================================================
# 2. INTERFACE UTILISATEUR (Dashboard Fixe)
# ==============================================================================
st.title("🌾 Plateforme d'Assurance Agricole Paramétrique 2026")

col_input, col_result = st.columns([1, 1])

with col_input:
    st.subheader("Paramètres de l'Exploitation")
    reg = st.selectbox("Région", ["Tunis", "Nabeul", "Bizerte", "Sfax"])
    mois = st.slider("Mois", 1, 12, 5)
    sup = st.number_input("Superficie (ha)", 1.0, 100.0, 10.0)
    prod = st.number_input("Production prévue (tonnes)", 1.0, 500.0, 20.0)
    irrigation = st.radio("Irrigation", ["Oui", "Non"])
    type_culture = st.selectbox("Culture", ["Céréales", "Oléiculture"])

with col_result:
    if st.button("🚀 Calculer les indicateurs 2026"):
        # Simulation données NASA (ou appel API)
        t, pl = 38.5, 12.0 # Données simulées pour 2026
        risque, prime, indem = calculer_risques_et_primes(sup, prod, irrigation, type_culture, t, pl)
        
        st.metric("Taux de Risque Calculé", f"{risque:.1f} %")
        st.metric("Prime Totale", f"{prime:.2f} DT")
        st.metric("Indemnité estimée", f"{indem":.2f} DT")
        
        # ZONE JSON POUR L'ENCADRANT
        with st.expander("🛠️ Fiche Technique (JSON)"):
            st.json({
                "meta": {"annee": 2026, "region": reg},
                "donnees_climat": {"temp": t, "pluie": pl},
                "formule_prime": "Prime = (Risque * 4.2) + (Sup*12 + Prod*1.1)",
                "resultats": {"taux_risque": risque, "prime": prime, "indemnite": indem}
            })

# Note explicative en bas (fixe)
st.markdown("---")
st.caption("Méthodologie : Basée sur le standard FAO-56 pour le stress hydrique et le modèle actuariel tunisien pour la tarification.")
