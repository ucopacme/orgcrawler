import time

from organizer import utils


DEFAULT_REGION = 'us-east-1'


class Crawler(object):
    """
    ISSUE: what if regions is an empty list?  this is likely in
    case of a global service.  for example:
    >>>> utils.regions_for_service('iam')
    []
    """

    def __init__(self, org, **kwargs):
        self.org = org
        self.access_role = kwargs.get('access_role', org.access_role)
        self.accounts = kwargs.get('accounts', org.accounts)
        self.regions = kwargs.get('regions', [DEFAULT_REGION])
        if len(self.regions) == 0:
            self.regions.append(DEFAULT_REGION)
        self.requests = []

    def get_regions(self):
        return self.regions

    def update_regions(self, regions):
        self.regions = regions
        if len(self.regions) == 0:
            self.regions.append(DEFAULT_REGION)

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

        def run_payload_in_account(account_region_map, request, *args):
            region = account_region_map['region']
            account = account_region_map['account']
            response = CrawlerResponse(region, account)
            response.timer.start()
            response.payload_output = request.payload(region, account, *args)
            response.timer.stop()
            request.responses.append(response)

        accounts_and_regions = []
        for region in self.regions:
            for account in self.accounts:
                accounts_and_regions.append(dict(account=account, region=region))
        thread_count = kwargs.get('thread_count', len(self.accounts))
        request = CrawlerRequest(payload)
        request.timer.start()
        utils.queue_threads(
            accounts_and_regions,
            run_payload_in_account,
            func_args=(request, *args),
            thread_count=thread_count,
        )
        request.timer.stop()
        self.requests.append(request)
        return request

    # def execute_unthreaded(self, payload, *args, **kwargs):

    #     def run_payload_in_account(account, region, request, *args):
    #         response = CrawlerResponse(region, account)
    #         response.timer.start()
    #         response.payload_output = request.payload(region, account, *args)
    #         response.timer.stop()
    #         request.responses.append(response)

    #     request = CrawlerRequest(payload)
    #     request.timer.start()
    #     for region in self.regions:
    #         for account in self.accounts:
    #             run_payload_in_account(region, request, *args)
    #     request.timer.stop()
    #     self.requests.append(request)
    #     return request

    # NO TEST
    def get_request(self, name):
        return next((r for r in self.requests if r.name == name), None)


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


class CrawlerRequest(object):

    def __init__(self, payload):
        self.payload = payload
        self.name = payload.__name__
        self.responses = []
        self.timer = CrawlerTimer()

    def dump(self):
        return dict(
            payload=self.payload.__repr__(),
            name=self.name,
            responses=[r.dump() for r in self.responses],
            statistics=self.timer.dump()
        )


class CrawlerResponse(object):

    def __init__(self, region, account):
        self.region = region
        self.account = account
        self.payload_output = None
        self.timer = CrawlerTimer()

    def dump(self):
        return dict(
            region=self.region,
            account=self.account.dump(),
            payload_output=self.payload_output,
            statistics=self.timer.dump()
        )
