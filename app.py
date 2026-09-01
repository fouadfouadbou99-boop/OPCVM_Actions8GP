import streamlit as st
import pandas as pd
import io
from datetime import datetime

# =====================================================
# CONFIG
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
# ASFIM
# =====================================================

def lire_asfim(fichier):

    for header in range(6):

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

            return df

        except Exception:
            pass

    raise Exception(
        "Impossible de lire ASFIM"
    )

# =====================================================
# APP
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

    tabs = st.tabs(
        [
            "📂 Portefeuille",
            "📊 Dashboard",
            "📥 Reporting"
        ]
    )

    tab_portefeuille = tabs[0]
    tab_dashboard = tabs[1]
    tab_reporting = tabs[2]

    with tab_portefeuille:

        st.subheader(
            "Portefeuille"
        )

        st.dataframe(
            portefeuille,
            width="stretch"
        )

    if uploaded_asfim is not None:

        try:

            asfim = lire_asfim(
                uploaded_asfim
            )

            # =================================
            # DETECTION DES COLONNES
            # =================================

            col_code = None
            col_vl = None
            col_opcvm = None
            col_sg = None
            col_classif = None

            for col in asfim.columns:

                texte = str(col)

                if "Maroclear" in texte:
                    col_code = col

                if texte == "VL":
                    col_vl = col

                if "OPCVM" == texte:
                    col_opcvm = col

                if "Société" in texte:
                    col_sg = col

                if "Classification" in texte:
                    col_classif = col

            if col_code is None:

                st.error(
                    "Colonne Maroclear introuvable."
                )

                st.write(
                    asfim.columns.tolist()
                )

                st.stop()

            portefeuille["Code"] = (

                pd.to_numeric(
                    portefeuille["Code"],
                    errors="coerce"
                )

                .fillna(0)
                .astype(int)
                .astype(str)
            )

            asfim[col_code] = (

                pd.to_numeric(
                    asfim[col_code],
                    errors="coerce"
                )

                .fillna(0)
                .astype(int)
                .astype(str)
            )

            resultat = portefeuille.merge(

                asfim[
                    [
                        col_code,
                        col_opcvm,
                        col_sg,
                        col_classif,
                        col_vl
                    ]
                ],

                left_on="Code",
                right_on=col_code,
                how="left"

            )

            resultat.rename(
                columns={
                    col_vl: "VL",
                    col_sg: "Societe_Gestion",
                    col_classif: "Classification",
                    col_opcvm: "OPCVM"
                },
                inplace=True
            )

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
                *
                resultat["VL"]

            )

            if (
                "CMP_VL_Net"
                in resultat.columns
            ):

                resultat["PMV"] = (

                    resultat["VL"]

                    -

                    resultat["CMP_VL_Net"]

                )

            with tab_dashboard:

                vl_trouvees = (
                    resultat["VL"]
                    .notna()
                    .sum()
                )

                st.success(
                    f"VL trouvées : {vl_trouvees}/{len(resultat)}"
                )

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "OPCVM",
                    len(resultat)
                )

                c2.metric(
                    "Valorisation",
                    f"{resultat['Valorisation_ASFIM'].sum():,.0f} MAD"
                )

                c3.metric(
                    "VL Moyenne",
                    f"{resultat['VL'].mean():,.2f}"
                )

                if "PMV" in resultat.columns:

                    c4.metric(
                        "PMV Moyenne",
                        f"{resultat['PMV'].mean():,.2f}"
                    )

                top10 = (

                    resultat

                    .sort_values(
                        "Valorisation_ASFIM",
                        ascending=False
                    )

                    .head(10)

                )

                st.subheader(
                    "Top 10 Positions"
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

            with tab_reporting:

                output = io.BytesIO()

                with pd.ExcelWriter(
                    output,
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
                    "📥 Télécharger Reporting",
                    data=output.getvalue(),
                    file_name="Reporting_OPCVM.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:

            st.error(
                f"Erreur ASFIM : {e}"
            )

st.divider()

st.caption(
    "Dernière actualisation : "
    + datetime.now().strftime("%d/%m/%Y %H:%M")
)
