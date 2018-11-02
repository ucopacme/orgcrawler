import os
import sys
import time
import json
import boto3
import pytest
import click
from click.testing import CliRunner
from moto import (
    mock_organizations,
    mock_sts,
    mock_iam,
)

import organizer
from organizer import crawlers, orgs, utils, payloads
from organizer.cli import orgcrawler
from ..test_orgs import (
    MASTER_ACCOUNT_ID,
    ORG_ACCESS_ROLE,
    SIMPLE_ORG_SPEC,
    COMPLEX_ORG_SPEC,
    build_mock_org,
)


def test_get_payload_function_from_string():
    payload = orgcrawler.get_payload_function_from_string(
        'organizer.payloads.set_account_alias'
    )
    assert payload == payloads.set_account_alias


def test_get_payload_function_from_file():
    payload_file = os.path.join(organizer.__path__.pop(), 'payloads.py')
    payload = orgcrawler.get_payload_function_from_file(payload_file, 'list_buckets')
    assert payload.__code__.co_filename == payloads.list_buckets.__code__.co_filename


@mock_sts
@mock_organizations
@mock_iam
def test_format_responses():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    crawler = crawlers.Crawler(org, access_role=ORG_ACCESS_ROLE)
    crawler.load_account_credentials()
    crawler.execute(payloads.set_account_alias)
    execution = crawler.execute(payloads.get_account_aliases)
    execution_responses = orgcrawler.format_responses(execution)
    print(utils.yamlfmt(execution_responses))
    assert isinstance(execution_responses, list)
    for response in execution_responses:
        assert 'Account' in response
        assert 'Regions' in response



@mock_sts
@mock_organizations
@mock_iam
def test_orgcrawler():
    print(payloads.__file__)
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    runner = CliRunner()
    result = runner.invoke(
        orgcrawler.main,
        # succeeds:
        #['--help'],
        #['--version'],
        #['--master-role', ORG_ACCESS_ROLE, 'payloads.get_account_aliases'],
        #['-r', ORG_ACCESS_ROLE, '--accounts', 'account01,account02', 'payloads.get_account_aliases'],
        #['-r', ORG_ACCESS_ROLE, '--regions', 'us-west-2', 'payloads.get_account_aliases'],
        #['-r', ORG_ACCESS_ROLE, '--service', 'iam', 'payloads.get_account_aliases'],
        #['-r', ORG_ACCESS_ROLE, 'payloads.get_account_aliases', '--account-role', ORG_ACCESS_ROLE],
        ['-r', ORG_ACCESS_ROLE, 'get_account_aliases', '--payload-file', payloads.__file__],

        # fails:
        #[],
        #['-r', 'blee'],
        #['-f', '/dev/shit']
        #['--master-role'],
        #['-r'],
        #['--accounts'],
        # returns version string only:
        #['-r', ORG_ACCESS_ROLE, 'organizer.payloads.get_account_aliases'],
        #['-r', ORG_ACCESS_ROLE, 'organizer.payloads.get_account_ali'],
        #['--help', '--piss-off']
    )
    print(result.runner)
    print(result.output_bytes)
    print(result.exit_code)
    print(result.exception)
    print(result.exc_info)
    assert result.exit_code == 0
    assert 0

