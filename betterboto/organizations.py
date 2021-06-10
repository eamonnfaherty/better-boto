import types
import logging

from .utils import slurp


logger = logging.getLogger(__file__)


def list_targets_for_policy_single_page(self, **kwargs):
    """
    This will continue to call list_targets_for_policy until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_targets_for_policy does.

    :param self: organizations client
    :param kwargs: these are passed onto the list_targets_for_policy method call
    :return: organizations_client.list_targets_for_policy.response
    """
    return slurp(
        'list_targets_for_policy',
        self.list_targets_for_policy,
        'Targets',
        'NextToken', 'NextToken',
        **kwargs
    )


def list_accounts_single_page(self, **kwargs):
    """
    This will continue to call list_accounts until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_accounts does.

    :param self: organizations client
    :param kwargs: these are passed onto the list_accounts method call
    :return: organizations_client.list_accounts.response
    """
    return slurp(
        'list_accounts',
        self.list_accounts,
        'Accounts',
        'NextToken', 'NextToken',
        **kwargs
    )


def list_children_single_page(self, **kwargs):
    """
    This will continue to call list_children until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_children does.

    :param self: organizations client
    :param kwargs: these are passed onto the list_children method call
    :return: organizations_client.list_children.response
    """
    return slurp(
        'list_children',
        self.list_children,
        'Children',
        'NextToken', 'NextToken',
        **kwargs
    )


def list_policies_single_page(self, **kwargs):
    """
    This will continue to call list_policies until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_policies does.

    :param self: organizations client
    :param kwargs: these are passed onto the list_policies method call
    :return: organizations_client.list_policies.response
    """
    return slurp(
        'list_policies',
        self.list_policies,
        'Policies',
        'NextToken', 'NextToken',
        **kwargs
    )


def list_policies_for_target_single_page(self, **kwargs):
    """
    This will continue to call list_policies_for_target until there are no more pages left to retrieve.  It will return
    the aggregated response in the same structure as list_policies_for_target does.

    :param self: organizations client
    :param kwargs: these are passed onto the list_policies_for_target method call
    :return: organizations_client.list_policies_for_target.response
    """
    return slurp(
        'list_policies_for_target',
        self.list_policies_for_target,
        'Policies',
        'NextToken', 'NextToken',
        **kwargs
    )


def list_organizational_units_for_parent_single_page(self, **kwargs):
    """
    This will continue to call list_organizational_units_for_parent until there are no more pages left to retrieve.
    It will return the aggregated response in the same structure as list_organizational_units_for_parent does.

    :param self: organizations client
    :param kwargs: these are passed onto the list_organizational_units_for_parent method call
    :return: organizations_client.list_organizational_units_for_parent.response
    """
    return slurp(
        'list_organizational_units_for_parent',
        self.list_organizational_units_for_parent,
        'OrganizationalUnits',
        'NextToken', 'NextToken',
        **kwargs
    )


def list_roots_single_page(self, **kwargs):
    """
    This will continue to call list_roots until there are no more pages left to retrieve.
    It will return the aggregated response in the same structure as list_roots does.

    :param self: organizations client
    :param kwargs: these are passed onto the list_roots method call
    :return: organizations_client.list_roots.response
    """
    return slurp(
        'list_roots',
        self.list_roots,
        'Roots',
        'NextToken', 'NextToken',
        **kwargs
    )


def list_parents_single_page(self, **kwargs):
    """
    This will continue to call list_parents until there are no more pages left to retrieve.
    It will return the aggregated response in the same structure as list_parents does.

    :param self: organizations client
    :param kwargs: these are passed onto the list_parents method call
    :return: organizations_client.list_parents.response
    """
    return slurp(
        'list_parents',
        self.list_parents,
        'Parents',
        'NextToken', 'NextToken',
        **kwargs
    )


def list_delegated_administrators_single_page(self, **kwargs):
    """
    This will continue to call list_delegated_administrators until there are no more pages left to retrieve.
    It will return the aggregated response in the same structure as list_delegated_administrators does.

    :param self: organizations client
    :param kwargs: these are passed onto the list_delegated_administrators method call
    :return: organizations_client.list_delegated_administrators.response
    """
    return slurp(
        'list_delegated_administrators',
        self.list_delegated_administrators,
        'DelegatedAdministrators',
        'NextToken', 'NextToken',
        **kwargs
    )


def list_delegated_services_for_account_single_page(self, **kwargs):
    """
    This will continue to call list_delegated_services_for_account until there are no more pages left to retrieve.
    It will return the aggregated response in the same structure as list_delegated_services_for_account does.

    :param self: organizations client
    :param kwargs: these are passed onto the list_delegated_services_for_account method call
    :return: organizations_client.list_delegated_services_for_account.response
    """
    return slurp(
        'list_delegated_services_for_account',
        self.list_delegated_services_for_account,
        'DelegatedServices',
        'NextToken', 'NextToken',
        **kwargs
    )


def list_children_nested(self, **kwargs):
    """
    This method will return a list of all children (either ACCOUNT or ORGANIZATIONAL_UNIT) for the given ParentId.  It
    includes children, grandchildren lower levels of nesting.

    :param self: organizations client
    :param kwargs: these are passed onto the list_children method call
    :return: list of children in the structure of [{'Id': "0123456789010"}, {'Id': "1009876543210"}]
    """
    child_type = kwargs.get('ChildType')
    parent_id = kwargs.get('ParentId')

    if child_type == 'ACCOUNT':
        response = self.list_children_single_page(ParentId=parent_id, ChildType='ACCOUNT')
        my_account_children = response.get('Children')

        response = self.list_children_single_page(ParentId=parent_id, ChildType='ORGANIZATIONAL_UNIT')
        my_org_children = response.get('Children')
        for my_org_child in my_org_children:
            my_account_children += self.list_children_nested(ParentId=my_org_child.get('Id'), ChildType='ACCOUNT')

        return my_account_children

    elif child_type == 'ORGANIZATIONAL_UNIT':
        my_account_children = [kwargs.get('ParentId')]

        response = self.list_children_single_page(ParentId=parent_id, ChildType='ORGANIZATIONAL_UNIT')
        my_org_children = response.get('Children')
        for my_org_child in my_org_children:
            my_account_children += self.list_children_nested(ParentId=my_org_child.get('Id'), ChildType='ORGANIZATIONAL_UNIT')

        return my_account_children

    else:
        raise Exception('Unsupported ChildType: {}'.format(child_type))


def build_ou_tree_branch(self, parent_id):
    logger.info("Building ou tree for: {}".format(parent_id))
    parent_unit = self.describe_organizational_unit(OrganizationalUnitId=parent_id)
    parent_unit['children'] = {}
    response = self.list_children_single_page(ParentId=parent_id, ChildType='ORGANIZATIONAL_UNIT')
    for child in response.get('Children', []):
        child_unit = self.build_ou_tree_branch(child.get('Id'))
        parent_unit['children'][child_unit.get('Name')] = child_unit
    return parent_unit


def find_match(self, parts, parent_id):
    part_looking_for = parts.pop()
    logger.info('Now looking for: {} in: {}'.format(part_looking_for, parent_id))
    response = self.list_organizational_units_for_parent_single_page(ParentId=parent_id)
    for organizational_unit in response.get('OrganizationalUnits', []):
        if organizational_unit.get('Name') == part_looking_for:
            if len(parts) == 0:
                return organizational_unit.get('Id')
            else:
                return self.find_match(parts, organizational_unit.get('Id'))


def convert_path_to_ou(self, path):
    """
    This method accepts a path and returns the ou.
    This raises an exception when converting / and you have more than one root

    :param self: organizations client
    :param path: organizations path
    :return: the ou of the path specified
    """
    logger.info("Converting: {}".format(path))

    if path == "/":
        response = self.list_roots()
        assert len(response.get('Roots')) == 1, "You have {} roots".format(len(response.get('Roots')))
        root = response.get('Roots')[0]
        return root.get('Id')
    else:
        parts = path.split("/")
        parts.reverse()
        parts.pop()
        part_looking_for = parts.pop()
        response = self.list_roots()
        for root in response.get('Roots', []):
            child_id = root.get('Id')
            response = self.list_organizational_units_for_parent_single_page(ParentId=child_id)
            for organizational_unit in response.get('OrganizationalUnits', []):
                if organizational_unit.get('Name') == part_looking_for:
                    logger.debug('Found {}: in {}'.format(part_looking_for, organizational_unit.get('Id')))
                    if len(parts) > 0:
                        return self.find_match(parts, organizational_unit.get('Id'))
                    else:
                        logger.debug('Finished looking: {}'.format(organizational_unit))
                        return organizational_unit.get('Id')
    raise Exception("not found")


def make_better(client):
    client.list_accounts_single_page = types.MethodType(list_accounts_single_page, client)
    client.find_match = types.MethodType(find_match, client)
    client.build_ou_tree_branch = types.MethodType(build_ou_tree_branch, client)
    client.convert_path_to_ou = types.MethodType(convert_path_to_ou, client)
    client.list_children_single_page = types.MethodType(list_children_single_page, client)
    client.list_children_nested = types.MethodType(list_children_nested, client)
    client.list_policies_single_page = types.MethodType(list_policies_single_page, client)
    client.list_policies_for_target_single_page = types.MethodType(list_policies_for_target_single_page, client)
    client.list_organizational_units_for_parent_single_page = types.MethodType(list_organizational_units_for_parent_single_page, client)
    client.list_roots_single_page = types.MethodType(list_roots_single_page, client)
    client.list_parents_single_page = types.MethodType(list_parents_single_page, client)
    client.list_delegated_administrators_single_page = types.MethodType(list_delegated_administrators_single_page, client)
    client.list_delegated_services_for_account_single_page = types.MethodType(list_delegated_services_for_account_single_page, client)
    client.list_targets_for_policy_single_page = types.MethodType(list_targets_for_policy_single_page, client)
    return client
