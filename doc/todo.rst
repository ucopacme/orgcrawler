project
-------

- Usage documantation in README


orgs.py
-------

- gather account aliases
- pickle org object and write to disk/s3
- read pickled org back from disk


crawlers.py
-----------

- make Crawler.execute run in queue_threads
- handle empty regions list intelegently
- convert datetime objects (others) in payload_output to json streamable content
- add exception handling for above json streaming errors
