Getting Started with OrgCrawler
===============================

A python library for managing resources across all accounts in an AWS Organization.

OrgCrawler package exports two primary classes:

``orgcrawler.orgs.Org``
  provides a data model and methods for querying AWS Organizations resources:

  - accounts
  - organizational units
  - service control policies

``orgcrawler.crawlers.Crawler``
  provides a framework for executing user defined python code in all accounts and regions or a subset thereof. 

OrgCrawler also contains two commandline scripts:

``orgquery``
  Provides a generic interface for running organization queries

``orgcrawler``
  Execute a custom boto3 payload function in all specified accounts/regions

See full documentation at https://orgcrawler.readthedocs.io/en/latest/

Currently orgcrawler is tested in python 3.6, 3.7.


The OrgCrawler package no longer contains payload functions.  These are now maintained
in package ``orgcrawler-payload``.


Installation
------------

::

  pip install orgcrawler
  pip install orgcrawler-payload




The Org object
--------------

Usage
*****

Create an orgcrawler.orgs.Org instance::

  master_account_id = orgcrawler.utils.get_master_account_id('myOrgMasterRole')
  my_org = orgcrawler.orgs.Org(master_account_id, 'myOrgMasterRole')

Load your organization's account and organizational unit resources into your instance::

  my_org.load()
 
Query your organization's account and organizational unit resources::

  all_accounts = my_org.list_accounts_by_name()
  all_org_units = my_org.list_org_units()
  test_accounts = my_org.list_accounts_in_ou('testing')


Details
*******

A newly initialized Org object only contains master account information.

The ``load()`` method makes boto3 client calls to the master account to
populate the Org object's Account and OrganizationalUnit resource data.

The `loaded` Org object is cached to local disk to improve the performance of
subsequent ``load()`` calls.  After an hour, the cached Org object is timed
out.  It contains no AWS account credentials.
   
Org object query methods can return listings of accounts based on OrganizationalUnit membership.
See the API docs for a full listing of query methods


The Crawler object
------------------

The orgcrawler.crawlers.Crawler object provides a framework for running python
functions in all accounts and regions in your organization or a subset thereof. 

Create an orgcrawler.crawlers.Crawler instance::

  my_crawler = orgcrawler.crawlers.Crawler(
      my_org,
      access_role='myAccountAdminRole',
      accounts=test_accounts,
      regions=['us-west-1', 'us-east-1'],
  )

Load AWS credentials for each account into your Crawler instance::

  my_crawler.load_account_credentials()


Shortcut Crawler Setup
----------------------

You can generate an Crawler object and associated Org object with a single utility function::

  from orgcrawler.cli.utils import setup_crawler
  my_crawler = crawler_setup('MyMasterAccountRole')

or::

  crawler_params = dict(
      access_role='myAccountAdminRole',
      accounts=test_accounts,
      regions=['us-west-1', 'us-east-1'],
  )
  my_crawler = crawler_setup('MyMasterAccountRole', **crawler_params)


Running Crawler Payload Functions
---------------------------------

Run your custom python code in all account/regions configured in your Crawler
by calling the ``execute()`` method of your Crawler instance.  Supply your
`payload` function and any function arguments as parameters::

  import my_payloads
  all_buckets = my_crawler.execute(my_payloads.list_s3_buckets)
  my_crawler.execute(my_payloads.create_bucket, 'my_bucket')


Requirments for Payload Functions
---------------------------------

The Crawler.execute method calls your custom function with the following
parameters: ``region, account, *args``, where ``region`` is a string,
``account`` is orgcrawler.orgs.OrgAccount instance, and ``args`` is a list of
positional parameters to pass to your function.  Your function must create its
own boto3 client for whatever services it will use.

Examples::

  def list_s3_buckets(region, account):
      client = boto3.client('s3', region_name=region, **account.credentials)
      response = client.list_buckets()

  def create_bucket(region, account, bucket_prefix):
      client = boto3.client('s3', region_name=region, **account.credentials)
      bucket_name = '-'.join([bucket_prefix, account.id, region])
      bucket_attributes = {'Bucket': bucket_name}
      if not region == 'us-east-1':
          bucket_attributes['CreateBucketConfiguration'] = {'LocationConstraint': region}
      response = client.create_bucket(**bucket_attributes)


Running payloads which call global AWS services
-----------------------------------------------

When calling a payload function which accesses a global service, set the
``regions`` attribute of your Crawler instance either to ``us-east-1`` or to
the keywork ``GLOBAL``.  Otherwise, Crawler.execute() will travers every AWS
region and redandantly run your payload::

  my_crawler = crawler_setup('MyMasterAccountRole')
  my_crawler.update_regions('GLOBAL')
  my_crawler.execute(iam_list_users)


OrgCrawler CLI Scripts
----------------------

This package contains two console scripts: ``orgquery`` and ``orgcrawler``.
These attempt to provide a generic interface for running organization queries
and custom crawler functions.  They provide concrete examples for how to build
orgcrawler applications.

See ``orgcrawler/cli/{orgquery|orgcrawler}.py`` for code.

Run with the ``--help`` option for usage.  


CLI Examples
------------

orgquery
********

::

  orgquery -h
  orgquery -r OrgMasterRole list_accounts_by_name
  orgquery -r OrgMasterRole -f yaml get_account_id_by_name webapps
  orgquery -r OrgMasterRole get_targets_for_policy LimitAWSRegions |  jq -re .[].Name


orgcrawler
**********

::

  orgcrawler -h
  orgcrawler -r OrgMasterRole orgcrawler.payloads.list_buckets
  orgcrawler -r OrgMasterRole --account-role S3Admin orgcrawler.payloads.create_bucket orgcrawler-testbucket
  orgcrawler -r OrgMasterRole --service codecommit --payload-file ~/my_payloads.py list_cc_repositories
  orgcrawler -r OrgMasterRole --accounts app-test,app-prod --regions us-east-1,us-west-2 orgcrawler.payloads.config_describe_rules

When running a payload function which calls a global AWS service such as IAM or
Route53, use the ``--service`` option.  This will set the ``regions`` attibute
of your crawler object to the default region ``us-east-1``::

  orgcrawler -r OrgMasterRole --service iam orgcrawler.payloads.iam_list_users
  orgcrawler -r OrgMasterRole --service route53 orgcrawler.payloads.list_hosted_zones

