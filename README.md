# MSF-OCR-Streamlit

Uses a Streamlit web app in conjunction with an OCR library to allow for uploading documents, scanning them, and correcting information.

### Docker Instructions

Build the image: `docker build -t msf-streamlit .`

Run the container: `docker run -p 8501:8501 msf-streamlit`

Make sure port 8501 is available, as it is the default for Streamlit.

In data_upload_DHIS2.py, replace dhis2_username and dhis2_password with your own personal login information. In the future, this will likely be done through a login on the main app page.