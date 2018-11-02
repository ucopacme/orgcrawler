#!/usr/bin/env python

import os
import sys
import importlib
import click

from organizer import __version__, utils
from organizer.cli.utils import setup_crawler, format_responses


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(__version__)
    ctx.exit()


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('payload')
@click.argument('payload_arg', nargs=-1)
@click.option('--master-role', '-r',
    required=True,
    help='IAM role to assume for accessing AWS Organization Master account.')
@click.option('--account-role', '-a',
    help='IAM role to assume for accessing AWS Organization child accounts. '
         'Defaults to "--master-role".')
@click.option('--accounts',
    help='Comma separated list of accounts to crawl. Can be account Id, name or '
         'alias. Default is all accounts in organization.')
@click.option('--regions',
    help='Comma separated list of AWS regions to crawl Default is all regions.')
@click.option('--service',
    help='The AWS service used to select region list.')
@click.option('--payload-file', '-f',
    type=click.Path(exists=True),
    help='Path to file containing payload function.')
@click.option('--version', '-V',
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help='Display version info and exit.')
def main(master_role, account_role, regions, accounts,
        service, payload_file, payload, payload_arg):

    ''' Where 'PAYLOAD' is name of the payload function to run in each account,
    and 'PAYLOAD_ARG' is, you guessed it, any payload function argument(s).
    Orgcrawler attempts to resolve payload function name from $PYTHON_PATH '''

    crawler_args = dict()
    if accounts:
        crawler_args['accounts'] = accounts.split(',')
    if service:
        crawler_args['regions'] = utils.regions_for_service(service)
    elif regions:
        crawler_args['regions'] = regions.split(',')
    if account_role:
        crawler_args['account_access_role'] = account_role
    if payload_file:
        payload = get_payload_function_from_file(payload_file, payload)
    else:
        payload = get_payload_function_from_string(payload)

    crawler = setup_crawler(master_role, **crawler_args)
    execution = crawler.execute(payload)
    click.echo(utils.jsonfmt(format_responses(execution)))


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


if __name__ == "__main__":
    main()  # pragma no cover
