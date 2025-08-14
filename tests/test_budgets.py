import unittest
from unittest.mock import MagicMock, patch

from betterboto import budgets


class TestBudgets(unittest.TestCase):

    def test_make_better(self):
        mock_client = MagicMock()
        better_client = budgets.make_better(mock_client)
        self.assertTrue(hasattr(better_client, 'describe_budgets_single_page'))

    @patch('betterboto.budgets.slurp')
    def test_describe_budgets_single_page(self, slurp):
        mock_client = MagicMock()
        better_client = budgets.make_better(mock_client)

        better_client.describe_budgets_single_page(AccountId='123456789012')

        slurp.assert_called_once_with(
            'describe_budgets',
            mock_client.describe_budgets,
            'Budgets',
            next_token_name_in_response='NextToken',
            next_token_name_in_request='NextToken',
            AccountId='123456789012'
