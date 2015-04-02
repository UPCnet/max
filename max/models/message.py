# -*- coding: utf-8 -*-
from max.models.activity import BaseActivity
from max.models.conversation import Conversation
from pyramid.decorator import reify
from max.security import Manager, Owner
from pyramid.security import Allow
from max.rest.utils import flatten
from max.security.permissions import view_message, modify_message

MESSAGE_CONTEXT_FIELDS = ['displayName', '_id', 'objectType']


class Message(BaseActivity):
    """
        An activity
    """
    default_field_view_permission = view_message
    default_field_edit_permission = modify_message
    collection = 'messages'
    context_collection = 'conversations'
    context_class = Conversation
    resource_root = 'messages'
    unique = '_id'
    schema = dict(BaseActivity.schema)
    schema['objectType'] = {'default': 'message'}

    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, view_message),
            (Allow, Owner, view_message)
        ]
        if self.get('contexts', []) and hasattr(self.request.actor, 'getSubscription'):
            from max.models import Conversation
            conversation = Conversation.from_database(self.contexts[0]['id'])
            subscription = self.request.actor.getSubscription(conversation)
            if subscription:
                permissions = subscription.get('permissions', [])
                if 'read' in permissions:
                    acl.append((Allow, self.request.authenticated_userid, view_message))

        return acl

    def buildObject(self):
        """
            Updates the dict content with the activity structure,
            with data parsed from the request
        """
        ob = {'actor': {'objectType': 'person',
                        'displayName': self.data['actor']['displayName'],
                        'username': self.data['actor']['username']
                        },
              'verb': self.data['verb'],
              'object': None,
              }

        wrapper = self.getObjectWrapper(self.data['object']['objectType'])
        subobject = wrapper(self.data['object'])
        ob['object'] = subobject

        # Append actor as username if object has keywords and actor is a Person
        if ob['object'].get('_keywords', None):
            ob['object']['_keywords'].append(self.data['actor']['username'])

        if 'contexts' in self.data:
            ob['contexts'] = [flatten(self.data['contexts'][0], preserve=MESSAGE_CONTEXT_FIELDS)]
        self.update(ob)

        # Set defaults
        properties = {}
        for key, value in self.schema.items():
            default = value.get('default', None)
            # Value is in the request but not set yet, set it please.
            if key in self.data and key not in self:
                properties[key] = self.data[key]
            # Value is not in the request and we have a default, set it please
            elif 'default' in value.keys():
                properties[key] = default
        self.update(properties)
