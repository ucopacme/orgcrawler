import re

import boto3
from moto import mock_sts, mock_organizations
import pytest

from organizer import utils

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
