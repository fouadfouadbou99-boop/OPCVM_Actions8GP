import streamlit as st
import pandas as pd
import numpy as np
import io

# ==========================
# CONFIGURATION
# ==========================

st.set_page_config(
    page_title="Tableau de Bord OPCVM",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Tableau de Bord OPCVM")

# ==========================
# FONCTION ASFIM
# ==========================

@st.cache_data(ttl=3600)
def charger_donnees_asfim():

    url = "https://asfim.ma/publications/tableaux-des-performances/"

    tables = pd.read_html(url)

    if len(tables) > 0:
        return tables[0]

    return pd.DataFrame()

# ==========================
# SIDEBAR
# ==========================

st.sidebar.header("Actions")

fichier = st.sidebar.file_uploader(
    "Importer le portefeuille OPCVM",
    type=["xls", "xlsx"]
)

# ==========================
# PORTEFEUILLE
# ==========================

if fichier:

    try:
        df = pd.read_excel(fichier)

    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        st.stop()

    st.subheader("Portefeuille")

    st.dataframe(
        df,
        width="stretch"
    )

    # =====================================
    # NORMALISATION DES COLONNES
    # =====================================

    df.columns = (
        df.columns
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    # =====================================
    # KPI
    # =====================================

    st.subheader("Indicateurs Clés")

    c1, c2, c3, c4 = st.columns(4)

    nb_fonds = len(df)

    c1.metric(
        "Nombre OPCVM",
        nb_fonds
    )

    if "Nombre_Parts" in df.columns:

        c2.metric(
            "Nombre de Parts",
            f"{df['Nombre_Parts'].sum():,.0f}"
        )

    if "CMP_VL_Net" in df.columns:

        c3.metric(
            "VL Moyenne",
            f"{df['CMP_VL_Net'].mean():,.2f}"
        )

    # =====================================
    # VALORISATION
    # =====================================

    if (
        "Nombre_Parts" in df.columns
        and "CMP_VL_Net" in df.columns
    ):

        df["Valorisation"] = (
            df["Nombre_Parts"] *
            df["CMP_VL_Net"]
        )

        valorisation_totale = df["Valorisation"].sum()

        c4.metric(
            "Valorisation Totale",
            f"{valorisation_totale:,.0f} MAD"
        )

    # =====================================
    # PMV
    # =====================================

    if (
        "Valo_Unitaire_(S_1)" in df.columns
        and "CMP_VL_Net" in df.columns
    ):

        df["PMV"] = (
            df["CMP_VL_Net"]
            - df["Valo_Unitaire_(S_1)"]
        )

    # =====================================
    # TOP POSITIONS
    # =====================================

    if "Valorisation" in df.columns:

        st.subheader("Top Positions")

        top = (
            df[["Description", "Valorisation"]]
            .sort_values(
                by="Valorisation",
                ascending=False
            )
            .head(10)
        )

        st.dataframe(
            top,
            width="stretch"
        )

    # =======================
