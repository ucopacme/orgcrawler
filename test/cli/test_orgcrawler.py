import pytest
from click.testing import CliRunner
from moto import (
    mock_organizations,
    mock_sts,
    mock_iam,
)

import orgcrawler
from orgcrawler.cli import orgcrawler
from orgcrawler.mock import payload
from orgcrawler.mock.org import (
    MockOrganization,
    MASTER_ACCOUNT_ID,
    ORG_ACCESS_ROLE,
)


@mock_sts
@mock_organizations
@mock_iam
@pytest.mark.parametrize('options_list', [
    (['--help']),
    (['--version']),
    (['--master-role', ORG_ACCESS_ROLE, 'orgcrawler.mock.payload.get_mock_account_alias']),
    (['-r', ORG_ACCESS_ROLE, '--accounts', 'account01,account02', 'orgcrawler.mock.payload.get_mock_account_alias']),
    (['-r', ORG_ACCESS_ROLE, '--regions', 'us-west-2', 'orgcrawler.mock.payload.get_mock_account_alias']),
    (['-r', ORG_ACCESS_ROLE, '--service', 'iam', 'orgcrawler.mock.payload.get_mock_account_alias']),
    (['-r', ORG_ACCESS_ROLE, 'orgcrawler.mock.payload.get_mock_account_alias', '--account-role', ORG_ACCESS_ROLE]),
    (['-r', ORG_ACCESS_ROLE, 'get_mock_account_alias', '--payload-file', payload.__file__]),
    (['-r', ORG_ACCESS_ROLE, '--service', 'iam', 'orgcrawler.mock.payload.mixed_params',
        'cat', 'dog', 'rat', 'kwarg3=cow', 'kwarg2=sheep', 'kwarg1=horse',
    ]),
    (['-r', ORG_ACCESS_ROLE, '--service', 'iam', 'orgcrawler.mock.payload.mixed_params',
        'cat', 'dog', 'rat',
    ]),
    (['-r', ORG_ACCESS_ROLE, '--service', 'iam', 'orgcrawler.mock.payload.mixed_params',
        'cat', 'dog', 'rat', 'kwarg3=cow',
    ]),
])
def test_orgcrawler_success(options_list):
    MockOrganization().simple()
    runner = CliRunner()
    result = runner.invoke(
        orgcrawler.main,
        options_list,
    )
    assert result.exit_code == 0


@mock_sts
@mock_organizations
@mock_iam
@pytest.mark.parametrize('options_list', [
    (['--blee']),
    (['--master-role']),
    (['--master-role', 'blee']),
    (['--master-role', ORG_ACCESS_ROLE, 'orgcrawler.mock.payload.blee']),
    (['-r', ORG_ACCESS_ROLE, 'orgcrawler.mock.payload.get_mock_account_alias', '--accounts']),
    (['-r', ORG_ACCESS_ROLE, 'orgcrawler.mock.payload.get_mock_account_alias', '--accounts', 'blee']),
    (['-r', ORG_ACCESS_ROLE, 'orgcrawler.mock.payload.get_mock_account_alias', '--regions']),
    (['-r', ORG_ACCESS_ROLE, 'orgcrawler.mock.payload.get_mock_account_alias', '--regions', 'blee']),
    (['-r', ORG_ACCESS_ROLE, 'orgcrawler.mock.payload.get_mock_account_alias', '--service']),
    (['-r', ORG_ACCESS_ROLE, 'orgcrawler.mock.payload.get_mock_account_alias', '--service', 'blee']),
    (['-r', ORG_ACCESS_ROLE, 'orgcrawler.mock.payload.get_mock_account_alias', '--account-role']),
    (['-r', ORG_ACCESS_ROLE, '--payload-file', '/no/such/file', 'get_mock_account_alias']),
    (['-r', ORG_ACCESS_ROLE, '--payload-file', payload.__file__, 'blee']),

    #(['-r', ORG_ACCESS_ROLE, '--service', 'iam', 'orgcrawler.mock.payload.positional_params',
    #    'cat', 'dog', 'rat', 'cow',
    #]),
    #(['-r', ORG_ACCESS_ROLE, '--service', 'iam', 'orgcrawler.mock.payload.positional_params',
    #    'cat', 'dog',
    #]),
    (['-r', ORG_ACCESS_ROLE, '--service', 'iam', 'orgcrawler.mock.payload.kwargs_params',
        'cat', 'kwarg3=cow', 'kwarg2=sheep', 'kwarg1=horse',
    ]),
    (['-r', ORG_ACCESS_ROLE, '--service', 'iam', 'orgcrawler.mock.payload.kwargs_params',
        'kwarg4=cat', 'kwarg3=cow', 'kwarg2=sheep',
    ]),
    #(['-r', ORG_ACCESS_ROLE, '--service', 'iam', 'orgcrawler.mock.payload.mixed_params',
    #    'cat', 'dog', 'rat', 'snake', 'kwarg3=cow', 'kwarg2=sheep', 'kwarg1=horse',
    #]),
])
def test_orgcrawler_failure(options_list):
    MockOrganization().simple()
    runner = CliRunner()
    result = runner.invoke(
        orgcrawler.main,
        options_list,
    )
    assert result.exit_code != 0
