from organizer import crawlers, orgs, utils


def setup_crawler(org_access_role, account_access_role=None, accounts=None, regions=None):
    """
    Returns a fully loaded organizer.crawlers.Crawler object
    """
    master_account_id = utils.get_master_account_id(org_access_role)
    my_org = orgs.Org(master_account_id, org_access_role)
    my_org.load()
    crawler_args = dict()
    my_crawler = crawlers.Crawler(
        my_org,
        access_role=account_access_role,
        accounts=accounts,
        regions=regions,
    )
    my_crawler.load_account_credentials()
    return my_crawler


def format_responses(execution):
    """ generate dictionary of orgcrawler payload execution responses
    formatted per region per account """
    collector = []
    responses = purge_empty_responses(execution)
    account_names = sorted(list(set([r.account.name for r in responses])))
    for account_name in account_names:
        d = dict(
            Account=account_name,
            Regions=[
                {r.region: r.payload_output} for r in responses if
                r.account.name == account_name
            ]
        )
        collector.append(d)
    return(collector)


def purge_empty_responses(execution):
    '''
    Return list of execution responses for which output is not empty.
    Expects each response to be a list of dict.
    '''
    responses = [
        r for r in execution.responses if
        len(r.payload_output) == 1 and
        list() not in r.payload_output.values()
    ]
    return responses
