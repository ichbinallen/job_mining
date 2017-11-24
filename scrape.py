# Allen Clark
# scrape.py performs the following:
# 1) Visit Indeed.com
# 2) Queries for a job title and location (loc = ctiy + State)
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
    base = 'https://www.indeed.com/jobs?q={}&l={}%2C+{}'
    jobtitle = jobtitle.replace(' ', '+')
    city = city.replace(' ', '+')
    webaddress = base.format(jobtitle, city, state)
    return webaddress


def get_html(url):
    response = urllib2.urlopen(url)
    html = response.read()
    return html


def get_row_result_data(row_result):
    h2element = row_result.h2
    job_id = h2element['id']
    job_href = h2element.a['href']
    job_title = h2element.a['title']
    try:
        job_company = row_result.span.a.string.strip()
    except AttributeError:
        job_company = row_result.span.string.strip()
    return (job_id, job_href, job_title, job_company)


def save_indeed_query(jobtitle, city, state):
    url = get_webaddress(jobtitle, city, state)
    oscommand = 'wget -O page.html -k "{}"'.format(url)
    os.system(oscommand)


def scrape_indeed(html):
    soup = BeautifulSoup(html, "lxml")
    postings = soup.find_all('div', {'class': '  row  result'})
    for p in postings:
        data = get_row_result_data(p)
        for thing in data:
            print thing
        print "\n"


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
    # save_indeed_query("Data Scientist", "Saint Paul", "MN")
    with open('page.html', 'r') as fp:
        html = fp.read()
    scrape_indeed(html)


if __name__ == "__main__":
    main()
