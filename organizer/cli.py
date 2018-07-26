#!/usr/bin/env python

"""
Example script for querying Organization resources

Usage:
  organizer [-h]
  organizer -r ROLE_NAME accounts
  organizer -r ROLE_NAME accounts_by_name
  organizer -r ROLE_NAME accounts_by_id
  organizer -r ROLE_NAME org_units
  organizer -r ROLE_NAME org_units_by_name ACCOUNT_NAME
  organizer -r ROLE_NAME org_units_by_id ACCOUNT_ID
  organizer -r ROLE_NAME accounts_in_ou OU_NAME
  organizer -r ROLE_NAME accounts_in_ou_by_name OU_NAME
  organizer -r ROLE_NAME accounts_in_ou_by_id OU_NAME
  organizer -r ROLE_NAME accounts_under_ou OU_NAME
  organizer -r ROLE_NAME accounts_under_ou_by_name OU_NAME
  organizer -r ROLE_NAME accounts_under_ou_by_id OU_NAME
  organizer -r ROLE_NAME get_account_id_by_name ACCOUNT_NAME
  organizer -r ROLE_NAME get_org_unit_id_by_name OU_NAME

Options:
    -h, --help              Print help message
    -r, --role ROLE_NAME    Role to assume when querying AWS Organizations
"""


import yaml
from docopt import docopt
from organizer import orgs
from organizer.utils import get_master_account_id

def yamlfmt(obj):
    if isinstance(obj, str):
        return obj
    return yaml.dump(obj, default_flow_style=False)


def main():
    args = docopt(__doc__)
    #print(args)
    master_account_id = get_master_account_id(args['--role'])
    #print(master_account_id)
    org = orgs.Org(master_account_id, args['--role'])
    org.load()
    print(yamlfmt(org.list_accounts()))
    print(yamlfmt(org.list_accounts_by_id()))
    print(yamlfmt(org.list_accounts_by_name()))


if __name__ == '__main__':
    main()
