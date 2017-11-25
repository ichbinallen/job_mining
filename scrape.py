# Allen Clark
# scrape.py performs the following:
# 1) Visit Indeed.com
# 2) Queries for a job title and location (loc = city + State)
# 3) Donwloads an html file containing the job posting
# 4) Converts the HTML page to json
# 5) Extracts the json elements containing text relevent to the job posting
# 6) Saves the relevent text in a .txt file

# Load Modules
import argparse
import urllib2
import os
from bs4 import BeautifulSoup


# Defined Functions
def get_webaddress(jobtitle, city, state):
    """Turns a jobtitle and location into an indeed query url"""
    base = 'https://www.indeed.com/jobs?q={}&l={}%2C+{}'
    jobtitle = jobtitle.replace(' ', '+')
    city = city.replace(' ', '+')
    webaddress = base.format(jobtitle, city, state)
    return webaddress


def get_html(url):
    """given a url, fetches the html and returns as a string"""
    response = urllib2.urlopen(url)
    html = response.read()
    return html


def get_row_result_data(row_result):
    """Extracts job_id, link, jobtitle, and company from indeed's query page"""
    h2element = row_result.h2
    job_id = h2element['id']
    job_href = h2element.a['href']
    if "indeed.com/" not in job_href:
        job_href = "https://www.indeed.com" + job_href
    job_title = h2element.a['title']
    try:
        job_company = row_result.span.a.string.strip()
    except AttributeError:
        job_company = row_result.span.string.strip()
    return (job_id, job_href, job_title, job_company)


def save_indeed_query(jobtitle, city, state):
    """ Saves indeed query page as a .html file. Only works on linux rn
    Usefull for testing with a specific .html page"""
    url = get_webaddress(jobtitle, city, state)
    oscommand = 'wget -O static.html"{}"'.format(url)
    os.system(oscommand)


def scrape_query_page(html):
    """Extracts data from job postings on indeed query page"""
    soup = BeautifulSoup(html, "lxml")
    postings = soup.find_all('div', {'class': '  row  result'})
    post_data = [None] * len(postings)
    for (i, p) in enumerate(postings):
        post_data[i] = get_row_result_data(p)
    return post_data


def scrape_job_post(url):
    """ Extracts text from job posting"""
    html = get_html(url)
    soup = BeautifulSoup(html, "lxml")
    if "indeed.com/company/" in url:  # internal (indeed) link
        job_desc = soup.find('span', {'id': 'job_summary'})
    else:  # external (not indeed) link
        job_desc = soup
    print job_desc.get_text()


# Main Function
def main():
    # my code here
    # parser=argparse.ArgumentParser(description='parse job, city, state args')
    # parser.add_argument('jobtitle', type=str,
    #                     help='enter the jobtitle to search for on Indeed')
    # parser.add_argument('city', type=str,
    #                     help='enter the city to search for on Indeed')
    # parser.add_argument('state', type=str,
    #                     help='enter the state to search for on Indeed')

    # args = parser.parse_args()

    # query indeed for ds html page.  Takes a while so commented out
    # save_indeed_query("IT Manager", "Saint Paul", "MN")

    # STATIC PAGE from .html file on computer
    with open('ITManagerLA.html', 'r') as fp:
        html = fp.read()
    IT_Manager_jobs = scrape_query_page(html)

    # FRESH PAGE from the web
    # url = get_webaddress("Data Scientist", "Seattle", "WA")
    # query_page_html = get_html(url)
    # Seattle_DS_Jobs = scrape_query_page(query_page_html)

    for job in IT_Manager_jobs:
        if "indeed.com/company/" in job[1]:
            print "internal job"
            for var in job:
                print var
        else:
            print "external job"
            for var in job:
                print var
        print ""


if __name__ == "__main__":
    main()
