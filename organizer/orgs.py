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

    def load(self):
        self.load_org()
        self.load_accounts()
        self.load_org_units()

    def get_org_client(self):
        credentials = assume_role_in_account(self.master_account_id, self.access_role)
        client = boto3.client('organizations', **credentials)
        return client

    def load_org(self):
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

    def load_org_units(self):
        client = self.get_org_client()
        self.recurse_organization(client, self.root_id)

    def recurse_organization(self, client, parent_id):
        response = client.list_organizational_units_for_parent(ParentId=parent_id)
        if 'OrganizationalUnits' in response:
            for ou in response['OrganizationalUnits']:
                self.org_units.append(
                    OrganizationalUnit(self, ou['Name'], ou['Id'], parent_id)
                )
                self.recurse_organization(client, ou['Id'])

    def list_accounts(self):
        return [dict(Name=a.name, Id=a.id) for a in self.accounts]

    def list_accounts_by_name(self):
        return [a.name for a in self.accounts]

    def list_accounts_by_id(self):
        return [a.id for a in self.accounts]

    def list_organizational_units(self):
        return [dict(Name=ou.name, Id=ou.id) for ou in self.org_units]

    def list_organizational_units_by_name(self):
        return [ou.name for ou in self.org_units]

    def list_organizational_units_by_id(self):
        return [ou.id for ou in self.org_units]

    def get_account_id_by_name(self, name):
        return next((a.id for a in self.accounts if a.name == name), None)

    def get_org_unit_id_by_name(self, name):
        return next((ou.id for ou in self.org_units if ou.name == name), None) 

    ### no tests yet
    def list_accounts_in_ou(self, ou_id):
        return [dict(Name=a.name, Id=a.id) for a in accounts if a.parent_id == ou_id]

    ### no tests yet
    def list_account_names_in_ou(self, ou_id):
        return [a.name for a in accounts if a.parent_id == ou_id]

    ### no tests yet
    def list_account_id_in_ou(self, ou_id):
        return [a.id for a in accounts if a.parent_id == ou_id]

    ### no tests yet
    def recurse_org_under_ou(self, parent_id):
        child_ou = []
        for ou in self.org_units:
            if ou.parent_id == parent_id:
                child_ou = recurse_org_under_ou(self, ou.id)
                child_ou += [ou for ou in org.org_units if ou.parent_id == parent_id]
        return child_ou

    ### under construction
    def list_accounts_under_ou(self, ou_id):
        pass

    ### under construction
    def list_account_names_under_ou(self, ou_id):
        pass

    ### under construction
    def list_account_id_under_ou(self, ou_id):
        pass


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

