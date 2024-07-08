import streamlit as st
import pandas as pd
import json
import data_upload_DHIS2 as dhis2
from msfocr.docTR import ocr_functions
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from img2table.document import Image as Image
from img2table.ocr import DocTR

# Initializing variables
form_types = ("ICCM", "OPD", "RHGynobs", "Vaccination")


# Function definitions
@st.cache_data
def data_values(df):
    data_values = []
    columns = df.columns.tolist()
    for col, i in df.iterrows():
        for cell in columns:
            if i[cell] is not None:
                new_cell = {"dataElement": f"{col}/{cell}", "value": f"{i[cell]}"}
                data_values.append(new_cell)
    return data_values


@st.cache_data
def dhis2_all_UIDs(item_type, search_items, dhis2_username, dhis2_password, DHIS2_Test_Server_URL):
    if search_items == "" or search_items is None:
        return []
    else:
        return dhis2.getAllUIDs(item_type, search_items, dhis2_username, dhis2_password, DHIS2_Test_Server_URL)


def convert_df(dfs):
    json_export = {}
    if data_set == "":
        data_set_id = ""
    else:
        data_set_id = dict(data_set_options)[data_set_dropdown]
    json_export["dataSet"] = f"{data_set_id}"
    json_export["period"] = f"{period_start}P7D"
    if org_unit == "":
        org_unit_id = ""
    else:
        org_unit_id = dict(org_unit_options)[org_unit_dropdown]
    json_export["orgUnit"] = f"{org_unit_id}"
    data_values_list = []
    for df in dfs.values():
        data_values_list += data_values(df)
    json_export["dataValues"] = data_values_list
    return json.dumps(json_export)

@st.cache_data
def get_uploaded_images(tally_sheet):
    return [DocumentFile.from_images(sheet.read()) for sheet in tally_sheet]

@st.cache_data
def get_results(uploaded_images):
    return [ocr_functions.get_word_level_content(ocr_model, doc) for doc in uploaded_images]

@st.cache_data
def get_tabular_content_wrapper(_doctr_ocr, img, confidence_lookup_dict):
    return ocr_functions.get_tabular_content(_doctr_ocr, img, confidence_lookup_dict)

@st.cache_data
def get_sheet_type_wrapper(_result):
    return ocr_functions.get_sheet_type(_result)

@st.cache_resource
def create_ocr():
    ocr_model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
    doctr_ocr = DocTR(detect_language=False)
    return ocr_model, doctr_ocr

# Set the page layout to centered
# st.set_page_config(layout="wide")

# Initiation
if 'upload_key' not in st.session_state: 
    st.session_state['upload_key'] = 1000

# Initial Display
st.title("MSF OCR Tool")
st.write("### File Upload ###")
tally_sheet = st.file_uploader("Please upload one or more images of a tally sheet", type=["png", "jpg", "jpeg"],
                               accept_multiple_files=True,
                               key=st.session_state['upload_key'])

# Displaying images so the user can see them
with st.expander("Show Images"):
    for sheet in tally_sheet:
        st.image(sheet)

# OCR Model
ocr_model, doctr_ocr = create_ocr()

# Once images are uploaded
if len(tally_sheet) > 0:    # Will have prefilled data when OCR works
    
    if st.button("Clear Form") and 'upload_key' in st.session_state.keys():
        st.session_state.upload_key += 1
        st.rerun()
        
    uploaded_images = get_uploaded_images(tally_sheet)
    results = get_results(uploaded_images)
    
    image = uploaded_images[0]
    result = results[0]

    # form_type looks like [dataSet, orgUnit, period=[startDate, endDate]]
    form_type = get_sheet_type_wrapper(result)
    
    if form_type[1]:
        org_unit = st.text_input("Organization Unit", value=form_type[1])    
    else: 
        org_unit = st.text_input("Organization Unit", placeholder="Search organisation unit name")
    
    if org_unit:
        org_unit_options = dhis2_all_UIDs("organisationUnits", [org_unit], **st.secrets.dhis2_credentials)
        org_unit_dropdown = st.selectbox(
            "Searched Organizations",
            [""]+[id[0] for id in org_unit_options],
            index=None
        )

    if form_type[0]:
        data_set = st.text_input("Data Set", value=form_type[0])
    else:
        data_set = st.text_input("Data Set", placeholder="Search data set name")

    if data_set:            
        data_set_options = dhis2_all_UIDs("dataSets", [data_set], **st.secrets.dhis2_credentials)
        data_set_dropdown = st.selectbox(
            "Searched Datasets",
            [id[0] for id in data_set_options],
            index=None
        )
    if form_type[2]:
        if form_type[2][0]:    
            period_start = st.date_input("Period Start Date", format="YYYY-MM-DD", value=form_type[2][0])
        else:
            period_start = st.date_input("Period Start Date", format="YYYY-MM-DD") 
        if form_type[2][1]:    
            period_end = st.date_input("Period End Date", format="YYYY-MM-DD", value=form_type[2][1])
        else:
            period_end = st.date_input("Period End Date", format="YYYY-MM-DD")        
    else:
        period_start = st.date_input("Period Start Date", format="YYYY-MM-DD")
        period_end = st.date_input("Period End Date", format="YYYY-MM-DD")

    uploaded_images = get_uploaded_images(tally_sheet)
    results = get_results(uploaded_images)

    # Display OCR results
    # for i, result in enumerate(results):
    #     st.write(f"OCR Result for Image {i + 1}:")
    #     for page in result.pages:
    #         for block in page.blocks:
    #             for line in block.lines:
    #                 st.write(" ".join(word.value for word in line.words))

    for result in results:
        confidence_lookup_dict = ocr_functions.get_confidence_values(result)
        table_dfs = []
        for sheet in tally_sheet:
            img = Image(src=sheet)
            table_df, confidence_df = get_tabular_content_wrapper(doctr_ocr, img, confidence_lookup_dict)
            table_dfs += table_df


            # Displaying the editable information
            df_index = 0
            edited_dfs = {}
            for i, df in enumerate(table_dfs):
                st.write(f"Table {i+1}")
    
                # Create two columns
                col1, col2 = st.columns([4, 1])  # Adjust the ratio as needed
                
                with col1:
                    edited_dfs[i] = st.data_editor(df, num_rows="dynamic", key=f"editor_{i}")
                
                with col2:
                    # Add column functionality
                    new_col_name = st.text_input(f"New column name", key=f"new_col_{i}")
                    if st.button(f"Add Column", key=f"add_col_{i}"):
                        if new_col_name:
                            df[new_col_name] = None

                    # Delete column functionality
                    if not df.empty:
                        col_to_delete = st.selectbox(f"Column to delete", df.columns, key=f"del_col_{i}")
                        if st.button(f"Delete Column", key=f"delete_col_{i}"):
                            df = df.drop(columns=[col_to_delete])
    
                table_dfs[i] = df  # Update the original dataframe

            # # Download JSON, will eventually run the submission
            # st.download_button(
            #     label="Download data as JSON",
            #     data=convert_df(edited_dfs),
            #     file_name="results.json",
            #     mime="application/json"
            # )

            # # Generate and display key-value pairs
            # if st.button("Generate Key-Value Pairs"):
            #     key_value_pairs = []
            #     for df in edited_dfs.values():
            #         key_value_pairs.extend(ocr_functions.generate_key_value_pairs(df))
            #     st.write("### Key-Value Pairs ###")
            #     st.json(key_value_pairs)
