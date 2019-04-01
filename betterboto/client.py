import boto3
from . import cloudformation
from . import servicecatalog


class BaseContextManager(object):
    
    def __init__(self):
        self.service_name = None
        self.client = None
        
    def make_better(self):
        if self.service_name == 'cloudformation':
            cloudformation.make_better(self.client)
        elif self.service_name == 'servicecatalog':
            servicecatalog.make_better(self.client)


class ClientContextManager(BaseContextManager):
    def __init__(self, service_name, **kwargs):
        super().__init__()
        self.service_name = service_name
        self.kwargs = kwargs

    def __enter__(self):
        self.client = boto3.client(
            self.service_name,
            **self.kwargs
        )
        self.make_better()
        return self.client

    def __exit__(self, *args, **kwargs):
        self.client = None


class CrossAccountClientContextManager(BaseContextManager):
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
            kwargs.update(kwargs)
        self.client = boto3.client(**kwargs)
        self.make_better()
        return self.client

    def __exit__(self, *args, **kwargs):
        self.client = None
