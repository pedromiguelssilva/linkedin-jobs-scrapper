# Data Wrangling & Other General Use
import pandas as pd
import time
import random
from datetime import datetime

# For scrapping
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import urllib
from urllib import parse


# For debugging
from icecream import ic
ic.configureOutput(prefix = 'Debug | ')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
start = time.time()




# 1. Gathering the page full HTML code (w/ Selenium) --------------------------------------------------------------------------------------------------

def build_url(keywords_in, location_in):
    """Pass the parameters to an url parser"""
    querystring = 'search?' + parse.urlencode({'keywords': keywords_in, 'location': location_in, 'position': 1, 'pageNum': 0})
    url = 'https://www.linkedin.com/jobs/' + querystring
    return url

def gather_full_html(url):
    """Gathering the page full HTML code (w/ Selenium)"""
    
    #driver_path = 'C:\Program Files (x86)\chromedriver.exe'
    driver_path = 'chromedriver.exe'
    driver = webdriver.Chrome(driver_path)
    driver.get(url)

    # Get the number of jobs the page shows on top of the cards
    soup = BeautifulSoup(driver.page_source, "lxml")
    
    try:
        # Click the "Accept Cookies" button, if it displays
        try:
            driver.find_element_by_xpath("//button[@class='artdeco-global-alert-action artdeco-button artdeco-button--inverse artdeco-button--2 artdeco-button--primary'] \
                                                   and @data-tracking-control-name='ga-cookie.consent.accept.v3'") \
                  .click()
            print('Cookies Accepted.\n')
        except:
            pass
        
        nr_jobs = soup.find('span', class_ = 'results-context-header__job-count').text.strip()
        print(f'\nTotal Number of Jobs Advertised in the Top: {nr_jobs}\n')

        nr_jobs_initial = get_jobs_loaded(driver)
        print('Number of Jobs Loaded in the Browser:')
        print(f'  @ Opening Page: {nr_jobs_initial}')

        scrolls = 0
        buttons = 0

        while soup.find('div', class_ = 'inline-notification see-more-jobs__viewed-all') is None:
            # Stop when a "You've viewed all jobs" card appears

            nr_jobs_loaded_init = get_jobs_loaded(driver)

            try:
                # Click the "Show More Jobs" button
                driver.find_element_by_xpath("//button[@class='infinite-scroller__show-more-button infinite-scroller__show-more-button--visible']").click()
                buttons += 1
                buttons_print = 'Button' if buttons == 1 else 'Buttons'

                # Give the browser some time to fetch the results
                time.sleep(1)

                # Printing the number of jobs already loaded
                nr_jobs_loaded = get_jobs_loaded(driver)
                if nr_jobs_loaded != nr_jobs_loaded_init:
                    print(f'  After {buttons} {buttons_print}: {nr_jobs_loaded}')

            except:
                # Scroll through the infinite scroll until the "Show More Jobs" button appears
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                scrolls += 1
                scrolls_print = 'Scroll' if scrolls == 1 else 'Scrolls'

                time.sleep(1.2)
                nr_jobs_loaded = get_jobs_loaded(driver)
                if nr_jobs_loaded != nr_jobs_loaded_init:
                    print(f'  After {scrolls} {scrolls_print}: {nr_jobs_loaded}')


            # Refreshing the soup for assessment in the while loop condition
            soup = BeautifulSoup(driver.page_source, "lxml")

        # Closing the browser
        print("\nBrowser is now closed.")
        driver.close()
    
    except:
        raise ValueError('Linkedin is blocking the crawling. Wait some more and try again.')
        driver.close()
    
    return soup


def get_jobs_loaded(driver):
    soup_jobs = BeautifulSoup(driver.page_source, "lxml")
    nr_jobs = len(soup_jobs.find('ul', class_ = 'jobs-search__results-list').find_all('li'))
    return nr_jobs



# 2. Gathering all information from the job cards (w/ BeautifulSoup) ----------------------------------------------------------------------------------

def gather_job_card_info(soup):
    """Gathering all information from the job cards (w/ BeautifulSoup)"""
    
    jobs_card = soup.find('ul', class_ = 'jobs-search__results-list')

    jobs = []

    for li in jobs_card.find_all('li'):
        full_details_url = li.find('a').get('href').replace('https://pt.linkedin', 'https://linkedin')
        position = li.find('h3', class_ = 'base-search-card__title').text.strip()
        company = li.find('h4', class_ = 'base-search-card__subtitle').text.strip()
        metadata = li.find('div', class_ = 'base-search-card__metadata')
        location = metadata.find('span', class_ = 'job-search-card__location').text.strip()
        posting_date = metadata.find('time').get('datetime')

        job_info = {'Company': company,
                    'Location': location,
                    'Position': position,
                    'PostingDate': posting_date,
                    'FullDetailsURL': full_details_url[:full_details_url.find('?refId=')]}

        if job_info not in jobs:
            jobs.append(job_info)
        else:
            print(job_info['Company'], '|', job_info['Position'])

    df_extr = pd.DataFrame(jobs)

    print(f"\nAll {len(jobs)} jobs' information is now loaded to a dataframe.\n")
    
    return df_extr



# 3. Gathering Full Job Info through the URL's -------------------------------------------------------------------------------------------------------
    
def gather_full_info(df_extr):

    try:
        # Reading previous days info from csv file
        df_full = pd.read_csv('FullInfoDataframe.csv') 
    except:
        # First instance of the dataframe 
        df_full = pd.DataFrame(columns = ['ResultsDate', 'Company', 'Location', 'Position', 'PostingDate', 'FullDetailsURL', 'AllQualifications', 'Applicants'])
        df_full.to_csv('FullInfoDataframe.csv',
                       index = False)

    print('Fetching results:\n')
    print('JobID | JobTitle | Company | Location')

    for i in range(len(df_extr)):

        if df_extr['FullDetailsURL'][i] not in df_full['FullDetailsURL'].unique():

            job_info = df_extr.iloc[i].to_dict()
            # Save the process datetime (day & hour)
            job_info['ResultsDate'] = datetime.now().strftime("%d/%m/%Y %Hh")

            print(i, '|', df_extr['Position'][i], '|', df_extr['Company'][i])

            job_url = df_extr['FullDetailsURL'][i]

            job_page = requests.get(job_url, headers)
            soup = BeautifulSoup(job_page.content, "lxml")

            try:
                # if full_description returns None, we know Linkedin blocked the request
                full_description = soup.find('div', class_ = 'show-more-less-html__markup')

                try:
                    # Store required qualifications in a list
                    qualifications = []
                    for qualification in full_description.find_all('li'):
                        qualification = qualification.text
                        qualifications.append(qualification)

                    job_info['AllQualifications'] = qualifications

                    try:
                        # Job Criteria List (Employment Type, Industries, Job Function, Seniority Level)
                        criteria = soup.find('ul', class_ = 'description__job-criteria-list')
                        criteria_boxes = criteria.find_all('li', class_ = 'description__job-criteria-item')
                        for box in criteria_boxes:
                            criteria_header = box.find('h3').text.strip()
                            criteria_text = box.find('span').text.strip()

                            job_info[criteria_header] = criteria_text

                        try:
                            # Get the info regarding current applicants
                            # If we were logged into Linkedin, we would have the exact number for those jobs under 25 applicants
                            try:
                                job_info['Applicants'] = soup.find('span', class_ = 'num-applicants__caption topcard__flavor--metadata topcard__flavor--bullet') \
                                                             .text.strip()
                            except:
                                job_info['Applicants'] = soup.find('figure', class_ = 'num-applicants__figure topcard__flavor--metadata topcard__flavor--bullet') \
                                                             .text.strip()

                        except:
                            print('     Errors occurred when parsing job "Applicants"')
                    except:
                        print('     Errors occurred when parsing job "Criteria"')
                except:
                    print('     Errors occurred when parsing job "Qualifications"')

            except:
                raise ValueError('LINKEDIN BLOCKED THE REQUEST')

            # Add the job dict to the dataframe
            df_full = df_full.append(job_info, ignore_index = True)

        time.sleep(random.random() * 3 + 1) # Waiting a randomized amount of time (higher than 1 and lower than 4 secs)

    df_full.to_csv('FullInfoDataframe.csv',
                   index = False)
    
    return df_full


# RUNNING THE WHOLE PROCESS ---------------------------------------------------------------------------------------------------------------------------
    
# INPUTS -------------------------------------------------------
# Select the company or the job you want to find results for
keywords_in = '"Data Scientist"'
# Select the location for it
location_in = 'Lisbon'
# --------------------------------------------------------------

# STAGE 1
soup = gather_full_html(build_url(keywords_in, location_in))

# STAGE 2
df_extr = gather_job_card_info(soup)
df_extr.head()

# STAGE 3
df_full = gather_full_info(df_extr)
df_full.head(3)



end = time.time()
print("Run Time: " + str('%.0f' % round(end - start,0)) + "s")