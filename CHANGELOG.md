# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

You should also add project tags for each release in Github, see [Managing releases in a repository](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).

## [Unreleased]

## [1.1.0] - 2024-07-26
### Added 
- More than one image can be uploaded and processed at a time
- User must verify that all images are correct before uploading
- Mathematical expressions that appear in cells are evaluated before displaying results to the user

### Changed
- Title color is responsive to theme

### Fixed
- Fix problem where sometimes table cells weren't editable in the Streamlit app


## [1.0.0] - 2024-07-19
### Added
- app_llm.py OCR backed by OpenAI GPT vision model
- Streamlit application that recognizes uploaded tally sheet tables and pushes data to DHIS2
- app_doctr.py OCR backed by DocTR computer vision models
- Containerization support using Dockerfile
