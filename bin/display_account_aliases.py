#!/usr/bin/env python

"""
Usage:
    display_account_aliases.py ROLE

Arguments:
    ROLE        The AWS role name to assume when running organizer
"""

import yaml
from docopt import docopt
from payloads import get_account_alias
from organizer import orgcrawler, orgs
from organizer.utils import get_master_account_id

def yamlfmt(obj):
    if isinstance(obj, str):
        return obj
    return yaml.dump(obj, default_flow_style=False)


def main():
    args = docopt(__doc__)
    master_account_id = get_master_account_id(args['ROLE'])
    org = orgs.Org(master_account_id, args['ROLE'])
    org.load()
    crawler = orgcrawler.Crawler(org)
    crawler.load_account_credentials()
    #print(yamlfmt(crawler.accounts))
    crawler.execute(get_account_alias.main)
    print(yamlfmt(crawler.responses))

if __name__ == "__main__":
    main()
