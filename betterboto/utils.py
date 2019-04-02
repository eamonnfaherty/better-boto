import logging

logger = logging.getLogger(__file__)


def slurp(name, func, response_to_concat, **kwargs):
    logger.info("{}: {}".format(name, kwargs))
    all_responses = []
    while True:
        logger.info("searching, PageToken: {}".format(kwargs.get('PageToken', 'FirstPage')))
        response = func(**kwargs)
        all_responses += response.get(response_to_concat)
        if response.get('NextPageToken') is None:
            response[response_to_concat] = all_responses
            return response
        else:
            kwargs['PageToken'] = response.get('NextPageToken')
