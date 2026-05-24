import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Assurance Paramétrique 2026", layout="wide")

# ==============================================================================
# 1. LOGIQUE MÉTIER & ACTUARIELLE (Formules)
# ==============================================================================
def calculer_risques_et_primes(sup, prod, irrigation, culture, t, pl):
    """
    Formule Hybride :
    1. Risque = Pondération (70% ML, 30% Stress Agronomique FAO)
    2. Prime = (Risque * Coeff_Securite) + (Frais_Gestion)
    """
    # Réduction risque si irrigué
    coef_irr = 0.5 if irrigation == "Oui" else 1.0
    
    # Seuils FAO-56
    seuil_pluie = 35 if culture == "Céréales" else 45
    
    # Calcul stress (0 à 100)
    stress_h = max(0, (seuil_pluie - pl) / seuil_pluie) * 100 * coef_irr
    stress_t = max(0, (t - 39) / (47 - 39)) * 100 if t > 39 else 0
    risque_agronomique = max(stress_h, stress_t)
    
    # Risque Hybride (Ici 27.5 est la valeur issue de ton modèle ML)
    risque_ml = 27.5
    risque_global = (0.7 * risque_ml) + (0.3 * risque_agronomique)
    
    # Prime Actuarielle
    prime_pure = (risque_global / 100) * 4.2
    frais_gestion = (sup * 12) + (prod * 1.1)
    prime_totale = prime_pure + frais_gestion
    
    # Indemnité
    capital_assure = (sup * 200) + (prod * 25)
    indemnite = capital_assure * (risque_global / 100)
    
    return float(risque_global), float(prime_totale), float(indemnite)

# ==============================================================================
# 2. INTERFACE UTILISATEUR
# ==============================================================================
st.title("🌾 Plateforme d'Assurance Agricole Paramétrique 2026")

# Layout en 2 colonnes pour éviter le scroll
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Entrées Exploitation")
    reg = st.selectbox("Région", ["Tunis", "Nabeul", "Bizerte", "Sfax"])
    sup = st.number_input("Superficie (ha)", min_value=1.0, max_value=100.0, value=10.0)
    prod = st.number_input("Production (t)", min_value=1.0, max_value=500.0, value=20.0)
    irrig = st.radio("Irrigation ?", ["Oui", "Non"])
    cult = st.selectbox("Type de Culture", ["Céréales", "Oléiculture"])

with col2:
    st.subheader("Résultats et Analyse")
    if st.button("🚀 Lancer l'analyse 2026"):
        # Simulation des données NASA
