# Linkedin Jobs Scrapper
Crawl Linkedin Jobs tab to scrape for all Data Scientist jobs in Lisbon, and store them into a dataframe, including information regarding qualifications, number of applicants and full job description. Ongoing project.

Note 1: Though the use case here is specific, the script works with any keywords and location (as in the original Linkedin Jobs tab).   
Note 2: Further automated analysis is to be done as a next step.

## Workflow:
As Is: A job is scheduled to daily run a batch file, which in turn runs the script "01. DataExtraction.py"

## Requirements:
* Python 3.x
* Pandas
* BeautifulSoup
* Selenium (and ChromeDriver)

## Disclaimer:
The task at hands does not involve a significant number of consecutive requests to Linkedin, therefore one can easily escape having their requests blocked. However, Linkedin actually requires permission to crawl through the website. See https://www.linkedin.com/legal/crawling-terms and https://www.linkedin.com/robots.txt: both lead to "Please email whitelist-crawl@linkedin.com if you would like to apply for permission to crawl LinkedIn."
