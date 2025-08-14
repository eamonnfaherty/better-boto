import unittest
import boto3
from moto import mock_aws
from betterboto import cloudformation


@mock_aws
class TestCloudformation(unittest.TestCase):

    def setUp(self):
        self.client = boto3.client('cloudformation', region_name='eu-west-1')
        cloudformation.make_better(self.client)

    def test_get_hash_for_template(self):
        hash = cloudformation.get_hash_for_template('template_body')
        self.assertEqual(hash, 'a553b064f79b3c7b093a75f955534616')

    @mock_aws
    def test_create_or_update_create(self):
        self.client.create_or_update(
            StackName='test-stack',
            TemplateBody='{"AWSTemplateFormatVersion": "2010-09-09"}'
        )
        response = self.client.describe_stacks(StackName='test-stack')
        self.assertEqual(len(response['Stacks']), 1)
        self.assertEqual(response['Stacks'][0]['StackName'], 'test-stack')
        self.assertEqual(response['Stacks'][0]['StackStatus'], 'CREATE_COMPLETE')

    def test_create_or_update_update(self):
        self.client.create_stack(
            StackName='test-stack',
            TemplateBody='{"AWSTemplateFormatVersion": "2010-09-09"}'
        )
        self.client.create_or_update(
            StackName='test-stack',
            TemplateBody='{"AWSTemplateFormatVersion": "2010-09-09", "Description": "new"}'
        )
        response = self.client.describe_stacks(StackName='test-stack')
        self.assertEqual(len(response['Stacks']), 1)
        self.assertEqual(response['Stacks'][0]['StackName'], 'test-stack')
        self.assertEqual(response['Stacks'][0]['StackStatus'], 'UPDATE_COMPLETE')

    def test_create_or_update_rollback_delete(self):
        # Create a stack that will fail and rollback
        with self.assertRaises(Exception):
            self.client.create_or_update(
                StackName='test-stack',
                TemplateBody='{"AWSTemplateFormatVersion": "2010-09-09", "Resources": {"A": "B"}}'
            )

        # Now try to create it again with the delete rollback flag
        self.client.create_or_update(
            StackName='test-stack',
            TemplateBody='{"AWSTemplateFormatVersion": "2010-09-09"}',
            ShouldDeleteRollbackComplete=True
        )
        response = self.client.describe_stacks(StackName='test-stack')
        self.assertEqual(len(response['Stacks']), 1)
        self.assertEqual(response['Stacks'][0]['StackName'], 'test-stack')
        self.assertEqual(response['Stacks'][0]['StackStatus'], 'CREATE_COMPLETE')

    def test_ensure_deleted(self):
        self.client.create_stack(
            StackName='test-stack',
            TemplateBody='{"AWSTemplateFormatVersion": "2010-09-09"}'
        )
        self.client.ensure_deleted(StackName='test-stack')
        with self.assertRaises(self.client.exceptions.ClientError):
            self.client.describe_stacks(StackName='test-stack')

    def test_ensure_deleted_does_not_exist(self):
        self.client.ensure_deleted(StackName='test-stack')

    def test_list_stacks(self):
        self.client.create_stack(
            StackName='test-stack-1',
            TemplateBody='{"AWSTemplateFormatVersion": "2010-09-09"}'
        )
        self.client.create_stack(
            StackName='test-stack-2',
            TemplateBody='{"AWSTemplateFormatVersion": "2010-09-09"}'
        )
        response = self.client.list_stacks_single_page()
        self.assertEqual(len(response['Stacks']), 2)

    def test_describe_stacks_single_page(self):
        self.client.create_stack(
            StackName='test-stack-1',
            TemplateBody='{"AWSTemplateFormatVersion": "2010-09-09"}'
        )
        self.client.create_stack(
            StackName='test-stack-2',
            TemplateBody='{"AWSTemplateFormatVersion": "2010-09-09"}'
        )
        response = self.client.describe_stacks_single_page()
        self.assertEqual(len(response['Stacks']), 2)

    def test_create_or_update_no_changes(self):
        self.client.create_stack(
            StackName='test-stack',
            TemplateBody='{"AWSTemplateFormatVersion": "2010-09-09"}'
        )
        self.client.create_or_update(
            StackName='test-stack',
            TemplateBody='{"AWSTemplateFormatVersion": "2010-09-09"}'
        )

