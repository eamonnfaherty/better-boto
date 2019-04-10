import types
import logging
import hashlib
import botocore
import yaml

logger = logging.getLogger(__file__)


def get_hash_for_template(template):
    hasher = hashlib.md5()
    hasher.update(str.encode(template))
    return "{}{}".format('a', hasher.hexdigest())


def create_or_update(self, **kwargs):
    """
    For the given template and stack name, this method will create a stack if it doesnt already exist otherwise it will
    generate a changeset and then execute it.  This method will wait for the operation to complete before returning and
    in the instance of an error it will print out the stack events to help you debug more easily.

    :param self: cloudformation client
    :param kwargs: these are passed onto the create_stack and create_change_set method calls
    :return: None
    """
    stack_name = kwargs.get('StackName')
    logger.info('Creating or updating: {}'.format(stack_name))

    is_first_run = True
    try:
        self.describe_stacks(
            StackName=stack_name
        )
        is_first_run = False
    except self.exceptions.ClientError as e:
        if "Stack with id {} does not exist".format(stack_name) not in str(e):
            raise e

    if is_first_run:
        logger.info('Creating: {}'.format(stack_name))
        self.create_stack(**kwargs)
        waiter = self.get_waiter('stack_create_complete')
        try:
            waiter.wait(StackName=stack_name)
        except Exception as e:
            response = self.describe_stack_events(StackName=stack_name)
            for stack_event in response.get('StackEvents'):
                logger.error('{}: {}'.format(
                    stack_event.get('ResourceStatus'),
                    stack_event.get('ResourceStatusReason'),
                ))
            raise e
    else:
        logger.info('Updating: {}'.format(stack_name))
        change_set_name = get_hash_for_template(kwargs.get('TemplateBody'))
        self.create_change_set(
            ChangeSetName=change_set_name,
            ChangeSetType="UPDATE",
            **kwargs,
        )
        change_set_create_complete_waiter = self.get_waiter('change_set_create_complete')
        try:
            change_set_create_complete_waiter.wait(
                ChangeSetName=change_set_name,
                StackName=stack_name,
            )
        except botocore.exceptions.WaiterError as e:
            if "Waiter ChangeSetCreateComplete failed: Waiter encountered a terminal failure state" not in str(e):
                raise e

        logger.info('Describing change set: {}'.format(stack_name))
        response = self.describe_change_set(
            ChangeSetName=change_set_name,
            StackName=stack_name
        )
        change_set = response.get('Changes')
        logger.info('Changes:' + yaml.safe_dump(change_set))
        if len(change_set) > 0:
            logger.info('Executing change set: {}'.format(stack_name))
            self.execute_change_set(
                ChangeSetName=change_set_name,
                StackName=stack_name,
            )
            logger.info('Waiting for change set to execute: {}'.format(stack_name))
            waiter = self.get_waiter('stack_update_complete')
            try:
                waiter.wait(StackName=stack_name)
            except Exception as e:
                response = self.describe_stack_events(StackName=stack_name)
                for stack_event in response.get('StackEvents'):
                    logger.error('{}: {}'.format(
                        stack_event.get('ResourceStatus'),
                        stack_event.get('ResourceStatusReason'),
                    ))
                raise e
            logger.info('Finished stack: {}'.format(stack_name))
        else:
            logger.info('No changes to build for stack: {}'.format(stack_name))
            logger.info('Finished stack: {}'.format(stack_name))


def make_better(client):
    client.create_or_update = types.MethodType(create_or_update, client)
    return client
