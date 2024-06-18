import streamlit as st
import pandas as pd
import time

# def loader():
#     latest_iteration = st.empty()
#     bar = st.progress(0)

# Initializing variables
form_types = ("ICCM", "OPD", "RHGynobs", "Vaccination")

st.title("MSF OCR Tool")

st.write("### File Upload ###")

# results = ocr.run()

tally_sheet = st.file_uploader(
    "Please upload one or more images of a tally sheet",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
    )

if len(tally_sheet) > 0:
    
    # loader()
    
    form_type = st.selectbox(
        "Which type of form is this?",
        form_types,
        index=None
    )

    if form_type == "ICCM":
        df = pd.DataFrame({
            'Column 1': [1, 2, 3, 4],
            'Column 2': [4, 3, 2, 1]
        })
    else:
        df = None

    @st.cache_data
    def convert_df(df):
        return df.to_csv().encode("utf-8")

    edited_df = st.data_editor(df)

    st.download_button(
        label="Download data as CSV",
        data = convert_df(edited_df),
        file_name="results.csv",
        mime="text/csv"
        )