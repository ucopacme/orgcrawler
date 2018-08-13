#!/usr/bin/env python

"""
Script for querying AWS Organization resources

Usage:
    organizer [-h][-V]
    organizer [-f format] [-m master_account_id] -r role COMMAND [ARGUMENT]

Arguments:
    COMMAND     An organizer query command to run
    ARGUMENT    A command argument to supply if needed

Options:
    -h, --help              Print help message
    -V, --version           Display version info and exit
    -f format               Output format:  "json" or "yaml". [Default: json]
    -m master_account_id    The master account id for the organization
    -r role                 The AWS role name to assume when running organizer

Available Query Commands:
    dump
    dump_accounts
    dump_org_units
    list_accounts_by_name
    list_accounts_by_id
    list_org_units_by_name
    list_org_units_by_id
    get_account ACCOUNT_IDENTIFIER
    get_account_id_by_name ACCOUNT_NAME
    get_account_name_by_id ACCOUNT_ID
    get_org_unit_id OU_IDENTIFIER
    list_accounts_in_ou OU_IDENTIFIER
    list_accounts_in_ou_recursive OU_IDENTIFIER
    list_org_units_in_ou OU_IDENTIFIER
    list_org_units_in_ou_recursive OU_IDENTIFIER
"""


import sys
from docopt import docopt
from organizer import __version__, orgs, utils


_COMMANDS = [
    'dump',
    'dump_accounts',
    'dump_org_units',
    'list_accounts_by_name',
    'list_accounts_by_id',
    'list_org_units_by_name',
    'list_org_units_by_id',
]
_COMMANDS_WITH_ARG = [
    'get_account',
    'get_account_id_by_name',
    'get_account_name_by_id',
    'get_org_unit_id',
    'list_accounts_in_ou',
    'list_accounts_in_ou_recursive',
    'list_org_units_in_ou',
    'list_org_units_in_ou_recursive',
]
AVAILABLE_COMMANDS = _COMMANDS + _COMMANDS_WITH_ARG


def jsonfmt(obj):
    return utils.jsonfmt(obj, orgs.OrgObject.dump)


def main():
    args = docopt(__doc__, version=__version__)
    if len(sys.argv) == 1:
        sys.exit(__doc__)
    if args['COMMAND'] not in AVAILABLE_COMMANDS:
        print('ERROR: "{}" not an available query command'.format(args['COMMAND']))
        sys.exit(__doc__)
    if args['COMMAND'] in _COMMANDS_WITH_ARG and not args['ARGUMENT']:
        print('ERROR: Query command "{}" requires an argument'.format(args['COMMAND']))
        sys.exit(__doc__)
    if args['-f'] == 'json':
        formatter = jsonfmt
    elif args['-f'] == 'yaml':
        formatter = utils.yamlfmt
    else:
        print('ERROR: Print format must be either "json" or "yaml"')
        sys.exit(__doc__)

    if args['-m'] is None:
        master_account_id = utils.get_master_account_id(args['-r'])
    else:
        master_account_id = args['-m']

    org = orgs.Org(master_account_id, args['-r'])
    org.load()
    cmd = eval('org.' + args['COMMAND'])
    if args['ARGUMENT']:
        print(formatter(cmd(args.get('ARGUMENT'))))
    else:
        print(formatter(cmd()))


if __name__ == '__main__':
    main()
