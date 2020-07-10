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


def list_principals_for_portfolio_single_page(self, **kwargs):
    """
    This will continue to call list_principals_for_portfolio until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_principals_for_portfolio does.

    :param self: servicecatalog client
    :param kwargs: these are passed onto the list_principals_for_portfolio method call
    :return: servicecatalog_client.list_principals_for_portfolio.response
    """
    return slurp(
        'list_principals_for_portfolio',
        self.list_principals_for_portfolio,
        'Principals',
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


def list_portfolios_for_product_single_page(self, **kwargs):
    """
    This will continue to call list_portfolios_for_product until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_portfolios_for_product does.

    :param self: servicecatalog client
    :param kwargs: these are passed onto the list_portfolios_for_product method call
    :return: servicecatalog_client.list_portfolios_for_product.response
    """
    return slurp(
        'list_portfolios_for_product',
        self.list_portfolios_for_product,
        'PortfolioDetails',
        **kwargs
    )


def list_provisioned_product_plans_single_page(self, **kwargs):
    """
    This will continue to call list_provisioned_product_plans until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_provisioned_product_plans does.

    :param self: servicecatalog client
    :param kwargs: these are passed onto the list_provisioned_product_plans method call
    :return: servicecatalog_client.list_provisioned_product_plans.response
    """
    return slurp(
        'list_provisioned_product_plans',
        self.list_provisioned_product_plans,
        'ProvisionedProductPlans',
        **kwargs
    )


def search_provisioned_products_single_page(self, **kwargs):
    """
    This will continue to call search_provisioned_products until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as search_provisioned_products does.

    :param self: servicecatalog client
    :param kwargs: these are passed onto the search_provisioned_products method call
    :return: servicecatalog_client.search_provisioned_products.response
    """
    return slurp(
        'search_provisioned_products',
        self.search_provisioned_products,
        'ProvisionedProducts',
        **kwargs
    )


def list_launch_paths_single_page(self, **kwargs):
    """
    This will continue to call list_launch_paths until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_launch_paths does.

    :param self: servicecatalog client
    :param kwargs: these are passed onto the list_launch_paths method call
    :return: servicecatalog_client.list_launch_paths.response
    """
    return slurp(
        'list_launch_paths',
        self.list_launch_paths,
        'LaunchPathSummaries',
        **kwargs
    )


def list_accepted_portfolio_shares_single_page(self, **kwargs):
    """
    This will continue to call list_accepted_portfolio_shares until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_accepted_portfolio_shares does.

    :param self: servicecatalog client
    :param kwargs: these are passed onto the list_accepted_portfolio_shares method call
    :return: servicecatalog_client.list_accepted_portfolio_shares.response
    """
    return slurp(
        'list_accepted_portfolio_shares',
        self.list_accepted_portfolio_shares,
        'PortfolioDetails',
        **kwargs
    )


def scan_provisioned_products_single_page(self, **kwargs):
    """
    This will continue to call scan_provisioned_products until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as scan_provisioned_products does.

    :param self: servicecatalog client
    :param kwargs: these are passed onto the scan_provisioned_products method call
    :return: servicecatalog_client.scan_provisioned_products.response
    """
    return slurp(
        'scan_provisioned_products',
        self.scan_provisioned_products,
        'ProvisionedProducts',
        **kwargs
    )


def list_portfolio_access_single_page(self, **kwargs):
    """
    This will continue to call list_portfolio_access until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_portfolio_access does.

    :param self: servicecatalog client
    :param kwargs: these are passed onto the list_portfolio_access method call
    :return: servicecatalog_client.list_portfolio_access.response
    """
    return slurp(
        'list_portfolio_access',
        self.list_portfolio_access,
        'AccountIds',
        **kwargs
    )


def make_better(client):
    client.search_products_as_admin_single_page = types.MethodType(search_products_as_admin_single_page, client)
    client.list_portfolios_single_page = types.MethodType(list_portfolios_single_page, client)
    client.list_provisioning_artifacts_single_page = types.MethodType(list_provisioning_artifacts_single_page, client)
    client.list_portfolios_for_product_single_page = types.MethodType(list_portfolios_for_product_single_page, client)
    client.list_provisioned_product_plans_single_page = types.MethodType(list_provisioned_product_plans_single_page,
                                                                         client)
    client.search_provisioned_products_single_page = types.MethodType(search_provisioned_products_single_page, client)
    client.list_launch_paths_single_page = types.MethodType(list_launch_paths_single_page, client)
    client.list_principals_for_portfolio_single_page = types.MethodType(list_principals_for_portfolio_single_page,
                                                                        client)
    client.list_accepted_portfolio_shares_single_page = types.MethodType(list_accepted_portfolio_shares_single_page,
                                                                         client)
    client.scan_provisioned_products_single_page = types.MethodType(scan_provisioned_products_single_page, client)
    client.list_portfolio_access_single_page = types.MethodType(list_portfolio_access_single_page, client)
    return client
