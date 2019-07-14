Testing Notes
=============

Testing org setup for TooManyRequestsException errors:

::

  i=0
  while (( $i < 100 )); do
      rm ~/.aws/orgcrawler-cache/*
      time orgquery -r awsauth/OrgAudit list_accounts_by_name > /dev/null
      let i=i+1
  done


