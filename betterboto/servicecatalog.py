import types
import logging


logger = logging.getLogger(__file__)


def search_products_as_admin_single_page(self, **kwargs):
    logger.info("search_products_as_admin: {}".format(kwargs))
    all_product_view_details = []
    while True:
        logger.info("searching, PageToken: {}".format(kwargs.get('PageToken', 'FirstPage')))
        response = self.search_products_as_admin(**kwargs)
        all_product_view_details += response.get('ProductViewDetails')
        if response.get('NextPageToken') is None:
            response['ProductViewDetails'] = all_product_view_details
            return response
        else:
            kwargs['PageToken'] = response.get('NextPageToken')


def make_better(client):
    client.search_products_as_admin_single_page = types.MethodType(search_products_as_admin_single_page, client)
    return client
