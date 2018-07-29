import boto3
from botocore.exceptions import ClientError

from organizer import orgs, utils


DEFAULT_REGION = 'us-east-1'


class Crawler(object):

    def __init__(self, org, **kwargs):
        self.org = org
        self.access_role = kwargs.get('access_role', org.access_role)
        self.accounts = kwargs.get('accounts', org.accounts)
        self.regions = kwargs.get('regions', [DEFAULT_REGION])
        self.responses = []
        self.stats = {}

    def load_account_credentials(self):
        def get_credentials_for_account(account, crawler):
            account.load_credentials(crawler.access_role)
        utils.queue_threads(
            self.accounts,
            get_credentials_for_account,
            func_args=(self,),
            thread_count=len(self.accounts)
        )

    def execute(self, payload, *args, **kwargs):
        thread_count = kwargs('thread_count', len(self.accounts))
        for region in self.regions:
            for account in self.accounts:
                response = account.run_payload(region, payload, *args)
                self.responses.append(response)

