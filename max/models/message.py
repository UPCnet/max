# -*- coding: utf-8 -*-
from max.MADMax import MADMaxCollection
from max.models.activity import BaseActivity
from max.rest.utils import canWriteInContexts


class Message(BaseActivity):
    """
        An activity
    """
    collection = 'messages'
    context_collection = 'conversations'
    unique = '_id'
    schema = dict(BaseActivity.schema)
    schema['objectType'] = dict(default='message')

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

        #Append actor as username if object has keywords and actor is a Person
        if ob['object'].get('_keywords', None):
            ob['object']['_keywords'].append(self.data['actor']['username'])

        if 'contexts' in self.data:
            # When a person posts an activity it can be targeted
            # to multiple contexts. here we construct the basic info
            # of each context and store them in contexts key
            ob['contexts'] = []
            for cobject in self.data['contexts']:
                subscription = dict(self.data['actor'].getSubscription(cobject))

                #Clean innecessary fields
                non_needed_subscription_fields = ['tags', 'published', 'permissions', 'participants']
                for fieldname in non_needed_subscription_fields:
                    if fieldname in subscription:
                        del subscription[fieldname]

                ob['contexts'].append(subscription)
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

    def _on_create_custom_validations(self):
        """
            Perform custom validations on the Activity Object

            * If the actor is a person, check wether can write in all contexts
            * If the actor is a context, check if the context is the same
        """
        collection = getattr(self.mdb_collection.database, self.context_collection)
        contextsdb = MADMaxCollection(collection, query_key='_id')

        # If we are updating, we already have all data on the object, so we read self directly
        result = True
        wrapped_contexts = []
        for context in self.data.get('contexts', []):
            # Get hash from context or calculate it from the url
            # XXX Too coupled ...
            wrapped = contextsdb[context['id']]
            wrapped_contexts.append(wrapped)

        result = result and canWriteInContexts(self.data['actor'], wrapped_contexts)
        return result
