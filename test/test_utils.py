import boto3
import moto
from moto import mock_sts

from organizer import utils

@mock_sts
def test_assume_role_in_account():
    role_name = 'myrole'
    account_id = '123456789012'
    credentials = utils.assume_role_in_account(account_id, role_name)
    print(credentials)
    assert isinstance(credentials, dict)
    #assert False

