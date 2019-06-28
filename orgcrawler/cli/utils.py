import os
import sys
import importlib

import click
import pkg_resources

from orgcrawler import crawlers, orgs
from orgcrawler.utils import get_master_account_id


def print_version(click_context, param, value):
    '''Click callback function to display package version'''
    if not value or click_context.resilient_parsing:
        return
    package_version = pkg_resources.get_distribution('orgcrawler').version
    click.echo(package_version)
    click_context.exit()


def get_payload_function_from_string(payload_name):
    module_name, _, function_name = payload_name.rpartition('.')
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def get_payload_function_from_file(file_name, payload_name):
    file_name = os.path.expanduser(file_name)
    module_dir = os.path.dirname(file_name)
    sys.path.append(os.path.abspath(module_dir))
    module_name = os.path.basename(file_name).replace('.py', '')
    module = importlib.import_module(module_name)
    return getattr(module, payload_name)


def setup_crawler(org_access_role, account_access_role=None, accounts=None, regions=None):
    """
    Returns a fully loaded orgcrawler.crawlers.Crawler object
    """
    master_account_id = get_master_account_id(org_access_role)
    my_org = orgs.Org(master_account_id, org_access_role)
    my_org.load()
    my_crawler = crawlers.Crawler(
        my_org,
        access_role=account_access_role,
        accounts=accounts,
        regions=regions,
    )
    my_crawler.load_account_credentials()
    return my_crawler


def format_responses(execution):
    """ generate dictionary of orgcrawler payload execution responses
    formatted per region per account """
    collector = []
    responses = purge_empty_responses(execution)
    account_names = sorted(list(set([r.account.name for r in responses])))
    for account_name in account_names:
        d = dict(
            Account=account_name,
            Regions=[
                {'Region': r.region, 'Output': r.payload_output} for r in responses if
                r.account.name == account_name
            ]
        )
        collector.append(d)
    return(collector)


def purge_empty_responses(execution):
    '''
    Return list of execution responses for which output is not empty.
    Expects each response to be a list of dict.
    '''
    responses = [
        r for r in execution.responses if (
            len(r.payload_output) == 1 and list() not in r.payload_output.values()
        )
    ]
    return responses
