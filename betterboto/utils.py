import logging
import time

logger = logging.getLogger(__file__)


def slurp(
        name, func, response_to_concat,
        next_token_name_in_response='NextPageToken', next_token_name_in_request='PageToken',
        wait_between_pages=0,
        **kwargs
):
    logger.info("{}: {}".format(name, kwargs))
    all_responses = []
    while True:
        logger.info(f"searching, {next_token_name_in_request}: {kwargs.get(next_token_name_in_request, 'FirstPage')}")
        response = func(**kwargs)
        all_responses += response.get(response_to_concat)
        if response.get(next_token_name_in_response) is None:
            response[response_to_concat] = all_responses
            return response
        else:
            kwargs[next_token_name_in_request] = response.get(next_token_name_in_response)
        time.sleep(wait_between_pages)
