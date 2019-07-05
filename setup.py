#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_namespace_packages


VERSION = '1.0.0a5'
LONGDESC = '''
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
  Execute a custom boto3 payload pythonfunction in all specified accounts/regions

See full documentation at https://orgcrawler.readthedocs.io/en/latest/
'''


setup(
    name='orgcrawler',
    version=VERSION,
    description='Tools for working with AWS Organizations',
    long_description=LONGDESC,
    long_description_content_type='text/x-rst',
    url='https://github.com/ucopacme/orgcrawler',
    project_urls={
        'Documentation': 'https://orgcrawler.readthedocs.io/en/latest/',
        'Issues': 'https://github.com/ucopacme/orgcrawler/issues',
    },

    keywords='aws organizations boto3',
    author='Ashley Gould - University of California Office of the President',
    author_email='agould@ucop.edu',
    license='GPLv3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
        'botocore',
        'boto3',
        'PyYAML',
        'click',
    ],
    packages=find_namespace_packages(
        include=['orgcrawler', 'orgcrawler.*'],
        #exclude=['test', 'docs'],
    ),
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'orgquery=orgcrawler.cli.orgquery:main',
            'orgcrawler=orgcrawler.cli.orgcrawler:main',
        ],
    },
)
