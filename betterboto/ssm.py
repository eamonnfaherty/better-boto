import types
import logging
import time

logger = logging.getLogger(__file__)

put_parameter_and_wait_max_retries = 10


def put_parameter_and_wait(self, Name, **kwargs):
    """
    This will call put_parameter and ensure it has been successfully put by checking it

    :param self: ssm client
    :param Name: The fully qualified name of the parameter that you want to add to the system
    :param kwargs: These args are passed through to ssm.put_parameter
    :return: ssm.get_parameter.response
    """
    new_version = self.put_parameter(Name=Name, **kwargs).get('Version')
    count = 0
    current_parameter = {
        "Parameter": {
            "Version": -1
        }
    }
    while current_parameter.get('Parameter').get('Version') < new_version:
        count += 1
        if count > put_parameter_and_wait_max_retries:
            raise Exception(f"Putting and waiting for param {Name} failed")
        time.sleep(1)
        if new_version == 1:
            try:
                current_parameter = self.get_parameter(Name=Name)
            except self.exceptions.ParameterNotFound:
                pass
        else:
            current_parameter = self.get_parameter(Name=Name)
    return current_parameter


def make_better(client):
    client.put_parameter_and_wait = types.MethodType(put_parameter_and_wait, client)
    return client
