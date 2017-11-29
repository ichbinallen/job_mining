# Allen Clark
# scrape.py performs the following:
# 1) Visit Indeed.com
# 2) Queries for a job title and location (loc = city + state)
# 3) Turns this html into an IndeedQuery Object
# 4) IndeedQuery scrape method gets metadata from indeedpage
# 5) IndeedQuery get_job_desc method gets job posting text
# 6) IndeedQuery keep_jobs method deletes a job if we couldn't scrape the job
# desc from the job posting website
#
# Options:
# can save or load queries as .pk pickle objects for faster testing
#
# TODO: priority high to low
# run all the queries in the crossprod view
# inefficient to read url twice, once in scrape, once in get_job_desc
# make to_db method more robust, exceptions for internet access, ???
# replace to_string with __str__ or __repr__ method
# convert everything scraped to ascii? or handle in data analysis?

# Load Modules
import urllib2  # retrieve html
import psycopg2  # postgresql database api
from bs4 import BeautifulSoup  # parse html
from bs4 import Comment  # parse html
import cPickle as pickle  # save queries to file
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
        response = urllib2.urlopen(self.url)
        html = response.read()
        soup = BeautifulSoup(html, "lxml")
        postings = soup.find_all('div', {'class': '  row  result'})
        self.jobs = [None] * len(postings)
        for (index, job) in enumerate(postings):
            h2_elem = job.h2
            job_href = h2_elem.a['href']
            if "indeed.com/" not in job_href:
                job_href = "https://www.indeed.com" + job_href
            try:
                response = urllib2.urlopen(job_href)
                job_href = response.geturl()
            except urllib2.URLError:
                pass
            if 'indeed.com/cmp/' in job_href:
                job_source = 'internal'
            else:
                job_source = 'external'
            job_title = h2_elem.a['title']
            try:
                job_company = job.span.a.string.strip()
            except AttributeError:
                job_company = job.span.string.strip()
            now = datetime.datetime.now()
            now = now.strftime("%Y-%m-%d")
            self.jobs[index] = {'query_term': self.query_term,
                                'query_city': self.query_city,
                                'query_state': self.query_state,
                                'job_url': job_href,
                                'job_source': job_source,
                                'job_title': job_title,
                                'job_company': job_company,
                                'job_desc': "NA",
                                'date': now}
        logging.info("Successfully scraped indeed query page")

    def get_job_desc(self):
        """Scrapes the job posting text"""
        logging.info("Looking for job description text")
        for job in self.jobs:
            try:
                response = urllib2.urlopen(job['job_url'])
                html = response.read()
                soup = BeautifulSoup(html, "lxml")
                logging.info("Beautiful soup created for %s at  %s",
                             job['job_title'], job['job_company'])
            except urllib2.URLError:
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

    def to_db(self):
        con_str = "dbname='webscrape' user='allen'"
        try:
            conn = psycopg2.connect(con_str)
            cur = conn.cursor()
            logging.info("Successfully connected to webscrape DB")
        except:
            logging.info("Cannot connect to webscrape DB")
        SQL = """INSERT INTO
            jobpostings (query_term, query_city, query_state,
                         job_url, job_source, job_title,
                         job_company, job_desc, date)
            VALUES (%(query_term)s, %(query_city)s, %(query_state)s,
                    %(job_url)s, %(job_source)s, %(job_title)s,
                    %(job_company)s, %(job_desc)s, %(date)s);
              """
        for job in self.jobs:
            try:
                logging.info("Attempting insert of %s, %s record into DB",
                             job['job_company'], job['job_title'])
                cur.execute(SQL, job)
                conn.commit()
                logging.info('successfully inserted record')
            except psycopg2.ProgrammingError:
                logging.warning("cannot access jobpostings table.")
                logging.warning("Did you forget \i create_jobpostings.sql?")
                continue
            except psycopg2.IntegrityError:
                logging.warning("job %s, %s already exists, skipping record",
                                job['job_company'], job['job_title'])
                conn.rollback()
                continue
        try:
            conn.close()
        except:
            pass

    def to_string(self):
        query_string = "Query: {}, {}, {}"
        query_string = query_string.format(self.query_term,
                                           self.query_city,
                                           self.query_state)
        logging.info("%s", query_string)
        logging.info("%s", self.url)
        logging.info("")
        for job in self.jobs:
            for k, v in job.iteritems():
                logging.info("%s %s", k, v)
            logging.info("")
        logging.info("")


# Main Function
def main():
    logging.basicConfig(filename='scrape.log',
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.INFO)
    # These records are already in the db, should be skipped
    # DS_NY = IndeedQuery("Data Scientist", "New York", "NY")
    # DS_NY.scrape()
    # DS_NY.get_job_desc()
    # DS_NY.keep_jobs()
    # DS_NY.save_query("DS_NY.pk")
    # DS_NY.to_db()

    # These are new records.  Should be INSERTED INTO jobpostings Table
    # DS_Denver = IndeedQuery("Data Scientist", "Denver", "CO")
    # DS_Denver.scrape()
    # DS_Denver.get_job_desc()
    # DS_Denver.keep_jobs()
    # DS_Denver.save_query("DS_Denver.pk")
    # DS_Denver.to_db()

    # DS_DC = IndeedQuery("Data Scientist", "Washington", "DC")
    # DS_DC.scrape()
    # DS_DC.get_job_desc()
    # DS_DC.keep_jobs()
    # DS_DC.save_query("DS_DC.pk")
    # DS_DC.to_db()

    # Cyber_NY = IndeedQuery("Cyber Security", "New York", "NY")
    # Cyber_NY.scrape()
    # Cyber_NY.get_job_desc()
    # Cyber_NY.keep_jobs()
    # Cyber_NY.save_query("Cyber_NY.pk")
    Cyber_NY = IndeedQuery.load_query("Cyber_NY.pk")
    Cyber_NY.to_db()

    logging.info("python script scrape.py completed successfully")


if __name__ == "__main__":
    main()
