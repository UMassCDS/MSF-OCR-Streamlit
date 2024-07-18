import base64
import json
import pandas as pd
from PIL import Image, ExifTags
from openai import OpenAI
from msfocr.data import data_upload_DHIS2 as dhis2
import configparser

OPENAI_API_KEY = None

def configure_openai(config_path="settings.ini"):
    """
    Configures the OpenAI API key from a settings file.

    Usage:
    configure_openai()  # Uses default settings.ini
    configure_openai("custom_settings.ini")  # Uses a custom config file
    """
    config = configparser.ConfigParser()
    config.read(config_path)
    openai_section = config["OpenAI"]
    global OPENAI_API_KEY
    OPENAI_API_KEY = openai_section["api_key"]


def get_results(uploaded_image_paths):
    """
    Processes uploaded image paths using the OpenAI API and returns the results.

    Usage:
    image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]
    results = get_results(image_paths)

    :param uploaded_image_paths: List of uploaded image file paths.
    :return: List of results from the OpenAI API.
    """
    results = []
    for img_path in uploaded_image_paths:
        result = extract_text_from_image(img_path)
        results.append(result)
    return results


def parse_table_data(result):
    """
    Parses table data from the OpenAI API results into DataFrames.

    Usage:
    table_names, dataframes = parse_table_data(api_result)

    :param result: Result from the GPT-4o API containing table data.
    :return: Tuple containing a list of table names and a list of DataFrames parsed from the table data.
    """
    table_data = result["tables"]
    table_names = []
    dataframes = []

    for table in table_data:
        table_name = table.get("table_name", f"Table {len(dataframes) + 1}")
        columns = table["headers"]
        data = table["data"]
        data.insert(0, columns)
        df = pd.DataFrame(data)
        table_names.append(table_name)
        dataframes.append(df)

    return table_names, dataframes


def encode_image(image_path):
    """
    Encodes an image file to base64 string.

    Usage:
    base64_string = encode_image(image_file)

    :param image_path: File object of the image to encode.
    :return: Base64 encoded string of the image.
    """
    image_path.seek(0)
    return base64.b64encode(image_path.read()).decode("utf-8")


def extract_text_from_image(image_path):
    """
    Extracts text and table data from an image using OpenAI's GPT-4 vision model.

    Usage:
    result = extract_text_from_image("path/to/image.jpg")

    :param image_path: Path to the image file.
    :return: JSON object containing extracted text and table data.
    """
    configure_openai()
    client = OpenAI(api_key=OPENAI_API_KEY)
    MODEL = "gpt-4o"
    base64_image = encode_image(image_path)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": [
                {"type": "text",
                 "text": "Analyze this image as a completely new task. "
                         "Identify and parse all tables and non-table data. "
                         "For each table, carefully examine and transcribe its name from the image, typically located at the top left of the table. "
                         "If the table name is unclear or missing, label it 'Table X' where X is a sequential number. "
                         "Do not use any previously identified table names. "
                         "Apply image corrections if needed for better text recognition. "
                         "Construct each table with its newly identified name, columns, and rows, extracting all visible numbers. "
                         "Format JSON with two main objects: 1) 'tables': an array of table objects {'table_name': '...', 'headers': [...], 'data': [[...], ...]}, 2) 'non_table_data': an object with key-value pairs for all non-table information. "
                         "Respond only with the JSON: {'tables': [...], 'non_table_data': {...}}. "
                         "No explanations. "
                         "Treat this as an entirely new image with no relation to any previous tasks."

                 },
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"}
                 }
            ]}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def correct_image_orientation(image_path):
    """
    Corrects the orientation of an image based on its EXIF data.

    Usage:
    corrected_image = correct_image_orientation("path/to/image.jpg")

    :param image_path: The path to the image file.
    :return: PIL.Image.Image: The image with corrected orientation.
    """
    image = Image.open(image_path)
    orientation = None
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image.getexif().items())
        if exif.get(orientation) == 3:
            image = image.rotate(180, expand=True)
        elif exif.get(orientation) == 6:
            image = image.rotate(270, expand=True)
        elif exif.get(orientation) == 8:
            image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return image


