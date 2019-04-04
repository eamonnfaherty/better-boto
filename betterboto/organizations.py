import types
import logging

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


def convert_path_to_ou(self, ou):
    """
    This method accepts an ou and returns the path from the root account down to the ou

    :param self: organizations client
    :param ou: the account
    :return: the path from the root account down to the ou
    """
    response = self.list_roots()
    for r in response.get('Roots', []):
        r_id = r.get('Id')
        self.list_children(ParentId=r_id, ChildType='ORGANIZATIONAL_UNIT')


def make_better(client):
    client.convert_path_to_ou = types.MethodType(convert_path_to_ou, client)
    client.list_children_single_page = types.MethodType(list_children_single_page, client)
    client.list_children_nested = types.MethodType(list_children_nested, client)
    return client
