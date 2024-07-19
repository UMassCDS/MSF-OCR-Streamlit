# MSF-OCR-Streamlit

Uses a Streamlit web app in conjunction with an Optical Character Recognition (OCR) library to allow for uploading documents, scanning them, and correcting information.

This repository contains two version of the application:
- `app_llm.py` uses [OpenAI's GPT 4o model](https://platform.openai.com/docs/guides/vision) as an OCR engine to 'read' the tables from images
- `app_doctr.py` uses a the [docTR](https://pypi.org/project/python-doctr/) library as an OCR engine to parse text from the tables in images.

## Necessary environment variables
In order to use the application, you will need to set the following environment variables for the Streamlit app to access the DHIS2 server:
```
DHIS2_USERNAME=<your username>
DHIS2_PASSWORD=<your password>
DHIS2_SERVER_URL=<server url>
```

If you are using the `app_llm.py` version of the application, you will also need to set `OPENAI_API_KEY` with an API key obtained from [OpenAI's online portal](https://platform.openai.com/).

## Running Locally
1) Set your environment variables. On a unix system the easiest way to do this is put them in a `.env` file, then run `set -a && source .env && set +a`. You can also set them in your System Properties or shell environment profile.  

2) Install the python dependencies with `pip install -r requirements.txt`. Note the `msfocr` package is in a private repository, so you may want to put [add your GitHub access token to the dependency](https://docs.readthedocs.io/en/stable/guides/private-python-packages.html) in `requirements.txt` first. 

3) Run your desired Streamlit application with one of the following commands:
    - OpenAI version: `streamlit run app_llm.py` 
    - DocTR version: `streamlit run app_doctr.py` 

## Docker Instructions
We have provided a Dockerfile in order to easily build and deploy the OpenAI application version as a Docker container. 

1) Build an image named `msf-streamlit`: `docker build -t msf-streamlit .`. Note the `msfocr` package is in a private repository, so you may want to put [add your GitHub access token to the dependency](https://docs.readthedocs.io/en/stable/guides/private-python-packages.html) in `requirements.txt` first. 

2) Run the `msf-streamlit` image in a container, passing the necessary environment variables: 
    ```
    docker run -p 8501:8501 -e DHIS2_USERNAME=<your username> -e DHIS2_PASSWORD=<your password> -e DHIS2_SERVER_URL=<server url> -e OPENAI_API_KEY=<your key> msf-streamlit
    ```

    If you have a `.env` file, you can keep things simple with `docker run -p 8501:8501 --env-file .env msf-streamlit`. 

    Make sure port 8501 is available, as it is the default for Streamlit.

