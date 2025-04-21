# Job Agent

## Overview

Job Agent is a job recommendation engine that leverages OpenAI's API to analyze resumes and provide personalized job recommendations based on the user's resume and personal details. Additionally, it includes functionality for scraping job postings from LinkedIn using Selenium.

## Features

- **Resume Analysis:** Converts uploaded PDF resumes into text chunks and generates a detailed summary using the OpenAI API.
- **Job Recommendations:** Utilizes the resume summary and user data to provide personalized job roles, key skills to highlight, and job search keywords.
- **LinkedIn Job Scraping:** Scrapes job postings from LinkedIn based on specified job titles and location.
- **User Interfaces:** 
  - A FastAPI backend (`main.py`) exposing API endpoints for job recommendations and LinkedIn job scraping.
  - A Streamlit frontend (`app_copy.py`) that provides a user-friendly interface for interacting with the functionalities.

## Project Structure

- `main.py`: FastAPI backend with endpoints:
  - `/job-recommendations` for analyzing resumes and generating job recommendations.
  - `/linkedin-jobs` for scraping job postings from LinkedIn.
- `core_functions.py`: Contains core classes (`ResumeAnalyzer` and `LinkedinScraper`) providing resume processing and job scraping functionalities.
- `app_copy.py`: Streamlit application that offers a GUI for resume analysis, strength/weakness analysis, job title suggestions, and LinkedIn job scraping.
- `.env`: Environment file to store configuration such as the `OPENAI_API_KEY`.
- `requirements.txt`: List of dependencies required to run the project.

## Installation

1. **Clone the Repository**

   ```bash
   git clone <repository_url>
   cd job_agent
   ```

2. **Create a Virtual Environment and Install Dependencies**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**

   Create a `.env` file in the project root and add your OpenAI API key:

   ```env
   OPENAI_API_KEY="your_openai_api_key_here"
   ```

## Running the Application

### FastAPI Backend

To start the FastAPI backend server, run:

```bash
uvicorn main:app --reload
```

The API will be accessible at `http://localhost:8000`.

### Streamlit Frontend

To launch the Streamlit application, run:

```bash
streamlit run app_copy.py
```

Then open the provided URL in your browser to interact with the GUI.

## API Endpoints

- **Job Recommendations**
  - **Endpoint:** `/job-recommendations`
  - **Method:** `POST`
  - **Parameters:** Includes user details (name, age, gender, experience, job type, location, skills), resume (PDF file), and OpenAI API key.
  - **Returns:** A resume summary and personalized job recommendations.

- **LinkedIn Jobs**
  - **Endpoint:** `/linkedin-jobs`
  - **Method:** `POST`
  - **Parameters:** Job titles (comma-separated), job location, and job count (number of jobs to fetch).
  - **Returns:** A list of job postings with company name, job title, location, website URL, and job description.

## Notes

- Ensure that you have Google Chrome installed for Selenium-based scraping.
- Make sure your OpenAI API key has sufficient quota to handle requests.
- Error handling is implemented to assist in debugging API issues or scraping errors.

## License

This project is licensed under the MIT License.

## Acknowledgements

- [OpenAI](https://openai.com/) for the API and powerful language models.
- [Selenium](https://www.selenium.dev/) for web scraping capabilities.
- [Streamlit](https://streamlit.io/) for providing an intuitive interface for data apps.
