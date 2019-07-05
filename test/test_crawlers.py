import time
from inspect import isfunction

import pytest
from moto import (
    mock_organizations,
    mock_sts,
    mock_iam,
    mock_s3,
)

from orgcrawler import crawlers, orgs, utils
from orgcrawler.mock.org import (
    MockOrganization,
    ORG_ACCESS_ROLE,
    MASTER_ACCOUNT_ID,
)
from orgcrawler.mock.payload import *


ALL_REGIONS = utils.all_regions()

def test_crawler_timer_init():
    timer = crawlers.CrawlerTimer()
    timer.start()
    time.sleep(0.1)
    timer.stop()
    assert isinstance(timer.start_time, float)
    assert isinstance(timer.end_time, float)
    assert isinstance(timer.elapsed_time, float)
    assert timer.start_time < timer.end_time
    assert int(timer.elapsed_time * 10) == 1
    assert isinstance(timer.dump(), dict)


@mock_sts
@mock_organizations
def test_crawler_response_init():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    response = crawlers.CrawlerResponse('us-east-1', org.accounts[0])
    assert response.region == 'us-east-1'
    assert isinstance(response.account, orgs.OrgAccount)
    assert response.payload_output is None
    assert isinstance(response.timer, crawlers.CrawlerTimer)
    assert isinstance(response.dump(), dict)


@mock_sts
@mock_organizations
def test_crawler_execution_init():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    execution = crawlers.CrawlerExecution(get_mock_account_alias)
    assert isfunction(execution.payload)
    assert execution.name == 'get_mock_account_alias'
    assert execution.responses == []
    assert isinstance(execution.timer, crawlers.CrawlerTimer)
    assert isinstance(execution.dump(), dict)


@mock_sts
@mock_organizations
def test_crawler_init():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    crawler = crawlers.Crawler(org)
    assert isinstance(crawler, crawlers.Crawler)
    assert isinstance(crawler.org, orgs.Org)
    assert crawler.access_role == org.access_role
    assert crawler.accounts == org.accounts
    assert crawler.regions == ALL_REGIONS

    crawler = crawlers.Crawler(org, accounts='', regions='')
    assert crawler.accounts == org.accounts
    assert crawler.regions == ALL_REGIONS

    crawler = crawlers.Crawler(org, accounts=[], regions=[])
    assert crawler.accounts == org.accounts
    assert crawler.regions == ALL_REGIONS

    crawler = crawlers.Crawler(org, accounts=None, regions=None)
    assert crawler.accounts == org.accounts
    assert crawler.regions == ALL_REGIONS

    crawler = crawlers.Crawler(org, accounts='account01', regions='us-west-2')
    assert len(crawler.accounts) == 1
    assert isinstance(crawler.accounts[0], orgs.OrgAccount)
    assert crawler.accounts[0].name == 'account01'
    assert len(crawler.regions) == 1
    assert crawler.regions == ['us-west-2']

    crawler = crawlers.Crawler(org, 
        accounts=org.get_account('account02'),
        regions='GLOBAL',
    )
    assert isinstance(crawler.accounts[0], orgs.OrgAccount)
    assert crawler.accounts[0].name == 'account02'
    assert crawler.regions == [crawlers.DEFAULT_REGION]

    crawler = crawlers.Crawler(org, 
        accounts=['account01', org.get_account_id_by_name('account02'), org.get_account('account03')], 
        regions=['us-west-2', 'us-east-1'],
    )
    for account in crawler.accounts:
        assert isinstance(account, orgs.OrgAccount)
    assert len(crawler.regions) == 2

    crawler = crawlers.Crawler(org,
        accounts=org.list_accounts_in_ou('ou01'),
        regions=utils.regions_for_service('iam'),
        access_role='OrgCrawlerAdmin',
    )
    assert len(crawler.accounts) == 3
    for account in crawler.accounts:
        assert isinstance(account, orgs.OrgAccount)
    assert crawler.regions == [crawlers.DEFAULT_REGION]
    assert crawler.access_role == 'OrgCrawlerAdmin'

    with pytest.raises(ValueError) as e:
        crawler = crawlers.Crawler(org, accounts=dict(key='bogus'))

    with pytest.raises(ValueError) as e:
        crawler = crawlers.Crawler(org, regions=dict(key='bogus'))

    with pytest.raises(ValueError) as e:
        crawler = crawlers.Crawler(org, regions=['us-west-1', 'bogus-1', 'bogus-2'])
    assert str(e.value) == 'Invalid regions: bogus-1, bogus-2'


@mock_sts
@mock_organizations
def test_load_account_credentials():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    crawler = crawlers.Crawler(org)
    crawler.load_account_credentials()
    assert isinstance(crawler.accounts, list)
    assert len(crawler.accounts) == len(org.accounts)
    for account in crawler.accounts:
        assert isinstance(account.credentials, dict)


@mock_sts
@mock_organizations
@mock_iam
def test_get_or_update_regions():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    crawler = crawlers.Crawler(org)
    assert crawler.get_regions() == ALL_REGIONS
    crawler.update_regions('GLOBAL')
    assert crawler.get_regions() == [crawlers.DEFAULT_REGION]
    crawler.update_regions(utils.regions_for_service('iam'))
    assert crawler.get_regions() == [crawlers.DEFAULT_REGION]
    crawler.update_regions(ALL_REGIONS)
    assert crawler.get_regions() == ALL_REGIONS
    crawler.update_regions(utils.regions_for_service('cloud9'))
    assert crawler.get_regions() == utils.regions_for_service('cloud9')


@mock_sts
@mock_organizations
def test_get_or_update_accounts():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    crawler = crawlers.Crawler(org)
    assert crawler.get_accounts() == crawler.accounts
    crawler.update_accounts('account01')
    assert len(crawler.accounts) == 1
    assert isinstance(crawler.accounts[0], orgs.OrgAccount)
    assert crawler.accounts[0].name == 'account01'
    crawler.update_accounts(['account01', 'account02'])
    assert len(crawler.accounts) == 2
    assert isinstance(crawler.accounts[0], orgs.OrgAccount)
    assert isinstance(crawler.accounts[1], orgs.OrgAccount)
    assert crawler.accounts[0].name == 'account01'
    assert crawler.accounts[1].name == 'account02'
    crawler.update_accounts('ALL')
    assert crawler.accounts == crawler.org.accounts
    crawler.update_accounts([])
    assert len(crawler.accounts) == 0
    crawler.update_accounts(None)
    assert len(crawler.accounts) == 0
    crawler.update_accounts(None)
    with pytest.raises(ValueError) as e:
        crawler.update_accounts('')
    with pytest.raises(ValueError) as e:
        crawler.update_accounts(1234)
    with pytest.raises(ValueError) as e:
        crawler.update_accounts(dict())


@mock_sts
@mock_organizations
@mock_iam
@mock_s3
def test_execute():
    MockOrganization().complex()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    crawler = crawlers.Crawler(org)
    crawler.load_account_credentials()
    execution1= crawler.execute(set_mock_account_alias)
    execution2 = crawler.execute(get_mock_account_alias)
    assert len(crawler.executions) == 2
    assert execution1 == crawler.executions[0]
    assert execution2 == crawler.executions[1]
    for execution in crawler.executions:
        assert isinstance(execution, crawlers.CrawlerExecution)
        assert len(execution.responses) == len(crawler.accounts) * len(crawler.regions)
        for response in execution.responses:
            assert isinstance(response, crawlers.CrawlerResponse)
    assert crawler.executions[0].name == 'set_mock_account_alias'
    assert crawler.executions[1].name == 'get_mock_account_alias'
    for response in crawler.executions[0].responses:
        assert response.payload_output is None
    for response in crawler.executions[1].responses:
        assert isinstance(response.payload_output, list)
        assert response.payload_output[0].startswith('alias-account')

    crawler.update_regions(ALL_REGIONS)
    execution3 = crawler.execute(create_mock_bucket, 'mockbucket')
    assert len(crawler.executions) == 3
    assert len(execution3.responses) == len(crawler.accounts) * len(crawler.regions)
    for response in execution3.responses:
        assert response.payload_output['ResponseMetadata']['HTTPStatusCode'] == 200

    assert crawler.get_execution('set_mock_account_alias') == crawler.executions[0]
    assert crawler.get_execution('get_mock_account_alias') == crawler.executions[1]
    assert crawler.get_execution('create_mock_bucket') == crawler.executions[2]

    with pytest.raises(SystemExit):
        bad_execution = crawler.execute(bad_payload_func)


args = ('cat', 'dog', 'rat')
two_args = ('dog', 'rat')
kwargs = dict(
    kwarg1='horse',
    kwarg2='sheep',
    kwarg3='cow',
)
two_kwargs = dict(
    kwarg2='sheep',
    kwarg3='cow',
)
args_dict = dict(
    arg1='cat',
    arg2='dog',
    arg3='rat',
)
all_args = dict(
    arg1='cat',
    arg2='dog',
    arg3='rat',
    kwarg1='horse',
    kwarg2='sheep',
    kwarg3='cow',
)


@mock_sts
@mock_organizations
def test_execute_parameter_handling():
    MockOrganization().simple()
    org = orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    org.load()
    crawler = crawlers.Crawler(org, accounts='account01', regions='us-east-1')
    crawler.load_account_credentials()

    execution = crawler.execute(positional_params, 'cat', 'dog', 'rat')
    assert execution.responses[0].payload_output['params'] == args_dict
    execution = crawler.execute(positional_params, *args)
    assert execution.responses[0].payload_output['params'] == args_dict
    execution = crawler.execute(positional_params, 'cat', *two_args)
    assert execution.responses[0].payload_output['params'] == args_dict

    execution = crawler.execute(kwarg_params, kwarg3='cow', kwarg2='sheep', kwarg1='horse')
    assert execution.responses[0].payload_output['params'] == kwargs
    execution = crawler.execute(kwarg_params, **kwargs)
    assert execution.responses[0].payload_output['params'] == kwargs
    execution = crawler.execute(kwarg_params, kwarg1='horse', **two_kwargs)
    assert execution.responses[0].payload_output['params'] == kwargs

    execution = crawler.execute(mixed_params,
        'cat', 'dog', 'rat',
        kwarg3='cow', kwarg2='sheep', kwarg1='horse',
    )
    assert execution.responses[0].payload_output['params'] == all_args
    execution = crawler.execute(mixed_params, *args, **kwargs)
    assert execution.responses[0].payload_output['params'] == all_args
    execution = crawler.execute(mixed_params, 'cat', *two_args, kwarg1='horse', **two_kwargs)
    assert execution.responses[0].payload_output['params'] == all_args
