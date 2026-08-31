
import streamlit as st
import pandas as pd

st.set_page_config(page_title="OPCVM Dashboard", layout="wide")
st.title("Suivi OPCVM")

uploaded = st.file_uploader("Charger un fichier Excel", type=["xls","xlsx"])

if uploaded:
    try:
        df = pd.read_excel(uploaded)
    except Exception:
        df = pd.read_excel(uploaded, header=None)

    st.subheader("Données")
    st.dataframe(df, use_container_width=True)

    st.subheader("Statistiques")
    num_cols = df.select_dtypes(include='number').columns
    if len(num_cols)>0:
        st.dataframe(df[num_cols].describe(), use_container_width=True)

    if len(num_cols)>0:
        col = st.selectbox('Variable', num_cols)
        st.bar_chart(df[col])
else:
    st.info('Chargez le fichier OPCVM pour lancer l’analyse.')
