#!/usr/bin/env python

import sys

from botocore.exceptions import ClientError

from orgcrawler import orgs, crawlers, utils
from orgcrawler.cli.utils import setup_crawler

#cycles = 5
cycles = 100 
errors = 0
role = sys.argv[1]
timer = crawlers.CrawlerTimer()
cycle_timer = crawlers.CrawlerTimer()
master_account_id = utils.get_master_account_id(role)
longest_time = 0
shortest_time = None

timer.start()
for i in range(cycles):
    cycle_timer.start()
    try:
        org = orgs.Org(master_account_id, role)
        org.load()
    except ClientError as e:
        errors += 1
        print(e)
    org.clear_cache()
    org = None 
    cycle_timer.stop()
    print('cycle: {}\ttime: {}'.format(i, cycle_timer.elapsed_time))
    if longest_time < cycle_timer.elapsed_time:
        longest_time = cycle_timer.elapsed_time
    if shortest_time is None or shortest_time > cycle_timer.elapsed_time:
        shortest_time = cycle_timer.elapsed_time
timer.stop()

print('cycles:', cycles)
print('errors:', errors)
print('warnings: ')
print('elapsed time:', round(timer.elapsed_time, 2))
print('average time:', round(timer.elapsed_time/cycles, 2))
print('longest time:', round(longest_time, 2))
print('shortest time:', round(shortest_time, 2))


