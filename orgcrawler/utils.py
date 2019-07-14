import sys
import threading
try:
    import queue
except ImportError:     # pragma: no cover
    import Queue as queue
import json
import yaml
import inspect
import time
from datetime import datetime
from functools import singledispatch

import boto3
from botocore.exceptions import ClientError

from orgcrawler.logger import Logger


DEFAULT_LOGLEVEL = 'warning'
DEFAULT_THREAD_COUNT = 6


def get_logger(log_level=DEFAULT_LOGLEVEL):
    my_logger = Logger(loglevel=log_level)
    message = {
        'FILE': __file__.split('/')[-1],
        'FUCNTION': inspect.stack()[0][3],
    }
    my_logger.info(message)
    return my_logger


@singledispatch
def to_serializable(val):
    return str(val)     # pragma: no cover


@to_serializable.register(datetime)
def _(val):
    return val.isoformat()


# @to_serializable.register(orgcrawler.orgs.OrgObject)
# def _(val):
#     return val.dump()
#
# Unfortunateley, This does not work:
#   File "/home/agould/git-repos/github/ucopacme/orgcrawler/orgcrawler/utils.py", line 34, in <module>
#     def ts_org_object(val: orgs.OrgObject):
# AttributeError: module 'orgcrawler.orgs' has no attribute 'OrgObject'


def jsonfmt(obj, default=to_serializable):
    if isinstance(obj, str):
        return obj
    return json.dumps(
        obj,
        indent=4,
        separators=(',', ': '),
        default=default,
    )


def yamlfmt(obj):
    if isinstance(obj, str):
        return obj
    try:
        return yaml.dump(obj, default_flow_style=False)
    except Exception:  # pragma: no cover
        return yaml.dump(str(obj))


def assume_role_in_account(account_id, role_name):
    # any exceptions must be caugh by calling function
    role_arn = 'arn:aws:iam::{}:role/{}'.format(account_id, role_name)
    role_session_name = account_id + '-' + role_name.split('/')[-1]
    sts_client = boto3.client('sts')
    credentials = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName=role_session_name
    )['Credentials']
    return dict(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )


def get_master_account_id(role_name=None):
    sts_client = boto3.client('sts')
    try:
        account_id = sts_client.get_caller_identity()['Account']
    except ClientError as e:    # pragma: no cover
        sys.exit('Cant obtain master account id: {}'.format(e.response['Error']['Code']))
    try:
        credentials = assume_role_in_account(account_id, role_name)
    except ClientError as e:    # pragma: no cover
        errmsg = 'cannot assume role {} in account {}: {}'.format(
            role_name,
            account_id,
            e.response['Error']['Code'],
        )
        sys.exit(errmsg)
    client = boto3.client('organizations', **credentials)
    try:
        return client.describe_organization()['Organization']['MasterAccountId']
    except ClientError as e:
        sys.exit(e)


def queue_threads(sequence, func, func_args=(), thread_count=DEFAULT_THREAD_COUNT, logger=get_logger()):
    """
    Generalized abstraction for running queued tasks in a thread pool

    Args:
        sequence (list): list of items or data structures to iterate over
        func (Function): python code to run within the threads
        func_args (tuple): optional arguments for 'func'
        thread_count (int): number of threads to create [Default: DEFAULT_THREAD_COUNT]
        logger (orgcrawler.logger.Logger): a logger instance [Default: get_logger()]
    """
    message = {
        'FILE': __file__.split('/')[-1],
        'METHOD': inspect.stack()[0][3],
        'func': func,
        'func_args': func_args,
    }
    logger.info(message)

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
    regions = s.get_available_regions(service_name)
    if len(regions) == 0:
        regions = 'GLOBAL'
    return regions


def all_regions():
    return regions_for_service('ec2')


def handle_nexttoken_and_retries(obj, collector_key, function, kwargs=dict()):
    message = {
        'FILE': __file__.split('/')[-1],
        'FUNCTION': inspect.stack()[0][3],
        'OBJECT': obj.__class__,
        'object_id': obj.id,
    }
    obj.logger.info(message)
    max_retry = 4
    retry_count = 0
    response = None
    next_token = None
    collector = []
    while response is None or next_token is not None:
        try:
            if next_token is None:
                response = function(**kwargs)
            else:
                response = function(NextToken=next_token, **kwargs)
            next_token = response.get('NextToken')
            collector += response[collector_key]
        except ClientError as e:
            if e.response['Error']['Code'] == 'TooManyRequestsException':
                if retry_count < max_retry:
                    retry_count += 1
                    message['passed_function'] = function
                    message['error'] = 'TooManyRequestsException'
                    message['retry_count'] = retry_count
                    obj.logger.warning(message)
                    time.sleep(1)
                    continue
                else:
                    raise e
            else:
                raise e
    return collector
