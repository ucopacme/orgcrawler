import re
import boto3
from botocore.exceptions import ClientError


def status_config_svcs(region, account):    # pragma: no cover
    client = boto3.client('config', region_name=region, **account.credentials)
    response = client.describe_configuration_recorder_status()
    response.pop('ResponseMetadata')
    if response['ConfigurationRecordersStatus']:
        state = dict(recording=True)
    else:
        state = dict(recording=False)
    return dict(ConfigurationRecordersStatus=state)


def iam_list_users(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    response = client.list_users()
    collector = response['Users']
    if 'IsTruncated' in response and response['IsTruncated']:   # pragma: no cover
        response = client.list_users(Marker=response['Marker'])
        collector += response['Users']
    return dict(Users=collector)


def set_account_alias(region, account, alias=None):
    client = boto3.client('iam', region_name=region, **account.credentials)
    if alias is None:
        alias = account.name
    client.create_account_alias(AccountAlias=alias)
    return


def get_account_aliases(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    response = client.list_account_aliases()
    return dict(Aliases=', '.join(response['AccountAliases']))


def create_bucket(region, account, bucket_prefix):
    '''
    usage example:
      orgcrawler -r awsauth/OrgAdmin orgcrawler.payloads.create_bucket orgcrawler-testbucket
    '''
    client = boto3.client('s3', region_name=region, **account.credentials)
    bucket_name = '-'.join([bucket_prefix, account.id, region])
    bucket_attributes = {'Bucket': bucket_name}
    if not region == 'us-east-1':
        bucket_attributes['CreateBucketConfiguration'] = {'LocationConstraint': region}
    try:
        response = client.create_bucket(**bucket_attributes)
        operation_outputs = dict(
            BucketName=bucket_name,
            Succeeded=True,
            HTTPStatusCode=response['ResponseMetadata']['HTTPStatusCode']
        )
    except ClientError as e:
        operation_outputs = dict(
            BucketName=bucket_name,
            Succeeded=False,
            ErrorCode=e.response['Error']['Code']
        )
    return dict(CreateBucketOperation=operation_outputs)


def delete_bucket(region, account, bucket_prefix):
    '''
    usage example:
      orgcrawler -r awsauth/OrgAdmin orgcrawler.payloads.delete_bucket orgcrawler-testbucket
    '''
    client = boto3.client('s3', region_name=region, **account.credentials)
    bucket_name = '-'.join([bucket_prefix, account.id, region])
    try:
        response = client.delete_bucket(Bucket=bucket_name)
        operation_outputs = dict(
            BucketName=bucket_name,
            Succeeded=True,
            HTTPStatusCode=response['ResponseMetadata']['HTTPStatusCode']
        )
    except ClientError as e:
        operation_outputs = dict(
            BucketName=bucket_name,
            Succeeded=False,
            ErrorCode=e.response['Error']['Code']
        )
    return dict(DeleteBucketOperation=operation_outputs)


def list_buckets(region, account):
    client = boto3.client('s3', region_name=region, **account.credentials)
    response = client.list_buckets()
    return dict(Buckets=[b['Name'] for b in response['Buckets']])


def list_hosted_zones(region, account):
    client = boto3.client('route53', region_name=region, **account.credentials)
    response = client.list_hosted_zones()
    hosted_zones = []
    for zone in response['HostedZones']:
        response = client.list_resource_record_sets(HostedZoneId=zone['Id'])
        hosted_zones.append(dict(
            Name=zone['Name'],
            Id=zone['Id'],
            RecordSets=response['ResourceRecordSets'],
        ))
    return dict(HostedZones=hosted_zones)


def config_resource_counts(region, account):        # pragma: no cover
    client = boto3.client('config', region_name=region, **account.credentials)
    response = client.get_discovered_resource_counts()
    return dict(resourceCounts=response['resourceCounts'])


def config_describe_rules(region, account):     # pragma: no cover
    '''
    usage example:

      orgcrawler -r OrganizationAccountAccessRole orgcrawler.payloads.config_describe_rules

      orgcrawler -r OrganizationAccountAccessRole --regions us-west-2 orgcrawler.payloads.config_describe_rules | jq -r '.[] | .Account, (.Regions[] | ."us-west-2".ConfigRules[].ConfigRuleName), ""' | tee config_rules_in_accounts.us-west-2
    '''
    client = boto3.client('config', region_name=region, **account.credentials)
    response = client.describe_config_rules()
    rules = response['ConfigRules']
    while 'NextToken' in response:
        response = client.describe_config_rules(NextToken=response['NextToken'])
        rules += response['ConfigRules']
    return dict(ConfigRules=rules)


def config_describe_recorder_status(region, account):
    client = boto3.client('config', region_name=region, **account.credentials)
    response = client.describe_configuration_recorder_status()
    response.pop('ResponseMetadata')
    return response


def check_cloudtrail_status(region, account):   # pragma: no cover
    client = boto3.client('cloudtrail', region_name=region, **account.credentials)
    response = client.describe_trails()
    trail_accounts = []
    for trail in response['trailList']:
        x = re.findall(r"\BloudTrail", trail["Name"])
        if x:
            trail_accounts.append(dict(
                Name=trail['Name'],
                status="enabled",
            ))
    return dict(TrailAccounts=trail_accounts)
