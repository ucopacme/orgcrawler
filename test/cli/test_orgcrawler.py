import pytest
from click.testing import CliRunner
from moto import (
    mock_organizations,
    mock_sts,
    mock_iam,
)

import organizer
from organizer import payloads
from organizer.cli import orgcrawler
from ..test_orgs import (
    ORG_ACCESS_ROLE,
    SIMPLE_ORG_SPEC,
    build_mock_org,
)


@mock_sts
@mock_organizations
@mock_iam
@pytest.mark.parametrize('options_list', [
    (['--help']),
    (['--version']),
    (['--master-role', ORG_ACCESS_ROLE, 'organizer.payloads.get_account_aliases']),
    (['-r', ORG_ACCESS_ROLE, '--accounts', 'account01,account02', 'organizer.payloads.get_account_aliases']),
    (['-r', ORG_ACCESS_ROLE, '--regions', 'us-west-2', 'organizer.payloads.get_account_aliases']),
    (['-r', ORG_ACCESS_ROLE, '--service', 'iam', 'organizer.payloads.get_account_aliases']),
    (['-r', ORG_ACCESS_ROLE, 'organizer.payloads.get_account_aliases', '--account-role', ORG_ACCESS_ROLE]),
    (['-r', ORG_ACCESS_ROLE, 'get_account_aliases', '--payload-file', payloads.__file__]),
])
def test_orgcrawler_success(options_list):
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    runner = CliRunner()
    result = runner.invoke(
        orgcrawler.main,
        options_list,
    )
    print(result.output_bytes)
    print(result.exit_code)
    print(result.exception)
    print(result.exc_info)
    assert result.exit_code == 0


@mock_sts
@mock_organizations
@mock_iam
@pytest.mark.parametrize('options_list', [
    (['--blee']),
    (['--master-role']),
    (['--master-role', 'blee']),
    (['--master-role', ORG_ACCESS_ROLE, 'organizer.payloads.blee']),
    (['-r', ORG_ACCESS_ROLE, 'organizer.payloads.get_account_aliases', '--accounts']),
    (['-r', ORG_ACCESS_ROLE, 'organizer.payloads.get_account_aliases', '--accounts', 'blee']),
    (['-r', ORG_ACCESS_ROLE, 'organizer.payloads.get_account_aliases', '--regions']),
    (['-r', ORG_ACCESS_ROLE, 'organizer.payloads.get_account_aliases', '--regions', 'blee']),
    (['-r', ORG_ACCESS_ROLE, 'organizer.payloads.get_account_aliases', '--service']),
    (['-r', ORG_ACCESS_ROLE, 'organizer.payloads.get_account_aliases', '--service', 'blee']),
    (['-r', ORG_ACCESS_ROLE, 'organizer.payloads.get_account_aliases', '--account-role']),
    (['-r', ORG_ACCESS_ROLE, '--payload-file', '/no/such/file', 'get_account_aliases']),
    (['-r', ORG_ACCESS_ROLE, '--payload-file', payloads.__file__, 'blee']),
])
def test_orgcrawler_failure(options_list):
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    runner = CliRunner()
    result = runner.invoke(
        orgcrawler.main,
        options_list,
    )
    print(result.output_bytes)
    print(result.exit_code)
    print(result.exception)
    print(result.exc_info)
    assert result.exit_code != 0
