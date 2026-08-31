import streamlit as st
import pandas as pd
import io

st.set_page_config(
    page_title="Suivi OPCVM Actions",
    layout="wide"
)

st.title("📈 Tableau de bord OPCVM")

uploaded_file = st.file_uploader(
    "Charger le fichier OPCVM",
    type=["xls", "xlsx"]
)

if uploaded_file:

    try:
        df = pd.read_excel(uploaded_file)
    except:
        st.error("Impossible de lire le fichier")
        st.stop()

    st.subheader("Données importées")
    st.dataframe(df, width="stretch")

    # KPIs

    col1, col2, col3 = st.columns(3)

    if "Nombre_Parts" in df.columns:
        total_parts = df["Nombre_Parts"].sum()
        col1.metric("Nombre total de parts", f"{total_parts:,.0f}")

    if "CMP_VL_Net" in df.columns:
        vl_moyenne = df["CMP_VL_Net"].mean()
        col2.metric("VL moyenne", f"{vl_moyenne:,.2f}")

    if "Description" in df.columns:
        nb_fonds = df["Description"].nunique()
        col3.metric("Nombre de fonds", nb_fonds)

    st.divider()

    # Calcul valorisation

    if (
        "Nombre_Parts" in df.columns
        and "CMP_VL_Net" in df.columns
    ):

        df["Valorisation"] = (
            df["Nombre_Parts"] *
            df["CMP_VL_Net"]
        )

        valorisation_totale = df["Valorisation"].sum()

        st.metric(
            "Valorisation totale",
            f"{valorisation_totale:,.0f} MAD"
        )

    st.divider()

    st.subheader("Répartition des valorisations")

    if "Valorisation" in df.columns:

        graphique = (
            df.groupby("Description")["Valorisation"]
            .sum()
            .sort_values(ascending=False)
        )

        st.bar_chart(graphique)

    st.divider()

    st.subheader("Statistiques")

    numeriques = df.select_dtypes(include="number")

    if not numeriques.empty:
        st.dataframe(
            numeriques.describe(),
            width="stretch"
        )

    # Export Excel

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            sheet_name="Résultat",
            index=False
        )

    st.download_button(
        label="📥 Télécharger Excel",
        data=output.getvalue(),
        file_name="Reporting_OPCVM.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Veuillez charger un fichier Excel.")
