import types
import logging
from copy import copy

from .utils import slurp


logger = logging.getLogger(__file__)


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
    response = self.list_organizational_units_for_parent(ParentId=parent_id)
    for organizational_unit in response.get('OrganizationalUnits', []):
        logger.info("Described: {}".format(organizational_unit))
        if organizational_unit.get('Name') == part_looking_for:
            logger.info('Found: {}'.format(part_looking_for))
            if len(parts) == 0:
                logger.info('Finished looking for a match: {}'.format(organizational_unit))
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
            response = self.list_organizational_units_for_parent(ParentId=child_id)
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
    client.find_match = types.MethodType(find_match, client)
    client.build_ou_tree_branch = types.MethodType(build_ou_tree_branch, client)
    client.convert_path_to_ou = types.MethodType(convert_path_to_ou, client)
    client.list_children_single_page = types.MethodType(list_children_single_page, client)
    client.list_children_nested = types.MethodType(list_children_nested, client)
    return client
