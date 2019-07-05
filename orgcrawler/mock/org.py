import json
import yaml
import boto3


ORG_ACCESS_ROLE = 'myrole'
MASTER_ACCOUNT_ID = '123456789012'
POLICY_DOC = dict(
    Version='2012-10-17',
    Statement=[dict(
        Sid='MockPolicyStatement',
        Effect='Allow',
        Action='s3:*',
        Resource='*',
    )]
)
SIMPLE_ORG_SPEC = """
root:
  - name: root
    policies:
    - policy01
    accounts:
    - name: account01
      policies:
      - policy02
    - name: account02
    - name: account03
    child_ou:
      - name: ou01
        policies:
        - policy03
        child_ou:
          - name: ou01-sub0
      - name: ou02
        child_ou:
          - name: ou02-sub0
      - name: ou03
        child_ou:
          - name: ou03-sub0
"""
COMPLEX_ORG_SPEC = """
root:
  - name: root
    accounts:
    - name: account01
    - name: account02
    - name: account03
    policies:
    - policy01
    - policy02
    child_ou:
      - name: ou01
        accounts:
        - name: account04
          policies:
          - policy01
          - policy03
          - policy04
        - name: account05
        child_ou:
          - name: ou01-1
            accounts:
            - name: account08
          - name: ou01-2
            accounts:
            - name: account09
            - name: account10
            policies:
            - policy01
            - policy05
            - policy06
      - name: ou02
        accounts:
        - name: account06
        - name: account07
          policies:
          - policy01
          - policy05
          - policy06
        child_ou:
          - name: ou02-1
            accounts:
            - name: account11
          - name: ou02-2
            accounts:
            - name: account12
            - name: account13
              policies:
              - policy03
              - policy04
"""


class MockOrganization(object):
    '''
    mock_org = mock.MockOrganization()
    '''

    def __init__(self):
        self.master_id = MASTER_ACCOUNT_ID
        self.access_role = ORG_ACCESS_ROLE
        self.policy_doc = POLICY_DOC
        self.spec = None
        self.policy_list = []
        self.org_id = None
        self.root_id = None
        self.client = boto3.client('organizations')

    def simple(self):
        self.build(SIMPLE_ORG_SPEC)

    def complex(self):
        self.build(COMPLEX_ORG_SPEC)

    def build(self, yaml_str):
        self._load_org(yaml_str)
        self._mock_org_gen(self.root_id, self.spec['root'])

    def _load_org(self, yaml_str):
        self.spec = yaml.safe_load(yaml_str)
        self.client.create_organization(FeatureSet='ALL')
        self.org_id = self.client.describe_organization()['Organization']['Id']
        self.root_id = self.client.list_roots()['Roots'][0]['Id']

    def _mock_org_gen(self, parent_id, spec):
        for ou in spec:
            if ou['name'] == 'root':
                ou_id = self.root_id
            else:
                ou_id = self._ou_gen(ou, parent_id)
            if 'accounts' in ou:
                for account in ou['accounts']:
                    self._account_gen(account, ou_id)
            if 'policies' in ou:
                for policy_name in ou['policies']:
                    self._policy_gen(policy_name, ou_id)
            if 'child_ou' in ou:
                self._mock_org_gen(ou_id, ou['child_ou'])
        return

    def _ou_gen(self, ou, parent_id):
        return self.client.create_organizational_unit(
            ParentId=parent_id,
            Name=ou['name'],
        )['OrganizationalUnit']['Id']

    def _policy_gen(self, policy_name, target_id):
        policy = next((p for p in self.policy_list if p['Name'] == policy_name), None)
        if policy is None:
            policy = self.client.create_policy(
                Name=policy_name,
                Type='SERVICE_CONTROL_POLICY',
                Content=json.dumps(self.policy_doc),
                Description='Mock service control policy',
            )['Policy']['PolicySummary']
            self.policy_list.append(policy)
        self.client.attach_policy(
            PolicyId=policy['Id'],
            TargetId=target_id,
        )
        return

    def _account_gen(self, account, ou_id):
        account_id = self.client.create_account(
            AccountName=account['name'],
            Email=account['name'] + '@example.com',
        )['CreateAccountStatus']['AccountId']
        self.client.move_account(
            AccountId=account_id,
            SourceParentId=self.root_id,
            DestinationParentId=ou_id,
        )
        if 'policies' in account:
            for policy_name in account['policies']:
                self._policy_gen(policy_name, account_id)
        return
