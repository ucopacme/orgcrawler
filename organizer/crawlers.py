import time

import boto3
#from botocore.exceptions import ClientError

from organizer import orgs, utils


DEFAULT_REGION = 'us-east-1'


class Crawler(object):

    def __init__(self, org, **kwargs):
        self.org = org
        self.access_role = kwargs.get('access_role', org.access_role)
        self.accounts = kwargs.get('accounts', org.accounts)
        self.regions = kwargs.get('regions', [DEFAULT_REGION])
        self.requests = []

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
        thread_count = kwargs.get('thread_count', len(self.accounts))
        request = CrawlerRequest(payload)
        request.starttime = time.perf_counter()
        for region in self.regions:
            for account in self.accounts:
                response = CrawlerResponse(region, account)
                response.starttime = time.perf_counter()
                response.payload_output = payload(region, account, *args)
                response.endtime = time.perf_counter()
                response.elapsedtime = response.endtime - response.starttime
                request.responses.append(response)
        request.endtime = time.perf_counter()
        request.elapsedtime = request.endtime - request.starttime
        self.requests.append(request)
        

    def get_request_by_name(self, name):
        return next((
            r for r in self.requests if r['Name'] == name), None)


class CrawlerRequest(object):

    def __init__(self, payload):
        self.payload = payload,
        self.name = payload.__name__
        self.responses = []
        self.starttime = None
        self.endtime = None
        self.elapsedtime = None

    def dump(self):
        return dict(
            payload=self.payload.__repr__(),
            name=self.name,
            responses=[r.dump() for r in self.responses],
            starttime=self.starttime,
            endtime=self.endtime,
            elapsedtime=self.elapsedtime,
        )


class CrawlerResponse(object):

    def __init__(self, region, account):
        self.region = region
        self.account = account
        self.payload_output = None
        self.starttime = None
        self.endtime = None
        self.elapsedtime = None

    def dump(self):
        return dict(
            region=self.region,
            account=self.account.dump(),
            payload_output=self.payload_output,
            starttime=self.starttime,
            endtime=self.endtime,
            elapsedtime=self.elapsedtime,
        )

