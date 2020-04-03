Testing Notes
=============

Test from CLI showing missed coverage::

  pytest --disable-warnings --cov-report term-missing --cov-fail-under=100 --verbose

Test individual module::

  pytest --disable-warnings --no-cov --verbose test_blee.py

  pytest --disable-warnings --cov-report term-missing --verbose test_blee.py


Testing org setup for TooManyRequestsException errors:

::

  i=0
  while (( $i < 100 )); do
      rm ~/.aws/orgcrawler-cache/*
      time orgquery -r awsauth/OrgAudit list_accounts_by_name > /dev/null
      let i=i+1
  done

