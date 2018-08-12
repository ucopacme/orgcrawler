project
-------

- DONE Usage documantation in README

cli/
----
- DONE move orgcrawler.py under organizer.cli/
- DONE add params to orgcrawler.py to retrieve region/account listing
- DONE create lib of payload functions for use with orgcrawler.py
- DONE add params to orgcrawler.py to allow reading functions from file or other mod/package

orgs.py
-------

- gather account aliases
- DONE pickle org object and write to disk/s3
- DONE read pickled org back from disk
- add docstrings to methods with complex params


crawlers.py
-----------

- DONE make Crawler.execute run in queue_threads
- DONE handle empty regions list intelegently, as for global services.
- DONE convert datetime objects (others) in payload_output to json streamable content
- NA add exception handling for above json streaming errors
- DONE CrawlerRequest to CrawlerExec. all 'request' to 'execution'
- DONE add exception handling for payload errors
- add docstrings to methods with complex params
