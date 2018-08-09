#import re
#import botocore
from inspect import isfunction
import time
import boto3
import pytest
from moto import (
    mock_organizations,
    mock_sts,
    mock_iam,
    mock_s3,
)

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
def test_crawler_init():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org_id, root_id = build_mock_org(COMPLEX_ORG_SPEC)
    org.load()
    crawler = crawlers.Crawler(org)
    assert isinstance(crawler, crawlers.Crawler)
    assert isinstance(crawler.org, orgs.Org)
    assert crawler.access_role == org.access_role
    assert crawler.accounts == org.accounts
    assert crawler.regions == utils.all_regions()
    
    ou01_id = org.get_org_unit_id('ou01')
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
@mock_iam
def test_get_or_update_regions():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org_id, root_id = build_mock_org(COMPLEX_ORG_SPEC)
    org.load()
    crawler = crawlers.Crawler(org)
    assert crawler.get_regions() == utils.all_regions()
    crawler.update_regions(utils.regions_for_service('iam'))
    assert crawler.get_regions() == ['us-east-1']
    crawler.update_regions(utils.all_regions())
    assert crawler.get_regions() == utils.all_regions()
    crawler.update_regions(utils.regions_for_service('cloud9'))
    assert crawler.get_regions() == utils.regions_for_service('cloud9')


# payload functions:

def set_account_alias(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    client.create_account_alias(AccountAlias='alias-' + account.name)
    return 


def get_account_alias(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    response = client.list_account_aliases()
    return response['AccountAliases']


def create_mock_bucket(region, account, bucket_prefix):
    client = boto3.client('s3', region_name=region, **account.credentials)
    response = client.create_bucket(Bucket='-'.join([bucket_prefix, account.id]))
    return response


@mock_sts
@mock_organizations
@mock_iam
@mock_s3
def test_execute():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org_id, root_id = build_mock_org(COMPLEX_ORG_SPEC)
    org.load()
    crawler = crawlers.Crawler(org)
    crawler.load_account_credentials()
    request1= crawler.execute(set_account_alias)
    request2 = crawler.execute(get_account_alias)
    assert len(crawler.requests) == 2
    assert request1 == crawler.requests[0]
    assert request2 == crawler.requests[1]
    for request in crawler.requests:
        assert isinstance(request, crawlers.CrawlerRequest)
        assert len(request.responses) == len(crawler.accounts) * len(crawler.regions)
        for response in request.responses:
            assert isinstance(response, crawlers.CrawlerResponse)
    assert crawler.requests[0].name == 'set_account_alias'
    assert crawler.requests[1].name == 'get_account_alias'
    for response in crawler.requests[0].responses:
        assert response.payload_output is None
    for response in crawler.requests[1].responses:
        assert isinstance(response.payload_output, list)
        assert response.payload_output[0].startswith('alias-account')

    crawler.update_regions(utils.all_regions())
    request3 = crawler.execute(create_mock_bucket, 'mockbucket')
    assert len(crawler.requests) == 3
    assert len(request3.responses) == len(crawler.accounts) * len(crawler.regions)
    for response in request3.responses:
        assert response.payload_output['ResponseMetadata']['HTTPStatusCode'] == 200

    assert crawler.get_request('set_account_alias') == crawler.requests[0]
    assert crawler.get_request('get_account_alias') == crawler.requests[1]
    assert crawler.get_request('create_mock_bucket') == crawler.requests[2]

    
