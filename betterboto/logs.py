import types
import logging

from .utils import slurp


logger = logging.getLogger(__file__)


def get_log_events_single_page(self, **kwargs):
    """
    This will continue to call get_log_events until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as get_log_events does.

    :param self: logs client
    :param kwargs: these are passed onto the get_log_events method call
    :return: logs.get_log_events.response
    """
    return slurp(
        'get_log_events',
        self.get_log_events,
        'events',
        next_token_name_in_response='nextForwardToken', next_token_name_in_request='nextToken',
        **kwargs
    )


def make_better(client):
    client.get_log_events_single_page = types.MethodType(get_log_events_single_page, client)
    return client
