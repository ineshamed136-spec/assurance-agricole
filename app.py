import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Assurance Paramétrique 2026", layout="wide")

# ==============================================================================
# 1. LOGIQUE MÉTIER & ACTUARIELLE
# ==============================================================================
def calculer_risques_et_primes(sup, prod, irrigation, culture, t, pl):
    # Réduction risque si irrigué
    coef_irr = 0.5 if irrigation == "Oui" else 1.0
    
    # Seuils FAO-56
    seuil_pluie = 35 if culture == "Céréales" else 45
    
    # Calcul stress (0 à 100)
    stress_h = max(0, (seuil_pluie - pl) / seuil_pluie) * 100 * coef_irr
    stress_t = max(0, (t - 39) / (47 - 39)) * 100 if t > 39 else 0
    risque_agronomique = max(stress_h, stress_t)
    
    # Risque Hybride (70% ML, 30% FAO)
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

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Entrées Exploitation")
    reg = st.selectbox("Région", ["Tunis", "Nabeul", "Bizerte", "Sfax"])
    sup = st.number_input("Superficie (ha)", 1.0, 100.0, 10.0)
    prod = st.number_input("Production (t)", 1.0, 500.0, 20.0)
    irrig = st.radio("Irrigation ?", ["Oui", "Non"])
    cult = st.selectbox("Type de Culture", ["Céréales", "Oléiculture"])

with col2:
    st.subheader("Résultats et Analyse")
    if st.button("🚀 Lancer l'analyse 2026"):
        # Ces lignes sont maintenant correctement indentées sous le 'if'
        t_sim, pl_sim = 38.5, 12.0
        
        risque, prime, indem = calculer_risques_et_primes(sup, prod, irrig, cult, t_sim, pl_sim)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Score Risque", f"{risque:.1f}%")
        m2.metric("Prime Totale", f"{prime:.2f} DT")
        m3.metric("Indemnité", f"{indem:.2f} DT")
        
        with st.expander("📝 Détails des formules"):
            st.latex(r"Indemnite = Capital\_Assure \times Taux\_Risque")
            st.latex(r"Prime = (Risque \times 4.2) + (Sup \times 12) + (Prod \times 1.1)")
            st.json({"annee": 2026, "risque": round(risque, 2)})
