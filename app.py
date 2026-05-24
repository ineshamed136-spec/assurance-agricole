import streamlit as st
import pandas as pd
import requests

# ==============================================================================
# 1. LOGIQUE ACTUARIELLE & AGRONOMIQUE (Le cœur du modèle)
# ==============================================================================
class ModeleAssuranceExpert:
    def __init__(self, sup, prod, irrigation, culture):
        self.sup = sup
        self.prod = prod
        self.irrigation = 0.5 if irrigation == "Oui" else 1.0  # Réduction risque si irrigué
        self.culture = culture
        
    def calculer_taux_perte(self, t, pl, risque_ml):
        """
        Calcul Hybride : 70% ML (IA) + 30% Règles Métier (FAO)
        """
        # Seuil de flétrissement (FAO)
        seuil = 35 if self.culture == "Céréales" else 45
        
        # Stress calculé (0 à 1)
        stress_h = max(0, (seuil - pl) / seuil) * self.irrigation
        stress_t = max(0, (t - 39) / (47 - 39)) if t > 39 else 0
        règle_metier = max(stress_h, stress_t)
        
        # Pondération hybride
        taux_perte = (0.7 * (risque_ml/100)) + (0.3 * règle_metier)
        return min(taux_perte, 1.0)

    def calculer_prime(self, taux_perte):
        # Formule Actuarielle : Prime = Risque + Chargement
        prime_pure = taux_perte * 4.2 # Coefficient de sécurité actuariel
        frais_gestion = (self.sup * 12) + (self.prod * 1.1)
        return prime_pure + frais_gestion

# ==============================================================================
# 2. INTERFACE DASHBOARD (Sans scroll)
# ==============================================================================
st.set_page_config(page_title="Assurance Paramétrique 2026", layout="wide")
st.title("🌾 Plateforme d'Assurance Agricole Paramétrique")

c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("Entrées Exploitation")
    reg = st.selectbox("Région", ["Tunis", "Nabeul", "Bizerte", "Sfax"])
    sup = st.number_input("Superficie (ha)", 1.0, 100.0, 10.0)
    prod = st.number_input("Production (t)", 1.0, 500.0, 20.0)
    irr = st.radio("Irrigation", ["Oui", "Non"])
    cult = st.selectbox("Culture", ["Céréales", "Oléiculture"])

with c2:
    st.subheader("Analyse & Résultats")
    # Simulation données climatiques 2026 (NASA Power)
    t, pl = 38.5, 12.0
    model = ModeleAssuranceExpert(sup, prod, irr, cult)
    
    if st.button("🚀 Calculer les indicateurs 2026"):
        taux = model.calculer_taux_perte(t, pl, 27.5) # 27.5% est le risque IA
        prime = model.calculer_prime(taux)
        indem = ((sup * 200) + (prod * 25)) * taux
        
        # Affichage metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Risque Hybride", f"{taux*100:.1f}%")
        m2.metric("Prime Totale (DT)", f"{prime:.2f}")
        m3.metric("Indemnité (DT)", f"{indem:.2f}")
        
        # Transparence pour l'encadrant
        with st.expander("🛠️ Détails techniques (JSON)"):
            st.json({
                "formule_prime": "Prime = (Risque * 4.2) + (Sup*12 + Prod*1.1)",
                "donnees_climat": {"temp": t, "pluie": pl},
                "logique": "Hybride (70% ML / 30% FAO-56)",
                "culture": cult
            })
