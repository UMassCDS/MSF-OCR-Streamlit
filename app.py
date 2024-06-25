import streamlit as st
import pandas as pd
import json
import data_upload_DHIS2 as dhis2

# Initializing variables
form_types = ("ICCM", "OPD", "RHGynobs", "Vaccination")
# Ideally, these could be set in this app?
# dhis2_username = ''
# dhis2_password = ''
# DHIS2_Test_Server_URL = ''


# Function definitions!
# """ Creates a list of dataValues by going through each cell
# and recording the column, header, and cell value of non-None

# :param df: an iterable of data frames
# :return: a list of JSON-ready dataValues
# """
def data_values(dfs):
    data_values = []
    for df in dfs:
        columns = df.columns.tolist()
        for col, i in df.iterrows():
            for cell in columns:
                if i[cell] is not None:
                    new_cell = {"dataElement": f"{col}/{cell}", "value": f"{i[cell]}"}
                    data_values.append(new_cell)
    return data_values
            
# @st.cache_data
# Ideally this would cache data but it messes with filling in info
# """ Creates a JSON payload through the form inputs and, if not empty,
# calling the getUID command to find the proper ID.

# :param df: an iterable of data frames
# :return: the JSON payload
# """
def convert_df(dfs):
    json_export = {}
    
    if data_set == "":
        data_set_id = ""
    else:
        data_set_id = dhis2.getUID("dataSets", data_set)
    json_export["dataSet"] = f"{data_set_id}"
    
    json_export["period"] = f"{period_start}P7D"
    
    if org_unit == "":
        org_unit_id = ""
    else:
        org_unit_id = dhis2.getUID("organisationUnits", org_unit)
        
    json_export["orgUnit"] = f"{org_unit_id}"
    
    json_export["dataValues"] = data_values(dfs.values())
    return json.dumps(json_export)


# Initial Display
st.title("MSF OCR Tool")
st.write("### File Upload ###")
tally_sheet = st.file_uploader(
    "Please upload one or more images of a tally sheet",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
    )

# Displaying images so the user can see them
with st.expander("Show Images"):
    for sheet in tally_sheet:
        st.image(sheet)

# Once images are uploaded
if len(tally_sheet) > 0:
    
    # Will have prefilled data when OCR works
    form_type = st.selectbox(
        "Which type of form is this?",
        form_types,
        index=None
    )
    data_set = st.text_input("Data Set:")
    org_unit = st.text_input("Organization Unit:")
    period_start = st.date_input("Period Start Date:", format="YYYY-MM-DD")
    period_end = st.date_input("Period End Date:", format="YYYY-MM-DD")

    
    if form_type == "ICCM":
        # Hardcoded sheets, ideally replace with metadata get
        dfs = [
            pd.DataFrame({
                '2-5m': [None, None, None, None, None, None, None, None, None, None],
                '6-59m': [None, None, None, None, None, None, None, None, None, None],
                '5-14y': [None, None, None, None, None, None, None, None, None, None],
                ">=15y": [None, None, None, None, None, None, None, None, None, None]
            }, index=["No. of consultations", "Patients treated repeat past 28d", "No. of patients with RDT performed", "No. RDT+: P. falciparum", "No. RDT+: P. falciparum and/or mixed", "No. RDT+: non P. falciparum", "RDT+ treated with ACT past 28 days", "No. of patients with danger signs", "No. with bloody diarrhoea", "No. with acute watery diarrhoea"]),
            pd.DataFrame({
                '6-59m': [None, None, None, None],
            }, index=["Bilateral oedema", "MUAC SAM", "MUAC MAN", "MUAC no AM"]),
            pd.DataFrame({
                '2-5m': [None, None, None, None, None, None, None, None, None, None, None, None],
                '6-59m': [None, None, None, None, None, None, None, None, None, None, None, None],
                '5-14y': [None, None, None, None, None, None, None, None, None, None, None, None],
                ">=15y": [None, None, None, None, None, None, None, None, None, None, None, None]
            }, index=["Uncomplicated malaria", "Suspected severe malaria", "Uncomplicated pneumonia", "Uncomplicated diarrhoea", "Cough/cold", "Severe acute malnutrition", "Other (uncomplicated)", "Other (severe)", "Malaria with severe acute malnutrition", "Malaria with pneumonia", "Malaria with diarrhoea", "Other combination"]),
            pd.DataFrame({
                '2-5m': [None, None, None, None, None, None],
                '6-59m': [None, None, None, None, None, None],
                '5-14y': [None, None, None, None, None, None],
                ">=15y": [None, None, None, None, None, None]
            }, index=["No. treated ACT 1st line", "No. treated ACT 2nd line", "No. treated pre-referral artesunate", "No. of patients referred", "No. treated antibiotics", "No. treated ORS/Albendazole/Zr"]),
            pd.DataFrame({
                '<5y': [None, None],
                '>=5y': [None, None]
            }, index=["No. patients with bednets at home", "No. patients that slept under a bednet last night"])
        ]
        titles = [
            "Initial Assessment",
            "Malnutrition",
            "Diagnoses",
            "Treatment",
            "Bednets"
            ]
    else:
        # Not hardocding the rest just yet
        dfs = []
        titles = None
    
    # Displaying the editable information
    df_index = 0
    edited_dfs = {}
    for df in dfs:
        st.write(titles[df_index])
        edited_dfs[df_index] = st.data_editor(df, key=df_index)
        df_index += 1

    # Download JSON, will eventually run the submission
    st.download_button(
        label="Download data as JSON",
        data = convert_df(edited_dfs),
        file_name="results.json",
        mime="application/json"
        )