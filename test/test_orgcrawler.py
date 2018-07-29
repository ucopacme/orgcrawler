#import re
#import botocore
#import boto3
#import yaml
#import json
#import moto
from moto import mock_organizations, mock_sts
import pytest

from organizer import orgcrawler, orgs
from .test_orgs import (
    MASTER_ACCOUNT_ID,
    ORG_ACCESS_ROLE,
    COMPLEX_ORG_SPEC,
    build_mock_org,
)


@mock_sts
@mock_organizations
def test_crawler_init():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org_id, root_id = build_mock_org(COMPLEX_ORG_SPEC)
    org.load()
    crawler = orgcrawler.Crawler(org)
    assert isinstance(crawler, orgcrawler.Crawler)
    assert isinstance(crawler.org, orgs.Org)
    assert crawler.access_role == org.access_role
    assert crawler.accounts == org.accounts
    assert crawler.regions == [orgcrawler.DEFAULT_REGION]
    
    ou01_id = org.get_org_unit_id_by_name('ou01')
    ou01_accounts = org.list_accounts_in_ou(ou01_id)
    crawler = orgcrawler.Crawler(
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
    crawler = orgcrawler.Crawler(org)
    crawler.load_account_credentials()
    assert isinstance(crawler.accounts, list)
    assert len(crawler.accounts) == len(org.accounts)
    for account in crawler.accounts:
        assert isinstance(account.credentials, dict)

    
