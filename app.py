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
# FONCTION LECTURE ASFIM
# =====================================================

def lire_asfim(fichier):

    for header in range(0, 6):

        try:

            fichier.seek(0)

            df = pd.read_excel(
                fichier,
                header=header
            )

            df.columns = [
                str(c).strip()
                for c in df.columns
            ]

            if "Code Maroclear" in df.columns:
                return df

        except:
            pass

    raise Exception(
        "Impossible d'identifier les colonnes ASFIM"
    )


# =====================================================
# PORTEFEUILLE
# =====================================================

if uploaded_portefeuille is not None:

    portefeuille = pd.read_excel(
        uploaded_portefeuille
    )

    portefeuille.columns = [

        str(c)
        .replace(" ", "_")
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

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Nombre OPCVM",
        len(portefeuille)
    )

    if "Nombre_Parts" in portefeuille.columns:

        c2.metric(
            "Nombre Parts",
            f"{portefeuille['Nombre_Parts'].sum():,.0f}"
        )

    if "CMP_VL_Net" in portefeuille.columns:

        c3.metric(
            "VL Moyenne",
            f"{portefeuille['CMP_VL_Net'].mean():,.2f}"
        )

    # =================================================
    # ASFIM
    # =================================================

    if uploaded_asfim is not None:

        try:

            asfim = lire_asfim(
                uploaded_asfim
            )

            st.header("📡 Mise à jour ASFIM")

            st.success(
                f"{len(asfim)} lignes ASFIM chargées"
            )

            # -----------------------------------------
            # NORMALISATION DES CODES
            # -----------------------------------------

            portefeuille["Code"] = (

                pd.to_numeric(
                    portefeuille["Code"],
                    errors="coerce"
                )
                .fillna(0)
                .astype(int)
                .astype(str)

            )

            asfim["Code Maroclear"] = (

                pd.to_numeric(
                    asfim["Code Maroclear"],
                    errors="coerce"
                )
                .fillna(0)
                .astype(int)
                .astype(str)

            )

            # -----------------------------------------
            # MERGE
            # -----------------------------------------

            resultat = portefeuille.merge(

                asfim[
                    [
                        "Code Maroclear",
                        "OPCVM",
                        "Société de Gestion",
                        "Classification",
                        "VL"
                    ]
                ],

                left_on="Code",
                right_on="Code Maroclear",
                how="left"

            )

            # -----------------------------------------
            # SI PAS DE MATCH PAR CODE
            # -----------------------------------------

            if resultat["VL"].notna().sum() == 0:

                portefeuille["Description"] = (
                    portefeuille["Description"]
                    .astype(str)
                    .str.upper()
                    .str.strip()
                )

                asfim["OPCVM"] = (
                    asfim["OPCVM"]
                    .astype(str)
                    .str.upper()
                    .str.strip()
                )

                resultat = portefeuille.merge(

                    asfim[
                        [
                            "OPCVM",
                            "Société de Gestion",
                            "Classification",
                            "VL"
                        ]
                    ],

                    left_on="Description",
                    right_on="OPCVM",
                    how="left"

                )

            nb_match = resultat["VL"].notna().sum()

            st.info(
                f"VL trouvées : {nb_match} / {len(resultat)}"
            )

            # -----------------------------------------
            # CALCULS
            # -----------------------------------------

            resultat["VL"] = pd.to_numeric(
                resultat["VL"],
                errors="coerce"
            )

            resultat["Nombre_Parts"] = pd.to_numeric(
                resultat["Nombre_Parts"],
                errors="coerce"
            )

            resultat["Valorisation_ASFIM"] = (
                resultat["Nombre_Parts"]
                * resultat["VL"]
            )

            resultat["Valorisation_ASFIM"] = (
                resultat["Valorisation_ASFIM"]
                .fillna(0)
            )

            if "CMP_VL_Net" in resultat.columns:

                resultat["Ecart_VL"] = (
                    resultat["VL"]
                    - resultat["CMP_VL_Net"]
                )

            # -----------------------------------------
            # KPI
            # -----------------------------------------

            st.header("📊 Dashboard ASFIM")

            d1, d2, d3, d4 = st.columns(4)

            d1.metric(
                "Nombre OPCVM",
                len(resultat)
            )

            d2.metric(
                "Valorisation",
                f"{resultat['Valorisation_ASFIM'].sum():,.0f} MAD"
            )

            d3.metric(
                "VL Moyenne",
                f"{resultat['VL'].mean():,.2f}"
            )

            if "Ecart_VL" in resultat.columns:

                d4.metric(
                    "Ecart VL Moyen",
                    f"{resultat['Ecart_VL'].mean():,.2f}"
                )

            # -----------------------------------------
            # TOP POSITIONS
            # -----------------------------------------

            st.subheader("🏆 Top 10 Positions")

            top10 = (
                resultat
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

            # -----------------------------------------
            # EXPORT
            # -----------------------------------------

            sortie = io.BytesIO()

            with pd.ExcelWriter(
                sortie,
                engine="openpyxl"
            ) as writer:

                resultat.to_excel(
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
                sortie.getvalue(),
                file_name="Reporting_OPCVM_Complet.xlsx",
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
    "Dernière actualisation : "
    + datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )
)
