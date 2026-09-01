import streamlit as st
import pandas as pd
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
# FONCTION ASFIM
# =====================================================

def lire_asfim(fichier):

    essais = [0, 1, 2, 3, 4, 5]

    for h in essais:

        try:

            df = pd.read_excel(
                fichier,
                header=h
            )

            noms = [
                str(c).strip()
                for c in df.columns
            ]

            if any(
                "Maroclear" in c
                for c in noms
            ):

                df.columns = noms
                return df

        except:
            pass

    raise Exception(
        "Impossible d'identifier automatiquement les colonnes ASFIM."
    )

# =====================================================
# PORTEFEUILLE
# =====================================================

if uploaded_portefeuille:

    try:

        portefeuille = pd.read_excel(
            uploaded_portefeuille
        )

    except Exception as e:

        st.error(
            f"Erreur lecture portefeuille : {e}"
        )
        st.stop()

    portefeuille.columns = [

        str(col)
        .replace(" ", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")

        for col in portefeuille.columns
    ]

    st.header("📂 Portefeuille")

    st.dataframe(
        portefeuille,
        width="stretch"
    )

    # KPI PORTFEUILLE

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

    if uploaded_asfim:

        try:

            asfim = lire_asfim(
                uploaded_asfim
            )

            st.header("📡 Mise à jour ASFIM")

            st.success(
                f"{len(asfim):,} OPCVM ASFIM chargés"
            )

            # Détection automatique

            code_col = next(
                c for c in asfim.columns
                if "Maroclear" in c
            )

            opcvm_col = next(
                c for c in asfim.columns
                if "OPCVM" in c
            )

            vl_col = next(
                c for c in asfim.columns
                if c == "VL"
            )

            sg_col = next(
                c for c in asfim.columns
                if "Société" in c
            )

            class_col = next(
                c for c in asfim.columns
                if "Classification" in c
            )

            portefeuille["Code"] = (
                portefeuille["Code"]
                .astype(str)
            )

            asfim[code_col] = (
                asfim[code_col]
                .astype(str)
            )

            portefeuille = portefeuille.merge(
                asfim[
                    [
                        code_col,
                        opcvm_col,
                        sg_col,
                        class_col,
                        vl_col
                    ]
                ],
                left_on="Code",
                right_on=code_col,
                how="left"
            )

            # ==========================================
            # VALORISATION
            # ==========================================

            portefeuille["Valorisation_ASFIM"] = (
                portefeuille["Nombre_Parts"]
                * portefeuille[vl_col]
            )

            portefeuille["Ecart_VL"] = (
                portefeuille[vl_col]
                -
                portefeuille["CMP_VL_Net"]
            )

            # ==========================================
            # DASHBOARD
            # ==========================================

            st.header(
                "📊 Dashboard ASFIM"
            )

            d1, d2, d3, d4 = st.columns(4)

            d1.metric(
                "OPCVM",
                len(portefeuille)
            )

            d2.metric(
                "Valorisation",
                f"{portefeuille['Valorisation_ASFIM'].sum():,.0f} MAD"
            )

            d3.metric(
                "VL Moyenne",
                f"{portefeuille[vl_col].mean():,.2f}"
            )

            d4.metric(
                "Écart VL",
                f"{portefeuille['Ecart_VL'].mean():,.2f}"
            )

            # ==========================================
            # TOP 10
            # ==========================================

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
                )[
                    "Valorisation_ASFIM"
                ]
            )

            # ==========================================
            # REPARTITION GESTION
            # ==========================================

            st.subheader(
                "🏢 Société de Gestion"
            )

            sg = portefeuille.groupby(
                sg_col
            )[
                "Valorisation_ASFIM"
            ].sum()

            st.bar_chart(sg)

            # ==========================================
            # CLASSIFICATION
            # ==========================================

            st.subheader(
                "📑 Classification"
            )

            cl = portefeuille.groupby(
                class_col
            )[
                "Valorisation_ASFIM"
            ].sum()

            st.bar_chart(cl)

            # ==========================================
            # EXPORT
            # ==========================================

            sortie = io.BytesIO()

            with pd.ExcelWriter(
                sortie,
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
`
