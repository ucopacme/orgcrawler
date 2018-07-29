import boto3

def main(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    response = client.list_account_aliases()
    return response['AccountAliases']
