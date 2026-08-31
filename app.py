import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime

# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Tableau de Bord OPCVM",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Tableau de Bord OPCVM")

# =====================================================
# ASFIM
# =====================================================

@st.cache_data(ttl=3600)
def recuperer_asfim():

    url = "https://asfim.ma/publications/tableaux-des-performances/"

    tables = pd.read_html(url)

    if len(tables) == 0:
        raise Exception("Aucune donnée ASFIM trouvée")

    return tables[0]

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("Paramètres")

uploaded_file = st.sidebar.file_uploader(
    "Charger le portefeuille OPCVM",
    type=["xlsx", "xls"]
)

st.sidebar.success(
    "✅ Application opérationnelle"
)

# =====================================================
# PORTEFEUILLE
# =====================================================

if uploaded_file is not None:

    try:

        df = pd.read_excel(uploaded_file)

        st.header("📁 Portefeuille")

        st.dataframe(
            df,
            width="stretch"
        )

        # -----------------------------------------
        # NORMALISATION DES COLONNES
        # -----------------------------------------

        df.columns = (
            df.columns.astype(str)
            .str.replace(" ", "_")
            .str.replace("-", "_")
            .str.replace("(", "", regex=False)
            .str.replace(")", "", regex=False)
        )

        # -----------------------------------------
        # KPIs
        # -----------------------------------------

        st.subheader("📊 Indicateurs")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Nombre OPCVM",
            len(df)
        )

        if "Nombre_Parts" in df.columns:

            c2.metric(
                "Nombre Parts",
                f"{df['Nombre_Parts'].sum():,.0f}"
            )

        if "CMP_VL_Net" in df.columns:

            c3.metric(
                "VL Moyenne",
                f"{df['CMP_VL_Net'].mean():,.2f}"
            )

        if (
            "Nombre_Parts" in df.columns
            and
            "CMP_VL_Net" in df.columns
        ):

            df["Valorisation"] = (
                df["Nombre_Parts"]
                * df["CMP_VL_Net"]
            )

            valorisation_totale = (
                df["Valorisation"].sum()
            )

            c4.metric(
                "Valorisation Totale",
                f"{valorisation_totale:,.0f} MAD"
            )

        # -----------------------------------------
        # TOP 10
        # -----------------------------------------

        if (
            "Description" in df.columns
            and
            "Valorisation" in df.columns
        ):

            st.subheader(
                "🏆 Top 10 Positions"
            )

            top10 = (
                df[
                    [
                        "Description",
                        "Valorisation"
                    ]
                ]
                .sort_values(
                    by="Valorisation",
                    ascending=False
                )
                .head(10)
            )

            st.dataframe(
                top10,
                width="stretch"
            )

            st.bar_chart(
                top10.set_index(
                    "Description"
                )
            )

        # -----------------------------------------
        # STATISTIQUES
        # -----------------------------------------

        st.subheader(
            "📈 Statistiques"
        )

        num = df.select_dtypes(
            include=np.number
        )

        if not num.empty:

            st.dataframe(
                num.describe(),
                width="stretch"
            )

        # -----------------------------------------
        # EXPORT EXCEL
        # -----------------------------------------

        st.subheader(
            "📥 Export Reporting"
        )

        output = io.BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="Portefeuille"
            )

        st.download_button(
            label="📥 Télécharger Reporting Excel",
            data=output.getvalue(),
            file_name="Reporting_OPCVM.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error(
            f"Erreur : {e}"
        )

# =====================================================
# ASFIM
# =====================================================

st.divider()

st.header(
    "📡 Données ASFIM"
)

col1, col2 = st.columns(2)

with col1:

    charger = st.button(
        "📥 Charger ASFIM"
    )

with col2:

    refresh = st.button(
        "🔄 Rafraîchir ASFIM"
    )

if refresh:

    st.cache_data.clear()

if charger or refresh:

    try:

        with st.spinner(
            "Chargement ASFIM..."
        ):

            asfim_df = recuperer_asfim()

        st.success(
            f"{len(asfim_df)} lignes récupérées"
        )

        st.dataframe(
            asfim_df,
            width="stretch"
        )

        export_asfim = io.BytesIO()

        with pd.ExcelWriter(
            export_asfim,
            engine="openpyxl"
        ) as writer:

            asfim_df.to_excel(
                writer,
                sheet_name="ASFIM",
                index=False
            )

        st.download_button(
            "📥 Télécharger ASFIM.xlsx",
            export_asfim.getvalue(),
            file_name="ASFIM.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error(
            f"Erreur ASFIM : {e}"
        )

# =====================================================
# FOOTER
# =====================================================

st.divider()

st.caption(
    f"Dernière actualisation : "
    f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
)
