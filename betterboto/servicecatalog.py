import types
import logging

from .utils import slurp


logger = logging.getLogger(__file__)


def search_products_as_admin_single_page(self, **kwargs):
    """
    This will continue to call search_products_as_admin until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as search_products_as_admin does.

    :param self: servicecatalog client
    :param kwargs: these are passed onto the search_products_as_admin method call
    :return: servicecatalog_client.search_products_as_admin.response
    """
    return slurp(
        'search_products_as_admin',
        self.search_products_as_admin,
        'ProductViewDetails',
        **kwargs
    )


def list_portfolios_single_page(self, **kwargs):
    """
    This will continue to call list_portfolios until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_portfolios does.

    :param self: servicecatalog client
    :param kwargs: these are passed onto the list_portfolios method call
    :return: servicecatalog_client.list_portfolios.response
    """
    return slurp(
        'list_portfolios',
        self.list_portfolios,
        'PortfolioDetails',
        **kwargs
    )


def list_provisioning_artifacts_single_page(self, **kwargs):
    """
    This will continue to call list_provisioning_artifacts until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_provisioning_artifacts does.

    :param self: servicecatalog client
    :param kwargs: these are passed onto the list_provisioning_artifacts method call
    :return: servicecatalog_client.list_provisioning_artifacts.response
    """
    return slurp(
        'list_provisioning_artifacts',
        self.list_provisioning_artifacts,
        'ProvisioningArtifactDetails',
        **kwargs
    )


def make_better(client):
    client.search_products_as_admin_single_page = types.MethodType(search_products_as_admin_single_page, client)
    client.list_portfolios_single_page = types.MethodType(list_portfolios_single_page, client)
    client.list_provisioning_artifacts_single_page = types.MethodType(list_provisioning_artifacts_single_page, client)
    return client
