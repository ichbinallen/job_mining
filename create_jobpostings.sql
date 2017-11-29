CREATE TABLE jobpostings (
	    query_term	    varchar(80),  --search term input to indeed
	    query_city	    varchar(80),  --City input to indeed
	    query_state	    char(2),  --State code input to indeed
	    job_id	    SERIAL PRIMARY KEY,  --id var for jobs
	    job_url	    text UNIQUE,  --url location of the job post, must be unique
	    job_source	    varchar(10),  --binary, posted on indeed.com (internal) or companies own job site (external)
	    job_title	    varchar(80),  --Job title, (may be different from Query term)
	    job_company	    varchar(80),  --Company
	    job_desc	    text,  --Text of the job description scraped from website
	    date            date   --Date when the job was scraped off the web

);

CREATE TABLE cities (
	city	varchar(80),
	state	char(2)
);


CREATE TABLE searchterms (
	query_term	varchar(80) PRIMARY KEY
);

\copy cities FROM 'cities.txt' DELIMITERS ',' CSV;

\copy searchterms FROM 'searchterms.txt' DELIMITERS ',' CSV;

CREATE VIEW searches as SELECT * FROM searchterms CROSS JOIN cities ;
