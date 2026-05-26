# =========================
# ANALYSE
# =========================
if btn:

    # 🔥 RISQUE
    risque_final = min(
        max(
            (25.0 * cfg["facteur"])
            + (mois * 0.5)
            + (15 if irrigation == "Non" else 0),
            5.0
        ),
        95.0
    )

    risque_norm = risque_final / 100

    prod_totale = sup * prod
    cap_max = (sup * 200) + (prod_totale * 25)

    # =========================
    # 💳 PRIME (FORMULE CORRIGÉE SIMPLE)
    # =========================
    prime = cap_max * (0.02 + 0.01 * risque_norm)

    st.divider()

    a, b = st.columns(2)
    a.metric("🔥 Risque", f"{risque_final:.1f} %")
    b.metric("💳 Prime", f"{prime:.2f} DT")

    st.divider()

    # =========================
    # 💰 INDEMNITÉ (PARAMÉTRIQUE CORRIGÉE)
    # =========================
    if pl < cfg["seuil"]:

        # 🌧️ Trigger climatique (déficit de pluie)
        trigger = max(0, (cfg["seuil"] - pl) / cfg["seuil"])

        # 🔥 indemnité corrélée au risque
        indemn = cap_max * trigger * (0.5 + 0.5 * risque_norm)

        st.error(f"💰 Indemnité : {indemn:.2f} DT")

    else:
        st.success("✅ Pas de sinistre déclenché")

    # =========================
    # 📌 INTERPRÉTATION AMÉLIORÉE
    # =========================
    st.markdown("## 📌 Interprétation")

    st.markdown(f"""
- 🌧️ **Seuil de déclenchement : {cfg['seuil']} mm**
- 📊 Si pluie < seuil → activation automatique du contrat
- 🔥 Risque actuel : {risque_final:.1f} %

👉 Le système combine un **indice climatique (pluie)** et un **score de risque ML** pour ajuster les paiements.
""")

    # =========================
    # ℹ️ MÉTHODOLOGIE
    # =========================
    with st.expander("ℹ️ Modèle et formules"):

        st.markdown("""
### ⚙️ Déclenchement du sinistre
Un sinistre est déclenché lorsque la pluie mensuelle est inférieure au seuil régional.

### 💳 Prime
Prime = Capital × (0.02 + 0.01 × Risque)

### 💰 Indemnité
Indemnité = Capital × Trigger × (0.5 + 0.5 × Risque)

### 🌧️ Trigger climatique
Trigger = max(0, (Seuil - Pluie) / Seuil)
""")

        st.latex(
            r"Indemnité = Capital \times \max\left(0, \frac{Seuil - Pluie}{Seuil}\right) \times (0.5 + 0.5 \times Risque)"
        )
