import sys
import threading
try:
    import queue
except ImportError:
    import Queue as queue

import boto3
from botocore.exceptions import ClientError


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


def queue_threads(sequence, func, func_args=(), thread_count=20, debug=False):
    """generalized abstraction for running queued tasks in a thread pool"""
    #queue_threads(deployed_accounts, get_account_alias,
    #        func_args=(role, aliases), thread_count=10)
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


#def queue_threads(sequence, func, func_args=(), thread_count=20, debug=False):
#    """generalized abstraction for running queued tasks in a thread pool"""
#    #queue_threads(deployed_accounts, get_account_alias,
#    #        func_args=(role, aliases), thread_count=10)
#    def worker(*args):
#        if debug:
#            print('%s: q.empty: %s' % (threading.current_thread().name, q.empty()))
#        while not q.empty():
#            if debug:
#                print('%s: task: %s' % (threading.current_thread().name, func))
#            item = q.get()
#            if debug:
#                print('%s: processing item: %s' % (threading.current_thread().name, item))
#            func(item, *args)
#            q.task_done()
#    q = queue.Queue()
#    for item in sequence:
#        if debug:
#            print('queuing item: %s' % item)
#        q.put(item)
#    if debug:
#        print('queue length: %s' % q.qsize())
#    for i in range(thread_count):
#        t = threading.Thread(target=worker, args=func_args)
#        t.setDaemon(True)
#        t.start()
#    q.join()

