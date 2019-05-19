import os
import pytest
from moto import (
    mock_organizations,
    mock_sts,
    mock_iam,
)

import orgcrawler
from orgcrawler import crawlers, payloads
from orgcrawler.utils import yamlfmt
from orgcrawler.cli.utils import (
    get_payload_function_from_string,
    get_payload_function_from_file,
    setup_crawler,
    format_responses,
)

from ..test_orgs import (
    ORG_ACCESS_ROLE,
    SIMPLE_ORG_SPEC,
    build_mock_org,
    clean_up,
)


def test_get_payload_function_from_string():
    payload = get_payload_function_from_string(
        'orgcrawler.payloads.get_account_aliases'
    )
    assert payload == payloads.get_account_aliases


def test_get_payload_function_from_file():
    print(orgcrawler.__path__)
    payload_file = os.path.join(orgcrawler.__path__[0], 'payloads.py')
    payload = get_payload_function_from_file(payload_file, 'list_buckets')
    assert payload.__code__.co_filename == payloads.list_buckets.__code__.co_filename


@mock_sts
@mock_organizations
@mock_iam
def test_setup_crawler():
    clean_up()
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    assert isinstance(crawler, crawlers.Crawler)
    assert len(crawler.org.accounts) == 3
    assert len(crawler.org.org_units) == 6
    for account in crawler.accounts:
        assert 'aws_access_key_id' in account.credentials
        assert 'aws_secret_access_key' in account.credentials
        assert 'aws_session_token' in account.credentials
    crawler = setup_crawler(ORG_ACCESS_ROLE,
        'account_role',
        ['account02', 'account03'],
        ['us-west-2', 'us-east-1'],
    )
    assert crawler.access_role == 'account_role'
    assert len(crawler.accounts) == 2
    assert len(crawler.regions) == 2
    assert set([a.name for a in crawler.accounts]) == set(['account02', 'account03'])
    assert set(crawler.regions) == set(['us-west-2', 'us-east-1'])
    with pytest.raises(TypeError):
        crawler = setup_crawler()
    with pytest.raises(ValueError):
        crawler = setup_crawler(ORG_ACCESS_ROLE, accounts='bogus_01')
    with pytest.raises(ValueError):
        crawler = setup_crawler(ORG_ACCESS_ROLE, regions='bogus_01')


@mock_sts
@mock_organizations
@mock_iam
def test_format_responses():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    crawler.execute(payloads.get_account_aliases)
    execution = crawler.execute(payloads.get_account_aliases)
    execution_responses = format_responses(execution)
    print(yamlfmt(execution_responses))
    assert isinstance(execution_responses, list)
    for response in execution_responses:
        assert 'Account' in response
        assert 'Regions' in response
