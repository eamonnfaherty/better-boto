import types
import logging

from .utils import slurp


logger = logging.getLogger(__file__)


def describe_budgets_single_page(self, **kwargs):
    """
    This will continue to call describe_budgets until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as describe_budgets does.

    :param self: budgets client
    :param kwargs: these are passed onto the describe_budgets method call
    :return: budgets.describe_budgets.response
    """
    return slurp(
        'describe_budgets',
        self.describe_budgets,
        'Budgets',
        next_token_name_in_response='NextToken', next_token_name_in_request="NextToken",
        **kwargs
    )


def make_better(client):
    client.describe_budgets_single_page = types.MethodType(describe_budgets_single_page, client)
    return client
