import sys
import os

import boto3
from moto import mock_sts, mock_organizations
import pytest

from organizer import orgs, cli
from .test_orgs import (
    MASTER_ACCOUNT_ID,
    ORG_ACCESS_ROLE,
    COMPLEX_ORG_SPEC,
    build_mock_org,
)


def test_cli_syntax_error():
    output = os.system('organizer >/dev/null 2>&1')
    assert output == 256
    output = os.system('organizer -h >/dev/null 2>&1')
    assert output == 0
    output = os.system('organizer bogus_rolename blivit >/dev/null 2>&1')
    assert output == 256
    output = os.system('organizer -f blee bogus_rolename list_accounts >/dev/null 2>&1')
    assert output == 256
    output = os.system('organizer bogus_rolename list_accounts_in_ou >/dev/null 2>&1')
    assert output == 256


"""
This test cannot run because os.system runs commands in a subshell which has
no notion of my mocked organization.  I should figure out about moto server

@mock_sts
@mock_organizations
def test_cli_commands():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org_id, root_id = build_mock_org(COMPLEX_ORG_SPEC)
    org.load()
    output = os.system('organizer {} list_accounts >/dev/null 2>&1'.format(ORG_ACCESS_ROLE))
    assert output == 0
"""
