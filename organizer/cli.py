#!/usr/bin/env python

"""
Example script for querying Organization resources

Usage:
    organizer [-h]
    organizer -r ROLE_NAME -c COMMAND [-o OU_NAME] [-a ACCOUNT_NAME]

Options:
    -h, --help                       Print help message
    -r, --role ROLE_NAME             Role to assume when querying AWS Organizations
    -c, --command COMMAND            Organizer quary to run
    -o, --ou-name OU_NAME            Name of an organizational unit
    -a, --account-name ACCOUNT_NAME  Name of account

Available Commands:
    list_accounts
    list_accounts_by_name
    list_accounts_by_id
    list_org_units
    list_org_units_by_name
    list_org_units_by_id
    list_accounts_in_ou OU_NAME
    list_accounts_in_ou_by_name OU_NAME
    list_accounts_in_ou_by_id OU_NAME
    list_accounts_under_ou OU_NAME
    list_accounts_under_ou_by_name OU_NAME
    list_accounts_under_ou_by_id OU_NAME
    get_account_id_by_name ACCOUNT_NAME
    get_org_unit_id_by_name OU_NAME
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
    master_account_id = get_master_account_id(args['--role'])
    org = orgs.Org(master_account_id, args['--role'])
    org.load()
    cmd = eval('org.' + args['--command'])
    if args['--ou-name']:
        arg = org.get_org_unit_id_by_name(args['--ou-name'])
        print(yamlfmt(cmd(arg)))
    elif args['--account-name']:
        arg = args['--account-name']
        print(yamlfmt(cmd(arg)))
    else:
        print(yamlfmt(cmd()))


if __name__ == '__main__':
    main()
