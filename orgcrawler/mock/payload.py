import boto3


args_dict = dict(
    arg1='cat',
    arg2='dog',
    arg3='rat',
)
args = ('cat', 'dog', 'rat')
two_args = ('dog', 'rat')
kwargs = dict(
    kwarg1='horse',
    kwarg2='sheep',
    kwarg3='cow',
)
two_kwargs = dict(
    kwarg2='sheep',
    kwarg3='cow',
)
all_args = dict(
    arg1='cat',
    arg2='dog',
    arg3='rat',
    kwarg1='horse',
    kwarg2='sheep',
    kwarg3='cow',
)


def set_mock_account_alias(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    client.create_account_alias(AccountAlias='alias-' + account.name)
    return


def get_mock_account_alias(region, account):
    client = boto3.client('iam', region_name=region, **account.credentials)
    response = client.list_account_aliases()
    return response['AccountAliases']


def create_mock_bucket(region, account, bucket_prefix):
    client = boto3.client('s3', region_name=region, **account.credentials)
    response = client.create_bucket(Bucket='-'.join([bucket_prefix, account.id]))
    return response


def bad_payload_func(region, account):
    client = boto3.client('ec2', region_name=region, **account.credentials)
    response = client.create_instance(BadParam='bogus')
    return response  # pragma: no cover


def positional_params(region, account, arg1, arg2, arg3):
    return dict(params=dict(
        arg1=arg1,
        arg2=arg2,
        arg3=arg3,
    ))


def kwarg_params(region, account, kwarg1='default1', kwarg2='default2', kwarg3='default3'):
    return dict(params=dict(
        kwarg1=kwarg1,
        kwarg2=kwarg2,
        kwarg3=kwarg3,
    ))


def mixed_params(region, account, arg1, arg2, arg3, kwarg1='default1', kwarg2='default2', kwarg3='default3'):
    return dict(params=dict(
        arg1=arg1,
        arg2=arg2,
        arg3=arg3,
        kwarg1=kwarg1,
        kwarg2=kwarg2,
        kwarg3=kwarg3,
    ))
