# job_mining
Scrape keywords out of online job postings

scrape.py uses the python beautiful soup package to 
1) Go to indeed.com
2) Query for a jobtitle and location
3) Download the page as HTML
4) Extract the 10 Job postings from this HTML
5) Print out the linkid, webaddress, jobtitle, and companyname
