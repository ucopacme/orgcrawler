Getting Started with Organizer
==============================

A toolset for managing AWS resources across an organization


Installation
------------

organizer is not yet up on pypi.  Install it directly from github::

  pip install https://github.com/ucopacme/organizer/archive/master.zip

Currently organizer only supports python 3.6.


The Org object
--------------

The organizer.orgs.Org class provides a data model and methods for querying AWS
organizations resources.

Create an organizer.orgs.Org instance::

  master_account_id = organizer.utils.get_master_account_id('myOrgMasterRole')
  my_org = organizer.orgs.Org(master_account_id, 'myOrgMasterRole')

Load your organization's account and organizational unit resources into your instance::

  my_org.load()

 
Query your organization's account and organizational unit resources::

  all_accounts = my_org.list_accounts_by_name()
  all_org_units = my_org.list_org_units()
  test_accounts = my_org.list_accounts_in_ou('testing')

   
The Crawler object
------------------

The organizer.crawlers.Crawler object provides a framework for running python
functions in all accounts and regions in your organization or a subset thereof. 

Create an organizer.crawlers.Crawler instance::

  my_crawler = organizer.crawlers.Crawler(
      my_org,
      access_role='myAccountAdminRole',
      accounts=test_accounts,
      regions=['us-west-1', 'us-east-1'],
  )

Load AWS credentials for each account into your Crawler instance::

  my_crawler.load_account_credentials()

Run your custom python functions in all account/regions configured in your Crawler::

  import crawler_functions
  all_buckets = my_crawler.execute(crawler_functions.list_s3_buckets)
  all_sg = my_crawler.execute(crawler_functions.list_ec2_securety_groups)


Requirments for python functions called with Crawler.execute()
--------------------------------------------------------------

The Crawler.execute method calls your custom function with the following
parameters: ``region, account, *args``, where ``region`` is a string,
``account`` is organizer.orgs.OrgAccount instance, and ``args`` is a list of
positional parameters to pass to your function.  Your function must create its
own boto3 client for whatever services it will use::

  def list_s3_buckets(region, account):
      client = boto3.client('s3', region_name=region, **account.credentials)
      response = client.list_buckets()


Organizer CLI Scripts
---------------------

This package contains two console scripts: ``organizer`` and ``orgcrawler``.
These attempt to provide a generic interface for running organization queries
and custom crawler functions.  At the very least they provide concrete examples
for how to build organizer applications.

See ``organizer/cli/{organizer|orgcrawler}.py`` for code.

Run with the ``--help`` option for usage.  
