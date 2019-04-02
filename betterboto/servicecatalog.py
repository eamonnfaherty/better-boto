import types
import logging

from .utils import slurp


logger = logging.getLogger(__file__)


def search_products_as_admin_single_page(self, **kwargs):
    return slurp(
        'search_products_as_admin',
        self.search_products_as_admin,
        'ProductViewDetails',
        **kwargs
    )


def list_portfolios_single_page(self, **kwargs):
    return slurp(
        'list_portfolios',
        self.list_portfolios,
        'PortfolioDetails',
        **kwargs
    )


def list_provisioning_artifacts_single_page(self, **kwargs):
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
