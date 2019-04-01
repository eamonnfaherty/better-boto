# What is this?

This is a util package to help making boto3 more enjoyable.

Below is a list of the use cases:

### client
instead of doing:
```python
import boto3

client = boto3.client('cloudformation')
```
You can do
```python
import betterboto

with betterboto.ClientContextManager('cloudformation') as client:
    client.create_stack
```

Instead of doing:
```python
import boto3 

role_arn = 'arn:aws:iam::123456789010:role/super-role'
role_session_name = 'super-role'

sts = boto3.client('sts')
assumed_role_object = sts.assume_role(
    RoleArn=role_arn,
    RoleSessionName=role_session_name,
)
credentials = assumed_role_object['Credentials']
kwargs = {
    "aws_access_key_id": credentials['AccessKeyId'],
    "aws_secret_access_key": credentials['SecretAccessKey'],
    "aws_session_token": credentials['SessionToken'],
}
client = boto3.client(
    'cloudformation',
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken'],
)
```
You can do
```python
import betterboto

with betterboto.CrossAccountClientContextManager('cloudformation', 'arn:aws:iam::123456789010:role/super-role', 'super-role') as client:
    client.create_stack
```

### cloudformation

instead of 