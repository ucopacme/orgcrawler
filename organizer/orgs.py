import os
import sys
import pickle
import json
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

from organizer import utils


class Org(object):
    """
    Data model and methods for querying AWS Organizations resources.

    The Org object is used to retrieve resource attributes for all AWS Accounts
    and Organizational Units in your AWS Organization.  It provides an API for
    listing accounts or account attributes based on ancestor organizational
    unit or other criteria.

    Once loaded, your Org object is cached locally to reduce load time during
    subsequent use.  Account credentails are not cached.  Cached Org objects
    time out after a configurable amount of time [Default: 60 minutes].

    Attributes:
        master_account_id (str): Account Id of the Organization master account.
        access_role (str): The IAM role to assume when loading Organization
            resource data.
        id (str): The Organization resource Id.
        root_id (str): The root Organizational Unit resource Id.
        accounts (list(:obj:`OrgAccount`)): List of account in the Organization.
        org_units (list(:obj:`OrganizationalUnit`)): List of organizational
            units in the Organization.

    Example:
        my_org = organizer.orgs.Org('123456789012', 'myOrgMasterRole')
        my_org.load()
        all_accounts = my_org.list_accounts_by_name()

    """

    def __init__(self, master_account_id, org_access_role, **kwargs):
        # TODO: make client and cache attrs private
        self.master_account_id = master_account_id
        self.access_role = org_access_role
        self.id = None
        self.root_id = None
        self.client = None
        self.cache_dir = os.path.expanduser(
            kwargs.get('cache_dir', '~/.aws/organizer-cache')
        )
        self.cache_file = os.path.join(
            self.cache_dir,
            kwargs.get('cache_file', '-'.join(['cache_file', master_account_id])),
        )
        self.cache_file_max_age = kwargs.get('cache_file_max_age', 60)
        self.accounts = []
        self.org_units = []

    def dump_accounts(self, account_list=None):
        if not account_list:
            account_list = self.accounts
        return [a.dump() for a in account_list]

    def dump_org_units(self):
        return [ou.dump() for ou in self.org_units]

    def dump(self):
        org_dump = dict()
        org_dump.update(vars(self).items())
        org_dump.update(dict(client=None))
        org_dump['accounts'] = self.dump_accounts()
        org_dump['org_units'] = self.dump_org_units()
        return org_dump

    def dump_json(self):
        """
        Return loaded Org object as formatted json string
        """
        return json.dumps(self.dump(), indent=4, separators=(',', ': '))

    def load(self):
        """
        Make boto3 client calls to populate the Org object's Account and
        OrganizationalUnit resource data
        """
        self._load_client()
        try:
            org_dump = self._get_cached_org_from_file()
            self._load_org_dump(org_dump)
        except RuntimeError as e:
            self._load_org()
            self.accounts = []
            self._load_accounts()
            self.org_units = []
            self._load_org_units()
            self._save_cached_org_to_file()

    def _load_client(self):
        self.client = self._get_org_client()

    def _get_org_client(self):
        """ Returns a boto3 client for Organizations object """
        try:
            credentials = utils.assume_role_in_account(
                self.master_account_id,
                self.access_role,
            )
        except ClientError as e:    # pragma: no cover
            errmsg = 'cannot assume role {} in account {}: {}'.format(
                self.access_role,
                self.master_account_id,
                e.response['Error']['Code'],
            )
            sys.exit(errmsg)
        return boto3.client('organizations', **credentials)

    def _get_cached_org_from_file(self):
        if not os.path.isfile(self.cache_file):
            raise RuntimeError('Cache file not found')
        cache_file_mod_time = datetime.fromtimestamp(os.stat(self.cache_file).st_mtime)
        now = datetime.today()
        max_delay = timedelta(minutes=self.cache_file_max_age)
        if now - cache_file_mod_time > max_delay:
            raise RuntimeError('Cache file too old')
        with open(self.cache_file, 'rb') as pf:
            return pickle.load(pf)

    def _load_org_dump(self, org_dump):
        self.id = org_dump['id']
        self.root_id = org_dump['root_id']
        self.accounts = [
            OrgAccount(self, **account) for account in org_dump['accounts']
        ]
        self.org_units = [
            OrganizationalUnit(self, **org_unit) for org_unit in org_dump['org_units']
        ]

    def _load_org(self):
        response = self.client.describe_organization()
        self.id = response['Organization']['Id']
        self.root_id = self.client.list_roots()['Roots'][0]['Id']

    def _load_accounts(self):
        response = self.client.list_accounts()
        accounts = response['Accounts']
        while 'NextToken' in response and response['NextToken']:    # pragma: no cover
            try:
                response = self.client.list_accounts(NextToken=response['NextToken'])
                accounts += response['Accounts']
            except ClientError as e:
                if e.response['Error']['Code'] == 'TooManyRequestsException':
                    continue
        # skip accounts with no 'Name' key as these are not fully created yet.
        accounts = [account for account in accounts if 'Name' in account]

        # use threading to query all accounts
        def make_org_account_object(account, org):
            # thread worker function: get parent_id and create OrgAccount object
            response = org.client.list_parents(ChildId=account['Id'])
            parent_id = response['Parents'][0]['Id']
            org_account = OrgAccount(
                org,
                name=account['Name'],
                id=account['Id'],
                email=account['Email'],
                parent_id=parent_id,
            )
            org.accounts.append(org_account)
        utils.queue_threads(
            accounts,
            make_org_account_object,
            func_args=(self,),
            thread_count=len(accounts)
        )

    def _load_org_units(self):
        self._recurse_organization(self.root_id)

    def _recurse_organization(self, parent_id):
        response = self.client.list_organizational_units_for_parent(ParentId=parent_id)
        org_units = response['OrganizationalUnits']
        while 'NextToken' in response and response['NextToken']:    # pragma: no cover
            response = self.client.list_organizational_units_for_parent(
                ParentId=parent_id,
                NextToken=response['NextToken']
            )
            org_units += response['OrganizationalUnits']
        for ou in org_units:
            self.org_units.append(
                OrganizationalUnit(
                    self,
                    name=ou['Name'],
                    id=ou['Id'],
                    parent_id=parent_id,
                )
            )
            self._recurse_organization(ou['Id'])

    def _save_cached_org_to_file(self):
        os.makedirs(self.cache_dir, 0o700, exist_ok=True)
        with open(self.cache_file, 'wb') as pf:
            pickle.dump(self.dump(), pf)

    # Query methods

    def list_accounts_by_name(self, account_list=None):
        if not account_list:
            account_list = self.accounts
        return [a.name for a in account_list]

    def list_accounts_by_id(self, account_list=None):
        if not account_list:
            account_list = self.accounts
        return [a.id for a in account_list]

    def get_account_id_by_name(self, name):
        return next((a.id for a in self.accounts if a.name == name), None)

    def get_account_name_by_id(self, account_id):
        return next((a.name for a in self.accounts if a.id == account_id), None)

    def get_account(self, identifier):
        if isinstance(identifier, OrgAccount):
            return identifier
        return next((
            a for a in self.accounts if (
                identifier == a.name or
                identifier == a.id or
                identifier in a.aliases
            )
        ), None)

    def list_org_units_by_name(self, ou_list=None):
        if not ou_list:
            ou_list = self.org_units
        return [ou.name for ou in ou_list]

    def list_org_units_by_id(self, ou_list=None):
        if not ou_list:
            ou_list = self.org_units
        return [ou.id for ou in ou_list]

    def get_org_unit_id(self, identifier):
        # ISSUE: should self.org_units contain the root ou?
        if identifier == 'root' or identifier == self.root_id:
            return self.root_id
        if isinstance(identifier, OrganizationalUnit):
            return identifier.id
        return next((
            ou.id for ou in self.org_units if (
                identifier == ou.name or
                identifier == ou.id
            )
        ), None)

    def list_accounts_in_ou(self, ou):
        ou_id = self.get_org_unit_id(ou)
        return [a for a in self.accounts if a.parent_id == ou_id]

    def list_org_units_in_ou(self, ou):
        ou_id = self.get_org_unit_id(ou)
        return [ou for ou in self.org_units if ou.parent_id == ou_id]

    def list_org_units_in_ou_recursive(self, ou):
        ou_list = self.list_org_units_in_ou(ou)
        for ou in ou_list:
            ou_list += self.list_org_units_in_ou_recursive(ou)
        return ou_list

    def list_accounts_in_ou_recursive(self, ou):
        account_list = self.list_accounts_in_ou(ou)
        for ou in self.list_org_units_in_ou_recursive(ou):
            account_list += self.list_accounts_in_ou(ou)
        return account_list


class OrgObject(object):

    def __init__(self, organization, **kwargs):
        self.organization_id = organization.id
        self.master_account_id = organization.master_account_id
        self.name = kwargs['name']
        self.id = kwargs.get('id')
        self.parent_id = kwargs.get('parent_id')

    def dump(self):
        org_object_dump = dict()
        org_object_dump.update(vars(self).items())
        return org_object_dump


class OrganizationalUnit(OrgObject):

    def __init__(self, *args, **kwargs):
        super(OrganizationalUnit, self).__init__(*args, **kwargs)


class OrgAccount(OrgObject):

    def __init__(self, *args, **kwargs):
        super(OrgAccount, self).__init__(*args, **kwargs)
        self.email = kwargs['email']
        self.aliases = kwargs.get('aliases', [])
        self.credentials = {}

    def load_credentials(self, access_role):
        self.credentials = utils.assume_role_in_account(self.id, access_role)

    def dump(self):
        account_dump = super(OrgAccount, self).dump()
        account_dump.update(dict(credentials={}))
        return account_dump
