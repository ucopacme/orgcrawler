#!/usr/bin/env python

"""
Usage:
    orgcrawler  [-h] [-m id] -r role [-a role] [-f file] PAYLOAD [ARGS...]
                [--regions csvlist | --regions-for-service name]
                [--accounts csvlist | --account-query command]
                [--account-query-arg arg]

Arguments:
    PAYLOAD         Name of the payload function to run in each account
                    Orgcrawler attempts to resolve this name from $PYTHON_PATH
    ARGS            Argument list for PAYLOAD

Options:
    -h, --help                  Print help message
    -m, --master-account-id id  The master account id of the organization
    -r, --master-role role      The IAM role to assume in master account
    -a, --account-role role     The IAM role to assume in organization accounts
                                if different from --master-role
    -f, --payload-file file     Path to file containing payload function
    --regions csvlist           Comma separated list of AWS regions to crawl
                                Default is all regions
    --accounts csvlist          Comma separated list of accounts to crawl
                                Can be account Id, name or alias
                                Default is all accounts in organization
    --regions-for-service name  The AWS service used to select region list
    --account-query command     The organizer query command used to select
                                accounts
    --account-query-arg arg     The organizer query command argument

"""

import os
import sys
import importlib

from docopt import docopt

from organizer import crawlers, orgs, utils


# ISSUE: not printing account, region names with response outputs
def process_execution_outputs(execution):
    collector = []
    for response in execution.responses:
        d = dict(Account=response.account.name)
        d.update(response.payload_output)
        collector.append(d)
    return(utils.jsonfmt(collector))


def get_payload_function_from_string(payload_name):
    module_name, unused, function_name = payload_name.rpartition('.')
    if module_name:
        module = importlib.import_module(module_name)
        return getattr(module, function_name)
    return eval(payload_name)


def get_payload_function_from_file(file_name, payload_name):
    if file_name.startswith('~'):
        file_name = os.path.expanduser(file_name)
    module_dir = os.path.dirname(file_name)
    sys.path.append(os.path.abspath(module_dir))
    module_name = os.path.basename(file_name).replace('.py', '')
    module = importlib.import_module(module_name)
    return getattr(module, payload_name)


def main():
    args = docopt(__doc__)

    if args['--master-account-id'] is None:
        args['--master-account-id'] = utils.get_master_account_id(args['--master-role'])

    crawler_args = dict()
    if args['--account-query']:
        crawler_args['accounts'] = eval('org.' + args['--account-query'])(args['--account-query-arg'])
    elif args['--accounts']:
        crawler_args['accounts'] = args['--accounts'].split(',')

    if args['--regions-for-service']:
        crawler_args['regions'] = utils.regions_for_service(args['--regions-for-service'])
    elif args['--regions']:
        crawler_args['regions'] = args['--regions'].split(',')

    if args['--account-role']:
        crawler_args['access_role'] = args['--account-role']

    if args['--payload-file']:
        payload = get_payload_function_from_file(args['--payload-file'], args['PAYLOAD'])
    else:
        payload = get_payload_function_from_string(args['PAYLOAD'])

    org = orgs.Org(args['--master-account-id'], args['--master-role'])
    org.load()
    crawler = crawlers.Crawler(org, **crawler_args)
    crawler.load_account_credentials()
    execution = crawler.execute(payload)
    print(process_execution_outputs(execution))


if __name__ == "__main__":
    main()
