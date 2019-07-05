import sys
import time

from botocore.exceptions import ClientError

from orgcrawler import utils


DEFAULT_REGION = 'us-east-1'


class Crawler(object):

    all_regions = utils.all_regions()

    def __init__(self, org, **kwargs):
        """
        kwargs:
        :access_role: string
        :accounts: string, list of string, or list of OrgAccount
        :regions: string, or list of string
        """
        self.org = org
        self.access_role = kwargs.get('access_role') or org.access_role
        self.accounts = kwargs.get('accounts') or org.accounts
        self.validate_accounts()
        self.regions = kwargs.get('regions') or self.all_regions
        self.validate_regions()
        self.executions = []
        self.exc_info = None
        self.error = None

    def is_valid_account(self, account):
        if self.org.get_account(account) is None:
            raise ValueError('"{}" is not a valid organization account'.format(account))
        return True

    def validate_accounts(self):
        if self.accounts != self.org.accounts:
            if not isinstance(self.accounts, list):
                self.accounts = [self.accounts]
            self.accounts = [
                self.org.get_account(a) for a in self.accounts
                if self.is_valid_account(a)
            ]

    def validate_regions(self):
        if self.regions == 'GLOBAL':
            self.regions = [DEFAULT_REGION]
        else:
            if isinstance(self.regions, str):
                self.regions = [self.regions]
            elif not isinstance(self.regions, list):
                raise ValueError('keyword argument "regions" must be list or str')
            no_such_regions = [r for r in self.regions if r not in self.all_regions]
            if no_such_regions:
                raise ValueError('Invalid regions: {}'.format(', '.join(no_such_regions)))

    def get_regions(self):
        return self.regions

    def update_regions(self, regions):
        self.regions = regions
        self.validate_regions()

    def get_accounts(self):
        return self.accounts

    def update_accounts(self, accounts):
        '''
        Args:
            accounts (str, list(str), list(OrgAccount), None)

        Resets Cralwer.accounts list in place.  If `accounts` is None, sets
        Cralwer.accounts to an empty list.  If `accounts` is keyword "ALL", sets
        Cralwer.accounts to all accounts in the Organization.
        '''
        if accounts == 'ALL':
            self.accounts = self.org.accounts
        elif accounts is None:
            self.accounts = []
        else:
            self.accounts = accounts
            self.validate_accounts()

    def load_account_credentials(self):
        def get_credentials_for_account(account, crawler):
            try:
                account.load_credentials(crawler.access_role)
            except ClientError as e:    # pragma: no cover
                crawler.error = 'cannot assume role {} in account {}: {}'.format(
                    crawler.access_role,
                    account.name,
                    e.response['Error']['Code']
                )
            except Exception:   # pragma: no cover
                crawler.exc_info = sys.exc_info()
        utils.queue_threads(
            self.accounts,
            get_credentials_for_account,
            func_args=(self,),
            thread_count=len(self.accounts)
        )
        if self.error:  # pragma: no cover
            sys.exit(self.error)
        if self.exc_info:   # pragma: no cover
            raise self.exc_info[1].with_traceback(self.exc_info[2])

    def execute(self, payload, *args, **kwargs):

        def run_payload_in_account(account_region_map, execution, args, kwargs):
            region = account_region_map['region']
            account = account_region_map['account']
            response = CrawlerResponse(region, account)
            response.timer.start()
            try:
                response.payload_output = execution.payload(region, account, *args, **kwargs)
            except Exception:
                response.exc_info = sys.exc_info()
                execution.errors = True
            response.timer.stop()
            execution.responses.append(response)

        accounts_and_regions = []
        for region in self.regions:
            for account in self.accounts:
                accounts_and_regions.append(dict(account=account, region=region))
        thread_count = kwargs.get('thread_count', len(self.accounts))
        execution = CrawlerExecution(payload)
        execution.timer.start()
        utils.queue_threads(
            accounts_and_regions,
            run_payload_in_account,
            func_args=(execution, args, kwargs),
            thread_count=thread_count,
        )
        execution.timer.stop()
        if execution.errors:
            execution.handle_errors()
        self.executions.append(execution)
        return execution

    def get_execution(self, name):
        return next((r for r in self.executions if r.name == name), None)


class CrawlerTimer(object):

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        if self.start_time:
            self.end_time = time.perf_counter()
            self.elapsed_time = self.end_time - self.start_time

    def dump(self):
        return dict(
            start_time=self.start_time,
            end_time=self.end_time,
            elapsed_time=self.elapsed_time,
        )


class CrawlerExecution(object):

    def __init__(self, payload):
        self.payload = payload
        self.name = payload.__name__
        self.responses = []
        self.errors = None
        self.timer = CrawlerTimer()

    def dump(self):
        return dict(
            payload=self.payload.__repr__(),
            name=self.name,
            responses=[r.dump() for r in self.responses],
            statistics=self.timer.dump()
        )

    def handle_errors(self):
        errors = [response for response in self.responses if response.exc_info]
        exc_info = errors.pop().exc_info
        errmsg = (
            'OrgCrawler.execute encountered {} errors while running "{}". '
            'Example:\n'.format(
                len(errors),
                self.name,
            )
        )
        print(errmsg, file=sys.stderr)
        sys.excepthook(*exc_info)
        sys.exit()


class CrawlerResponse(object):

    def __init__(self, region, account):
        self.region = region
        self.account = account
        self.payload_output = None
        self.timer = CrawlerTimer()
        self.exc_info = None

    def dump(self):
        return dict(
            region=self.region,
            account=self.account.dump(),
            payload_output=self.payload_output,
            statistics=self.timer.dump()
        )
