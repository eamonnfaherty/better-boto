import logging
import time
import copy

logger = logging.getLogger(__file__)


def slurp(
        name, func, response_to_concat,
        next_token_name_in_response='NextPageToken', next_token_name_in_request='PageToken',
        wait_between_pages=0,
        **kwargs
):
    kwargs_to_use = copy.deepcopy(kwargs)
    logging_prefix = ''
    if kwargs_to_use.get('logging_prefix'):
        logging_prefix = kwargs_to_use.get('logging_prefix')
        del kwargs_to_use['logging_prefix']

    logger.info("{}{}: {}".format(logging_prefix, name, kwargs_to_use))
    all_responses = []
    while True:
        logger.info(f"{logging_prefix}{name} searching, {next_token_name_in_request}: {kwargs_to_use.get(next_token_name_in_request, 'FirstPage')}")
        response = func(**kwargs_to_use)
        all_responses += response.get(response_to_concat)
        if response.get(next_token_name_in_response) is None:
            response[response_to_concat] = all_responses
            return response
        else:
            kwargs_to_use[next_token_name_in_request] = response.get(next_token_name_in_response)
        time.sleep(wait_between_pages)
