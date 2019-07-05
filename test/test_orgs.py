import os
import re
import time
import json
import pickle
import shutil

import yaml
import botocore
import boto3
import pytest
import moto
from moto import mock_organizations, mock_sts

from orgcrawler import utils, orgs, crawlers
from orgcrawler.mock.org import (
    MockOrganization,
    ORG_ACCESS_ROLE,
    MASTER_ACCOUNT_ID,
)


@mock_organizations
def test_org():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    assert isinstance(org, orgs.Org)
    assert org.master_account_id == MASTER_ACCOUNT_ID
    assert org.access_role == ORG_ACCESS_ROLE


@mock_sts
@mock_organizations
def test_get_org_client():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    client = org._get_org_client()
    assert str(type(client)).find('botocore.client.Organizations') > 0

@mock_sts
@mock_organizations
def test_load_client():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org._load_client()
    assert str(type(org._client)).find('botocore.client.Organizations') > 0

@mock_sts
@mock_organizations
def test_load_org():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    client = org._get_org_client()
    client.create_organization(FeatureSet='ALL')
    org._load_client()
    org._load_org()
    assert org.id is not None
    assert org.root_id is not None

@mock_sts
@mock_organizations
def test_org_objects():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    client = org._get_org_client()
    client.create_organization(FeatureSet='ALL')
    org._load_client()
    org._load_org()

    org_object = orgs.OrgObject(org, name='generic')
    assert isinstance(org_object, orgs.OrgObject)
    assert org_object.organization_id == org.id
    assert org_object.master_account_id == org.master_account_id
    assert org_object.name == 'generic'

    policy = orgs.OrgPolicy(
        org,
        name='policy01',
        id='p-fue927ci',
    )
    assert isinstance(policy, orgs.OrgPolicy)
    assert policy.organization_id == org.id
    assert policy.master_account_id == org.master_account_id
    assert policy.name == 'policy01'
    assert policy.id == 'p-fue927ci'
    assert isinstance(policy.targets, list)

    account = orgs.OrgAccount(
        org,
        name='account01',
        id='112233445566',
        parent_id=org.root_id,
        email='account01@example.org',
    )
    assert isinstance(account, orgs.OrgAccount)
    assert account.organization_id == org.id
    assert account.master_account_id == org.master_account_id
    assert account.name == 'account01'
    assert account.id == '112233445566'
    assert account.parent_id == org.root_id
    assert account.email == 'account01@example.org'

    ou = orgs.OrganizationalUnit(
        org,
        name='production',
        id='o-jfk0',
        parent_id=org.root_id,
    )
    assert isinstance(ou, orgs.OrganizationalUnit)
    assert ou.organization_id == org.id
    assert ou.master_account_id == org.master_account_id
    assert ou.name == 'production'
    assert ou.id == 'o-jfk0'
    assert ou.parent_id == org.root_id


@mock_sts
@mock_organizations
def test_load_accounts():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org._load_client()
    org._load_org()
    org._load_accounts()
    assert len(org.accounts) == 3
    assert isinstance(org.accounts[0], orgs.OrgAccount)
    assert org.accounts[0].parent_id == org.root_id


@mock_sts
@mock_organizations
def test_load_org_units():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org._load_client()
    org._load_org()
    org._load_org_units()
    assert len(org.org_units) == 6
    for ou in org.org_units:
        assert isinstance(ou, orgs.OrganizationalUnit)

 
@mock_sts
@mock_organizations
def test_load_policies():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org._load_client()
    org._load_org()
    org._load_policies()
    assert len(org.policies) == 3
    for policy in org.policies:
        assert isinstance(policy, orgs.OrgPolicy)


@mock_sts
@mock_organizations
def test_org_cache():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org._load_client()
    org._load_org()
    org._load_accounts()
    org._load_org_units()

    org._save_cached_org_to_file()
    assert os.path.exists(org._cache_file)

    org.clear_cache()
    assert not os.path.exists(org._cache_file)
    assert not os.path.exists(org._cache_dir)

    #os.remove(org._cache_file)
    with pytest.raises(RuntimeError) as e:
        loaded_dump = org._get_cached_org_from_file()
    assert str(e.value) == 'Cache file not found'

    org._save_cached_org_to_file()
    timestamp = os.path.getmtime(org._cache_file) - 3600
    os.utime(org._cache_file,(timestamp,timestamp))
    with pytest.raises(RuntimeError) as e:
        loaded_dump = org._get_cached_org_from_file()
    assert str(e.value) == 'Cache file too old'

    org._save_cached_org_to_file()
    org_dump = org.dump()
    loaded_dump = org._get_cached_org_from_file()
    assert loaded_dump == org_dump

    org_from_cache = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org_from_cache._load_org_dump(loaded_dump)
    assert org.dump() == org_from_cache.dump()


@mock_sts
@mock_organizations
def test_load():
    mock_org = MockOrganization()
    mock_org.simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.clear_cache()
    assert not os.path.exists(org._cache_dir)
    assert not os.path.exists(org._cache_file)
    org.load()
    assert os.path.exists(org._cache_file)
    assert org.id == mock_org.org_id
    assert org.root_id == mock_org.root_id
    assert len(org.accounts) == 3
    assert len(org.org_units) == 6
    assert len(org.policies) == 3

    for ou in org.org_units:
        for policy_id in ou.attached_policy_ids:
            assert policy_id in [p.id for p in org.policies]
    for account in org.accounts:
        for policy_id in account.attached_policy_ids:
            assert policy_id in [p.id for p in org.policies]

    for policy in org.policies:
        for target in policy.targets:
            if target['Type'] == 'ROOT':
                assert target['TargetId'] == mock_org.root_id
            elif target['Type'] == 'ORGANIZATIONAL_UNIT':
                assert target['TargetId'] in [ou.id for ou in org.org_units]
            elif target['Type'] == 'ACCOUNT':
                assert target['TargetId'] in [a.id for a in org.accounts]

    org_from_cache = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org_from_cache.load()
    assert org.dump() == org_from_cache.dump()
    org.clear_cache()

@mock_sts
@mock_organizations
def test_dump_accounts():
    mock_org = MockOrganization()
    mock_org.simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    response = org.dump_accounts()
    assert isinstance(response, list)
    assert len(response) == 3
    mock_accounts = mock_org.spec['root'][0]['accounts']
    for account in response:
        assert account['master_account_id'] == MASTER_ACCOUNT_ID
        assert account['organization_id'] == org.id
        assert account['name'] in [a['name'] for a in mock_accounts]
        assert re.compile(r'[0-9]{12}').match(account['id'])
        assert account['parent_id'] == org.root_id
        assert account['email'] == account['name'] + '@example.com'
        assert len(account['aliases']) == 0
        assert len(account['credentials']) == 0
    org.clear_cache()

 
@mock_sts
@mock_organizations
def test_list_accounts_by_name_or_id():
    mock_org = MockOrganization()
    mock_org.simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    mock_accounts = mock_org.spec['root'][0]['accounts']
    response = org.list_accounts_by_name()
    assert isinstance(response, list)
    assert len(response) == 3
    assert sorted(response) == [a['name'] for a in mock_accounts]
    response = org.list_accounts_by_id()
    assert isinstance(response, list)
    assert len(response) == 3
    for account_id in response:
        assert re.compile(r'[0-9]{12}').match(account_id)
    org.clear_cache()


@mock_sts
@mock_organizations
def test_dump_org_units():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    response = org.dump_org_units()
    assert isinstance(response, list)
    assert len(response) == 6
    for ou in response:
        assert isinstance(ou, dict)
        assert ou['master_account_id'] == MASTER_ACCOUNT_ID
        assert ou['organization_id'] == org.id
        assert ou['name'].startswith('ou0')
        assert ou['id'].startswith('ou-')
        assert (
            ou['parent_id'] == org.root_id
            or ou['parent_id'].startswith(org.root_id.replace('r-', 'ou-'))
        )
    org.clear_cache()

 
@mock_sts
@mock_organizations
def test_list_org_units_by_name_or_id():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    response = org.list_org_units_by_name()
    assert isinstance(response, list)
    assert len(response) == 6
    for ou_name in response:
        assert ou_name.startswith('ou0')
    response = org.list_org_units_by_id()
    assert isinstance(response, list)
    assert len(response) == 6
    for ou_id in response:
        assert ou_id.startswith('ou-')
    org.clear_cache()


@mock_sts
@mock_organizations
def test_org_dump():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    crawler = crawlers.Crawler(org)
    crawler.load_account_credentials()
    dump = org.dump()
    assert isinstance(dump, dict)
    assert dump['id']
    assert dump['id'].startswith('o-')
    assert dump['master_account_id'] == MASTER_ACCOUNT_ID
    assert dump['root_id'].startswith('r-')
    assert dump['accounts'] == org.dump_accounts()
    assert dump['org_units'] == org.dump_org_units()
    json_dump = org.dump_json()
    assert isinstance(json_dump, str)
    assert json.loads(json_dump) == dump
    org.clear_cache()

 
@mock_sts
@mock_organizations
def test_get_account_id_by_name():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    account_id = org.get_account_id_by_name('account01')
    accounts_by_boto_client = org._client.list_accounts()['Accounts']
    assert account_id == next((
        a['Id'] for a in accounts_by_boto_client if a['Name'] == 'account01'
    ), None)
    org.clear_cache()

 
@mock_sts
@mock_organizations
def test_get_account_name_by_id():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    account_id = org.get_account_id_by_name('account01')
    account_name = org.get_account_name_by_id(account_id)
    accounts_by_boto_client = org._client.list_accounts()['Accounts']
    assert account_name == next((
        a['Name'] for a in accounts_by_boto_client if a['Id'] == account_id
    ), None)
    org.clear_cache()

 
@mock_sts
@mock_organizations
def test_get_account():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    account = org.get_account('account01')
    assert isinstance(account, orgs.OrgAccount)
    assert org.get_account(account) == account
    assert account.name == 'account01'
    assert account.id == org.get_account_id_by_name('account01')
    org.clear_cache()

 
@mock_sts
@mock_organizations
def test_get_org_unit_id():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    ou = org.org_units[0]
    assert ou.id == org.get_org_unit_id(ou)
    assert ou.id == org.get_org_unit_id(ou.id)
    assert ou.id == org.get_org_unit_id(ou.name)
    assert org.get_org_unit_id('Blee') is None
    org.clear_cache()

 
@mock_sts
@mock_organizations
def test_list_accounts_in_ou():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    response = org.list_accounts_in_ou(org.root_id)
    accounts_by_boto_client = org._client.list_accounts_for_parent(
        ParentId=org.root_id
    )['Accounts']
    for account in response:
        assert account.id == next((
            a['Id'] for a in accounts_by_boto_client
            if a['Name'] == account.name
        ), None)
    response = org.list_accounts_in_ou('ou02')
    accounts_by_boto_client = org._client.list_accounts_for_parent(
        ParentId=org.get_org_unit_id('ou02')
    )['Accounts']
    for account in response:
        assert account.id == next((
            a['Id'] for a in accounts_by_boto_client
            if a['Name'] == account.name
        ), None)
    org.clear_cache()

 
@mock_sts
@mock_organizations
def test_list_org_units_in_ou():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    response = org.list_org_units_in_ou(org.root_id)
    ou_by_boto_client = org._client.list_organizational_units_for_parent(
        ParentId=org.root_id
    )['OrganizationalUnits']
    for org_unit in response:
        assert org_unit.id == next((
            ou['Id'] for ou in ou_by_boto_client
            if ou['Name'] == org_unit.name
        ), None)
    response = org.list_org_units_in_ou('ou02')
    ou_by_boto_client = org._client.list_organizational_units_for_parent(
        ParentId=org.get_org_unit_id('ou02')
    )['OrganizationalUnits']
    for org_unit in response:
        assert org_unit.id == next((
            ou['Id'] for ou in ou_by_boto_client
            if ou['Name'] == org_unit.name
        ), None)
    org.clear_cache()

 
@mock_sts
@mock_organizations
def test_list_org_units_in_ou_recursive():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    response = org.list_org_units_in_ou_recursive(org.root_id)
    assert len(response) == 6
    for ou in response:
        assert isinstance(ou, orgs.OrganizationalUnit)
        assert ou.id.startswith('ou-')
    response = org.list_org_units_in_ou_recursive('ou02')
    assert len(response) == 2
    org.clear_cache()


@mock_sts
@mock_organizations
def test_list_accounts_in_ou_recursive():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    response = org.list_accounts_in_ou_recursive(org.root_id)
    assert len(response) == 13
    for account in response:
        assert isinstance(account, orgs.OrgAccount)
        assert account.name.startswith('account')
        assert re.compile(r'[0-9]{12}').match(account.id)
    response = org.list_accounts_in_ou_recursive('ou02')
    assert len(response) == 5
    response = org.list_accounts_in_ou_recursive('ou02-1')
    assert len(response) == 1
    org.clear_cache()


@mock_sts
@mock_organizations
def test_list_policies_by_name():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    response = org.list_policies_by_name()
    print(response)
    assert len(response) == 6
    for name in response:
        assert name.startswith('policy')
    org.clear_cache()


@mock_sts
@mock_organizations
def test_list_policies_by_id():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    response = org.list_policies_by_id()
    print(response)
    assert len(response) == 6
    for policy_id in response:
        assert re.compile(r'p-[a-z0-9]{8}').match(policy_id)
    org.clear_cache()


@mock_sts
@mock_organizations
def test_get_policy():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    policy = org.get_policy('policy01')
    assert isinstance(policy, orgs.OrgPolicy)
    assert policy.name == 'policy01'
    assert org.get_policy(policy) == policy
    policy_id = next((p.id for p in org.policies))
    policy = org.get_policy(policy_id)
    assert isinstance(policy, orgs.OrgPolicy)
    assert policy.id == policy_id
    assert org.get_policy('BLEE') is None
    assert org.get_policy(org) is None
    org.clear_cache()


@mock_sts
@mock_organizations
def test_get_policy_id_by_name():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    policy_id = org.get_policy_id_by_name('policy01')
    assert isinstance(policy_id, str)
    assert policy_id == org.get_policy('policy01').id
    assert org.get_policy_id_by_name('BLEE') is None
    org.clear_cache()


@mock_sts
@mock_organizations
def test_get_policy_name_by_id():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    policy_id = org.get_policy_id_by_name('policy01')
    response = org.get_policy_name_by_id(policy_id)
    assert isinstance(response, str)
    assert response == 'policy01'
    assert org.get_policy_name_by_id('BLEE') is None
    org.clear_cache()


@mock_sts
@mock_organizations
def test_get_policy_id():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    policy_id = org.get_policy_id('policy01')
    assert isinstance(policy_id, str)
    assert re.compile(r'p-[a-z0-9]{8}').match(policy_id)
    assert policy_id == org.get_policy_id(policy_id)
    assert policy_id == org.get_policy('policy01').id
    assert policy_id == org.get_policy_id_by_name('policy01')
    policy = org.get_policy('policy01')
    assert policy_id == org.get_policy_id(policy)
    assert org.get_policy_id('Blee') is None
    org.clear_cache()


#@mock_sts
#@mock_organizations
#def test_get_policy_document():
#    MockOrganization().complex()
#    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
#    org.load()
#    policy_id = org.get_policy_id('policy01')
#    print(policy_id)
#    response = org._client.describe_policy(PolicyId=policy_id)
#    print(response)
#    #policy_doc = org.get_policy_document('policy01')
#    #print(policy_doc)
#    assert False
#    assert isinstance(policy_doc, str)
#    assert policy_doc == org.get_policy_document(org.get_policy('policy01'))
#    assert policy_doc == org.get_policy_document(org.get_policy_id('policy01'))
#    assert policy_doc == json.loads(POLICY_DOC)
#    org.clear_cache()


@mock_sts
@mock_organizations
def test_get_targets_for_policy():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    targets = org.get_targets_for_policy('policy01')
    assert len(targets) == 4
    for target in targets:
        assert sorted(target.keys()) == [
            'Arn',
            'Name',
            'TargetId',
            'Type',
        ]
    assert sorted([t['Name'] for t in targets]) == [
        'Root',
        'account04',
        'account07',
        'ou01-2',
    ]
    assert org.get_targets_for_policy('Blee') is None
    org.clear_cache()


@mock_sts
@mock_organizations
def test_get_policies_for_target():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    policies = org.get_policies_for_target('account04')
    assert len(policies) == 3
    for policy in policies:
        assert isinstance(policy, orgs.OrgPolicy)
    policies = org.get_policies_for_target('ou01-2')
    assert len(policies) == 3
    for policy in policies:
        assert isinstance(policy, orgs.OrgPolicy)
    policies = org.get_policies_for_target('ou01')
    assert policies is None
    org.clear_cache()


@mock_sts
@mock_organizations
def test_get_accounts_for_policy_recursive():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    accounts_for_policy = org.get_accounts_for_policy_recursive('policy01')
    assert len(accounts_for_policy) == 13
    assert sorted([a.name for a in accounts_for_policy]) == sorted([a.name for a in org.accounts])
    accounts_for_policy = org.get_accounts_for_policy_recursive('policy02')
    assert len(accounts_for_policy) == 13
    accounts_for_policy = org.get_accounts_for_policy_recursive('policy03')
    assert len(accounts_for_policy) == 2 
    assert sorted([a.name for a in accounts_for_policy]) == ['account04', 'account13']
    accounts_for_policy = org.get_accounts_for_policy_recursive('policy04')
    assert len(accounts_for_policy) == 2 
    assert sorted([a.name for a in accounts_for_policy]) == ['account04', 'account13']
    accounts_for_policy = org.get_accounts_for_policy_recursive('policy05')
    assert len(accounts_for_policy) == 3 
    assert sorted([a.name for a in accounts_for_policy]) == ['account07', 'account09', 'account10']
    accounts_for_policy = org.get_accounts_for_policy_recursive('policy06')
    assert len(accounts_for_policy) == 3 
    assert sorted([a.name for a in accounts_for_policy]) == ['account07', 'account09', 'account10']
    assert org.get_accounts_for_policy_recursive('Blee') is None
    org.clear_cache()
