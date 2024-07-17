from datetime import date
import streamlit as st
import copy
import requests
from msfocr.data.data_upload_DHIS2 import configure_DHIS2_server
from msfocr.data import data_upload_DHIS2 as dhis2
from LLM.ocr_functions import *

@st.cache_data
def dhis2_all_UIDs(item_type, search_items):
    """
    Gets all fields similar to search_items from the metadata.

    Usage:
    uids = dhis2_all_UIDs("dataElements", ["Malaria", "HIV"])

    :param item_type: Defines the type of metadata (dataset, organisation unit, data element) to search
    :param search_items: A list of text to search
    :return: A list of all (name,id) pairs of fields that match the search words
    """
    if search_items == "" or search_items is None:
        return []
    else:
        return dhis2.getAllUIDs(item_type, search_items)

def create_server():
    """
    Configures the DHIS2 server connection.

    Usage:
    create_server()
    """
    dhis2.configure_DHIS2_server()

@st.cache_data
def get_data_sets(data_set_uids):
    """
    Retrieves data sets based on their UIDs.

    Usage:
    data_sets = get_data_sets(["uid1", "uid2"])

    :param data_set_uids: List of data set UIDs
    :return: List of data sets
    """
    return dhis2.getDataSets(data_set_uids)

@st.cache_data
def get_org_unit_children(org_unit_id):
    """
    Retrieves children of an organization unit.

    Usage:
    children = get_org_unit_children("parent_uid")

    :param org_unit_id: UID of the parent organization unit
    :return: List of child organization units
    """
    return dhis2.getOrgUnitChildren(org_unit_id)

def week1_start_ordinal(year):
    """
    Calculates the ordinal date of the start of the first week of the year.

    Usage:
    start_ordinal = week1_start_ordinal(2023)

    :param year: The year to calculate for
    :return: Ordinal date of the start of the first week
    """
    jan1 = date(year, 1, 1)
    jan1_ordinal = jan1.toordinal()
    jan1_weekday = jan1.weekday()
    week1_start_ordinal = jan1_ordinal - ((jan1_weekday + 1) % 7)
    return week1_start_ordinal

def week_from_date(date_object):
    """
    Calculates the week number from a given date.

    Usage:
    year, week = week_from_date(date(2023, 5, 15))

    :param date_object: Date to calculate the week for
    :return: Tuple of (year, week number)
    """
    date_ordinal = date_object.toordinal()
    year = date_object.year
    week = ((date_ordinal - week1_start_ordinal(year)) // 7) + 1
    if week >= 52:
        if date_ordinal >= week1_start_ordinal(year + 1):
            year += 1
            week = 1
    return year, week

def get_period():
    """
    Generates the period string based on the selected period type and start date.

    Usage:
    period_string = get_period()

    :return: Formatted period string
    """
    year, week = week_from_date(period_start)
    return PERIOD_TYPES[period_type].format(
        year=year,
        day=period_start.day,
        month=period_start.month,
        week=week
    )

def json_export(kv_pairs):
    """
    Converts tabular data into JSON format required for DHIS2 data upload.

    Usage:
    json_data = json_export(key_value_pairs)

    :param kv_pairs: List of key-value pairs representing the data
    :return: JSON string ready for DHIS2 upload
    """
    json_export = {}
    if org_unit_dropdown == None:
        raise ValueError("Please select organisation unit")
    if data_set == "":
        raise ValueError("Please select data set")
    json_export["dataSet"] = data_set_selected_id
    json_export["period"] = get_period()
    json_export["orgUnit"] = org_unit_child_id
    json_export["dataValues"] = kv_pairs
    return json.dumps(json_export)


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
        image = correct_image_orientation(sheet)
        st.image(image)

create_server()

# Hardcoded Periods, probably won't update but can get them through API
PERIOD_TYPES = {
    "Daily": "{year}{month}{day}",
    "Weekly": "{year}W{week}",
    "WeeklyWednesday": "{year}WedW{week}",
    "WeeklyThursday": "{year}ThuW{week}",
    "WeeklySaturday": "{year}SatW{week}",
    "WeeklySunday": "{year}SunW{week}",
    "BiWeekly": "{year}Bi{week}",
    "Monthly": "{year}{month}",
    "BiMonthly": "{year}{month}B",
    "Quarterly": "{year}{quarter_number}",
    "SixMonthly": "{year}{semiyear_number}",
    "SixMonthlyApril": "{year}April{semiyear_number}",
    "SixMonthlyNovember": "{year}Nov{semiyear_number}",
    "Yearly": "{year}",
    "FinancialApril": "{year}April",
    "FinancialJuly": "{year}July",
    "FinancialOct": "{year}Oct",
    "FinancialNov": "{year}Nov",
}

# Once images are uploaded
if len(tally_sheet) > 0:

    if st.button("Clear Form") and 'upload_key' in st.session_state.keys():
        st.session_state.upload_key += 1
        if 'table_dfs' in st.session_state:
            del st.session_state['table_dfs']
        st.rerun()

    results = get_results(tally_sheet)

    # ***************************************
    result = results[0]

    # Initialize from JSON result
    # dataSet = result.get('dataSet', None)
    # orgUnit = result.get('Health Structure', None)
    # start_date = result.get('Start Date', None)
    # end_date = result.get('End Date', None)
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

    org_unit_dropdown = None
    org_unit_options = None

    # Get all UIDs corresponding to the text field value
    if org_unit:
        org_unit_options = dhis2_all_UIDs("organisationUnits", [org_unit])
        org_unit_dropdown = st.selectbox(
            "Searched Organizations",
            [id[0] for id in org_unit_options],
            index=None
        )

    # Get org unit children
    if org_unit_dropdown is not None:
        if org_unit_options:
            org_unit_id = [id[1] for id in org_unit_options if id[0] == org_unit_dropdown][0]
            org_unit_children_options = get_org_unit_children(org_unit_id)
            org_unit_children_dropdown = st.selectbox(
                "Organization Children",
                sorted([id[0] for id in org_unit_children_options]),
                index=None
            )

            if org_unit_children_dropdown is not None:

                org_unit_child_id = [id[2] for id in org_unit_children_options if id[0] == org_unit_children_dropdown][0]
                data_set_ids = [id[1] for id in org_unit_children_options if id[0] == org_unit_children_dropdown][0]
                data_set_options = get_data_sets(data_set_ids)
                data_set = st.selectbox(
                    "Data Set",
                    sorted([id[0] for id in data_set_options]),
                    index=None
                )

                if data_set is not None:
                    data_set_selected_id = [id[1] for id in data_set_options if id[0] == data_set][0]
                    period_type = [id[2] for id in data_set_options if id[0] == data_set][0]
                    st.write("Period Type\: " + period_type)

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
    table_names, table_dfs = [], []
    for result in results:
        names, df = parse_table_data(result)
        table_names.extend(names)
        table_dfs.extend(df)

        if 'table_names' not in st.session_state:
            st.session_state.table_names = table_names
        if 'table_dfs' not in st.session_state:
            st.session_state.table_dfs = table_dfs

        # Displaying the editable information
        for i, (table_name, df) in enumerate(zip(st.session_state.table_names, st.session_state.table_dfs)):
            st.write(f"{table_name}")
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

            if 'data_payload' not in st.session_state:
                st.session_state.data_payload = None

        configure_DHIS2_server("settings.ini")
        # Generate and display key-value pairs
        if st.button("Generate Key-Value Pairs"):
            # Set first row as header of df
            final_dfs = copy.deepcopy(st.session_state.table_dfs)
            print(final_dfs)
            key_value_pairs = []
            for df in final_dfs:
                key_value_pairs.extend(generate_key_value_pairs(df))
            st.write("Completed")

            st.session_state.data_payload = json_export(key_value_pairs)
            print(st.session_state.data_payload)

        if st.button("Upload to DHIS2"):
            if st.session_state.data_payload == None:
                raise ValueError("Data empty - generate key value pairs first")
            else:
                URL = ''
                data_value_set_url = f'{URL}/api/dataValueSets?dryRun=true'
                # Send the POST request with the data payload
                response = requests.post(
                    data_value_set_url,
                    auth=('', ''),
                    headers={'Content-Type': 'application/json'},
                    data=st.session_state.data_payload
                )

                # # Check the response status
                # if response.status_code == 200:
                print('Data entry dry run successful')
                print('Response data:')
                print(response.json())
                # else:
                print(f'Failed to enter data, status code: {response.status_code}')
                print('Response data:')
                print(response.json())
            st.write("Completed")

