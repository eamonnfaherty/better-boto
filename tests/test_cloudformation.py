import unittest
from unittest.mock import MagicMock, patch, call

from botocore.exceptions import ClientError

from betterboto import cloudformation


class TestCloudformation(unittest.TestCase):

    def test_get_hash_for_template(self):
        template_body = "Resources: {}
        template_hash = cloudformation.get_hash_for_template(template_body)
        self.assertEqual(template_hash, 'a9d52258223936342449112e37b7b472')

    def test_make_better(self):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        self.assertTrue(hasattr(better_client, 'create_or_update'))
        self.assertTrue(hasattr(better_client, 'describe_stacks_single_page'))
        self.assertTrue(hasattr(better_client, 'ensure_deleted'))
        self.assertTrue(hasattr(better_client, 'list_stacks_single_page'))

    @patch('betterboto.cloudformation.slurp')
    def test_describe_stacks_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        better_client.describe_stacks_single_page(StackName='test-stack')
        slurp.assert_called_once_with(
            'describe_stacks',
            mock_client.describe_stacks,
            'Stacks',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            StackName='test-stack'
        )

    @patch('betterboto.cloudformation.slurp')
    def test_list_stacks_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        better_client.list_stacks_single_page(StackStatusFilter=['CREATE_COMPLETE'])
        slurp.assert_called_once_with(
            'list_stacks',
            mock_client.list_stacks,
            'Stacks',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            StackStatusFilter=['CREATE_COMPLETE']
        )

    @patch('time.sleep')
    def test_create_or_update_create_stack(self, time_sleep):
        mock_client = MagicMock()
        mock_client.exceptions.ClientError = ClientError
        mock_client.describe_stacks.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
            'DescribeStacks'
        )
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_called_once_with(StackName='test-stack', TemplateBody='body')
        mock_client.get_waiter.assert_called_once_with('stack_create_complete')
        waiter.wait.assert_called_once_with(StackName='test-stack')
        mock_client.create_change_set.assert_not_called()

    @patch('time.sleep')
    def test_create_or_update_update_stack(self, time_sleep):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        mock_client.create_change_set.return_value = {'Id': 'change-set-id'}
        mock_client.describe_change_set.return_value = {'Status': 'CREATE_COMPLETE'}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_not_called()
        self.assertTrue(mock_client.create_change_set.called)
        self.assertEqual(mock_client.get_waiter.call_count, 2)
        mock_client.get_waiter.assert_any_call('change_set_create_complete')
        mock_client.get_waiter.assert_any_call('stack_update_complete')
        waiter.wait.assert_any_call(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        mock_client.execute_change_set.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        waiter.wait.assert_any_call(StackName='test-stack')

    @patch('time.sleep')
    def test_create_or_update_no_changes(self, time_sleep):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        mock_client.create_change_set.return_value = {'Id': 'change-set-id'}
        mock_client.describe_change_set.return_value = {
            'Status': 'FAILED',
            'StatusReason': "The submitted information didn't contain changes."
        }
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_not_called()
        self.assertTrue(mock_client.create_change_set.called)
        mock_client.get_waiter.assert_called_once_with('change_set_create_complete')
        waiter.wait.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        mock_client.execute_change_set.assert_not_called()
        mock_client.delete_change_set.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')

    @patch('betterboto.cloudformation.ensure_deleted')
    @patch('time.sleep')
    def test_create_or_update_rollback_complete(self, time_sleep, ensure_deleted):
        mock_client = MagicMock()
        mock_client.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'ROLLBACK_COMPLETE'}]},
            ClientError(
                {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
                'DescribeStacks'
            )
        ]
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body', ShouldDeleteRollbackComplete=True)

        ensure_deleted.assert_called_once_with(better_client, 'test-stack')
        mock_client.create_stack.assert_called_once_with(StackName='test-stack', TemplateBody='body')

    def test_ensure_deleted_does_not_exist(self):
        mock_client = MagicMock()
        mock_client.exceptions.ClientError = ClientError
        mock_client.describe_stacks.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
            'DescribeStacks'
        )
        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')
        mock_client.delete_stack.assert_not_called()

    def test_ensure_deleted_in_deletable_status(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')

        mock_client.delete_stack.assert_called_once_with(StackName='test-stack')
        mock_client.get_waiter.assert_called_once_with('stack_delete_complete')
        waiter.wait.assert_called_once_with(StackName='test-stack')

    def test_ensure_deleted_in_non_deletable_status(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'DELETE_IN_PROGRESS'}]}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')

        mock_client.delete_stack.assert_not_called()

    def test_ensure_deleted_waiter_error(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        waiter = MagicMock()
        waiter.wait.side_effect = Exception("Waiter failed")
        mock_client.get_waiter.return_value = waiter
        mock_client.describe_stack_events.return_value = {'StackEvents': []}

        better_client = cloudformation.make_better(mock_client)
        with self.assertRaises(Exception):
            better_client.ensure_deleted(StackName='test-stack')

        mock_client.describe_stack_events.assert_called_once_with(StackName='test-stack')

import unittest
from unittest.mock import MagicMock, patch, call

from botocore.exceptions import ClientError

from betterboto import cloudformation


class TestCloudformation(unittest.TestCase):

    def test_get_hash_for_template(self):
        template_body = "Resources: {}
        template_hash = cloudformation.get_hash_for_template(template_body)
        self.assertEqual(template_hash, 'a9d52258223936342449112e37b7b472')

    def test_make_better(self):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        self.assertTrue(hasattr(better_client, 'create_or_update'))
        self.assertTrue(hasattr(better_client, 'describe_stacks_single_page'))
        self.assertTrue(hasattr(better_client, 'ensure_deleted'))
        self.assertTrue(hasattr(better_client, 'list_stacks_single_page'))

    @patch('betterboto.cloudformation.slurp')
    def test_describe_stacks_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        better_client.describe_stacks_single_page(StackName='test-stack')
        slurp.assert_called_once_with(
            'describe_stacks',
            mock_client.describe_stacks,
            'Stacks',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            StackName='test-stack'
        )

    @patch('betterboto.cloudformation.slurp')
    def test_list_stacks_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        better_client.list_stacks_single_page(StackStatusFilter=['CREATE_COMPLETE'])
        slurp.assert_called_once_with(
            'list_stacks',
            mock_client.list_stacks,
            'Stacks',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            StackStatusFilter=['CREATE_COMPLETE']
        )

    @patch('time.sleep')
    def test_create_or_update_create_stack(self, time_sleep):
        mock_client = MagicMock()
        mock_client.exceptions.ClientError = ClientError
        mock_client.describe_stacks.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
            'DescribeStacks'
        )
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_called_once_with(StackName='test-stack', TemplateBody='body')
        mock_client.get_waiter.assert_called_once_with('stack_create_complete')
        waiter.wait.assert_called_once_with(StackName='test-stack')
        mock_client.create_change_set.assert_not_called()

    @patch('time.sleep')
    def test_create_or_update_update_stack(self, time_sleep):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        mock_client.create_change_set.return_value = {'Id': 'change-set-id'}
        mock_client.describe_change_set.return_value = {'Status': 'CREATE_COMPLETE'}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_not_called()
        self.assertTrue(mock_client.create_change_set.called)
        self.assertEqual(mock_client.get_waiter.call_count, 2)
        mock_client.get_waiter.assert_any_call('change_set_create_complete')
        mock_client.get_waiter.assert_any_call('stack_update_complete')
        waiter.wait.assert_any_call(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        mock_client.execute_change_set.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        waiter.wait.assert_any_call(StackName='test-stack')

    @patch('time.sleep')
    def test_create_or_update_no_changes(self, time_sleep):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        mock_client.create_change_set.return_value = {'Id': 'change-set-id'}
        mock_client.describe_change_set.return_value = {
            'Status': 'FAILED',
            'StatusReason': "The submitted information didn't contain changes."
        }
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_not_called()
        self.assertTrue(mock_client.create_change_set.called)
        mock_client.get_waiter.assert_called_once_with('change_set_create_complete')
        waiter.wait.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        mock_client.execute_change_set.assert_not_called()
        mock_client.delete_change_set.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')

    @patch('betterboto.cloudformation.ensure_deleted')
    @patch('time.sleep')
    def test_create_or_update_rollback_complete(self, time_sleep, ensure_deleted):
        mock_client = MagicMock()
        mock_client.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'ROLLBACK_COMPLETE'}]},
            ClientError(
                {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
                'DescribeStacks'
            )
        ]
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body', ShouldDeleteRollbackComplete=True)

        ensure_deleted.assert_called_once_with(better_client, 'test-stack')
        mock_client.create_stack.assert_called_once_with(StackName='test-stack', TemplateBody='body')

    def test_ensure_deleted_does_not_exist(self):
        mock_client = MagicMock()
        mock_client.exceptions.ClientError = ClientError
        mock_client.describe_stacks.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
            'DescribeStacks'
        )
        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')
        mock_client.delete_stack.assert_not_called()

    def test_ensure_deleted_in_deletable_status(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')

        mock_client.delete_stack.assert_called_once_with(StackName='test-stack')
        mock_client.get_waiter.assert_called_once_with('stack_delete_complete')
        waiter.wait.assert_called_once_with(StackName='test-stack')

    def test_ensure_deleted_in_non_deletable_status(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'DELETE_IN_PROGRESS'}]}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')

        mock_client.delete_stack.assert_not_called()

    def test_ensure_deleted_waiter_error(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        waiter = MagicMock()
        waiter.wait.side_effect = Exception("Waiter failed")
        mock_client.get_waiter.return_value = waiter
        mock_client.describe_stack_events.return_value = {'StackEvents': []}

        better_client = cloudformation.make_better(mock_client)
        with self.assertRaises(Exception):
            better_client.ensure_deleted(StackName='test-stack')

        mock_client.describe_stack_events.assert_called_once_with(StackName='test-stack')

import unittest
from unittest.mock import MagicMock, patch, call

from botocore.exceptions import ClientError

from betterboto import cloudformation


class TestCloudformation(unittest.TestCase):

    def test_get_hash_for_template(self):
        template_body = "Resources: {}
        template_hash = cloudformation.get_hash_for_template(template_body)
        self.assertEqual(template_hash, 'a9d52258223936342449112e37b7b472')

    def test_make_better(self):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        self.assertTrue(hasattr(better_client, 'create_or_update'))
        self.assertTrue(hasattr(better_client, 'describe_stacks_single_page'))
        self.assertTrue(hasattr(better_client, 'ensure_deleted'))
        self.assertTrue(hasattr(better_client, 'list_stacks_single_page'))

    @patch('betterboto.cloudformation.slurp')
    def test_describe_stacks_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        better_client.describe_stacks_single_page(StackName='test-stack')
        slurp.assert_called_once_with(
            'describe_stacks',
            mock_client.describe_stacks,
            'Stacks',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            StackName='test-stack'
        )

    @patch('betterboto.cloudformation.slurp')
    def test_list_stacks_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        better_client.list_stacks_single_page(StackStatusFilter=['CREATE_COMPLETE'])
        slurp.assert_called_once_with(
            'list_stacks',
            mock_client.list_stacks,
            'Stacks',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            StackStatusFilter=['CREATE_COMPLETE']
        )

    @patch('time.sleep')
    def test_create_or_update_create_stack(self, time_sleep):
        mock_client = MagicMock()
        mock_client.exceptions.ClientError = ClientError
        mock_client.describe_stacks.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
            'DescribeStacks'
        )
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_called_once_with(StackName='test-stack', TemplateBody='body')
        mock_client.get_waiter.assert_called_once_with('stack_create_complete')
        waiter.wait.assert_called_once_with(StackName='test-stack')
        mock_client.create_change_set.assert_not_called()

    @patch('time.sleep')
    def test_create_or_update_update_stack(self, time_sleep):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        mock_client.create_change_set.return_value = {'Id': 'change-set-id'}
        mock_client.describe_change_set.return_value = {'Status': 'CREATE_COMPLETE'}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_not_called()
        self.assertTrue(mock_client.create_change_set.called)
        self.assertEqual(mock_client.get_waiter.call_count, 2)
        mock_client.get_waiter.assert_any_call('change_set_create_complete')
        mock_client.get_waiter.assert_any_call('stack_update_complete')
        waiter.wait.assert_any_call(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        mock_client.execute_change_set.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        waiter.wait.assert_any_call(StackName='test-stack')

    @patch('time.sleep')
    def test_create_or_update_no_changes(self, time_sleep):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        mock_client.create_change_set.return_value = {'Id': 'change-set-id'}
        mock_client.describe_change_set.return_value = {
            'Status': 'FAILED',
            'StatusReason': "The submitted information didn't contain changes."
        }
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_not_called()
        self.assertTrue(mock_client.create_change_set.called)
        mock_client.get_waiter.assert_called_once_with('change_set_create_complete')
        waiter.wait.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        mock_client.execute_change_set.assert_not_called()
        mock_client.delete_change_set.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')

    @patch('betterboto.cloudformation.ensure_deleted')
    @patch('time.sleep')
    def test_create_or_update_rollback_complete(self, time_sleep, ensure_deleted):
        mock_client = MagicMock()
        mock_client.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'ROLLBACK_COMPLETE'}]},
            ClientError(
                {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
                'DescribeStacks'
            )
        ]
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body', ShouldDeleteRollbackComplete=True)

        ensure_deleted.assert_called_once_with(better_client, 'test-stack')
        mock_client.create_stack.assert_called_once_with(StackName='test-stack', TemplateBody='body')

    def test_ensure_deleted_does_not_exist(self):
        mock_client = MagicMock()
        mock_client.exceptions.ClientError = ClientError
        mock_client.describe_stacks.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
            'DescribeStacks'
        )
        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')
        mock_client.delete_stack.assert_not_called()

    def test_ensure_deleted_in_deletable_status(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')

        mock_client.delete_stack.assert_called_once_with(StackName='test-stack')
        mock_client.get_waiter.assert_called_once_with('stack_delete_complete')
        waiter.wait.assert_called_once_with(StackName='test-stack')

    def test_ensure_deleted_in_non_deletable_status(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'DELETE_IN_PROGRESS'}]}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')

        mock_client.delete_stack.assert_not_called()

    def test_ensure_deleted_waiter_error(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        waiter = MagicMock()
        waiter.wait.side_effect = Exception("Waiter failed")
        mock_client.get_waiter.return_value = waiter
        mock_client.describe_stack_events.return_value = {'StackEvents': []}

        better_client = cloudformation.make_better(mock_client)
        with self.assertRaises(Exception):
            better_client.ensure_deleted(StackName='test-stack')

        mock_client.describe_stack_events.assert_called_once_with(StackName='test-stack')

import unittest
from unittest.mock import MagicMock, patch, call

from botocore.exceptions import ClientError

from betterboto import cloudformation


class TestCloudformation(unittest.TestCase):

    def test_get_hash_for_template(self):
        template_body = "Resources: {}
        template_hash = cloudformation.get_hash_for_template(template_body)
        self.assertEqual(template_hash, 'a9d52258223936342449112e37b7b472')

    def test_make_better(self):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        self.assertTrue(hasattr(better_client, 'create_or_update'))
        self.assertTrue(hasattr(better_client, 'describe_stacks_single_page'))
        self.assertTrue(hasattr(better_client, 'ensure_deleted'))
        self.assertTrue(hasattr(better_client, 'list_stacks_single_page'))

    @patch('betterboto.cloudformation.slurp')
    def test_describe_stacks_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        better_client.describe_stacks_single_page(StackName='test-stack')
        slurp.assert_called_once_with(
            'describe_stacks',
            mock_client.describe_stacks,
            'Stacks',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            StackName='test-stack'
        )

    @patch('betterboto.cloudformation.slurp')
    def test_list_stacks_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        better_client.list_stacks_single_page(StackStatusFilter=['CREATE_COMPLETE'])
        slurp.assert_called_once_with(
            'list_stacks',
            mock_client.list_stacks,
            'Stacks',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            StackStatusFilter=['CREATE_COMPLETE']
        )

    @patch('time.sleep')
    def test_create_or_update_create_stack(self, time_sleep):
        mock_client = MagicMock()
        mock_client.exceptions.ClientError = ClientError
        mock_client.describe_stacks.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
            'DescribeStacks'
        )
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_called_once_with(StackName='test-stack', TemplateBody='body')
        mock_client.get_waiter.assert_called_once_with('stack_create_complete')
        waiter.wait.assert_called_once_with(StackName='test-stack')
        mock_client.create_change_set.assert_not_called()

    @patch('time.sleep')
    def test_create_or_update_update_stack(self, time_sleep):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        mock_client.create_change_set.return_value = {'Id': 'change-set-id'}
        mock_client.describe_change_set.return_value = {'Status': 'CREATE_COMPLETE'}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_not_called()
        self.assertTrue(mock_client.create_change_set.called)
        self.assertEqual(mock_client.get_waiter.call_count, 2)
        mock_client.get_waiter.assert_any_call('change_set_create_complete')
        mock_client.get_waiter.assert_any_call('stack_update_complete')
        waiter.wait.assert_any_call(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        mock_client.execute_change_set.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        waiter.wait.assert_any_call(StackName='test-stack')

    @patch('time.sleep')
    def test_create_or_update_no_changes(self, time_sleep):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        mock_client.create_change_set.return_value = {'Id': 'change-set-id'}
        mock_client.describe_change_set.return_value = {
            'Status': 'FAILED',
            'StatusReason': "The submitted information didn't contain changes."
        }
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_not_called()
        self.assertTrue(mock_client.create_change_set.called)
        mock_client.get_waiter.assert_called_once_with('change_set_create_complete')
        waiter.wait.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        mock_client.execute_change_set.assert_not_called()
        mock_client.delete_change_set.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')

    @patch('betterboto.cloudformation.ensure_deleted')
    @patch('time.sleep')
    def test_create_or_update_rollback_complete(self, time_sleep, ensure_deleted):
        mock_client = MagicMock()
        mock_client.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'ROLLBACK_COMPLETE'}]},
            ClientError(
                {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
                'DescribeStacks'
            )
        ]
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body', ShouldDeleteRollbackComplete=True)

        ensure_deleted.assert_called_once_with(better_client, 'test-stack')
        mock_client.create_stack.assert_called_once_with(StackName='test-stack', TemplateBody='body')

    def test_ensure_deleted_does_not_exist(self):
        mock_client = MagicMock()
        mock_client.exceptions.ClientError = ClientError
        mock_client.describe_stacks.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
            'DescribeStacks'
        )
        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')
        mock_client.delete_stack.assert_not_called()

    def test_ensure_deleted_in_deletable_status(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')

        mock_client.delete_stack.assert_called_once_with(StackName='test-stack')
        mock_client.get_waiter.assert_called_once_with('stack_delete_complete')
        waiter.wait.assert_called_once_with(StackName='test-stack')

    def test_ensure_deleted_in_non_deletable_status(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'DELETE_IN_PROGRESS'}]}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')

        mock_client.delete_stack.assert_not_called()

    def test_ensure_deleted_waiter_error(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        waiter = MagicMock()
        waiter.wait.side_effect = Exception("Waiter failed")
        mock_client.get_waiter.return_value = waiter
        mock_client.describe_stack_events.return_value = {'StackEvents': []}

        better_client = cloudformation.make_better(mock_client)
        with self.assertRaises(Exception):
            better_client.ensure_deleted(StackName='test-stack')

        mock_client.describe_stack_events.assert_called_once_with(StackName='test-stack')

import unittest
from unittest.mock import MagicMock, patch, call

from botocore.exceptions import ClientError

from betterboto import cloudformation


class TestCloudformation(unittest.TestCase):

    def test_get_hash_for_template(self):
        template_body = "Resources: {}
        template_hash = cloudformation.get_hash_for_template(template_body)
        self.assertEqual(template_hash, 'a9d52258223936342449112e37b7b472')

    def test_make_better(self):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        self.assertTrue(hasattr(better_client, 'create_or_update'))
        self.assertTrue(hasattr(better_client, 'describe_stacks_single_page'))
        self.assertTrue(hasattr(better_client, 'ensure_deleted'))
        self.assertTrue(hasattr(better_client, 'list_stacks_single_page'))

    @patch('betterboto.cloudformation.slurp')
    def test_describe_stacks_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        better_client.describe_stacks_single_page(StackName='test-stack')
        slurp.assert_called_once_with(
            'describe_stacks',
            mock_client.describe_stacks,
            'Stacks',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            StackName='test-stack'
        )

    @patch('betterboto.cloudformation.slurp')
    def test_list_stacks_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        better_client.list_stacks_single_page(StackStatusFilter=['CREATE_COMPLETE'])
        slurp.assert_called_once_with(
            'list_stacks',
            mock_client.list_stacks,
            'Stacks',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            StackStatusFilter=['CREATE_COMPLETE']
        )

    @patch('time.sleep')
    def test_create_or_update_create_stack(self, time_sleep):
        mock_client = MagicMock()
        mock_client.exceptions.ClientError = ClientError
        mock_client.describe_stacks.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
            'DescribeStacks'
        )
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_called_once_with(StackName='test-stack', TemplateBody='body')
        mock_client.get_waiter.assert_called_once_with('stack_create_complete')
        waiter.wait.assert_called_once_with(StackName='test-stack')
        mock_client.create_change_set.assert_not_called()

    @patch('time.sleep')
    def test_create_or_update_update_stack(self, time_sleep):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        mock_client.create_change_set.return_value = {'Id': 'change-set-id'}
        mock_client.describe_change_set.return_value = {'Status': 'CREATE_COMPLETE'}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_not_called()
        self.assertTrue(mock_client.create_change_set.called)
        self.assertEqual(mock_client.get_waiter.call_count, 2)
        mock_client.get_waiter.assert_any_call('change_set_create_complete')
        mock_client.get_waiter.assert_any_call('stack_update_complete')
        waiter.wait.assert_any_call(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        mock_client.execute_change_set.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        waiter.wait.assert_any_call(StackName='test-stack')

    @patch('time.sleep')
    def test_create_or_update_no_changes(self, time_sleep):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        mock_client.create_change_set.return_value = {'Id': 'change-set-id'}
        mock_client.describe_change_set.return_value = {
            'Status': 'FAILED',
            'StatusReason': "The submitted information didn't contain changes."
        }
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_not_called()
        self.assertTrue(mock_client.create_change_set.called)
        mock_client.get_waiter.assert_called_once_with('change_set_create_complete')
        waiter.wait.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        mock_client.execute_change_set.assert_not_called()
        mock_client.delete_change_set.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')

    @patch('betterboto.cloudformation.ensure_deleted')
    @patch('time.sleep')
    def test_create_or_update_rollback_complete(self, time_sleep, ensure_deleted):
        mock_client = MagicMock()
        mock_client.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'ROLLBACK_COMPLETE'}]},
            ClientError(
                {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
                'DescribeStacks'
            )
        ]
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body', ShouldDeleteRollbackComplete=True)

        ensure_deleted.assert_called_once_with(better_client, 'test-stack')
        mock_client.create_stack.assert_called_once_with(StackName='test-stack', TemplateBody='body')

    def test_ensure_deleted_does_not_exist(self):
        mock_client = MagicMock()
        mock_client.exceptions.ClientError = ClientError
        mock_client.describe_stacks.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
            'DescribeStacks'
        )
        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')
        mock_client.delete_stack.assert_not_called()

    def test_ensure_deleted_in_deletable_status(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')

        mock_client.delete_stack.assert_called_once_with(StackName='test-stack')
        mock_client.get_waiter.assert_called_once_with('stack_delete_complete')
        waiter.wait.assert_called_once_with(StackName='test-stack')

    def test_ensure_deleted_in_non_deletable_status(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'DELETE_IN_PROGRESS'}]}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')

        mock_client.delete_stack.assert_not_called()

    def test_ensure_deleted_waiter_error(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        waiter = MagicMock()
        waiter.wait.side_effect = Exception("Waiter failed")
        mock_client.get_waiter.return_value = waiter
        mock_client.describe_stack_events.return_value = {'StackEvents': []}

        better_client = cloudformation.make_better(mock_client)
        with self.assertRaises(Exception):
            better_client.ensure_deleted(StackName='test-stack')

        mock_client.describe_stack_events.assert_called_once_with(StackName='test-stack')

import unittest
from unittest.mock import MagicMock, patch, call

from botocore.exceptions import ClientError

from betterboto import cloudformation


class TestCloudformation(unittest.TestCase):

    def test_get_hash_for_template(self):
        template_body = "Resources: {}
        template_hash = cloudformation.get_hash_for_template(template_body)
        self.assertEqual(template_hash, 'a9d52258223936342449112e37b7b472')

    def test_make_better(self):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        self.assertTrue(hasattr(better_client, 'create_or_update'))
        self.assertTrue(hasattr(better_client, 'describe_stacks_single_page'))
        self.assertTrue(hasattr(better_client, 'ensure_deleted'))
        self.assertTrue(hasattr(better_client, 'list_stacks_single_page'))

    @patch('betterboto.cloudformation.slurp')
    def test_describe_stacks_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        better_client.describe_stacks_single_page(StackName='test-stack')
        slurp.assert_called_once_with(
            'describe_stacks',
            mock_client.describe_stacks,
            'Stacks',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            StackName='test-stack'
        )

    @patch('betterboto.cloudformation.slurp')
    def test_list_stacks_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = cloudformation.make_better(mock_client)
        better_client.list_stacks_single_page(StackStatusFilter=['CREATE_COMPLETE'])
        slurp.assert_called_once_with(
            'list_stacks',
            mock_client.list_stacks,
            'Stacks',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            StackStatusFilter=['CREATE_COMPLETE']
        )

    @patch('time.sleep')
    def test_create_or_update_create_stack(self, time_sleep):
        mock_client = MagicMock()
        mock_client.exceptions.ClientError = ClientError
        mock_client.describe_stacks.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
            'DescribeStacks'
        )
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_called_once_with(StackName='test-stack', TemplateBody='body')
        mock_client.get_waiter.assert_called_once_with('stack_create_complete')
        waiter.wait.assert_called_once_with(StackName='test-stack')
        mock_client.create_change_set.assert_not_called()

    @patch('time.sleep')
    def test_create_or_update_update_stack(self, time_sleep):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        mock_client.create_change_set.return_value = {'Id': 'change-set-id'}
        mock_client.describe_change_set.return_value = {'Status': 'CREATE_COMPLETE'}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_not_called()
        self.assertTrue(mock_client.create_change_set.called)
        self.assertEqual(mock_client.get_waiter.call_count, 2)
        mock_client.get_waiter.assert_any_call('change_set_create_complete')
        mock_client.get_waiter.assert_any_call('stack_update_complete')
        waiter.wait.assert_any_call(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        mock_client.execute_change_set.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        waiter.wait.assert_any_call(StackName='test-stack')

    @patch('time.sleep')
    def test_create_or_update_no_changes(self, time_sleep):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        mock_client.create_change_set.return_value = {'Id': 'change-set-id'}
        mock_client.describe_change_set.return_value = {
            'Status': 'FAILED',
            'StatusReason': "The submitted information didn't contain changes."
        }
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body')

        mock_client.create_stack.assert_not_called()
        self.assertTrue(mock_client.create_change_set.called)
        mock_client.get_waiter.assert_called_once_with('change_set_create_complete')
        waiter.wait.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')
        mock_client.execute_change_set.assert_not_called()
        mock_client.delete_change_set.assert_called_once_with(ChangeSetName='a9d52258223936342449112e37b7b472', StackName='test-stack')

    @patch('betterboto.cloudformation.ensure_deleted')
    @patch('time.sleep')
    def test_create_or_update_rollback_complete(self, time_sleep, ensure_deleted):
        mock_client = MagicMock()
        mock_client.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'ROLLBACK_COMPLETE'}]},
            ClientError(
                {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
                'DescribeStacks'
            )
        ]
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.create_or_update(StackName='test-stack', TemplateBody='body', ShouldDeleteRollbackComplete=True)

        ensure_deleted.assert_called_once_with(better_client, 'test-stack')
        mock_client.create_stack.assert_called_once_with(StackName='test-stack', TemplateBody='body')

    def test_ensure_deleted_does_not_exist(self):
        mock_client = MagicMock()
        mock_client.exceptions.ClientError = ClientError
        mock_client.describe_stacks.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}},
            'DescribeStacks'
        )
        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')
        mock_client.delete_stack.assert_not_called()

    def test_ensure_deleted_in_deletable_status(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')

        mock_client.delete_stack.assert_called_once_with(StackName='test-stack')
        mock_client.get_waiter.assert_called_once_with('stack_delete_complete')
        waiter.wait.assert_called_once_with(StackName='test-stack')

    def test_ensure_deleted_in_non_deletable_status(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'DELETE_IN_PROGRESS'}]}
        waiter = MagicMock()
        mock_client.get_waiter.return_value = waiter

        better_client = cloudformation.make_better(mock_client)
        better_client.ensure_deleted(StackName='test-stack')

        mock_client.delete_stack.assert_not_called()

    def test_ensure_deleted_waiter_error(self):
        mock_client = MagicMock()
        mock_client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        waiter = MagicMock()
        waiter.wait.side_effect = Exception("Waiter failed")
        mock_client.get_waiter.return_value = waiter
        mock_client.describe_stack_events.return_value = {'StackEvents': []}

        better_client = cloudformation.make_better(mock_client)
        with self.assertRaises(Exception):
            better_client.ensure_deleted(StackName='test-stack')

        mock_client.describe_stack_events.assert_called_once_with(StackName='test-stack')






