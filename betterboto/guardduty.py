import types
import logging

from .utils import slurp


logger = logging.getLogger(__file__)


def list_members_single_page(self, **kwargs):
    """
    This will continue to call list_members until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_members does.

    :param self: guardduty client
    :param kwargs: these are passed onto the list_members method call
    :return: guardduty_client.list_members.response
    """
    return slurp(
        'list_members',
        self.list_members,
        'Members',
        **kwargs
    )


def make_better(client):
    client.list_members_single_page = types.MethodType(list_members_single_page, client)
    return client
