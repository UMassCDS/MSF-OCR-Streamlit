import streamlit as st
import pandas as pd
import json
import data_upload_DHIS2 as dhis2
from msfocr.docTR import ocr_functions
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from img2table.document import Image as Image
from img2table.ocr import DocTR

# Function definitions
@st.cache_data
def data_values(df):
    """
    Converts data from tables into key-value pairs 
    """
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
    """
    Gets all fields similar to search_items from the metadata
    :param item_type: Defines the type of metadata (dataset, organisation unit, data element) to search
           search_items: A list of text to search
           dhis2_username, dhis2_password, DHIS2_Test_Server_URL: DHIS2 login credentials
    :return A list of all (name,id) pairs of fields that match the search words       
    """
    if search_items == "" or search_items is None:
        return []
    else:
        return dhis2.getAllUIDs(item_type, search_items, dhis2_username, dhis2_password, DHIS2_Test_Server_URL)


def convert_df(dfs):
    """
    Converts tabular data recognized into json format required to upload data into DHIS2
    :param Data as dataframes
    :return Data in json format with form identification information
    """
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

def correct_field_names(dfs):
    """
    Corrects the text data in tables by replacing with closest match among the hardcoded fieldnames
    :param Data as dataframes
    :return Corrected data as dataframes
    """
    dataElement_list = ['', 'Paed (0-59m) vacc target population', 'BCG', 'HepB (birth dose, within 24h)',
            'HepB (birth dose, 24h or later)',
            'Polio (OPV) 0 (birth dose)', 'Polio (OPV) 1 (from 6 wks)', 'Polio (OPV) 2', 'Polio (OPV) 3',
            'Polio (IPV)', 'DTP+Hib+HepB (pentavalent) 1', 'DTP+Hib+HepB (pentavalent) 2',
            'DTP+Hib+HepB (pentavalent) 3']
    categoryOptionsList = ['', '0-11m', '12-59m', '5-14y']
    
    for table in dfs:
        for row in range(table.shape[0]):
            max_similarity_dataElement = 0
            dataElement = ""
            text = table.iloc[row,0]
            if text is not None:
                for name in dataElement_list:
                    sim = ocr_functions.letter_by_letter_similarity(text, name)
                    if max_similarity_dataElement < sim:
                        max_similarity_dataElement = sim
                        dataElement = name
                table.iloc[row,0] = dataElement

    for table in dfs:
        for id,col in enumerate(table.columns):
            max_similarity_catOpt = 0
            catOpt = ""
            text = table.iloc[0,id]
            if text is not None:
                for name in categoryOptionsList:
                    sim = ocr_functions.letter_by_letter_similarity(text, name)
                    if max_similarity_catOpt < sim:
                        max_similarity_catOpt = sim
                        catOpt = name
                table.iloc[0,id] = catOpt
    return dfs        

# Function to set the first row as header
def set_first_row_as_header(df):
    """
    Sets the first row in the recognized table (ideally the header information for each column) as the table header
    :param Dataframe
    :return Dataframe after correction
    """
    df.columns = df.iloc[0]  
    df = df.iloc[1:]  
    df.reset_index(drop=True, inplace=True)  
    print(df)
    return df

@st.cache_data
def get_uploaded_images(tally_sheet):
    """
    List of images uploaded by user as docTR DocumentFiles
    :param Files uploaded by user
    :return List of images uploaded by user as docTR DocumentFiles
    """
    return [DocumentFile.from_images(sheet.read()) for sheet in tally_sheet]

@st.cache_data
def get_results(uploaded_images):
    return [ocr_functions.get_word_level_content(ocr_model, doc) for doc in uploaded_images]

@st.cache_data
def get_tabular_content_wrapper(_doctr_ocr, img, confidence_lookup_dict):
    return ocr_functions.get_tabular_content(_doctr_ocr, img, confidence_lookup_dict)

def get_sheet_type_wrapper(result):
    return ocr_functions.get_sheet_type(result)

@st.cache_resource
def create_ocr():
    """
    Load docTR ocr model and img2table docTR model  
    """
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
if len(tally_sheet) > 0:    
    
    if st.button("Clear Form") and 'upload_key' in st.session_state.keys():
        st.session_state.upload_key += 1
        if 'table_dfs' in st.session_state:
            del st.session_state['table_dfs']
        st.rerun()
        
    uploaded_images = get_uploaded_images(tally_sheet)
    results = get_results(uploaded_images)
    
    ### CORRECT THIS TO ALLOW PROCESSING OF ALL IMAGES
    # ***************************************
    image = uploaded_images[0]
    result = results[0]
    # ***************************************

    # form_type looks like [dataSet, orgUnit, period=[startDate, endDate]]
    form_type = get_sheet_type_wrapper(result)
    
    # Initialize org_unit with any recognized text from tally sheet
    # Change the value when user edits the field
    if form_type[1]:
        org_unit = st.text_input("Organization Unit", value=form_type[1])    
    else: 
        org_unit = st.text_input("Organization Unit", placeholder="Search organisation unit name")
    
    # Get all UIDs corresponding to the text field value 
    if org_unit:
        org_unit_options = dhis2_all_UIDs("organisationUnits", [org_unit], **st.secrets.dhis2_credentials)
        org_unit_dropdown = st.selectbox(
            "Searched Organizations",
            [""]+[id[0] for id in org_unit_options],
            index=None
        )

    # Same as org_unit
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

    # Initialize with period values recognized from tally sheet or entered by user    
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


    # Populate streamlit with data recognized from tally sheets
    for result in results:
        # Get tabular data ad dataframes
        confidence_lookup_dict = ocr_functions.get_confidence_values(result)
        table_dfs = []
        for sheet in tally_sheet:
            img = Image(src=sheet)
            table_df, confidence_df = get_tabular_content_wrapper(doctr_ocr, img, confidence_lookup_dict)
            table_dfs += table_df
            
            # Change this line of code to docTR ocr function
            # for id, table in enumerate(table_dfs):
            #     table_dfs[id] = set_first_row_as_header(table)

            # Store table data in session state
            if 'table_dfs' not in st.session_state:
                st.session_state.table_dfs = table_dfs

            print(table_dfs)

            # Displaying the editable information
            for i, df in enumerate(st.session_state.table_dfs):
                st.write(f"Table {i+1}")
    
                col1, col2 = st.columns([4, 1]) 
                
                with col1:
                    # Display tables as editable fields
                    table_dfs[i] = st.data_editor(df, num_rows="dynamic", key=f"editor_{i}")
                
                with col2:
                    # Add column functionality
                    new_col_name = st.text_input(f"New column name", key=f"new_col_{i}")
                    if st.button(f"Add Column", key=f"add_col_{i}"):
                        if new_col_name:
                            table_dfs[i][new_col_name] = None

                    # Delete column functionality
                    if not table_dfs[i].empty:
                        col_to_delete = st.selectbox(f"Column to delete", table_dfs[i].columns, key=f"del_col_{i}")
                        if st.button(f"Delete Column", key=f"delete_col_{i}"):
                            table_dfs[i] = table_dfs[i].drop(columns=[col_to_delete])

            # Button that when clicked corrects the row and column indices of table with best match 
            if st.button(f"Correct field names", key=f"correct_names"):
                table_dfs = correct_field_names(table_dfs)   

            # Rerun the code to display any edits made by user
            for idx, table in enumerate(table_dfs):
                if not table_dfs[idx].equals(st.session_state.table_dfs[idx]):
                    st.session_state.table_dfs = table_dfs
                    st.rerun()

            
            # # Download JSON, will eventually run the submission
            # st.download_button(
            #     label="Download data as JSON",
            #     data=convert_df(edited_dfs),
            #     file_name="results.json",
            #     mime="application/json"
            # )

            # Generate and display key-value pairs
            # if st.button("Generate Key-Value Pairs"):
            #     final_dfs = st.session_state.table_dfs
            #     key_value_pairs = []
            #     for df in final_dfs:
            #         key_value_pairs.extend(ocr_functions.generate_key_value_pairs(df))
            #     st.write("### Key-Value Pairs ###")
            #     st.json(key_value_pairs)
