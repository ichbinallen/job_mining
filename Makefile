python = /usr/bin/python

scrape :
	$(python) scrape.py > errlog.log &


.PHONY : clean
clean :
	rm errlog.log scrape.log
