# MSF-OCR-Streamlit

Uses a Streamlit web app in conjunction with an OCR library to allow for uploading documents, scanning them, and correcting information.

### Docker Instructions

Build the image: `docker build -t msf-streamlit .`

Run the container: `docker run -p 8501:8501 msf-streamlit`

Make sure port 8501 is available, as it is the default for Streamlit.

### Login Information

In the main directory:
1. Create a file called `settings.ini`
2. Paste in the following text: 
```
[DHIS2Server]
username = '<your username here>'
password = '<your password here>'
server_url = '<test server url>'
```
3. Replace the bracketed text with your login information and the test server URL.