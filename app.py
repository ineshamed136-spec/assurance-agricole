import streamlit as st
import joblib
import pandas as pd
import requests

# 1. Chargement du modèle (Machine Learning)
# Ce modèle pourrait prédire le 'taux_risque' en fonction de la région ou de la culture
def charger_modele():
    # Assurez-vous d'avoir un fichier 'modele_risque.pkl' dans votre dossier
    return joblib.load('modele_risque.pkl')

# 2. Appel API (Optionnel)
# Exemple pour récupérer le cours actuel d'une monnaie ou données météo
def get_donnees_meteo():
    # Exemple fictif d'appel API
    # response = requests.get("https://api.meteo.tn/...")
    return 0.025 # Taux de risque par défaut simulé

# --- Interface ---
st.title("🛡️ Calculateur Intelligent de Prime")

valeur_bien = st.number_input("Valeur du bien", min_value=0.0)
region = st.selectbox("Région", ["Sfax", "Tunis", "Kairouan"])

if st.button("Calculer avec Prédiction IA"):
    # 3. Utilisation du modèle pour ajuster le taux de risque
    # model = charger_modele()
    # taux_risque = model.predict([[...]]) 
    
    taux_risque = get_donnees_meteo() # Simulation
    
    prime_pure = valeur_bien * taux_risque
    # ... (Suite du calcul comme vu précédemment)
    st.write(f"Taux de risque calculé par l'IA : {taux_risque * 100}%")
    st.success(f"Prime Totale : {prime_pure * 1.35:,.2f} DT")
