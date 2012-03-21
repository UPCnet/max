from max.MADObjects import MADBase
from max.rest.utils import canWriteInContexts
import datetime
from hashlib import sha1
from MADMax import MADMaxDB


class Activity(MADBase):
    """
        An activitystrea.ms Activity object representation
    """
    collection = 'activity'
    unique = '_id'
    schema = {
                '_id':         dict(required=0),
                'actor':       dict(required=1),
                'verb':        dict(required=1),
                'object':      dict(required=1),
                'published':   dict(required=0),
                'contexts':    dict(required=0),
                'replies':    dict(required=0),
                'generator':    dict(required=0),
             }

    def buildObject(self):
        """
            Updates the dict content with the activity structure,
            with data parsed from the request
        """
        ob = {'actor': {
                    'objectType': 'person',
                    '_id': self.data['actor']['_id'],
                    'username': self.data['actor']['username'],
                    'displayName': self.data['actor']['displayName'],
                    },
                'verb': self.data['verb'],
                'object': None,
                }
        wrapper = self.getObjectWrapper(self.data['object']['objectType'])
        subobject = wrapper(self.data['object'])
        ob['object'] = subobject

        if 'contexts' in self.data:
            ob['contexts'] = [dict(url=url, objectType='context') for url in self.data['contexts']]

        self.update(ob)

    def addComment(self, comment):
        """
            Adds a comment to an existing activity
        """
        self.addToList('replies', comment, allow_duplicates=True)

    def _validate(self):
        """
            Perform custom validations on the Activity Object
        """
        result = canWriteInContexts(self.data['actor'], self.data.get('contexts', []))
        return result


class User(MADBase):
    """
        An activitystrea.ms User object representation
    """
    collection = 'users'
    unique = 'username'
    schema = {
                '_id':          dict(),
                'username':     dict(required=1),
                'displayName':  dict(user_mutable=1),
                'last_login':   dict(),
                'following':    dict(default={'items':[]}),
                'subscribedTo': dict(default={'items':[]}),
                'published':    dict(),
                'twitterUsername':    dict(user_mutable=1),
             }

    def buildObject(self):
        """
            Updates the dict content with the user structure,
            with data from the request
        """
        ob = {'last_login': datetime.datetime.utcnow()}

        # Update properties from request data if defined in schema
        # Also create properties with a default value defined
        properties = {}
        for key, value in self.schema.items():
            default = value.get('default', None)
            if key in self.data:
                properties[key] = self.data[key]
            elif default:
                properties[key] = default

        ob.update(properties)
        self.update(ob)

    def addFollower(self, person):
        """
            Adds a follower to the list
        """
        self.addToList('following', person)

    def addSubscription(self, context):
        """
            Adds a comment to an existing activity
        """
        #XXX TODO Check authentication method, and if is oauth, check if user can auto join the context.
        subscription = context.flatten()
        permissions = subscription['permissions']

        #If we are subscribing the user, read permission is granted
        user_permissions = ['read']

        #Set other permissions based on context defaults
        if permissions['write'] in ['subscribed', 'public']:
            user_permissions.append('write')
        if permissions['invite'] in ['subscribed']:
            user_permissions.append('invite')

        #Assign permissions to the subscription object before adding it
        subscription['permissions'] = user_permissions

        self.addToList('subscribedTo', subscription, safe=False)

    def removeSubscription(self, url):
        """
            Adds a comment to an existing activity
        """
        self.deleteFromList('subscribedTo', url)

    def modifyUser(self, properties):
        """Update the user object with the given properties"""
        # Comprehension dict (Muahaha)
        self.updateFields(properties)

    def grantPermission(self, subscription, permission):
        """
        """
        criteria = {}
        criteria.update({'subscribedTo.items.urlHash':subscription['urlHash']})   # update object from "items" that matches urlHash
        criteria.update({'_id':self._id})                 # of collection entry with _id

         # Add permission to permissions array, of matched object of "items"
        what = {'$addToSet': {'subscribedTo.items.$.permissions':permission}}

        self.mdb_collection.update(criteria, what)

    def revokePermission(self, subscription, permission):
        """
        """
        criteria = {}
        criteria.update({'subscribedTo.items.urlHash':subscription['urlHash']})   # update object from "items" that matches urlHash
        criteria.update({'_id':self._id})                 # of collection entry with _id

         # deletes permission from permissions array, of matched object of "items"
        what = {'$pull': {'subscribedTo.items.$.permissions':permission}}

        self.mdb_collection.update(criteria, what)


class Context(MADBase):
    """
        A max Context object representation
    """
    collection = 'contexts'
    unique = 'url'
    schema = {
                '_id':          dict(),
                'url':          dict(required=1),
                'urlHash':      dict(),
                'displayName':  dict(operations_mutable=1),
                'published':    dict(),
                'twitterHashtag':    dict(operations_mutable=1),
                'twitterUsername':    dict(operations_mutable=1),
                'permissions':  dict(default={'read':'public', 'write':'public', 'join':'public', 'invite':'public'}),
             }

    def buildObject(self):
        """
            Updates the dict content with the context structure,
            with data from the request
        """

        # Update properties from request data if defined in schema
        # Also create properties with a default value defined
        ob = {}
        properties = {}
        for key, value in self.schema.items():
            default = value.get('default', None)
            if key in self.data:
                properties[key] = self.data[key]
            elif default:
                properties[key] = default

        ob['urlHash'] = sha1(self.data['url']).hexdigest()

        ob.update(properties)
        self.update(ob)

    def modifyContext(self, properties):
        """Update the user object with the given properties"""
        # Comprehension dict (Muahaha)
        self.updateFields(properties)

    def removeUserSubscriptions(self):
        """
        """
        # update object from "items" that matches urlHash
        criteria = {'subscribedTo.items.urlHash':self.urlHash}

         # deletes context from subcription list
        what = {'$pull': {'subscribedTo.items':{'urlHash':self.urlHash}}}

        self.mdb_collection.database.users.update(criteria, what)
