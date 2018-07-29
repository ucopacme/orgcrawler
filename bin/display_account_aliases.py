#!/usr/bin/env python

"""
Usage:
    display_account_aliases.py ROLE

Arguments:
    ROLE        The AWS role name to assume when running organizer
"""

import yaml
import boto3
from docopt import docopt

from organizer import crawlers, orgs, utils
from organizer.utils import get_master_account_id


def get_account_aliases(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    response = client.list_account_aliases()
    return dict(AccountAliases=response['AccountAliases'])


def main():
    print(type(get_account_aliases.__name__))
    args = docopt(__doc__)
    master_account_id = get_master_account_id(args['ROLE'])
    org = orgs.Org(master_account_id, args['ROLE'])
    org.load()
    crawler = crawlers.Crawler(org)
    crawler.load_account_credentials()
    #print(utils.yamlfmt(crawler.accounts))
    crawler.execute(get_account_aliases)
    print(utils.yamlfmt(crawler.get_payload_response_by_name('get_account_aliases').dump))



if __name__ == "__main__":
    main()
