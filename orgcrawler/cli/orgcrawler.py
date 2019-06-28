#!/usr/bin/env python

import click

from orgcrawler.utils import jsonfmt, regions_for_service
from orgcrawler.cli.utils import (
    setup_crawler,
    format_responses,
    get_payload_function_from_string,
    get_payload_function_from_file,
    print_version,
)


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
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
    help='Comma separated list of AWS regions to crawl. Default is all regions.')
@click.option('--service',
    help='The AWS service used to select region list.  Especially useful for payloads which call global services.')
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
    """
Arguments:

    \b
    PAYLOAD       Name of the payload function to run in each account
    PAYLOAD_ARG   The payload function argument(s) if any

Orgcrawler attempts to resolve payload function name from $PYTHON_PATH

Examples:

    \b
    orgcrawler -h
    orgcrawler -r OrgMasterRole orgcrawler.payloads.list_buckets
    orgcrawler -r OrgMasterRole --account-role S3Admin orgcrawler.payloads.list_buckets
    orgcrawler -r OrgMasterRole --service codecommit -f ~/my_payloads.py list_cc_repositories
    orgcrawler -r OrgMasterRole --service iam orgcrawler.payloads.get_account_aliases
    orgcrawler -r OrgMasterRole --accounts app-test,app-prod \\
            --regions us-east-1,us-west-2 orgcrawler.payloads.config_describe_rules
    """
    crawler_args = dict()
    if accounts:
        crawler_args['accounts'] = accounts.split(',')
    if service:
        crawler_args['regions'] = regions_for_service(service)
    elif regions:
        crawler_args['regions'] = regions.split(',')
    if account_role:
        crawler_args['account_access_role'] = account_role
    if payload_file:
        payload = get_payload_function_from_file(payload_file, payload)
    else:
        payload = get_payload_function_from_string(payload)

    crawler = setup_crawler(master_role, **crawler_args)
    execution = crawler.execute(payload, *payload_arg)
    click.echo(jsonfmt(format_responses(execution)))


if __name__ == "__main__":
    main()  # pragma no cover
