import time
import numpy as np
import pandas as pd
import os
import openai
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import warnings

warnings.filterwarnings('ignore')


class ResumeAnalyzer:
    """Class containing functions for resume processing and analysis without Streamlit."""

    @staticmethod
    def pdf_to_chunks(pdf):
        """Converts a PDF file (file-like object) to text chunks."""
        pdf_reader = PdfReader(pdf)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(text=text)
        return chunks

    @staticmethod
    def openai(openai_api_key, chunks, analyze):
        """Uses OpenAI's API to process the chunks with a given analysis prompt."""
        try:
            embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
            vectorstores = FAISS.from_texts(chunks, embedding=embeddings)
            docs = vectorstores.similarity_search(query=analyze, k=3)
            llm = ChatOpenAI(
                model='gpt-3.5-turbo', 
                api_key=openai_api_key,
                temperature=0.7
            )
            chain = load_qa_chain(llm=llm, chain_type='stuff')
            response = chain.run(input_documents=docs, question=analyze)
            return response
        except Exception as e:
            from openai import OpenAIError, RateLimitError, APIError, APIConnectionError
            if isinstance(e, (OpenAIError, RateLimitError, APIError, APIConnectionError)):
                print(f"OpenAI API Error: {str(e)}")
            else:
                print(f"An error occurred: {str(e)}")
            raise Exception("Failed to process with OpenAI API. Please check your API key and try again.")

    @staticmethod
    def summary_prompt(query_with_chunks):
        """Generates a summarization prompt for a resume based on given text chunks."""
        query = f''' need to detailed summarization of below resume and finally conclude them

                    """"""""""""""""""""""""""""""""""""""""""""""""""""
                    {query_with_chunks}
                    """""""""""""""""""""""""""""""""""""""""""""""""""""
                    '''
        return query

    @staticmethod
    def strength_prompt(query_with_chunks):
        """Generates a prompt to analyze strengths from the resume text chunks."""
        query = f'''need to detailed analysis and explain of the strength of below resume and finally conclude them
                    """"""""""""""""""""""""""""""""""""""""""""""""""""
                    {query_with_chunks}
                    """""""""""""""""""""""""""""""""""""""""""""""""""""
                    '''
        return query

    @staticmethod
    def weakness_prompt(query_with_chunks):
        """Generates a prompt to analyze weaknesses and improvement suggestions from the resume text chunks."""
        query = f'''need to detailed analysis and explain of the weakness of below resume and how to improve make a better resume.

                    """"""""""""""""""""""""""""""""""""""""""""""""""""
                    {query_with_chunks}
                    """""""""""""""""""""""""""""""""""""""""""""""""""""
                    '''
        return query

    @staticmethod
    def job_title_prompt(query_with_chunks):
        """Generates a prompt to suggest job roles based on the resume text chunks."""
        query = f''' what are the job roles i apply to likedin based on below?
                    
                    """"""""""""""""""""""""""""""""""""""""""""""""""""
                    {query_with_chunks}
                    """"""""""""""""""""""""""""""""""""""""""""""""""""
                    '''
        return query

    @staticmethod
    def job_recommendation_prompt(user_details, resume_summary):
        """Generates a job recommendation prompt using user details and a resume summary."""
        query = f'''Based on the following user details and resume summary, suggest specific job roles and skills to focus on:
                    
                    User Details:
                    Name: {user_details['name']}
                    Age: {user_details['age']}
                    Gender: {user_details['gender']}
                    Experience: {user_details['experience']} years
                    Preferred Job Types: {', '.join(user_details['job_type'])}
                    Location: {user_details['location']}
                    Skills: {user_details['skills']}
                    
                    Resume Summary:
                    {resume_summary}
                    
                    Please provide:
                    1. Recommended job titles
                    2. Key skills to highlight
                    3. Suggested job search keywords
                    '''
        return query


class LinkedinScraper:
    """Class containing functions for scraping LinkedIn jobs without Streamlit."""

    @staticmethod
    def webdriver_setup():
        """Sets up a headless Chrome WebDriver."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver

    @staticmethod
    def build_url(job_title, job_location):
        """Builds a LinkedIn job search URL from job titles and location. Expects job_title as a list of strings."""
        parts = []
        for title in job_title:
            words = title.split()
            joined = '%20'.join(words)
            parts.append(joined)
        job_title_param = '%2C%20'.join(parts)
        link = f"https://in.linkedin.com/jobs/search?keywords={job_title_param}&location={job_location}&locationId=&geoId=102713980&f_TPR=r604800&position=1&pageNum=0"
        return link

    @staticmethod
    def open_link(driver, link):
        """Opens a link using the driver. Continues trying until a specific element is found."""
        while True:
            try:
                driver.get(link)
                driver.implicitly_wait(5)
                time.sleep(3)
                driver.find_element(by=By.CSS_SELECTOR, value='span.switcher-tabs__placeholder-text.m-auto')
                return
            except NoSuchElementException:
                continue

    @staticmethod
    def link_open_scrolldown(driver, link, job_count):
        """Opens the link and scrolls down the page to load more jobs."""
        LinkedinScraper.open_link(driver, link)
        for _ in range(0, job_count):
            body = driver.find_element(by=By.TAG_NAME, value='body')
            body.send_keys(Keys.PAGE_UP)
            try:
                driver.find_element(by=By.CSS_SELECTOR, 
                                    value="button[data-tracking-control-name='public_jobs_contextual-sign-in-modal_modal_dismiss']>icon>svg").click()
            except Exception:
                pass
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.implicitly_wait(2)
            try:
                driver.find_element(by=By.CSS_SELECTOR, value="button[aria-label='See more jobs']").click()
                driver.implicitly_wait(5)
            except Exception:
                pass

    @staticmethod
    def job_title_filter(scrap_job_title, user_job_title_input):
        """Filters a scraped job title based on user input. Returns the title if it matches, else NaN."""
        user_input = [i.lower().strip() for i in user_job_title_input]
        scrap_title = [scrap_job_title.lower().strip()]
        confirmation_count = 0
        for term in user_input:
            if all(word in scrap_title[0] for word in term.split()):
                confirmation_count += 1
        if confirmation_count > 0:
            return scrap_job_title
        else:
            return np.nan

    @staticmethod
    def scrap_company_data(driver, job_title_input, job_location):
        """Scrapes company data (company name, job title, location, website URL) from the current page."""
        companies = driver.find_elements(by=By.CSS_SELECTOR, value='h4.base-search-card__subtitle')
        company_names = [elem.text for elem in companies]

        locations = driver.find_elements(by=By.CSS_SELECTOR, value='span.job-search-card__location')
        company_locations = [elem.text for elem in locations]

        titles = driver.find_elements(by=By.CSS_SELECTOR, value='h3.base-search-card__title')
        job_titles = [elem.text for elem in titles]

        urls = driver.find_elements(by=By.XPATH, value='//a[contains(@href, "/jobs/")]')
        website_urls = [elem.get_attribute('href') for elem in urls]
        
        df = pd.DataFrame(company_names, columns=['Company Name'])
        df['Job Title'] = pd.DataFrame(job_titles)
        df['Location'] = pd.DataFrame(company_locations)
        df['Website URL'] = pd.DataFrame(website_urls)
        df['Job Title'] = df['Job Title'].apply(lambda x: LinkedinScraper.job_title_filter(x, job_title_input))
        df['Location'] = df['Location'].apply(lambda x: x if job_location.lower() in x.lower() else np.nan)
        df = df.dropna()
        df.reset_index(drop=True, inplace=True)
        return df

    @staticmethod
    def scrap_job_description(driver, df, job_count):
        """Scrapes job descriptions for each job posting in the DataFrame."""
        website_urls = df['Website URL'].tolist()
        job_descriptions = []
        description_count = 0

        for url in website_urls:
            try:
                LinkedinScraper.open_link(driver, url)
                driver.find_element(by=By.CSS_SELECTOR, value='button[data-tracking-control-name="public_jobs_show-more-html-btn"]').click()
                driver.implicitly_wait(5)
                time.sleep(1)
                description_elements = driver.find_elements(by=By.CSS_SELECTOR, value='div.show-more-less-html__markup.relative.overflow-hidden')
                data = [elem.text for elem in description_elements][0]
                
                if len(data.strip()) > 0 and data not in job_descriptions:
                    job_descriptions.append(data)
                    description_count += 1
                else:
                    job_descriptions.append('Description Not Available')
            except Exception:
                job_descriptions.append('Description Not Available')
            if description_count == job_count:
                break

        df = df.iloc[:len(job_descriptions), :]
        df['Job Description'] = pd.DataFrame(job_descriptions, columns=['Description'])
        df['Job Description'] = df['Job Description'].apply(lambda x: np.nan if x == 'Description Not Available' else x)
        df = df.dropna()
        df.reset_index(drop=True, inplace=True)
        return df

    @staticmethod
    def get_linkedin_jobs(job_titles_list, job_location, job_count):
        """Combines the scraping functions to return a DataFrame of LinkedIn job postings."""
        driver = None
        try:
            driver = LinkedinScraper.webdriver_setup()
            link = LinkedinScraper.build_url(job_titles_list, job_location)
            LinkedinScraper.link_open_scrolldown(driver, link, job_count)
            df = LinkedinScraper.scrap_company_data(driver, job_titles_list, job_location)
            df_final = LinkedinScraper.scrap_job_description(driver, df, job_count)
            return df_final
        finally:
            if driver:
                driver.quit()


if __name__ == '__main__':
    # Example usage:
    # Resume Analysis Example:
    # with open('sample_resume.pdf', 'rb') as f:
    #     chunks = ResumeAnalyzer.pdf_to_chunks(f)
    #     summary_prompt = ResumeAnalyzer.summary_prompt(chunks)
    #     # Replace 'your_openai_api_key' with your actual API key
    #     summary = ResumeAnalyzer.openai('your_openai_api_key', chunks, analyze=summary_prompt)
    #     print(summary)
    
    # LinkedIn Scraping Example:
    # job_titles = ['Data Scientist', 'Machine Learning Engineer']
    # job_location = 'India'
    # job_count = 2
    # df_jobs = LinkedinScraper.get_linkedin_jobs(job_titles, job_location, job_count)
    # print(df_jobs.to_dict(orient='records'))
    pass 