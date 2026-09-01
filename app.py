import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime

# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Dashboard OPCVM",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Tableau de Bord OPCVM")

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("Chargement des données")

uploaded_portefeuille = st.sidebar.file_uploader(
    "Portefeuille OPCVM",
    type=["xlsx", "xls"]
)

uploaded_asfim = st.sidebar.file_uploader(
    "Fichier ASFIM",
    type=["xlsx"]
)

# =====================================================
# PORTEFEUILLE
# =====================================================

if uploaded_portefeuille:

    portefeuille = pd.read_excel(
        uploaded_portefeuille
    )

    portefeuille.columns = [
        str(c).replace(" ", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        for c in portefeuille.columns
    ]

    st.header("📂 Portefeuille")

    st.dataframe(
        portefeuille,
        width="stretch"
    )

    # =================================================
    # KPI DE BASE
    # =================================================

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Nombre OPCVM",
        len(portefeuille)
    )

    if "Nombre_Parts" in portefeuille.columns:

        col2.metric(
            "Nombre Parts",
            f"{portefeuille['Nombre_Parts'].sum():,.0f}"
        )

    if "CMP_VL_Net" in portefeuille.columns:

        col3.metric(
            "VL Moyenne",
            f"{portefeuille['CMP_VL_Net'].mean():,.2f}"
        )

    # =================================================
    # ASFIM
    # =================================================

    if uploaded_asfim:

        st.header("📡 Mise à jour ASFIM")

        asfim = pd.read_excel(
            uploaded_asfim
        )

        st.success(
            f"{len(asfim):,} OPCVM ASFIM chargés"
        )

        portefeuille["Code"] = (
            portefeuille["Code"]
            .astype(str)
        )

        asfim["Code Maroclear"] = (
            asfim["Code Maroclear"]
            .astype(str)
        )

        portefeuille = portefeuille.merge(
            asfim[
                [
                    "Code Maroclear",
                    "OPCVM",
                    "Société de Gestion",
                    "Classification",
                    "VL",
                    "YTD",
                    "1 semaine"
                ]
            ],
            left_on="Code",
            right_on="Code Maroclear",
            how="left"
        )

        # =============================================
        # VALORISATION
        # =============================================

        if (
            "Nombre_Parts" in portefeuille.columns
            and
            "VL" in portefeuille.columns
        ):

            portefeuille["Valorisation_ASFIM"] = (
                portefeuille["Nombre_Parts"]
                *
                portefeuille["VL"]
            )

        if (
            "VL" in portefeuille.columns
            and
            "CMP_VL_Net" in portefeuille.columns
        ):

            portefeuille["Ecart_VL"] = (
                portefeuille["VL"]
                -
                portefeuille["CMP_VL_Net"]
            )

        # =============================================
        # DASHBOARD
        # =============================================

        st.header("📊 Dashboard")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "OPCVM",
            len(portefeuille)
        )

        c2.metric(
            "Valorisation",
            f"{portefeuille['Valorisation_ASFIM'].sum():,.0f} MAD"
        )

        c3.metric(
            "VL Moyenne",
            f"{portefeuille['VL'].mean():,.2f}"
        )

        c4.metric(
            "Écart Moyen",
            f"{portefeuille['Ecart_VL'].mean():,.2f}"
        )

        # =============================================
        # TOP POSITIONS
        # =============================================

        st.subheader(
            "🏆 Top 10 Positions"
        )

        top10 = (
            portefeuille
            .sort_values(
                "Valorisation_ASFIM",
                ascending=False
            )
            .head(10)
        )

        st.dataframe(
            top10[
                [
                    "Description",
                    "Valorisation_ASFIM"
                ]
            ],
            width="stretch"
        )

        st.bar_chart(
            top10.set_index(
                "Description"
            )["Valorisation_ASFIM"]
        )

        # =============================================
        # TOP GAGNANTS
        # =============================================

        if "1 semaine" in portefeuille.columns:

            st.subheader(
                "🚀 Meilleures Performances"
            )

            gagnants = (
                portefeuille
                .sort_values(
                    "1 semaine",
                    ascending=False
                )
                .head(10)
            )

            st.dataframe(
                gagnants[
                    [
                        "Description",
                        "1 semaine"
                    ]
                ],
                width="stretch"
            )

            st.subheader(
                "🔻 Plus fortes baisses"
            )

            perdants = (
                portefeuille
                .sort_values(
                    "1 semaine"
                )
                .head(10)
            )

            st.dataframe(
                perdants[
                    [
                        "Description",
                        "1 semaine"
                    ]
                ],
                width="stretch"
            )

        # =============================================
        # SOCIETE DE GESTION
        # =============================================

        st.subheader(
            "🏢 Répartition par société de gestion"
        )

        sg = (
            portefeuille
            .groupby(
                "Société de Gestion"
            )["Valorisation_ASFIM"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        st.bar_chart(sg)

        # =============================================
        # CLASSIFICATION
        # =============================================

        st.subheader(
            "📑 Répartition par classification"
        )

        classe = (
            portefeuille
            .groupby(
                "Classification"
            )["Valorisation_ASFIM"]
            .sum()
        )

        st.bar_chart(classe)

        # =============================================
        # EXPORT
        # =============================================

        buffer = io.BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine="openpyxl"
        ) as writer:

            portefeuille.to_excel(
                writer,
                sheet_name="Portefeuille",
                index=False
            )

            asfim.to_excel(
                writer,
                sheet_name="ASFIM",
                index=False
            )

        st.download_button(
            "📥 Télécharger Reporting Complet",
            buffer.getvalue(),
            "Reporting_OPCVM_Complet.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# =====================================================
# FOOTER
# =====================================================

st.divider()

st.caption(
    f"Dernière actualisation : "
    f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
)
