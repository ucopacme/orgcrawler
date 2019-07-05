import re
import time
import datetime
import json

import yaml
import pytest
import boto3
from botocore.exceptions import ClientError
from moto import mock_sts, mock_organizations

from orgcrawler import utils, orgs
from orgcrawler.mock.org import (
    SIMPLE_ORG_SPEC,
    MASTER_ACCOUNT_ID,
    ORG_ACCESS_ROLE,
)


def test_jsonfmt():
    output = utils.jsonfmt(SIMPLE_ORG_SPEC)
    assert isinstance(output, str)
    dt = datetime.datetime.utcnow()
    output = utils.jsonfmt(dt)
    assert isinstance(output, str)
    account = orgs.OrgAccount(
        orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE),
        name='account01',
        id='112233445566',
        email='account01@example.org',
    )
    output = utils.jsonfmt(account, orgs.OrgObject.dump)
    assert isinstance(output, str)


def test_yamlfmt():
    output = utils.yamlfmt(SIMPLE_ORG_SPEC)
    assert isinstance(output, str)
    dt = datetime.datetime.utcnow()
    output = utils.yamlfmt(dt)
    assert isinstance(output, str)
    account = orgs.OrgAccount(
        orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE),
        name='account01',
        id='112233445566',
        email='account01@example.org',
    )
    output = utils.yamlfmt(account)
    assert isinstance(output, str)


@mock_sts
def test_assume_role_in_account():
    role_name = 'myrole'
    account_id = '123456789012'
    credentials = utils.assume_role_in_account(account_id, role_name)
    assert 'aws_access_key_id' in credentials
    assert 'aws_secret_access_key' in credentials
    assert 'aws_session_token' in credentials


@mock_sts
@mock_organizations
def test_get_master_account_id():
    role_name = 'myrole'
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']
    org_client = boto3.client('organizations')
    with pytest.raises(SystemExit):
        master_account_id = utils.get_master_account_id(role_name=role_name)
    org_client.create_organization(FeatureSet='ALL')
    master_account_id = utils.get_master_account_id(role_name=role_name)
    assert re.compile(r'[0-9]{12}').match(master_account_id)


def test_queue_threads():
    collector = []
    def thread_test(item, collector):
        time.sleep(0.1)
        collector.append('item-{}'.format(item))
    starttime = time.perf_counter()
    utils.queue_threads(
        range(10),
        thread_test,
        (collector,),
        thread_count=10
    )
    stoptime = time.perf_counter()
    assert len(collector) == 10
    for item in collector:
        assert re.compile(r'item-[0-9]').match(item)
    assert int((stoptime - starttime) *10) < 5


def test_regions_for_service():
    regions = utils.regions_for_service('lambda')
    assert isinstance(regions, list)
    assert 'us-east-1' in regions
    regions = utils.regions_for_service('iam')
    assert regions == 'GLOBAL'
    with pytest.raises(Exception):
        regions = utils.regions_for_service('blee')
    all_regions = utils.all_regions()
    assert all_regions == utils.regions_for_service('ec2')
