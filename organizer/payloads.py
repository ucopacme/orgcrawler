import boto3


def set_account_alias(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    client.create_account_alias(AccountAlias=account.name)
    return


def get_account_aliases(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    response = client.list_account_aliases()
    return dict(Aliases=', '.join(response['AccountAliases']))


def create_bucket(region, account, bucket_name):
    client = boto3.client('s3', region_name=region, **account.credentials)
    return client.create_bucket(
        Bucket = bucket_name,
        CreateBucketConfiguration={'LocationConstraint': region}
    )


def list_buckets(region, account):
    client = boto3.client('s3', region_name=region, **account.credentials)
    response = client.list_buckets()
    return dict(Buckets=[b['Name'] for b in response['Buckets']])


def create_hosted_zone(region, account, domain_name):
    client = boto3.client('route53', region_name=region, **account.credentials)
    return client.create_hosted_zone(
        Name=domain_name,
        CallerReference=domain_name,
    )


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


def config_resource_counts(region, account):
    client = boto3.client('config', region_name=region, **account.credentials)
    response = client.get_discovered_resource_counts()
    return dict(resourceCounts=response['resourceCounts'])


def config_describe_rules(region, account):
    client = boto3.client('config', region_name=region, **account.credentials)
    response = client.describe_config_rules()
    return dict(ConfigRules=response['ConfigRules'])


def config_describe_recorder_status(region, account):
    client = boto3.client('config', region_name=region, **account.credentials)
    response = client.describe_configuration_recorder_status()
    return dict(ConfigurationRecordersStatus=response['ConfigurationRecordersStatus'])
    # return dict(ConfigurationRecordersStatus=response['blee'])
