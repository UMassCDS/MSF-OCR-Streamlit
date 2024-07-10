import base64
import os
import streamlit as st
import json
import data_upload_DHIS2 as dhis2
import io
import anthropic
from PIL import Image
import pandas as pd


# Function definitions
def get_results(uploaded_images, api_key):
    """
    Processes uploaded images using the Claude API and returns the results.

    :param uploaded_images: List of uploaded images (PIL Image objects).
    :param api_key: API key for Claude API.
    :return: List of results from the Claude API.
    """
    results = []
    for img in uploaded_images:
        img_path = "temp_img.jpg"
        img.save(img_path)
        result = process_image_with_claude(api_key, img_path)
        results.append(result)
    return results


def parse_table_data(result):
    """
    Parses table data from the Claude API results into DataFrames.

    :param result: Result from the Claude API containing table data.
    :return: List of DataFrames parsed from the table data.
    """
    table_data = result["tables"]
    dataframes = []
    for table in table_data:
        columns = table["headers"]
        data = table["data"]
        df = pd.DataFrame(data, columns=columns)
        dataframes.append(df)
    return dataframes


def process_image_with_claude(api_key, img_path):
    """
    Processes an image using the Claude API and returns the result.

    :param api_key: API key for the Claude API.
    :param img_path: Path to the image file to be processed.
    :return: JSON result from the Claude API.

    Usage:
    Create a .env file and put ANTHROPIC_API_KEY in it.
    This key is necessary for using the Claude API.

    1. Create a .env file in your project directory.
    2. Add the following line to the .env file:
       ANTHROPIC_API_KEY=api_key_here
    """

    API_KEY_VAR = "ANTHROPIC_API_KEY"
    os.environ[API_KEY_VAR] = api_key

    # Constants
    ANTHROPIC_MODEL = "claude-3-5-sonnet-20240620"
    OUPUT_SIZE_LIMIT = 1024
    MAXIMUM_PIXEL_LENGTH = 1568
    MAXIMUM_BYTES = 5242880

    with Image.open(img_path) as test_img:
        img_to_send = test_img.copy()
        img_to_send.thumbnail((MAXIMUM_PIXEL_LENGTH, MAXIMUM_PIXEL_LENGTH))
        img_as_bytes = io.BytesIO()
        img_to_send.save(img_as_bytes, "jpeg")
        encoded_img = base64.b64encode(img_as_bytes.getvalue()).decode("utf-8")

    byte_size = encoded_img.__sizeof__()

    current_max_pixel_length = MAXIMUM_PIXEL_LENGTH
    while byte_size > MAXIMUM_BYTES:
        quality_scale = MAXIMUM_BYTES / byte_size
        current_max_pixel_length = int(quality_scale * current_max_pixel_length)
        img_to_send.thumbnail((current_max_pixel_length, current_max_pixel_length))
        img_as_bytes = io.BytesIO()
        img_to_send.save(img_as_bytes, "jpeg")
        encoded_img = base64.b64encode(img_as_bytes.getvalue()).decode("utf-8")
        byte_size = encoded_img.__sizeof__()

    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    message = anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=OUPUT_SIZE_LIMIT,
        # If set to 0, the model will use log probability 96 to automatically increase the temperature until certain thresholds are hit.
        temperature=0.1,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": encoded_img,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Identify all tables and table structure"
                                "Then hardcore the table structure with columns and rows."
                                "Extract the number from the tables, fill in the table."
                                "Make columns use headers field in json file, and data use data field."
                                "The non_table_data should be key-value pair "
                                "Respond directly in JSON format without any introduction, explanation, or additional text."
                    },
                ],
            }
        ]
    )
    return json.loads(message.content[0].text)


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

def get_uploaded_images(tally_sheet):
    uploaded_images = []
    for file in tally_sheet:
        img = Image.open(file)
        uploaded_images.append(img)
    return uploaded_images


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
api_key = os.environ.get("ANTHROPIC_API_KEY")

# Once images are uploaded
if len(tally_sheet) > 0:    
    
    if st.button("Clear Form") and 'upload_key' in st.session_state.keys():
        st.session_state.upload_key += 1
        if 'table_dfs' in st.session_state:
            del st.session_state['table_dfs']
        st.rerun()
        
    uploaded_images = get_uploaded_images(tally_sheet)
    results = get_results(uploaded_images, api_key)

    table_dfs = []
    for result in results:
        table_dfs.extend(parse_table_data(result))

    ### CORRECT THIS TO ALLOW PROCESSING OF ALL IMAGES
    # ***************************************
    image = uploaded_images[0]
    result = results[0]
    # ***************************************
    dataSet = None
    orgUnit = None
    start_date = None
    end_date = None

    # Initialize org_unit with any recognized text from tally sheet
    # Change the value when user edits the field
    if orgUnit:
        org_unit = st.text_input("Organization Unit", value=orgUnit)
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
    if dataSet:
        data_set = st.text_input("Data Set", value=dataSet)
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
    if (start_date and end_date):
        if start_date:
            period_start = st.date_input("Period Start Date", format="YYYY-MM-DD", value=start_date)
        else:
            period_start = st.date_input("Period Start Date", format="YYYY-MM-DD")
        if end_date:
            period_end = st.date_input("Period End Date", format="YYYY-MM-DD", value=start_date)
        else:
            period_end = st.date_input("Period End Date", format="YYYY-MM-DD")

    else:
        period_start = st.date_input("Period Start Date", format="YYYY-MM-DD")
        period_end = st.date_input("Period End Date", format="YYYY-MM-DD")

    # Populate streamlit with data recognized from tally sheets
    # Store table data in session state
    if 'table_dfs' not in st.session_state:
        st.session_state.table_dfs = table_dfs

    # Displaying the editable information
    for i, df in enumerate(st.session_state.table_dfs):
        st.write(f"Table {i + 1}")
        col1, col2 = st.columns([4, 1])

        with col1:
            # Display tables as editable fields
            st.session_state.table_dfs[i] = st.data_editor(df, num_rows="dynamic", key=f"editor_{i}")

        with col2:
            # Add column functionality
            new_col_name = st.text_input(f"New column name", key=f"new_col_{i}")
            if st.button(f"Add Column", key=f"add_col_{i}"):
                if new_col_name:
                    st.session_state.table_dfs[i][new_col_name] = None

            # Delete column functionality
            if not st.session_state.table_dfs[i].empty:
                col_to_delete = st.selectbox(f"Column to delete", st.session_state.table_dfs[i].columns,
                                             key=f"del_col_{i}")
                if st.button(f"Delete Column", key=f"delete_col_{i}"):
                    st.session_state.table_dfs[i] = st.session_state.table_dfs[i].drop(columns=[col_to_delete])

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
