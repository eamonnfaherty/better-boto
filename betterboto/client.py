import boto3
from . import cloudformation
from . import servicecatalog
from . import organizations


def make_better(service_name, client):
    if service_name == 'cloudformation':
        return cloudformation.make_better(client)
    elif service_name == 'servicecatalog':
        return servicecatalog.make_better(client)
    elif service_name == 'organizations':
        return organizations.make_better(client)
    return client


class ClientContextManager(object):
    def __init__(self, service_name, **kwargs):
        super().__init__()
        self.service_name = service_name
        self.kwargs = kwargs

    def __enter__(self):
        self.client = boto3.client(
            self.service_name,
            **self.kwargs
        )
        self.client = make_better(self.service_name, self.client)
        return self.client

    def __exit__(self, *args, **kwargs):
        self.client = None


class MultiRegionClientContextManager(object):
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
                boto3.client(
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
    def __init__(self, service_name, role_arn, role_session_name, **kwargs):
        super().__init__()
        self.service_name = service_name
        self.role_arn = role_arn
        self.role_session_name = role_session_name
        self.kwargs = kwargs

    def __enter__(self):
        sts = boto3.client('sts')
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
        self.client = boto3.client(**kwargs)
        self.client = make_better(self.service_name, self.client)
        return self.client

    def __exit__(self, *args, **kwargs):
        self.client = None
