project
-------

- Usage documantation in README

cli/
----
- move orgcrawler.py under organizer.cli/
- add params to orgcrawler.py to retrieve region/account listing
- create lib of payload functions for use with orgcrawler.py
- add params to orgcrawler.py to allow reading functions from file or other mod/package

orgs.py
-------

- gather account aliases
- pickle org object and write to disk/s3
- read pickled org back from disk
- add docstrings to methods with complex params


crawlers.py
-----------

- DONE make Crawler.execute run in queue_threads
- handle empty regions list intelegently, as for global services.
- convert datetime objects (others) in payload_output to json streamable content
- add exception handling for above json streaming errors
- rename CrawlerRequest to CrawlerExec. all 'request' to 'execution'
- add exception handling for payload errors
- add docstrings to methods with complex params
