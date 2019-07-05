import os
import sys
import shutil
import inspect
import pickle
import json
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

from orgcrawler import utils
from orgcrawler.logger import Logger


class Org(object):
    """
    Data model and methods for querying AWS Organizations resources.

    The Org object is used to retrieve resource attributes for all AWS Accounts
    and Organizational Units in your AWS Organization.  It provides an API for
    listing accounts or account attributes based on ancestor organizational
    unit or other criteria.

    Once loaded, your Org object is cached locally to reduce load time during
    subsequent use.  Account credentails are not cached.  Cached Org objects
    time out after a configurable amount of time.


    Args:
        master_account_id (str): Account Id of the Organization master account.
        access_role (str): The IAM role to assume when loading Organization
            resource data.
        log_level (str): Sets the logging level [Default: 'error'].
        cache_file_max_age (int): Cache file time out in minutes [Default: 60].
        cache_dir (str): Directory where to save cache files
            [Default: ``~/.aws/orgcrawler-cache``].
        cache_file (str): Cache file name
            [Default: ``cache_file-${master_account_id}``].

    Object Attributes and Methods:

    Attributes:
        master_account_id (str): Account Id of the Organization master account.
        access_role (str): The IAM role to assume when loading Organization
            resource data.
        id (str): The Organization resource Id.
        root_id (str): The root Organizational Unit resource Id.
        accounts (list(:obj:`OrgAccount`)): List of account in the Organization.
        org_units (list(:obj:`OrganizationalUnit`)): List of organizational
            units in the Organization.
        policies list(:obj:`OrgPolicy`)): List of Service Control Policies in
            the Organization.

    """

    def __init__(self,
            master_account_id,
            org_access_role,
            log_level=utils.DEFAULT_LOGLEVEL,
            cache_file_max_age=60,
            cache_dir='~/.aws/orgcrawler-cache',
            cache_file=None):
        self.master_account_id = master_account_id
        self.access_role = org_access_role
        self.logger = Logger(loglevel=log_level)
        self.id = None
        self.root_id = None
        self.accounts = []
        self.org_units = []
        self.policies = []
        self._client = None
        self._cache_file_max_age = cache_file_max_age
        self._cache_dir = os.path.expanduser(cache_dir)
        if cache_file is None:
            cache_file = '-'.join(['cache_file', master_account_id])
        self._cache_file = os.path.join(self._cache_dir, cache_file)
        self._exc_info = None

    def dump_accounts(self, account_list=None):
        """
        Dump loaded OrgAccount objects as list(dict)
        """
        if not account_list:
            account_list = self.accounts
        return [a.dump() for a in account_list]

    def dump_org_units(self):
        """
        Dump loaded OrganizationalUnit objects as list(dict)
        """
        return [ou.dump() for ou in self.org_units]

    def dump_policies(self):
        """
        Dump loaded OrgPolicy objects as list(dict)
        """
        return [policy.dump() for policy in self.policies]

    def dump(self):
        """
        Dump loaded Org object as dictionary
        """
        org_dump = dict()
        org_dump.update(vars(self).items())
        org_dump.pop('logger')
        org_dump.pop('_client')
        org_dump.pop('_cache_dir')
        org_dump.pop('_cache_file')
        org_dump.pop('_cache_file_max_age')
        org_dump['accounts'] = self.dump_accounts()
        org_dump['org_units'] = self.dump_org_units()
        org_dump['policies'] = self.dump_policies()
        return org_dump

    def dump_json(self):
        """
        Dump loaded Org object as formatted json string
        """
        return json.dumps(self.dump(), indent=4, separators=(',', ': '))

    def load(self):
        """
        Make boto3 client calls to populate the Org object's Account and
        OrganizationalUnit resource data
        """
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
        }
        self.logger.info(message)
        self._load_client()
        try:
            org_dump = self._get_cached_org_from_file()
            self._load_org_dump(org_dump)
        except RuntimeError:
            self._load_org()
            self.accounts = []
            self._load_accounts()
            self.org_units = []
            self._load_org_units()
            self.policies = []
            self._load_policies()
            self._save_cached_org_to_file()

    def clear_cache(self):
        '''
        Delete any pre-existing org cache files
        '''
        if os.path.isdir(self._cache_dir):
            shutil.rmtree(self._cache_dir)

    def _load_client(self):
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
        }
        self.logger.info(message)
        self._client = self._get_org_client()

    def _get_org_client(self):
        """ Returns a boto3 client for Organizations object """
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
        }
        self.logger.info(message)
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
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
        }
        self.logger.info(message)
        if not os.path.isfile(self._cache_file):
            raise RuntimeError('Cache file not found')
        cache_file_mod_time = datetime.fromtimestamp(os.stat(self._cache_file).st_mtime)
        now = datetime.today()
        max_delay = timedelta(minutes=self._cache_file_max_age)
        if now - cache_file_mod_time > max_delay:
            raise RuntimeError('Cache file too old')
        with open(self._cache_file, 'rb') as pf:
            return pickle.load(pf)

    def _load_org_dump(self, org_dump):
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
        }
        self.logger.info(message)
        self.id = org_dump['id']
        self.root_id = org_dump['root_id']
        self.accounts = [
            OrgAccount(self, **account) for account in org_dump['accounts']
        ]
        self.org_units = [
            OrganizationalUnit(self, **org_unit) for org_unit in org_dump['org_units']
        ]
        self.policies = [
            OrgPolicy(self, **policy) for policy in org_dump['policies']
        ]

    def _load_org(self):
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
        }
        self.logger.info(message)
        response = self._client.describe_organization()
        self.id = response['Organization']['Id']
        self.root_id = self._client.list_roots()['Roots'][0]['Id']

    def _load_accounts(self):
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
        }
        self.logger.info(message)
        response = self._client.list_accounts()
        accounts = response['Accounts']
        while 'NextToken' in response and response['NextToken']:    # pragma: no cover
            try:
                response = self._client.list_accounts(NextToken=response['NextToken'])
                accounts += response['Accounts']
            except ClientError as e:
                if e.response['Error']['Code'] == 'TooManyRequestsException':
                    continue
        # skip accounts with no 'Name' key as these are not fully created yet.
        accounts = [account for account in accounts if 'Name' in account]

        def make_org_account_object(account, org):
            try:
                response = org._client.list_parents(ChildId=account['Id'])
                parent_id = response['Parents'][0]['Id']
                org_account = OrgAccount(
                    org,
                    name=account['Name'],
                    id=account['Id'],
                    email=account['Email'],
                    parent_id=parent_id,
                )
                org_account.load_attached_policy_ids(org._client)
                org.accounts.append(org_account)

            except Exception:   # pragma: no cover
                org._exc_info = sys.exc_info()

        utils.queue_threads(
            accounts,
            make_org_account_object,
            func_args=(self,),
            thread_count=len(accounts),
            logger=self.logger,
        )
        if self._exc_info:   # pragma: no cover
            raise self._exc_info[1].with_traceback(self._exc_info[2])

    def _load_org_units(self):
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
        }
        self.logger.info(message)
        self._recurse_organization(self.root_id)

    def _recurse_organization(self, parent_id):
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
        }
        self.logger.info(message)
        response = self._client.list_organizational_units_for_parent(ParentId=parent_id)
        org_units = response['OrganizationalUnits']
        while 'NextToken' in response and response['NextToken']:    # pragma: no cover
            response = self._client.list_organizational_units_for_parent(
                ParentId=parent_id,
                NextToken=response['NextToken']
            )
            org_units += response['OrganizationalUnits']
        for ou in org_units:
            org_unit = OrganizationalUnit(
                self,
                name=ou['Name'],
                id=ou['Id'],
                parent_id=parent_id,
            )
            org_unit.load_attached_policy_ids(self._client)
            self.org_units.append(org_unit)
            self._recurse_organization(ou['Id'])

    def _load_policies(self):
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
        }
        self.logger.info(message)
        response = self._client.list_policies(Filter='SERVICE_CONTROL_POLICY')
        policies = response['Policies']
        while 'NextToken' in response and response['NextToken']:    # pragma: no cover
            response = self._client.list_policies(
                Filter='SERVICE_CONTROL_POLICY',
                NextToken=response['NextToken'],
            )
            policies += response['Policies']

        def make_org_policy_object(policy, org):
            message = {
                'FILE': __file__.split('/')[-1],
                'CLASS': self.__class__.__name__,
                'METHOD': inspect.stack()[0][3],
                'policy': policy,
            }
            self.logger.info(message)
            try:
                org_policy = OrgPolicy(
                    org,
                    name=policy['Name'],
                    id=policy['Id'],
                )
                org_policy.load_targets(org._client)
                org.policies.append(org_policy)
            except Exception:   # pragma: no cover
                org._exc_info = sys.exc_info()

        utils.queue_threads(
            policies,
            make_org_policy_object,
            func_args=(self,),
            thread_count=len(policies),
            logger=self.logger,
        )
        if self._exc_info:   # pragma: no cover
            raise self._exc_info[1].with_traceback(self._exc_info[2])

    def _save_cached_org_to_file(self):
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
        }
        self.logger.info(message)
        os.makedirs(self._cache_dir, 0o700, exist_ok=True)
        with open(self._cache_file, 'wb') as pf:
            pickle.dump(self.dump(), pf)

    # Query methods

    def list_accounts_by_name(self, account_list=None):
        """
        Args:
            account_list (list(OrgAccount)): Default: all accounts in Org
        Returns:
            list(str): account names for ``account_list``
        """
        if not account_list:
            account_list = self.accounts
        return [a.name for a in account_list]

    def list_accounts_by_id(self, account_list=None):
        """
        Args:
            account_list (list(OrgAccount)): Default: all accounts in Org
        Returns:
            list(str): account IDs for ``account_list``
        """
        if not account_list:
            account_list = self.accounts
        return [a.id for a in account_list]

    def get_account_id_by_name(self, name):
        """
        Args:
            name (str): account name
        Returns:
            str: account Id matching ``name``
        """
        return next((a.id for a in self.accounts if a.name == name), None)

    def get_account_name_by_id(self, account_id):
        """
        Args:
            id (str): account Id
        Returns:
            str: account name matching ``id``
        """
        return next((a.name for a in self.accounts if a.id == account_id), None)

    def get_account(self, identifier):
        """
        Args:
            identifier (str): account name, id or alias
        Returns:
            OrgAccount: account object containing ``identifier``.
        """
        if isinstance(identifier, OrgAccount):
            return identifier
        return next((
            a for a in self.accounts
            if (identifier == a.name or identifier == a.id or identifier in a.aliases)
        ), None)

    def list_org_units_by_name(self, ou_list=None):
        """
        Args:
            ou_list (list(OrgAccount)): Default: all org_units in Org
        Returns:
            list(str): org_unit names for ``ou_list``
        """
        if not ou_list:
            ou_list = self.org_units
        return [ou.name for ou in ou_list]

    def list_org_units_by_id(self, ou_list=None):
        """
        Args:
            ou_list (list(OrgAccount)): Default: all org_units in Org
        Returns:
            list(str): org_unit IDs for ``ou_list``
        """
        if not ou_list:
            ou_list = self.org_units
        return [ou.id for ou in ou_list]

    def get_org_unit(self, identifier):
        """
        Args:
            identifier (str, OrganizationalUnit): org_unit name, id or object
        Returns:
            OrganizationaUnit: matching org_unit object
        """
        if isinstance(identifier, OrganizationalUnit):
            return identifier
        return next((
            org_unit for org_unit in self.org_units
            if (identifier == org_unit.name or identifier == org_unit.id)
        ), None)

    def get_org_unit_id(self, identifier):
        """
        Args:
            identifier (str, OrganizationalUnit): org_unit name, id or object
        Returns:
            str: matching org_unit Id
        """
        # ISSUE: should self.org_units contain the root ou?
        if identifier == 'root' or identifier == self.root_id:
            return self.root_id
        org_unit = self.get_org_unit(identifier)
        if org_unit is not None:
            return org_unit.id
        return None

    def list_org_units_in_ou(self, ou):
        """
        Args:
            ou (str, OrganizationalUnit): org_unit name, id or object
        Returns:
            list(OrganizationalUnit): org_units for which ``ou`` is a direct parent
        """
        ou_id = self.get_org_unit_id(ou)
        return [ou for ou in self.org_units if ou.parent_id == ou_id]

    def list_accounts_in_ou(self, ou):
        """
        Args:
            ou (str, OrganizationalUnit): org_unit name, id or object
        Returns:
            list(OrgAccount): accounts for which ``ou`` is a direct parent
        """
        ou_id = self.get_org_unit_id(ou)
        return [a for a in self.accounts if a.parent_id == ou_id]

    def list_org_units_in_ou_recursive(self, ou):
        """
        Args:
            ou (str, OrganizationalUnit): org_unit name, id or object
        Returns:
            list(OrganizationalUnit): org_units for which ``ou`` is an ancestor
        """
        ou_list = self.list_org_units_in_ou(ou)
        for ou in ou_list:
            ou_list += self.list_org_units_in_ou_recursive(ou)
        return ou_list

    def list_accounts_in_ou_recursive(self, ou):
        """
        Args:
            ou (str, OrganizationalUnit): org_unit name, id or object
        Returns:
            list(OrgAccount): accounts for which ``ou`` is an ancestor
        """
        account_list = self.list_accounts_in_ou(ou)
        for ou in self.list_org_units_in_ou_recursive(ou):
            account_list += self.list_accounts_in_ou(ou)
        return account_list

    def list_policies_by_name(self, policy_list=None):
        """
        Args:
            policy_list (list(OrgPolicy)): Default: all policies in Org
        Returns:
            list(str): policy names for ``policy_list``
        """
        if not policy_list:
            policy_list = self.policies
        return [p.name for p in policy_list]

    def list_policies_by_id(self, policy_list=None):
        """
        Args:
            policy_list (list(OrgPolicy)): Default: all policies in Org
        Returns:
            list(str): policy Ids for ``policy_list``
        """
        if not policy_list:
            policy_list = self.policies
        return [p.id for p in policy_list]

    def get_policy(self, identifier):
        """
        Args:
            identifier (str): policy name or id
        Returns:
            OrgPolicy: policy object containing ``identifier``.
        """
        if isinstance(identifier, OrgPolicy):
            return identifier
        return next((
            p for p in self.policies
            if (identifier == p.name or identifier == p.id)
        ), None)

    def get_policy_id(self, identifier):
        """
        Args:
            identifier (str, OrgPolicy): policy name, id or object
        Returns:
            str: matching policy Id for ``identifier``
        """
        policy = self.get_policy(identifier)
        if policy is not None:
            return policy.id
        return None

    def get_policy_id_by_name(self, name):
        """
        Args:
            name (str): policy name
        Returns:
            str: policy Id matching ``name``
        """
        return next((p.id for p in self.policies if p.name == name), None)

    def get_policy_name_by_id(self, policy_id):
        """
        Args:
            id (str): policy Id
        Returns:
            str: policy name matching ``id``
        """
        return next((p.name for p in self.policies if p.id == policy_id), None)

    '''
    def get_policy_document(self, identifier):
        """
        Args:
            identifier (str): policy name or id
        Returns:
            str: the policy statement (json) for this policy
        """
        policy_id = self.get_policy_id(identifier)
        #if policy_id is not None:
        #    #return self._client.describe_policy(PolicyId=policy_id)['Policy']['Content']
        #    return self._client.describe_policy(PolicyId=policy_id)
        #return None
    '''

    def get_targets_for_policy(self, identifier):
        """
        Args:
            identifier (str, OrgPolicy): policy name, id or object
        Returns:
            list, None: list of OrgAccount and OrganzationalUnit objects
                        which are targets of this policy
        """
        policy = self.get_policy(identifier)
        if policy is not None:
            return self.get_policy(identifier).targets
        return None

    def get_policies_for_target(self, identifier):
        """
        Args:
            identifier (str, OrgObject): account or org_unit name, id or object
        Returns:
            list, None: list of OrgPolicy objects attached to this account
                        or org_unit
        """
        org_object = self.get_account(identifier)
        if org_object is None:
            org_object = self.get_org_unit(identifier)
        if org_object is not None:
            policies = [
                obj for obj in self.policies if obj.id in org_object.attached_policy_ids
            ]
            if policies:
                return policies
        return None

    def get_accounts_for_policy_recursive(self, identifier):
        """
        Args:
            identifier (str, OrgPolicy): policy name, id or object
        Returns:
            list, None: list of OrgAccount objects subject to the identified policy.
        """
        affected_accounts = []
        policy = self.get_policy(identifier)
        if policy is None:
            return None
        for target in policy.targets:
            if target['Type'] == 'ACCOUNT':
                affected_accounts.append(self.get_account(target['TargetId']))
            elif target['Type'] in ['ROOT', 'ORGANIZATIONAL_UNIT']:
                affected_accounts += self.list_accounts_in_ou_recursive(target['TargetId'])
        return list(set(affected_accounts))


class OrgObject(object):
    """
    Base class for Organization resource objects.
    """

    def __init__(self, organization, **kwargs):
        self.organization_id = organization.id
        self.master_account_id = organization.master_account_id
        self.logger = organization.logger
        self.name = kwargs['name']
        self.id = kwargs.get('id')
        self.parent_id = kwargs.get('parent_id')
        self.attached_policy_ids = kwargs.get('attached_policy_ids')

    def dump(self):
        """
        Return object as dict
        """
        org_object_dump = dict()
        org_object_dump.update(vars(self).items())
        org_object_dump.pop('logger')
        return org_object_dump

    def load_attached_policy_ids(self, client):
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
        }
        self.logger.info(message)
        response = client.list_policies_for_target(
            TargetId=self.id,
            Filter='SERVICE_CONTROL_POLICY',
        )
        policies = response['Policies']
        while 'NextToken' in response and response['NextToken']:  # pragma: no cover
            client.list_policies_for_target(
                TargetId=self.id,
                Filter='SERVICE_CONTROL_POLICY',
                NextToken=response['NextToken'],
            )
            policies += response['Policies']
        self.attached_policy_ids = [p['Id'] for p in policies]


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


class OrgPolicy(OrgObject):

    def __init__(self, *args, **kwargs):
        super(OrgPolicy, self).__init__(*args, **kwargs)
        self.targets = kwargs.get('targets', [])

    def load_targets(self, client):
        message = {
            'FILE': __file__.split('/')[-1],
            'CLASS': self.__class__.__name__,
            'METHOD': inspect.stack()[0][3],
            'policy': self.name,
        }
        self.logger.info(message)
        response = client.list_targets_for_policy(PolicyId=self.id)
        targets = response['Targets']
        while 'NextToken' in response and response['NextToken']:  # pragma: no cover
            response = client.list_targets_for_policy(
                PolicyId=self.id,
                NextToken=response['NextToken'],
            )
            targets += response['Targets']
        self.targets = targets
