import boto3

from organizer.utils import assume_role_in_account, queue_threads


class Org(object):

    def __init__(self, master_account_id, org_access_role):
        self.master_account_id = master_account_id
        self.access_role = org_access_role
        self.id = None
        self.root_id = None
        self.accounts = []
        self.org_units = []

    def load(self):
        """
        Make boto3 client calls to populate the Org object's Account and
        OrganizationalUnit resource data
        """
        self._load_client()
        self._load_org()
        self.accounts = []
        self._load_accounts()
        self.org_units = []
        self._load_org_units()

    def _load_client(self):
        self.client = self.get_org_client()

    def _load_org(self):
        response = self.client.describe_organization()
        self.id = response['Organization']['Id']
        self.root_id = self.client.list_roots()['Roots'][0]['Id']

    def _load_accounts(self):
        response = self.client.list_accounts()
        accounts = response['Accounts']
        while 'NextToken' in response and response['NextToken']:
            response = self.client.list_accounts(NextToken=response['NextToken'])
            accounts += response['Accounts']
        # only return accounts that have an 'Name' key
        accounts = [account for account in accounts if 'Name' in account]

        #def _make_org_account_object(account, org):
        #    response = org.client.list_parents(ChildId=account['Id'])
        #    parent_id = response['Parents'][0]['Id']
        #    org_account = OrgAccount(org, account['Name'], account['Id'], parent_id)
        #    org.accounts.append(org_account)
        #queue_threads(accounts, _make_org_account_object, func_args=(self,))

        for account in accounts:
            response = self.client.list_parents(ChildId=account['Id'])
            parent_id = response['Parents'][0]['Id']
            org_account = OrgAccount(self, account['Name'], account['Id'], parent_id)
            self.accounts.append(org_account)

    def _make_org_account_object(self, args):
        response = self.client.list_parents(ChildId=account['Id'])
        parent_id = response['Parents'][0]['Id']
        org_account = OrgAccount(self, account['Name'], account['Id'], parent_id)
        self.accounts.append(org_account)

    def _load_org_units(self):
        self._recurse_organization(self.root_id)

    def _recurse_organization(self, parent_id):
        response = self.client.list_organizational_units_for_parent(ParentId=parent_id)
        org_units = response['OrganizationalUnits']
        while 'NextToken' in response and response['NextToken']:
            response = self.client.list_organizational_units_for_parent(
                ParentId=parent_id,
                NextToken=response['NextToken']
            )
            org_units += response['OrganizationalUnits']
        for ou in org_units:
            self.org_units.append(
                OrganizationalUnit(self, ou['Name'], ou['Id'], parent_id)
            )
            self._recurse_organization(ou['Id'])

    def get_org_client(self):
        """ Returns a boto3 client for Organizations object """
        credentials = assume_role_in_account(self.master_account_id, self.access_role)
        return boto3.client('organizations', **credentials)

    def list_accounts(self):
        return [dict(Name=a.name, Id=a.id) for a in self.accounts]

    def list_accounts_by_name(self):
        return [a.name for a in self.accounts]

    def list_accounts_by_id(self):
        return [a.id for a in self.accounts]

    def list_org_units(self):
        return [dict(Name=ou.name, Id=ou.id) for ou in self.org_units]

    def list_org_units_by_name(self):
        return [ou.name for ou in self.org_units]

    def list_org_units_by_id(self):
        return [ou.id for ou in self.org_units]

    def get_account_id_by_name(self, name):
        return next((a.id for a in self.accounts if a.name == name), None)

    def get_org_unit_id_by_name(self, name):
        return next((ou.id for ou in self.org_units if ou.name == name), None)

    def list_accounts_in_ou(self, ou_id):
        return [dict(Name=a.name, Id=a.id) for a in self.accounts if a.parent_id == ou_id]

    def list_accounts_in_ou_by_name(self, ou_id):
        return [a.name for a in self.accounts if a.parent_id == ou_id]

    def list_accounts_in_ou_by_id(self, ou_id):
        return [a.id for a in self.accounts if a.parent_id == ou_id]

    def _recurse_org_units_under_ou(self, parent_id):
        ou_id_list = [
            ou.id for ou in self.org_units
            if ou.parent_id == parent_id
        ]
        for ou_id in ou_id_list:
            ou_id_list += self._recurse_org_units_under_ou(ou_id)
        return ou_id_list

    def list_accounts_under_ou(self, ou_id):
        account_list = self.list_accounts_in_ou(ou_id)
        for ou_id in self._recurse_org_units_under_ou(ou_id):
            account_list += self.list_accounts_in_ou(ou_id)
        return account_list

    def list_accounts_under_ou_by_name(self, ou_id):
        response = self.list_accounts_under_ou(ou_id)
        return [a['Name'] for a in response]

    def list_accounts_under_ou_by_id(self, ou_id):
        response = self.list_accounts_under_ou(ou_id)
        return [a['Id'] for a in response]


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
