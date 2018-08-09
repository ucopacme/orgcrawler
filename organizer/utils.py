import sys
import threading
try:
    import queue
except ImportError:
    import Queue as queue
import json
import yaml

import boto3
from botocore.exceptions import ClientError

import organizer


def jsonfmt(obj):
    if isinstance(obj, str):
        return obj
    return json.dumps(
        obj,
        indent=4,
        separators=(',', ': '),
        default=organizer.orgs.OrgObject.dump
    )


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
        elif e.response['Error']['Code'] == 'ExpiredToken':
            errmsg = 'cannot assume role {} in account {}: ExpiredToken'.format(
                role_name, account_id
            )
        else:
            raise e
        sys.exit(errmsg)
    return dict(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )


def get_master_account_id(role_name=None):
    sts_client = boto3.client('sts')
    try:
        account_id = sts_client.get_caller_identity()['Account']
    except ClientError as e:
        sys.exit('Cant obtain master account id: {}'.format(e.response['Error']['Code']))
    credentials = assume_role_in_account(account_id, role_name)
    client = boto3.client('organizations', **credentials)
    try:
        return client.describe_organization()['Organization']['MasterAccountId']
    except ClientError as e:
        sys.exit(e)


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


def regions_for_service(service_name):
    s = boto3.session.Session()
    if service_name not in s.get_available_services():
        raise ValueError("'{}' is not a valid AWS service".format(service_name))
    return s.get_available_regions(service_name)


def all_regions():
    return regions_for_service('ec2')
