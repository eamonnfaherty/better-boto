import unittest

from betterboto.utils import slurp


def mock_paginated_function(**kwargs):
    if kwargs.get('PageToken') == 'second':
        return {
            'things': [
                {'name': 'thing_two'},
            ],
        }
    return {
        'things': [
            {'name': 'thing_one'},
        ],
        'NextPageToken': 'second'
    }


class TestUtils(unittest.TestCase):

    def test_slurp(self):
        all_things = slurp('testing', mock_paginated_function, 'things')
        self.assertEqual(2, len(all_things['things']))
        self.assertIsNone(all_things.get('NextPageToken'))

