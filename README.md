# MSF-OCR-Streamlit

Uses a Streamlit web app in conjunction with an OCR library to allow for uploading documents, scanning them, and correcting information.

### Docker Instructions

Build the image: `docker build -t msf-streamlit .`

Run the container: `docker run -p 8501:8501 msf-streamlit`

Make sure port 8501 is available, as it is the default for Streamlit.
