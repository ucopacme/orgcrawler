#!/usr/bin/env python

"""
Usage:
    orgcrawler.py ROLE PAYLOAD

Arguments:
    ROLE        The AWS role name to assume when running organizer
    PAYLOAD    Name of the payload function to run in each account

Available Payload Functions:
    get_account_aliases
    list_buckets
    list_hosted_zones
"""

import boto3
from docopt import docopt

from organizer import crawlers, orgs, utils


def get_account_aliases(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    response = client.list_account_aliases()
    return dict(Aliases=', '.join(response['AccountAliases']))


def list_buckets(region, account):
    client = boto3.client('s3', region_name=region, **account.credentials)
    response = client.list_buckets()
    return dict(Buckets=[b['Name'] for b in response['Buckets']])


def list_hosted_zones(region, account):
    client = boto3.client('route53', region_name=region, **account.credentials)
    response = client.list_hosted_zones()
    hosted_zones = []
    for zone in response['HostedZones']:
        response = client.list_resource_record_sets(HostedZoneId=zone['Id'])
        hosted_zones.append(dict(
            Name=zone['Name'],
            Id=zone['Id'],
            RecordSets=response['ResourceRecordSets'],
        ))
    return dict(HostedZones=hosted_zones)


def initialize_crawler(role_name):
    master_account_id = utils.get_master_account_id(role_name)
    org = orgs.Org(master_account_id, role_name)
    org.load()
    crawler = crawlers.Crawler(org)
    crawler.load_account_credentials()
    return crawler


def process_request_outputs(request):
    collector = []
    for response in request.responses:
        d = dict(Account=response.account.name)
        d.update(response.payload_output)
        collector.append(d)
    return(utils.jsonfmt(collector))


def main():
    args = docopt(__doc__)
    crawler = initialize_crawler(args['ROLE'])
    request = crawler.execute(eval(args['PAYLOAD']))
    print(process_request_outputs(request))


if __name__ == "__main__":
    main()
