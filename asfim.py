# ==================================================
# ASFIM
# ==================================================

st.divider()

st.header("📡 Données ASFIM")

col1, col2 = st.columns(2)

with col1:

    charger = st.button(
        "📥 Charger les données ASFIM"
    )

with col2:

    refresh = st.button(
        "🔄 Rafraîchir ASFIM"
    )

if refresh:
    st.cache_data.clear()

if charger or refresh:

    try:

        asfim_df = recuperer_asfim()

        st.success(
            f"{len(asfim_df)} lignes récupérées"
        )

        st.dataframe(
            asfim_df,
            width="stretch"
        )

        output = io.BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            asfim_df.to_excel(
                writer,
                index=False,
                sheet_name="ASFIM"
            )

        st.download_button(
            label="📥 Télécharger ASFIM.xlsx",
            data=output.getvalue(),
            file_name="ASFIM.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error(
            f"Erreur ASFIM : {e}"
        )
