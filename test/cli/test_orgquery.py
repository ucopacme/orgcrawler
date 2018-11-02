import pytest
from moto import (
    mock_organizations,
    mock_sts,
)
from organizer import orgs, utils
from organizer.cli import orgquery
from ..test_orgs import (
    MASTER_ACCOUNT_ID,
    ORG_ACCESS_ROLE,
    SIMPLE_ORG_SPEC,
    build_mock_org,
)


@mock_sts
@mock_organizations
def test_jsonfmt():
    account = orgs.OrgAccount(
        orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE),
        name='account01',
        id='112233445566',
        email='account01@example.org',
    )
    output = orgquery.jsonfmt(account)
    assert isinstance(output, str)
