import boto3
import json
import yaml

from organizer.utils import assume_role_in_account


class Org(object):

    def __init__(self, master_account_id, org_access_role):
        self.master_account_id = master_account_id
        self.access_role = org_access_role
        self.id = None
        self.root_id = None
        self.accounts = []
        self.org_units = []
        self.sc_policies = []

    def get_org_client(self):
        credentials = assume_role_in_account(self.master_account_id, self.access_role)
        client = boto3.client('organizations', **credentials)
        return client

    def load(self):
        client = self.get_org_client()
        response = client.describe_organization()
        self.id = response['Organization']['Id']
        self.root_id = client.list_roots()['Roots'][0]['Id']

    def load_accounts(self):
        client = self.get_org_client()
        response = client.list_accounts()
        for account in response['Accounts']:
            parent_id = client.list_parents(ChildId=account['Id'])['Parents'][0]['Id']
            org_account = OrgAccount(self, account['Name'], account['Id'], parent_id)
            self.accounts.append(org_account)



class OrgObject(object):

    def __init__(self, organization, name, object_id=None, parent_id=None):
        self.organization_id = organization.id
        self.master_account_id = organization.master_account_id
        self.name = name
        self.id = object_id
        self.parent_id = parent_id


class OrgAccount(OrgObject):

    def __init__(self, *args):
        super(OrgAccount, self).__init__(*args)


class OrganizationalUnit(OrgObject):

    def __init__(self, *args):
        super(OrganizationalUnit, self).__init__(*args)

