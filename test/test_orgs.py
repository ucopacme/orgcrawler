import botocore
import boto3
import moto
from moto import mock_organizations, mock_sts

from organizer import orgs

ORG_ACCESS_ROLE='myrole'
MASTER_ACCOUNT_ID='123456789012'

@mock_organizations
def test_org():
    account_id = MASTER_ACCOUNT_ID
    role_name = ORG_ACCESS_ROLE
    org = orgs.Org(account_id, role_name)
    assert isinstance(org, orgs.Org)
    assert org.master_account_id == account_id
    assert org.access_role == role_name


@mock_sts
@mock_organizations
def test_get_org_client():
    account_id = MASTER_ACCOUNT_ID
    role_name = ORG_ACCESS_ROLE
    org = orgs.Org(account_id, role_name)
    client = org.get_org_client()
    assert str(type(client)).find('botocore.client.Organizations') > 0

@mock_sts
@mock_organizations
def test_load_org():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    client = org.get_org_client()
    client.create_organization(FeatureSet='ALL')
    org.load_org()
    assert org.id is not None
    assert org.root_id is not None
 
@mock_sts
@mock_organizations
def test_org_objects():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    client = org.get_org_client()
    client.create_organization(FeatureSet='ALL')
    org.load_org()
    org_object = orgs.OrgObject(org, 'generic')
    assert isinstance(org_object, orgs.OrgObject)
    assert org_object.organization_id == org.id
    assert org_object.master_account_id == org.master_account_id
    assert org_object.name == 'generic'
    account = orgs.OrgAccount(org, 'account01', '112233445566', org.root_id)
    assert isinstance(account, orgs.OrgAccount)
    assert account.organization_id == org.id
    assert account.master_account_id == org.master_account_id
    assert account.name == 'account01'
    assert account.id == '112233445566'
    assert account.parent_id == org.root_id
    ou = orgs.OrganizationalUnit(org, 'production', 'o-jfk0', org.root_id)
    assert isinstance(ou, orgs.OrganizationalUnit)
    assert ou.organization_id == org.id
    assert ou.master_account_id == org.master_account_id
    assert ou.name == 'production'
    assert ou.id == 'o-jfk0'
    assert ou.parent_id == org.root_id

 
@mock_sts
@mock_organizations
def test_load_accounts():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    client = org.get_org_client()
    client.create_organization(FeatureSet='ALL')
    org.load_org()
    for name in ['account01', 'account02', 'account03']:
        client.create_account(AccountName=name, Email=name + '@example.com')
    org.load_accounts()
    assert len(org.accounts) == 3
    assert isinstance(org.accounts[0], orgs.OrgAccount)
    assert org.accounts[0].parent_id == org.root_id

 
@mock_sts
@mock_organizations
def test_load_org_units():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    client = org.get_org_client()
    client.create_organization(FeatureSet='ALL')
    org.load_org()
    for name in ['ou01', 'ou02', 'ou03']:
        client.create_organizational_unit(ParentId=org.root_id, Name=name)
    org.load_org_units()
    assert len(org.org_units) == 3
    assert isinstance(org.org_units[0], orgs.OrganizationalUnit)
    assert org.org_units[0].parent_id == org.root_id
    for ou in org.org_units:
        client.create_organizational_unit(ParentId=ou.id, Name=name +'-sub0')
    org.org_units = []
    org.load_org_units()
    assert len(org.org_units) == 6

 
@mock_sts
@mock_organizations
def test_load():
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    client = org.get_org_client()
    client.create_organization(FeatureSet='ALL')
    org_id = client.describe_organization()['Organization']['Id']
    root_id = client.list_roots()['Roots'][0]['Id']
    for name in ['account01', 'account02', 'account03']:
        client.create_account(AccountName=name, Email=name + '@example.com')
    for name in ['ou01', 'ou02', 'ou03']:
        ou = client.create_organizational_unit(
                ParentId=root_id, Name=name)['OrganizationalUnit']
        client.create_organizational_unit(ParentId=ou['Id'], Name=ou['Name'] +'-sub0')
    org.load()
    assert org.id == org_id
    assert org.root_id == root_id
    assert len(org.accounts) == 3
    assert len(org.org_units) == 6

