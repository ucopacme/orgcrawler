#!/usr/bin/env python

"""
Usage:
    display_account_aliases.py ROLE

Arguments:
    ROLE        The AWS role name to assume when running organizer
"""

import boto3
from docopt import docopt

from organizer import crawlers, orgs, utils


def get_account_aliases(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    response = client.list_account_aliases()
    return dict(Aliases=response['AccountAliases'])


def initialize_crawler(role_name):
    master_account_id = utils.get_master_account_id(role_name)
    org = orgs.Org(master_account_id, role_name)
    org.load()
    crawler = crawlers.Crawler(org)
    crawler.load_account_credentials()
    return crawler


def process_request_outputs(request):
    accounts_with_aliases = []
    for response in request.responses:
        account = response.account.dump()
        account['Alias'] = ', '.join(response.payload_output['Aliases'])
        accounts_with_aliases.append(account)
    return(utils.jsonfmt(accounts_with_aliases))


def main():
    args = docopt(__doc__)
    crawler = initialize_crawler(args['ROLE'])
    print(crawler)
    request = crawler.execute(get_account_aliases)
    print(process_request_outputs(request))
    print()
    print(request.timer.elapsed_time)


if __name__ == "__main__":
    main()
