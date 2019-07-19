import types
import logging

from .utils import slurp


logger = logging.getLogger(__file__)


def list_branches_single_page(self, **kwargs):
    """
    This will continue to call list_branches until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_branches does.

    :param self: codecommit client
    :param kwargs: these are passed onto the list_branches method call
    :return: codecommit_client.list_branches.response
    """
    return slurp(
        'list_branches',
        self.list_branches,
        'branches',
        'nextToken',
        'nextToken',
        **kwargs
    )


def make_better(client):
    client.list_branches_single_page = types.MethodType(list_branches_single_page, client)
    return client
