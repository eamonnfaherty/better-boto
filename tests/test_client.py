import unittest
from unittest.mock import patch, MagicMock, call

from betterboto import client


class TestClient(unittest.TestCase):

    @patch('betterboto.client.make_better')
    @patch('betterboto.client.Session')
    def test_client_context_manager(self, session, make_better):
        mock_client = MagicMock()
        session.return_value.client.return_value = mock_client
        make_better.return_value = 'better_client'

        with client.ClientContextManager('s3', region_name='eu-west-1') as s3_client:
            self.assertEqual(s3_client, 'better_client')

        session.return_value.client.assert_called_once_with('s3', region_name='eu-west-1')
        make_better.assert_called_once_with('s3', mock_client)

    @patch('betterboto.client.make_better')
    @patch('betterboto.client.Session')
    def test_multi_region_client_context_manager(self, session, make_better):
        mock_client_1 = MagicMock()
        mock_client_2 = MagicMock()
        session.return_value.client.side_effect = [mock_client_1, mock_client_2]
        make_better.side_effect = ['better_client_1', 'better_client_2']

        regions = ['eu-west-1', 'us-east-1']
        with client.MultiRegionClientContextManager('s3', regions) as s3_clients:
            self.assertEqual(s3_clients['eu-west-1'], 'better_client_1')
            self.assertEqual(s3_clients['us-east-1'], 'better_client_2')

        self.assertEqual(session.return_value.client.call_count, 2)
        session.return_value.client.assert_has_calls([
            call('s3', region_name='eu-west-1'),
            call('s3', region_name='us-east-1')
        ], any_order=True)

        self.assertEqual(make_better.call_count, 2)
        make_better.assert_has_calls([
            call('s3', mock_client_1),
            call('s3', mock_client_2)
        ], any_order=True)

    @patch('betterboto.client.make_better')
    @patch('betterboto.client.Session')
    def test_cross_account_client_context_manager(self, session, make_better):
        mock_sts_client = MagicMock()
        mock_s3_client = MagicMock()

        assumed_role_object = {
            'Credentials': {
                'AccessKeyId': 'ACCESS_KEY_ID',
                'SecretAccessKey': 'SECRET_ACCESS_KEY',
                'SessionToken': 'SESSION_TOKEN',
            }
        }
        mock_sts_client.assume_role.return_value = assumed_role_object

        session.return_value.client.side_effect = [mock_sts_client, mock_s3_client]
        make_better.return_value = 'better_s3_client'

        role_arn = 'arn:aws:iam::123456789012:role/MyRole'
        role_session_name = 'my-session'

        with client.CrossAccountClientContextManager('s3', role_arn, role_session_name, region_name='eu-west-1') as s3_client:
            self.assertEqual(s3_client, 'better_s3_client')

        session.return_value.client.assert_any_call('sts')
        mock_sts_client.assume_role.assert_called_once_with(
            RoleArn=role_arn,
            RoleSessionName=role_session_name
        )

        expected_credentials = {
            'aws_access_key_id': 'ACCESS_KEY_ID',
            'aws_secret_access_key': 'SECRET_ACCESS_KEY',
            'aws_session_token': 'SESSION_TOKEN',
            'region_name': 'eu-west-1'
        }
        session.return_value.client.assert_any_call('s3', **expected_credentials)
        make_better.assert_called_once_with('s3', mock_s3_client)

    @patch('betterboto.client.make_better')
    @patch('betterboto.client.Session')
    def test_cross_multiple_accounts_client_context_manager(self, session, make_better):
        mock_sts_client_1 = MagicMock()
        mock_sts_client_2 = MagicMock()
        mock_s3_client = MagicMock()

        assumed_role_object_1 = {
            'Credentials': {
                'AccessKeyId': 'ACCESS_KEY_ID_1',
                'SecretAccessKey': 'SECRET_ACCESS_KEY_1',
                'SessionToken': 'SESSION_TOKEN_1',
            }
        }
        assumed_role_object_2 = {
            'Credentials': {
                'AccessKeyId': 'ACCESS_KEY_ID_2',
                'SecretAccessKey': 'SECRET_ACCESS_KEY_2',
                'SessionToken': 'SESSION_TOKEN_2',
            }
        }
        mock_sts_client_1.assume_role.return_value = assumed_role_object_1
        mock_sts_client_2.assume_role.return_value = assumed_role_object_2

        session.return_value.client.side_effect = [mock_sts_client_1, mock_sts_client_2, mock_s3_client]
        make_better.return_value = 'better_s3_client'

        assumable_details = [
            ('arn:aws:iam::111:role/Role1', 'session1'),
            ('arn:aws:iam::222:role/Role2', 'session2'),
        ]

        with client.CrossMultipleAccountsClientContextManager('s3', assumable_details, region_name='eu-west-1') as s3_client:
            self.assertEqual(s3_client, 'better_s3_client')

        self.assertEqual(session.return_value.client.call_count, 3)
        session.return_value.client.assert_any_call('sts', **{})
        mock_sts_client_1.assume_role.assert_called_once_with(
            RoleArn='arn:aws:iam::111:role/Role1',
            RoleSessionName='session1'
        )

        expected_credentials_1 = {
            'aws_access_key_id': 'ACCESS_KEY_ID_1',
            'aws_secret_access_key': 'SECRET_ACCESS_KEY_1',
            'aws_session_token': 'SESSION_TOKEN_1',
        }
        session.return_value.client.assert_any_call('sts', **expected_credentials_1)
        mock_sts_client_2.assume_role.assert_called_once_with(
            RoleArn='arn:aws:iam::222:role/Role2',
            RoleSessionName='session2'
        )

        expected_credentials_2 = {
            'aws_access_key_id': 'ACCESS_KEY_ID_2',
            'aws_secret_access_key': 'SECRET_ACCESS_KEY_2',
            'aws_session_token': 'SESSION_TOKEN_2',
            'region_name': 'eu-west-1'
        }
        session.return_value.client.assert_any_call('s3', **expected_credentials_2)
        make_better.assert_called_once_with('s3', mock_s3_client)

    @patch('betterboto.client.budgets')
    @patch('betterboto.client.ssm')
    @patch('betterboto.client.codecommit')
    @patch('betterboto.client.codebuild')
    @patch('betterboto.client.guardduty')
    @patch('betterboto.client.organizations')
    @patch('betterboto.client.servicecatalog')
    @patch('betterboto.client.cloudformation')
    def test_make_better(self, cloudformation, servicecatalog, organizations, guardduty, codebuild, codecommit, ssm, budgets):
        mock_client = MagicMock()
        client.make_better('cloudformation', mock_client); cloudformation.make_better.assert_called_with(mock_client)
        client.make_better('servicecatalog', mock_client); servicecatalog.make_better.assert_called_with(mock_client)
        client.make_better('organizations', mock_client); organizations.make_better.assert_called_with(mock_client)
        client.make_better('guardduty', mock_client); guardduty.make_better.assert_called_with(mock_client)
        client.make_better('codebuild', mock_client); codebuild.make_better.assert_called_with(mock_client)
        client.make_better('codecommit', mock_client); codecommit.make_better.assert_called_with(mock_client)
        client.make_better('ssm', mock_client); ssm.make_better.assert_called_with(mock_client)
        client.make_better('budgets', mock_client); budgets.make_better.assert_called_with(mock_client)
        returned_client = client.make_better('s3', mock_client)
        self.assertEqual(returned_client, mock_client)

