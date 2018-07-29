#import re
#import botocore
from inspect import isfunction
import time
import boto3
from moto import mock_organizations, mock_sts, mock_iam
import pytest

from organizer import crawlers, orgs, utils
from .test_orgs import (
    MASTER_ACCOUNT_ID,
    ORG_ACCESS_ROLE,
    SIMPLE_ORG_SPEC,
    COMPLEX_ORG_SPEC,
    build_mock_org,
)


def test_crawler_timer_init():
    timer = crawlers.CrawlerTimer()
    timer.start()
    time.sleep(0.1)
    timer.stop()
    assert isinstance(timer.start_time, float)
    assert isinstance(timer.end_time, float)
    assert isinstance(timer.elapsed_time, float)
    assert timer.start_time < timer.end_time
    assert int(timer.elapsed_time * 10) == 1
    assert isinstance(timer.dump(), dict)


@mock_sts
@mock_organizations
def test_crawler_response_init():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    org.load()
    response = crawlers.CrawlerResponse('us-east-1', org.accounts[0])
    assert response.region == 'us-east-1'
    assert isinstance(response.account, orgs.OrgAccount)
    assert response.payload_output is None
    assert isinstance(response.timer, crawlers.CrawlerTimer)
    assert isinstance(response.dump(), dict)
    #print(utils.jsonfmt(response.dump()))
    #assert False


@mock_sts
@mock_organizations
def test_crawler_request_init():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    org.load()
    request = crawlers.CrawlerRequest(get_account_alias)
    assert isfunction(request.payload)
    assert request.name == 'get_account_alias'
    assert request.responses == []
    assert isinstance(request.timer, crawlers.CrawlerTimer)
    assert isinstance(request.dump(), dict)
    #print(utils.jsonfmt(request.dump()))
    #assert False


@mock_sts
@mock_organizations
def test_load_account_credentials():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org_id, root_id = build_mock_org(COMPLEX_ORG_SPEC)
    org.load()
    crawler = crawlers.Crawler(org)
    crawler.load_account_credentials()
    assert isinstance(crawler.accounts, list)
    assert len(crawler.accounts) == len(org.accounts)
    for account in crawler.accounts:
        assert isinstance(account.credentials, dict)


@mock_sts
@mock_organizations
def test_crawler_init():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org_id, root_id = build_mock_org(COMPLEX_ORG_SPEC)
    org.load()
    crawler = crawlers.Crawler(org)
    assert isinstance(crawler, crawlers.Crawler)
    assert isinstance(crawler.org, orgs.Org)
    assert crawler.access_role == org.access_role
    assert crawler.accounts == org.accounts
    assert crawler.regions == [crawlers.DEFAULT_REGION]
    
    ou01_id = org.get_org_unit_id_by_name('ou01')
    ou01_accounts = org.list_accounts_in_ou(ou01_id)
    crawler = crawlers.Crawler(
        org,
        accounts=ou01_accounts,
        regions=['us-west-2', 'us-east-1'],
        access_role='OrganizerAdmin'
    )
    assert len(crawler.accounts) == len(ou01_accounts)
    assert len(crawler.regions) == 2
    assert crawler.access_role == 'OrganizerAdmin'
    #assert False


def set_account_alias(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    client.create_account_alias(AccountAlias='alias-' + account.name)
    return 


def get_account_alias(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    response = client.list_account_aliases()
    return response['AccountAliases']


@mock_sts
@mock_organizations
@mock_iam
def test_execute():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org_id, root_id = build_mock_org(COMPLEX_ORG_SPEC)
    org.load()
    crawler = crawlers.Crawler(org)
    crawler.load_account_credentials()
    crawler.execute(set_account_alias)
    crawler.execute(get_account_alias)
    assert len(crawler.requests) == 2
    for request in crawler.requests:
        assert isinstance(request, crawlers.CrawlerRequest)
        assert len(request.responses) == len(crawler.accounts)
        for response in request.responses:
            assert isinstance(response, crawlers.CrawlerResponse)
    assert crawler.requests[0].name == 'set_account_alias'
    assert crawler.requests[1].name == 'get_account_alias'
    for response in crawler.requests[0].responses:
        assert response.payload_output is None
    for response in crawler.requests[1].responses:
        assert isinstance(response.payload_output, list)
        assert response.payload_output[0].startswith('alias-account')
    #print(utils.jsonfmt(crawler.requests[0].dump()))
    #print()
    #print(utils.jsonfmt(crawler.requests[1].dump()))
    #assert False

    
