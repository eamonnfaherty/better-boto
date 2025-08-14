import unittest
from unittest.mock import MagicMock, patch, call

from betterboto import utils


class TestUtils(unittest.TestCase):

    @patch('time.sleep')
    def test_slurp_single_page(self, time_sleep):
        mock_func = MagicMock()
        mock_func.return_value = {
            'Things': ['thing1', 'thing2'],
        }

        response = utils.slurp(
            'get_things', mock_func, 'Things',
            thing_id='thing123'
        )

        self.assertEqual(len(response['Things']), 2)
        self.assertEqual(response['Things'][0], 'thing1')
        mock_func.assert_called_once_with(thing_id='thing123')
        time_sleep.assert_not_called()

    @patch('time.sleep')
    def test_slurp_multiple_pages(self, time_sleep):
        mock_func = MagicMock()
        mock_func.side_effect = [
            {
                'Things': ['thing1', 'thing2'],
                'NextPageToken': 'token1',
            },
            {
                'Things': ['thing3', 'thing4'],
            }
        ]

        response = utils.slurp(
            'get_things', mock_func, 'Things',
            wait_between_pages=5,
            thing_id='thing123'
        )

        self.assertEqual(len(response['Things']), 4)
        self.assertEqual(response['Things'][2], 'thing3')
        self.assertEqual(mock_func.call_count, 2)
        mock_func.assert_has_calls([
            call(thing_id='thing123'),
            call(thing_id='thing123', PageToken='token1')
        ])
        time_sleep.assert_called_once_with(5)

    @patch('time.sleep')
    def test_slurp_custom_tokens(self, time_sleep):
        mock_func = MagicMock()
        mock_func.side_effect = [
            {
                'Items': ['item1'],
                'CustomOutToken': 'token123',
            },
            {
                'Items': ['item2'],
            }
        ]

        response = utils.slurp(
            'get_items', mock_func, 'Items',
            next_token_name_in_response='CustomOutToken',
            next_token_name_in_request='CustomInToken'
        )

        self.assertEqual(len(response['Items']), 2)
