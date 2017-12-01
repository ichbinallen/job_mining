# job_mining
The job mining project collects text data on jobs posted on indeed.com.  So
far, the project contains the following files:
* scrape.py: scrapes job posting data from the web using beautifulsoup
* scrape.log: Used for debugging scrape.py
* webscrape: a Postgresql database that stores the data (use 'psql webscrape'
  to access)
* searchterms.txt: a text file containing query terms to search for on indeed.
  (e.g. 'Mechanical Engineer')
* cities.txt: a text file containing all the cities to search in.
* create_jobpostings.sql: a SQL script to create the database tables.  Creates
  jobpostings, searchterms, and cities. The view 'searches' (cross
  product of searchterms and cities) allows scrape.py to search for all
  searchterm by city combinations
* cleanup_webscrape.sql: a SQL script to remove all data from the database.
  Don't touch this!

## scrape.py

scrape.py performs the following:
1. Visit Indeed.com
2. Queries for a job title and location (loc = city + state)
3. Turns this html into an IndeedQuery Object
4. IndeedQuery scrape method gets metadata from indeedpage
5. IndeedQuery get_job_desc method gets job posting text
6. IndeedQuery keep_jobs method deletes a job if we couldn't scrape the job
desc from the job posting website
7. IndeedQuery to_db() puts the records in the webscrape postgres database
8. Main method searches for all combinations of query_terms and cities and query terms by inserting into searchterms table in webscrape db

Options:
save or load queries as .pk pickle objects for faster testing
