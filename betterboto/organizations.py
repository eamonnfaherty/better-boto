import types
import logging

from .utils import slurp


logger = logging.getLogger(__file__)


def list_children_single_page(self, **kwargs):
    return slurp(
        'list_children',
        self.list_children,
        'Children',
        **kwargs
    )


def list_children_nested(self, **kwargs):
    child_type = kwargs.get('ChildType')
    parent_id = kwargs.get('ParentId')

    if child_type == 'ACCOUNT':
        response = self.list_children_single_page(ParentId=parent_id, ChildType='ACCOUNT')
        my_account_children = response.get('Children')

        response = self.list_children_single_page(ParentId=parent_id, ChildType='ORGANIZATIONAL_UNIT')
        my_org_children = response.get('Children')
        for my_org_child in my_org_children:
            response = self.list_children_nested(ParentId=my_org_child.get('Id'), ChildType='ACCOUNT')
            my_account_children += response.get('Children')

        return my_account_children

    elif child_type == 'ORGANIZATIONAL_UNIT':
        my_account_children = [kwargs.get('ParentId')]

        response = self.list_children_single_page(ParentId=parent_id, ChildType='ORGANIZATIONAL_UNIT')
        my_org_children = response.get('Children')
        for my_org_child in my_org_children:
            response = self.list_children_nested(ParentId=my_org_child.get('Id'), ChildType='ORGANIZATIONAL_UNIT')
            my_account_children += response.get('Children')

        return my_account_children

    else:
        raise Exception('Unsupported ChildType: {}'.format(child_type))


def make_better(client):
    client.list_children_single_page = types.MethodType(list_children_single_page, client)
    client.list_children_nested = types.MethodType(list_children_nested, client)
    return client
