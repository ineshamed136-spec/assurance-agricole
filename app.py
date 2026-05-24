import pandas as pd

# ==============================================================================
# 1. CONFIGURATION ET PARAMÈTRES AGRONOMIQUES
# Basés sur la littérature scientifique : FAO Irrigation and Drainage Paper 56
# ==============================================================================
FAO_THRESHOLDS = {
    "pluie_confort": 35.0,  # mm/mois (Niveau de satisfaction hydrique)
    "pluie_critique": 8.0,   # mm/mois (Point de flétrissement permanent)
    "temp_echaudage": 39.0,  # °C (Risque d'échaudage pour céréales/olives)
    "temp_letal": 47.0       # °C (Mortalité végétale)
}

class ModeleAssuranceParametrique:
    def __init__(self, superficie, rendement, risque_ml):
        self.superficie = superficie
        self.rendement = rendement
        self.risque_ml = risque_ml # Valeur entre 0 et 1 (ex: 0.275)

    # ==========================================================================
    # 2. LOGIQUE D'INDEMNISATION (Smart Contract Paramétrique)
    # ==========================================================================
    def calculer_indemnite(self, pluie_mesuree, temp_max):
        """Calcule l'indemnité selon une règle paramétrique objective."""
        capital_max = (self.superficie * 200) + (self.rendement * 25)
        
        # Trigger de catastrophe (100% indemnisation)
        if pluie_mesuree <= FAO_THRESHOLDS["pluie_critique"] or temp_max >= FAO_THRESHOLDS["temp_letal"]:
            taux = 1.0
        # Trigger de stress (Indemnisation proportionnelle/linéaire)
        elif pluie_mesuree < FAO_THRESHOLDS["pluie_confort"] or temp_max > FAO_THRESHOLDS["temp_echaudage"]:
            taux_pluie = (FAO_THRESHOLDS["pluie_confort"] - pluie_mesuree) / (FAO_THRESHOLDS["pluie_confort"] - FAO_THRESHOLDS["pluie_critique"])
            taux_temp = (temp_max - FAO_THRESHOLDS["temp_echaudage"]) / (FAO_THRESHOLDS["temp_letal"] - FAO_THRESHOLDS["temp_echaudage"])
            taux = max(taux_pluie, taux_temp)
        else:
            taux = 0.0
            
        return capital_max * min(taux, 1.0)

    # ==========================================================================
    # 3. LOGIQUE ACTUARIELLE (Calcul de la Prime Totale)
    # ==========================================================================
    def calculer_prime_totale(self):
        """Calcul de la prime annuelle (Risque IA + Chargement de frais)."""
        # Prime Pure = Risque ML * Coefficient de sécurité (Actuariat)
        prime_pure = self.risque_ml * 4.2
        
        # Chargement des frais de gestion (opérationnel)
        chargement_frais = (self.superficie * 12) + (self.rendement * 1.1)
        
        return prime_pure + chargement_frais

# ==============================================================================
# 4. SIMULATION D'UTILISATION
# ==============================================================================
if __name__ == "__main__":
    # Paramètres d'une parcelle test
    parcelle = ModeleAssuranceParametrique(superficie=10, rendement=20, risque_ml=0.275)
    
    # Données météo captées via API NASA POWER
    pluie_actuelle = 5.0
    temp_actuelle = 40.0
    
    indemnite = parcelle.calculer_indemnite(pluie_actuelle, temp_actuelle)
    prime = parcelle.calculer_prime_totale()
    
    print("--- RÉSULTATS DU MODÈLE D'ASSURANCE ---")
    print(f"Indemnité à verser : {indemnite:.2f} DT")
    print(f"Prime annuelle totale : {prime:.2f} DT")
