import sys
import threading
try:
    import queue
except ImportError:
    import Queue as queue
import json
import yaml

import boto3


def jsonfmt(obj):
    if isinstance(obj, str):
        return obj
    return json.dumps(obj, indent=4, separators=(',', ': '))
from botocore.exceptions import ClientError


def yamlfmt(obj):
    if isinstance(obj, str):
        return obj
    return yaml.dump(obj, default_flow_style=False)


def assume_role_in_account(account_id, role_name):
    role_arn = 'arn:aws:iam::{}:role/{}'.format(account_id, role_name)
    role_session_name = account_id + '-' + role_name.split('/')[-1]
    sts_client = boto3.client('sts')
    try:
        credentials = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=role_session_name
        )['Credentials']
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDenied':
            errmsg = 'cannot assume role {} in account {}: AccessDenied'.format(
                role_name, account_id
            )
            sys.exit(errmsg)
    return dict(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )


def get_master_account_id(role_name=None):
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']
    credentials = assume_role_in_account(account_id, role_name)
    client = boto3.client('organizations', **credentials)
    try:
        return client.describe_organization()['Organization']['MasterAccountId']
    except ClientError as e:
        sys.exit(e)


# NO TEST YET
def queue_threads(sequence, func, func_args=(), thread_count=20):
    """generalized abstraction for running queued tasks in a thread pool"""
    def worker(*args):
        while not q.empty():
            item = q.get()
            func(item, *args)
            q.task_done()
    q = queue.Queue()
    for item in sequence:
        q.put(item)
    for i in range(thread_count):
        t = threading.Thread(target=worker, args=func_args)
        t.setDaemon(True)
        t.start()
    q.join()
