# -*- coding: utf-8 -*-
from max.MADObjects import MADBase
from max.exceptions import ValidationError
from max.security import Manager
from max.security import Owner
from max.security import is_owner
from max.security.permissions import change_ownership
from max.security.permissions import modify_immutable_fields
from max.security.permissions import modify_token
from max.security.permissions import view_private_fields
from max.security.permissions import view_token
from max.validators import is_valid_ios_token
from pyramid.decorator import reify
from pyramid.security import Allow


SUPPORTED_PLATFORMS = ['ios', 'android']


class Token(MADBase):
    """
        The User Device token representation
    """
    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, view_token),
            (Allow, Owner, view_token),
        ]

        # When checking permissions directly on the object (For example when determining
        # the visible fields), request.context.owner will be related to the owner of where we are posting the
        # activity, for example, when posting to a context, the context), so we need to provide permissions
        # for the owner of the object itself, or the flatten will result empty...
        if is_owner(self, self.request.authenticated_userid):
            acl.append((Allow, self.request.authenticated_userid, view_token))

        return acl

    default_field_view_permission = view_token
    default_field_edit_permission = modify_token
    collection = 'tokens'
    unique = 'token'
    schema = {
        '_id': {
            'edit': modify_immutable_fields,
        },
        '_creator': {
            'edit': modify_immutable_fields,
            'view': view_private_fields
        },
        '_owner': {
            'edit': change_ownership,
            'view': view_private_fields
        },
        'platform': {
            'required': 1
        },
        'device': {
            'default': None
        },
        'published': {
            'edit': modify_immutable_fields
        },
        'token': {
            'required': 1
        },
        'objectType': {
            'edit': modify_immutable_fields,
            'default': 'token'
        },
    }

    def format_unique(self, key):
        return key

    def buildObject(self):
        """
            Updates the dict content with the user structure,
            with data from the request
        """
        # Update properties from request data if defined in schema
        # Also create properties with a default value defined

        properties = {}
        for key, value in self.schema.items():
            default = value.get('default', None)
            if key in self.data:
                properties[key] = self.data[key]
            elif 'default' in value.keys():
                properties[key] = default

        if properties['platform'] == 'ios':
            if not is_valid_ios_token(properties['token']):
                raise ValidationError('Invalid {platform} token for'.format(**properties))

        properties['platform'] = properties.get('platform', '').lower()
        if properties['platform'] not in SUPPORTED_PLATFORMS:
            raise ValidationError('{platform} is not a supported platform.'.format(**properties))

        self.update(properties)

    def getOwner(self, request):
        """
            Overrides the getOwner method to set the
            current user object as owner instead of the creator
            Oneself will be always owner of oneself. If not found,
            look for data being processed and finally default to creator.
        """
        return self.get('username', self.data.get('username', request.authenticated_userid))
