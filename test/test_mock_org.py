import json

import yaml
import botocore
import boto3
import pytest
import moto
from moto import mock_organizations, mock_sts

from orgcrawler.mock.org import (
    MockOrganization,
    MASTER_ACCOUNT_ID,
    ORG_ACCESS_ROLE,
    SIMPLE_ORG_SPEC,
    COMPLEX_ORG_SPEC,
)

@mock_sts
@mock_organizations
def test_mock_org():
    mock_org = MockOrganization()
    assert isinstance(mock_org, MockOrganization)
    assert mock_org.master_id == MASTER_ACCOUNT_ID
    assert mock_org.access_role == ORG_ACCESS_ROLE
    assert str(type(mock_org.client)).find('botocore.client.Organizations') > 0


@mock_sts
@mock_organizations
def test_load_org():
    mock_org = MockOrganization()
    mock_org._load_org(SIMPLE_ORG_SPEC)
    assert isinstance(mock_org.spec, dict)
    assert mock_org.spec == yaml.safe_load(SIMPLE_ORG_SPEC)
    assert isinstance(mock_org.org_id, str)
    assert isinstance(mock_org.root_id, str)
            
@mock_sts
@mock_organizations
def test_ou_gen():
    mock_org = MockOrganization()
    mock_org._load_org(SIMPLE_ORG_SPEC)
    ou = dict(name='mock_ou')
    ou_id = mock_org._ou_gen(ou, mock_org.root_id)
    assert isinstance(ou_id, str)
    response = mock_org.client.describe_organizational_unit(OrganizationalUnitId=ou_id)
    assert response['OrganizationalUnit']['Name'] == ou['name']
            
@mock_sts
@mock_organizations
def test_policy_gen():
    mock_org = MockOrganization()
    mock_org._load_org(SIMPLE_ORG_SPEC)
    policy_name = 'mock_policy'
    mock_org._policy_gen(policy_name, mock_org.root_id)
    assert len(mock_org.policy_list) == 1
    assert mock_org.policy_list[0]['Name'] == policy_name
    response = mock_org.client.list_targets_for_policy(
        PolicyId=mock_org.policy_list[0]['Id']
    )
    assert response['Targets'][0]['TargetId'] == mock_org.root_id
            
@mock_sts
@mock_organizations
def test_account_gen():
    mock_org = MockOrganization()
    mock_org._load_org(SIMPLE_ORG_SPEC)
    account = dict(name='mock_account', policies=['p1', 'p2'])
    mock_org._account_gen(account, mock_org.root_id)
    assert len(mock_org.policy_list) == 2
    response = mock_org.client.list_accounts_for_parent(ParentId=mock_org.root_id)
    assert response['Accounts'][0]['Name'] == account['name']

@mock_sts
@mock_organizations
def test_simple_build():
    mock_org = MockOrganization()
    mock_org.simple()
    assert mock_org.spec == yaml.safe_load(SIMPLE_ORG_SPEC)
    assert len(mock_org.client.list_accounts()['Accounts']) == 3
    assert len(mock_org.client.list_policies(
        Filter='SERVICE_CONTROL_POLICY'
    )['Policies']) == 3
    assert len(mock_org.client.list_organizational_units_for_parent(
        ParentId=mock_org.root_id
    )['OrganizationalUnits']) == 3

@mock_sts
@mock_organizations
def test_complex_build():
    mock_org = MockOrganization()
    mock_org.complex()
    assert mock_org.spec == yaml.safe_load(COMPLEX_ORG_SPEC)
    assert len(mock_org.client.list_accounts()['Accounts']) == 13
    assert len(mock_org.client.list_policies(
        Filter='SERVICE_CONTROL_POLICY'
    )['Policies']) == 6
    assert len(mock_org.client.list_organizational_units_for_parent(
        ParentId=mock_org.root_id
    )['OrganizationalUnits']) == 2
