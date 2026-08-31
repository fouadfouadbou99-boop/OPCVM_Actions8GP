import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import io

# ==================================================
# CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Suivi OPCVM",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Tableau de Bord OPCVM")

# ==================================================
# FONCTION ASFIM
# ==================================================

@st.cache_data(ttl=3600)
def recuperer_liens_asfim():

    url = "https://asfim.ma/publications/tableaux-des-performances/"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    liens = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if any(
            ext in href.lower()
            for ext in [
                ".xlsx",
                ".xls",
                ".csv"
            ]
        ):

            if href.startswith("/"):

                href = (
                    "https://asfim.ma"
                    + href
                )

            liens.append(href)

    return liens


# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.header("Paramètres")

uploaded_file = st.sidebar.file_uploader(
    "Charger le portefeuille OPCVM",
    type=["xlsx", "xls"]
)

# ==================================================
# PORTFEUILLE
# ==================================================

if uploaded_file:

    try:

        df = pd.read_excel(
            uploaded_file
        )

    except Exception as e:

        st.error(
            f"Erreur lecture fichier : {e}"
        )
        st.stop()

    st.header("Portefeuille")

    st.dataframe(
        df,
        width="stretch"
    )

    # ------------------------------------------------

    df.columns = [
        str(c)
        .replace(" ", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        for c in df.columns
    ]

    # ==================================================
    # KPIs
    # ==================================================

    st.subheader("Indicateurs")

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

    # ==================================================
    # VALORISATION
    # ==================================================

    if (
        "Nombre_Parts" in df.columns
        and
        "CMP_VL_Net" in df.columns
    ):

        df["Valorisation"] = (
            df["Nombre_Parts"]
            *
            df["CMP_VL_Net"]
        )

        valorisation_totale = (
            df["Valorisation"]
            .sum()
        )

        c4.metric(
            "Valorisation Totale",
            f"{valorisation_totale:,.0f} MAD"
        )

    # ==================================================
    # TOP POSITIONS
    # ==================================================

    if (
        "Description" in df.columns
        and
        "Valorisation" in df.columns
    ):

        st.subheader(
            "Top 10 Positions"
        )

        top10 = (
            df[
                [
                    "Description",
                    "Valorisation"
                ]
            ]
            .sort_values(
                "Valorisation",
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

    # ==================================================
    # STATISTIQUES
    # ==================================================

    st.subheader(
        "Statistiques"
    )

    numeric_df = df.select_dtypes(
        include=np.number
    )

    if not numeric_df.empty:

        st.dataframe(
            numeric_df.describe(),
            width="stretch"
        )

    # ==================================================
    # EXPORT EXCEL
    # ==================================================

    st.subheader(
        "Export Reporting"
    )

    buffer = io.BytesIO()

    with pd.ExcelWriter(
        buffer,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Portefeuille"
        )

    st.download_button(
        label="📥 Télécharger Reporting Excel",
        data=buffer.getvalue(),
        file_name="Reporting_OPCVM.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==================================================
# ASFIM
# ==================================================

st.divider()

st.header(
    "📡 Données ASFIM"
)

if st.button(
    "Rechercher les fichiers ASFIM"
):

    try:

        liens = recuperer_liens_asfim()

        if len(liens) == 0:

            st.warning(
                "Aucun fichier détecté."
            )

        else:

            st.success(
                f"{len(liens)} fichier(s) trouvé(s)"
            )

            liens_df = pd.DataFrame(
                {
                    "Lien": liens
                }
            )

            st.dataframe(
                liens_df,
                width="stretch"
            )

            excel_buffer = io.BytesIO()

            with pd.ExcelWriter(
                excel_buffer,
                engine="openpyxl"
            ) as writer:

                liens_df.to_excel(
                    writer,
                    index=False,
                    sheet_name="ASFIM"
                )

            st.download_button(
                "📥 Télécharger la liste ASFIM",
                excel_buffer.getvalue(),
                file_name="ASFIM_FICHIERS.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:

        st.error(
            f"Erreur ASFIM : {e}"
        )

# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "Application OPCVM - Version 1.0"
)
