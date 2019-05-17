#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import io
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

# gather the package's long description from the README
with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

# load the package's __init__.py module as a dictionary.
about = {}
with open(os.path.join(here, 'orgcrawler/__init__.py')) as f:
    exec(f.read(), about)

setup(
    name='orgcrawler',
    version=about['__version__'],
    description='Tools for working with AWS Organizations',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/ucopacme/orgcrawler',
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
    packages=find_packages(exclude=['dist', 'test']),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'orgquery=orgcrawler.cli.orgquery:main',
            'orgcrawler=orgcrawler.cli.orgcrawler:main',
        ],
    },
)
