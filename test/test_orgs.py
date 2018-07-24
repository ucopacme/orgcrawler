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
def test_load():
    account_id = MASTER_ACCOUNT_ID
    role_name = ORG_ACCESS_ROLE
    org = orgs.Org(account_id, role_name)
    client = org.get_org_client()
    client.create_organization(FeatureSet='ALL')
    org.load()
    assert org.id is not None
    assert org.root_id is not None
 
@mock_sts
@mock_organizations
def test_org_objects():
    account_id = MASTER_ACCOUNT_ID
    role_name = ORG_ACCESS_ROLE
    org = orgs.Org(account_id, role_name)
    client = org.get_org_client()
    client.create_organization(FeatureSet='ALL')
    org.load()
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
    account_id = MASTER_ACCOUNT_ID
    role_name = ORG_ACCESS_ROLE
    org = orgs.Org(account_id, role_name)
    client = org.get_org_client()
    client.create_organization(FeatureSet='ALL')
    org.load()
    for name in ['account01', 'account02', 'account03']:
        client.create_account(AccountName=name, Email=name + '@example.com')
    org.load_accounts()
    assert len(org.accounts) == 3
    assert isinstance(org.accounts[0], orgs.OrgAccount)
    assert org.accounts[0].parent_id == org.root_id
