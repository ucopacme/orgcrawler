import os
import sys
import time
import json
import boto3
import pytest
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
