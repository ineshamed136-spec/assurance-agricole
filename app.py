    # ======================
    # ASSURANCE PARAMETRIQUE
    # ======================
    st.subheader(
        "🛡 Assurance Paramétrique"
    )

    evenement = None
    indemnite = 0

    # ======================
    # SECHERESSE SEVERE
    # ======================
    if pluie < 5 and temp > 35:

        evenement = "Sécheresse sévère"

        indemnite = (
            superficie * 180
            + production * 20
        )

    # ======================
    # CANICULE EXTREME
    # ======================
    elif temp > 45:

        evenement = "Canicule extrême"

        indemnite = (
            superficie * 150
            + production * 18
        )

    # ======================
    # TEMPETE / VENT VIOLENT
    # ======================
    elif vent > 25:

        evenement = "Vent violent"

        indemnite = (
            superficie * 120
            + production * 14
        )

    # ======================
    # HUMIDITE EXCESSIVE
    # ======================
    elif humidite > 90 and pluie > 40:

        evenement = "Humidité excessive"

        indemnite = (
            superficie * 100
            + production * 12
        )

    # ======================
    # RISQUE GLOBAL ELEVE
    # ======================
    elif risque > 80:

        evenement = "Risque climatique élevé"

        indemnite = (
            superficie * 130
            + production * 16
        )

    # ======================
    # RESULTATS PARAMETRIQUES
    # ======================
    if evenement is not None:

        st.error(
            f"⚠️ Événement détecté : {evenement}"
        )

        st.success(
            f"💰 Indemnisation automatique : {indemnite:.2f} DT"
        )

        st.info(
            "📌 Déclenchement automatique basé sur des seuils climatiques critiques"
        )

    else:

        st.success(
            "✅ Aucun seuil paramétrique déclenché"
        )
