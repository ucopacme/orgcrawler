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
from organizer import crawlers, orgs, utils
from organizer.cli import orgcrawler, payloads
from ..test_orgs import (
    MASTER_ACCOUNT_ID,
    ORG_ACCESS_ROLE,
    SIMPLE_ORG_SPEC,
    COMPLEX_ORG_SPEC,
    build_mock_org,
)


def test_get_payload_function_from_string():
    payload = orgcrawler.get_payload_function_from_string(
        'organizer.cli.payloads.set_account_alias'
    )
    assert payload == payloads.set_account_alias


def test_get_payload_function_from_file():
    payload_file = os.path.join(organizer.__path__.pop(), 'cli/payloads.py')
    payload = orgcrawler.get_payload_function_from_file(payload_file, 'list_buckets')
    assert payload.__code__.co_filename == payloads.list_buckets.__code__.co_filename


@mock_sts
@mock_organizations
@mock_iam
def test_process_request_outputs():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    crawler = crawlers.Crawler(org, access_role=ORG_ACCESS_ROLE)
    crawler.load_account_credentials()
    crawler.execute(payloads.set_account_alias)
    request = crawler.execute(payloads.get_account_aliases)
    response = orgcrawler.process_request_outputs(request)
    assert isinstance(response, str)
    aliases = json.loads(response)
    assert isinstance(aliases, list)
    for item in aliases:
        assert isinstance(item, dict)
        assert 'Account' in item
        assert 'Aliases' in item
