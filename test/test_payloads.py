from moto import (
    mock_organizations,
    mock_sts,
    mock_iam,
    mock_s3,
    mock_route53,
    #mock_config,
)

from organizer import payloads
from organizer.cli.utils import setup_crawler
from .test_orgs import (
    ORG_ACCESS_ROLE,
    SIMPLE_ORG_SPEC,
    build_mock_org,
)


@mock_sts
@mock_organizations
@mock_iam
def test_get_account_aliases():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    account = crawler.accounts[0]
    region = crawler.regions[0]

    response = payloads.set_account_alias(region, account)
    print(response)

    response = payloads.get_account_aliases(region, account)
    print(response)
    assert 0


@mock_sts
@mock_organizations
@mock_s3
def test_get_account_aliases():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    account = crawler.accounts[0]
    region = crawler.regions[0]
    bucket_name = 'test_payloads_bucket'

    response = payloads.create_bucket(region, account, bucket_name)
    print(response)

    response = payloads.list_buckets(region, account)
    print(response)
    assert 0


@mock_sts
@mock_organizations
@mock_route53
def test_get_account_aliases():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    account = crawler.accounts[0]
    region = crawler.regions[0]
    domain_name = 'payloads.orgcrawler.test'

    response = payloads.create_hosted_zone(region, account, domain_name)
    print(response)

    response = payloads.list_hosted_zones(region, account)
    print(response)
    assert 0

'''
@mock_sts
@mock_organizations
@mock_config
def test_get_account_aliases():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    account = crawler.accounts[0]
    region = crawler.regions[0]

    response = payloads.config_resource_counts(region, account)
    print(response)

    response = payloads.config_describe_rules(region, account)
    print(response)
    assert 0

    response = payloads.config_describe_recorder_status(region, account)
    print(response)
    assert 0
'''
