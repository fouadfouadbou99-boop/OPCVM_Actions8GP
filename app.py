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

    for h in [0, 1, 2, 3, 4, 5]:

        try:

            fichier.seek(0)

            df = pd.read_excel(
                fichier,
                header=h
            )

            df.columns = [
                str(c).strip()
                for c in df.columns
            ]

            if any(
                "Maroclear" in c
                for c in df.columns
            ):
                return df

        except Exception:
            pass

    raise Exception(
        "Structure ASFIM non reconnue."
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

    # =====================================================
    # ASFIM
    # =====================================================

    if uploaded_asfim:

        try:

            asfim = lire_asfim(
                uploaded_asfim
            )

            st.header("📡 Mise à jour ASFIM")

            st.success(
                f"{len(asfim):,} lignes ASFIM chargées"
            )

            st.subheader("Colonnes ASFIM détectées")

            st.write(
                asfim.columns.tolist()
            )

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

            portefeuille["Valorisation_ASFIM"] = (
                portefeuille["Nombre_Parts"]
                * portefeuille[vl_col]
            )

            portefeuille["Ecart_VL"] = (
                portefeuille[vl_col]
                - portefeuille["CMP_VL_Net"]
            )

            st.header("📊 Dashboard ASFIM")

            d1, d2, d3, d4 = st.columns(4)

            d1.metric(
                "Nombre OPCVM",
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
                "Écart VL Moyen",
                f"{portefeuille['Ecart_VL'].mean():,.2f}"
            )

            st.subheader(
                "🏆 Top 10 Positions"
            )

            top10 = portefeuille.sort_values(
                "Valorisation_ASFIM",
                ascending=False
            ).head(10)

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

            st.subheader(
                "🏢 Répartition Société de Gestion"
            )

            sg = portefeuille.groupby(
                sg_col
            )[
                "Valorisation_ASFIM"
            ].sum()

            st.bar_chart(sg)

            st.subheader(
                "📑 Répartition Classification"
            )

            cl = portefeuille.groupby(
                class_col
            )[
                "Valorisation_ASFIM"
            ].sum()

            st.bar_chart(cl)

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
