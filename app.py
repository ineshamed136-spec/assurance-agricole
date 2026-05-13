import numpy as np
import pandas as pd

if st.button("Prédire"):

    # créer dataframe vide avec toutes les colonnes du modèle
    X = pd.DataFrame(0, index=[0], columns=model_rf.feature_names_in_)

    # remplir seulement les vraies valeurs utilisateur
    X["temp"] = temp
    X["précipitations"] = pluie
    X["humidité"] = humidite
    X["vent"] = vent
    X["mois"] = mois
    X["annee"] = annee

    region_col = f"region_{region}"
    if region_col in X.columns:
        X[region_col] = 1

    saison_col = f"saison_{saison}"
    if saison_col in X.columns:
        X[saison_col] = 1

    # prédiction ML
    proba = model_rf.predict_proba(X)[0][1] * 100

    st.write("🌾 Score de risque :", round(proba, 2))
