import unittest
from unittest.mock import MagicMock, patch
from betterboto import cloudformation
import botocore


class TestCloudformation(unittest.TestCase):

    def setUp(self):
        self.client = MagicMock()
        self.client.exceptions = botocore.exceptions
        cloudformation.make_better(self.client)

    def test_get_hash_for_template(self):
        hash = cloudformation.get_hash_for_template('template_body')
        self.assertEqual(hash, 'a553b064f79b3c7b093a75f955534616')

    def test_create_or_update_create(self):
        self.client.describe_stacks.side_effect = self.client.exceptions.ClientError({'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}}, 'DescribeStacks')
        self.client.create_or_update(
            StackName='test-stack',
            TemplateBody='{}'
        )
        self.client.create_stack.assert_called_with(StackName='test-stack', TemplateBody='{}')

    def test_create_or_update_update(self):
        self.client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        self.client.create_change_set.return_value = {'Id': 'change-set-id'}
        self.client.create_or_update(
            StackName='test-stack',
            TemplateBody='{}'
        )
        self.client.create_change_set.assert_called_with(StackName='test-stack', TemplateBody='{}', ChangeSetName='a9993e364706816aba3e25717850c26c')
        self.client.execute_change_set.assert_called_with(ChangeSetName='a9993e364706816aba3e25717850c26c', StackName='test-stack')

    def test_create_or_update_rollback_delete(self):
        self.client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'ROLLBACK_COMPLETE'}]}
        self.client.create_or_update(
            StackName='test-stack',
            TemplateBody='{}',
            ShouldDeleteRollbackComplete=True
        )
        self.client.delete_stack.assert_called_with(StackName='test-stack')

    def test_ensure_deleted(self):
        self.client.describe_stacks_single_page.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        self.client.ensure_deleted(StackName='test-stack')
        self.client.delete_stack.assert_called_with(StackName='test-stack')

    def test_ensure_deleted_does_not_exist(self):
        self.client.describe_stacks_single_page.side_effect = self.client.exceptions.ClientError({'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}}, 'DescribeStacks')
        self.client.ensure_deleted(StackName='test-stack')
        self.client.delete_stack.assert_not_called()

    def test_list_stacks(self):
        self.client.list_stacks.return_value = {'Stacks': [{'StackName': 'test-stack-1'}]}
        response = self.client.list_stacks_single_page()
        self.assertEqual(len(response['Stacks']), 1)

    def test_describe_stacks_single_page(self):
        self.client.describe_stacks.return_value = {'Stacks': [{'StackName': 'test-stack-1'}]}
        response = self.client.describe_stacks_single_page()
        self.assertEqual(len(response['Stacks']), 1)

    def test_create_or_update_no_changes(self):
        self.client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        self.client.create_change_set.side_effect = self.client.exceptions.ClientError({'Error': {'Code': 'ValidationError', 'Message': 'No updates are to be performed.'}}, 'CreateChangeSet')
        self.client.create_or_update(
            StackName='test-stack',
            TemplateBody='{}'
        )
        self.client.execute_change_set.assert_not_called()

    def test_create_or_update_no_changeset(self):
        self.client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        self.client.create_or_update(
            StackName='test-stack',
            TemplateBody='{}',
            ShouldUseChangeSets=False
        )
        self.client.update_stack.assert_called_with(StackName='test-stack', TemplateBody='{}')

    def test_create_or_update_update_no_changeset_and_exception(self):
        self.client.describe_stacks.return_value = {'Stacks': [{'StackStatus': 'CREATE_COMPLETE'}]}
        self.client.update_stack.side_effect = self.client.exceptions.ClientError({'Error': {'Code': 'ValidationError', 'Message': 'No updates are to be performed.'}}, 'UpdateStack')
        self.client.create_or_update(
            StackName='test-stack',
            TemplateBody='{}',
            ShouldUseChangeSets=False
        )
        self.client.update_stack.assert_called_with(StackName='test-stack', TemplateBody='{}')

    def test_create_or_update_create_and_wait_fails(self):
        self.client.describe_stacks.side_effect = self.client.exceptions.ClientError({'Error': {'Code': 'ValidationError', 'Message': 'Stack with id test-stack does not exist'}}, 'DescribeStacks')
        waiter = MagicMock()
        waiter.wait.side_effect = Exception()
        self.client.get_waiter.return_value = waiter
        with self.assertRaises(Exception):
            self.client.create_or_update(
                StackName='test-stack',
                TemplateBody='{}'
            )
        self.client.describe_stack_events.assert_called_with(StackName='test-stack')



