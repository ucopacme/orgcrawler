import boto3
from moto import (
    mock_organizations,
    mock_sts,
    mock_iam,
    mock_s3,
    mock_route53,
    mock_config,
)

from orgcrawler import payloads
from orgcrawler.utils import yamlfmt
from orgcrawler.cli.utils import setup_crawler
from .test_orgs import (
    ORG_ACCESS_ROLE,
    SIMPLE_ORG_SPEC,
    build_mock_org,
)


@mock_sts
@mock_organizations
@mock_iam
def test_iam_list_users():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    account = crawler.accounts[0]
    region = crawler.regions[0]
    client = boto3.client('iam', region_name=region, **account.credentials)
    client.create_user(UserName='test_user')
    response = payloads.iam_list_users(region, account)
    assert response['Users'][0]['UserName'] == 'test_user'


@mock_sts
@mock_organizations
@mock_iam
def test_get_set_account_aliases():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    account = crawler.accounts[0]
    region = crawler.regions[0]
    response = payloads.set_account_alias(region, account)
    response = payloads.get_account_aliases(region, account)
    assert response['Aliases'] == account.name
    response = payloads.set_account_alias(region, account, alias='test_alias')
    response = payloads.get_account_aliases(region, account)
 

@mock_sts
@mock_organizations
@mock_s3
def test_create_list_delete_buckets():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    account = crawler.accounts[0]
    region = crawler.regions[0]

    # test create and list
    response = payloads.create_bucket(region, account, 'test_bucket')
    print(response)
    assert response['CreateBucketOperation']['BucketName'] == '-'.join(['test_bucket', account.id, region])
    assert response['CreateBucketOperation']['Succeeded'] == True
    assert response['CreateBucketOperation']['HTTPStatusCode'] == 200
    response = payloads.list_buckets(region, account)
    print(response)
    assert response['Buckets'][0] == '-'.join(['test_bucket', account.id, region])

    # test error conditions
    response = payloads.create_bucket(region, account, 'test_bucket')
    print(response)
    assert response['CreateBucketOperation']['BucketName'] == '-'.join(['test_bucket', account.id, region])
    assert response['CreateBucketOperation']['Succeeded'] == False
    assert response['CreateBucketOperation']['ErrorCode'] == 'BucketAlreadyExists'
    response = payloads.delete_bucket(region, account, 'test_bucket')
    print(response)
    assert response['DeleteBucketOperation']['BucketName'] == '-'.join(['test_bucket', account.id, region])
    assert response['DeleteBucketOperation']['Succeeded'] == True
    assert response['DeleteBucketOperation']['HTTPStatusCode'] == 204
    response = payloads.delete_bucket(region, account, 'test_bucket')
    print(response)
    assert response['DeleteBucketOperation']['BucketName'] == '-'.join(['test_bucket', account.id, region])
    assert response['DeleteBucketOperation']['Succeeded'] == False
    assert response['DeleteBucketOperation']['ErrorCode'] == 'NoSuchBucket'

    # test edge case for location constraint
    region = 'us-east-1'
    response = payloads.create_bucket(region, account, 'test_bucket')
    print(response)
    assert response['CreateBucketOperation']['Succeeded'] == True
    response = payloads.list_buckets(region, account)
    print(response)
    assert response['Buckets'][0] == '-'.join(['test_bucket', account.id, region])
 

@mock_sts
@mock_organizations
@mock_route53
def test_list_hosted_zones():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    account = crawler.accounts[0]
    region = crawler.regions[0]
    client = boto3.client('route53', region_name=region, **account.credentials)
    client.create_hosted_zone(
        Name='test_zone.example.com',
        CallerReference='a_unique_string'
    )
    response = payloads.list_hosted_zones(region, account)
    assert response['HostedZones'][0]['Name'] == 'test_zone.example.com.'


@mock_sts
@mock_organizations
@mock_config
def test_config_resource_counts():
    pass
    #NotImplementedError: The get_discovered_resource_counts action has not been implemented
    #response = payloads.config_resource_counts(region, account)


@mock_sts
@mock_organizations
@mock_config
def test_config_describe_rules():
    pass
    #NotImplementedError: The describe_config_rules action has not been implemented
    #response = payloads.config_describe_rules(region, account)


@mock_sts
@mock_organizations
@mock_config
def test_config_describe_recorder_status():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    account = crawler.accounts[0]
    region = crawler.regions[0]
    client = boto3.client('config', region_name=region, **account.credentials)
    client.put_configuration_recorder(ConfigurationRecorder={
        'name': 'config_test',
        'roleARN': 'config_test',
    })
    response = payloads.config_describe_recorder_status(region, account)
    assert response['ConfigurationRecordersStatus'][0]['name'] == 'config_test'

