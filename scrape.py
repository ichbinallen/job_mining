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
# TODO:
# inefficient to read url twice, once in scrape, once in get_job_desc
# Test on variety of sites
# Store in database

# Load Modules
import urllib2
from bs4 import BeautifulSoup
from bs4 import Comment
import cPickle as pickle


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
        self.job_desc = "unknown"

    def scrape(self):
        response = urllib2.urlopen(self.url)
        html = response.read()
        soup = BeautifulSoup(html, "lxml")
        postings = soup.find_all('div', {'class': '  row  result'})
        self.jobs = [None] * len(postings)
        for (index, job) in enumerate(postings):
            h2_elem = job.h2
            job_id = h2_elem['id']
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
            self.jobs[index] = {'id': job_id, 'url': job_href,
                                'job_title': job_title, 'company': job_company,
                                'source': job_source}

    def get_job_desc(self):
        """Scrapes the job posting text"""
        for job in self.jobs:
            print job['company']
            try:
                response = urllib2.urlopen(job['url'])
                html = response.read()
                soup = BeautifulSoup(html, "lxml")
            except urllib2.URLError:
                job['job_desc'] = "NA"
                continue  # cant read html, go to next job posting
            if job['source'] == "internal":
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
        """Remove jobs without any job description"""
        self.jobs = filter(lambda x: x['job_desc'] != "NA", self.jobs)

    def save_query(self, filename):
        with open(filename, 'wb') as outfile:
            pickle.dump(self, outfile, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load_query(filename):
        with open(filename, 'rb') as infile:
            return pickle.load(infile)

    def to_string(self):
        """ Should replace with __str__"""
        query_string = "Query: {}, {}, {}"
        query_string = query_string.format(self.query_term,
                                           self.query_city,
                                           self.query_state)
        print query_string
        print self.url
        print ""
        for job in self.jobs:
            for k, v in job.iteritems():
                print k, v
            print ""
        print ""


# Main Function
def main():
    DS_NY = IndeedQuery("Data Scientist", "New York", "NY")
    DS_NY.scrape()
    DS_NY.get_job_desc()
    DS_NY.keep_jobs()
    DS_NY.to_string()

    # DS_LA = IndeedQuery("Data Scientist", "Los Angeles", "CA")
    # DS_LA.scrape()
    # DS_LA.get_job_desc()
    # DS_LA.keep_jobs()
    # DS_LA.to_string()

    # DS_Chicago = IndeedQuery("Data Scientist", "Chicago", "IL")
    # DS_Chicago.scrape()
    # DS_Chicago.get_job_desc()
    # DS_Chicago.keep_jobs()
    # DS_Chicago.to_string()

    # DS_Houston = IndeedQuery("Data Scientist", "Houston", "TX")
    # DS_Houston.scrape()
    # DS_Houston.get_job_desc()
    # DS_Houston.keep_jobs()
    # DS_Houston.to_string()

    # DS_Phoenix = IndeedQuery("Data Scientist", "Phoenix", "AZ")
    # DS_Phoenix.scrape()
    # DS_Phoenix.get_job_desc()
    # DS_Phoenix.keep_jobs()
    # DS_Phoenix.to_string()

if __name__ == "__main__":
    main()
