from . import cloudformation
from . import servicecatalog
from . import organizations
from boto3.session import Session


def make_better(service_name, client):
    if service_name == 'cloudformation':
        return cloudformation.make_better(client)
    elif service_name == 'servicecatalog':
        return servicecatalog.make_better(client)
    elif service_name == 'organizations':
        return organizations.make_better(client)
    return client


class ClientContextManager(object):
    """
    ClientContextManager allows you to use boto3 client as a python context manager.
    This allows you to perform the following::

        with ClientContextManager('cloudformation') as cloudformation_client:
            cloudformation_client.create_stack(**args)
    """
    def __init__(self, service_name, **kwargs):
        super().__init__()
        self.service_name = service_name
        self.kwargs = kwargs

    def __enter__(self):
        self.client = Session().client(
            self.service_name,
            **self.kwargs
        )
        self.client = make_better(self.service_name, self.client)
        return self.client

    def __exit__(self, *args, **kwargs):
        self.client = None


class MultiRegionClientContextManager(object):
    """
    MultiRegionClientContextManager allows you to use boto3 client as a python context manager for multiple regions.
    This allows you to perform the following::

        with MultiRegionClientContextManager('cloudformation', ['us-east-1','eu-west-1']) as cloudformation_clients:
            for region_name, cloudformation_client in cloudformation_clients.items():
                cloudformation_client.create_stack(**args)

    If you want to deploy to multiple regions at the same time then you should use Python Threads
    """
    def __init__(self, service_name, regions, **kwargs):
        super().__init__()
        self.service_name = service_name
        self.regions = regions
        self.clients = {}
        self.kwargs = kwargs

    def __enter__(self):
        for region in self.regions:
            c = make_better(
                self.service_name,
                Session().client(
                    self.service_name,
                    region_name=region,
                    **self.kwargs
                )
            )
            self.clients[region] = c
        return self.clients

    def __exit__(self, *args, **kwargs):
        self.clients = None


class CrossAccountClientContextManager(object):
    """
    CrossAccountClientContextManager allows you to use boto3 client as a python context manager for another account.
    This allows you to perform the following::

        with CrossAccountClientContextManager(
            'cloudformation',
            'arn:aws:iam::0123456789010:role/deployer',
            'deployment_account_session',
        ) as deployment_account_cloudformation:
            deployment_account_cloudformation.create_stack(**args)
    """
    def __init__(self, service_name, role_arn, role_session_name, **kwargs):
        super().__init__()
        self.service_name = service_name
        self.role_arn = role_arn
        self.role_session_name = role_session_name
        self.kwargs = kwargs

    def __enter__(self):
        sts = Session().client('sts')
        assumed_role_object = sts.assume_role(
            RoleArn=self.role_arn,
            RoleSessionName=self.role_session_name,
        )
        credentials = assumed_role_object['Credentials']
        kwargs = {
            "service_name": self.service_name,
            "aws_access_key_id": credentials['AccessKeyId'],
            "aws_secret_access_key": credentials['SecretAccessKey'],
            "aws_session_token": credentials['SessionToken'],
        }
        if self.kwargs is not None:
            kwargs.update(self.kwargs)
        self.client = Session().client(**kwargs)
        self.client = make_better(self.service_name, self.client)
        return self.client

    def __exit__(self, *args, **kwargs):
        self.client = None
