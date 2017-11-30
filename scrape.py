# Allen Clark
# scrape.py performs the following:
# 1) Visit Indeed.com
# 2) Queries for a job title and location (loc = city + state)
# 3) Turns this html into an IndeedQuery Object
# 4) IndeedQuery scrape method gets metadata from indeedpage
# 5) IndeedQuery get_job_desc method gets job posting text
# 6) IndeedQuery keep_jobs method deletes a job if we couldn't scrape the job
# desc from the job posting website
# 7) IndeedQuery to_db() puts the records in the webscrape postgres database
# 8) Main method searches for all combinations of query_terms and cities
#
# Options:
# add query terms by inserting into searchterms table in webscrape db
# save or load queries as .pk pickle objects for faster testing
#
# TODO: priority high to low
# Make all exceptions more robust
# make to_db method more robust, exceptions for internet access, ???
# replace to_string with __str__ or __repr__ method
# convert everything scraped to ascii? or handle in data analysis?

# Load Modules
import urllib3  # retrieve html
# import psycopg2  # postgresql database api
from bs4 import BeautifulSoup  # parse html
from bs4 import Comment  # parse html
import pickle  # save queries to file
import datetime  # get date query was performed
import logging  # write script progress to logfile.log


# Defined Functions
def tag_visible(element):
    """Helper function to strip non-text html"""
    if element.parent.name in ['style', 'script', 'head', 'title',
                               'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


class IndeedQuery:
    """An IndeedQuery objects represents the jobs postings found on Indeed.com
    after searching for a specific query and location"""
    def __init__(self, query_term, query_city, query_state):
        """ Constructor for an indeed query object"""
        self.query_term = query_term
        self.query_city = query_city
        self.query_state = query_state
        base = 'https://www.indeed.com/jobs?q={}&l={}%2C+{}'
        j = query_term.replace(' ', '+')
        c = query_city.replace(' ', '+')
        self.url = base.format(j, c, query_state)
        self.jobs = []
        logging.info("Created IndeedQuery Object")
        logging.info("%s", self.url)

    def scrape(self):
        """ Collects metadata from indeed query page """
        logging.info("Attempting to scrape Indeed query page")
        try:
            pool_mgr = urllib3.PoolManager()
            response = pool_mgr.request('GET', self.url)
            html = response.data.decode('utf-8')
            soup = BeautifulSoup(html, "lxml")
            postings = soup.find_all('div', {'class': '  row  result'})
            self.jobs = [None] * len(postings)
            logging.info("turned html into soup")
        except:
            logging.error("Cannot read html from indeed")
            return
        for (index, job) in enumerate(postings):
            h2_elem = job.h2
            job_href = h2_elem.a['href']
            if "indeed.com/" not in job_href:
                job_href = "https://www.indeed.com" + job_href
            job_title = h2_elem.a['title']
            try:
                try:
                    job_company = job.span.a.string.strip()
                except AttributeError:
                    job_company = job.span.string.strip()
            except:
                job_company = "NA"
            now = datetime.datetime.now()
            now = now.strftime("%Y-%m-%d")
            self.jobs[index] = {'query_term': self.query_term,
                                'query_city': self.query_city,
                                'query_state': self.query_state,
                                'job_url': job_href,
                                'job_source': 'external',
                                'job_title': job_title,
                                'job_company': job_company,
                                'job_desc': "NA",
                                'date': now}
        logging.info("%s", self.to_string())
        logging.info("Successfully scraped indeed query page")

    def get_job_desc(self):
        """Scrapes the job posting text"""
        logging.info("Looking for job description text")
        for job in self.jobs:
            try:
                pool_mgr = urllib3.PoolManager()
                response = pool_mgr.request('GET', job['job_url'])
                html = response.data.decode('utf-8')
                soup = BeautifulSoup(html, "lxml")
                # job['job_url'] = response.geturl() need to fix for python3
                # if 'indeed.com/cmp/' in job['job_url']:
                #     job['job_source'] = 'internal'
                logging.info("Beautiful soup created for %s at  %s",
                             job['job_title'], job['job_company'])
            except Exception as e:
                logging.warning("%s", e)
                job['job_desc'] = "NA"
                logging.info("Beautiful soup failed for %s at  %s",
                             job['job_title'], job['job_company'])
                logging.info("skipping record")
                continue  # cant read html, go to next job posting
            if job['job_source'] == "internal":
                job_desc = soup.find('span', {'id': 'job_summary'})
                job_desc = job_desc.get_text()
            else:
                job_desc = soup.find_all(text=True)
                visible_texts = filter(tag_visible, job_desc)
                job_desc = u" ".join(t.strip() for t in visible_texts)
            if job_desc.isspace():
                job_desc = "NA"
            job['job_desc'] = job_desc.encode('ascii', 'ignore')

    def keep_jobs(self):
        """Remove jobs without any job description text"""
        self.jobs = filter(lambda x: x['job_desc'] != "NA", self.jobs)

    def save_query(self, filename):
        logging.info("Saving IndeedQuery object as %s", filename)
        with open(filename, 'wb') as outfile:
            pickle.dump(self, outfile, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load_query(filename):
        logging.info("Loading IndeedQuery object from %s", filename)
        with open(filename, 'rb') as infile:
            return pickle.load(infile)

    def to_string(self):
        query_string = "Query: {}, {}, {}"
        query_string = query_string.format(self.query_term,
                                           self.query_city,
                                           self.query_state)
        logging.info("%s", query_string)
        logging.info("%s", self.url)
        logging.info("")
        for job in self.jobs:
            for k, v in job.items():
                logging.info("%s %s", k, v)
            logging.info("")
        logging.info("")


# Main Function
def main():
    logging.basicConfig(filename='scrape.log',
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.INFO)

    ME_NY = IndeedQuery("Mechanical Engineer", "New York", "NY")
    ME_NY.scrape()
    ME_NY.get_job_desc()
    ME_NY.save_query("ME_NY.pk")
    # ME_NY = IndeedQuery.load_query("ME_NY.pk")
    ME_NY.to_string()

    logging.info("python script scrape.py completed successfully")


if __name__ == "__main__":
    main()
