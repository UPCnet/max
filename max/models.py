from max.MADObjects import MADBase
from max.rest.utils import canWriteInContexts
import datetime
from hashlib import sha1
from MADMax import MADMaxDB
from max.rest.utils import getUserIdFromTwitter, findKeywords, findHashtags
from max import DEFAULT_CONTEXT_PERMISSIONS


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
        isPerson = isinstance(self.data['actor'], User)
        isContext = isinstance(self.data['actor'], Context)

        # XXX Assuming here we won't support any other type as actor
        actorType = isPerson and 'person' or 'context'
        ob = {'actor': {
                    'objectType': actorType,
                    '_id': self.data['actor']['_id'],
                    'displayName': self.data['actor']['displayName'],
                    },
                'verb': self.data['verb'],
                'object': None,
                }
        if isPerson:
            ob['actor']['username'] = self.data['actor']['username']
        elif isContext:
            ob['actor']['urlHash'] = self.data['actor']['urlHash']
            ob['actor']['url'] = self.data['actor']['url']

        wrapper = self.getObjectWrapper(self.data['object']['objectType'])
        subobject = wrapper(self.data['object'])
        ob['object'] = subobject

        #Append actor as username if object has keywords and actor is a Person
        if ob['object'].get('_keywords',None):
            if isPerson:
                ob['object']['_keywords'].append(self.data['actor']['username'])

        if 'generator' in self.data:
            ob['generator'] = self.data['generator']

        if 'contexts' in self.data:
            if isPerson:
                # When a person posts an activity it can be targeted
                # to mulitple contexts. here we construct the basic info
                # of each context and store them in contexts key
                ob['contexts'] = []
                for url in self.data['contexts']:
                    subscription = self.data['actor'].getSubscriptionByURL(url)
                    context = dict(url=url,
                                   objectType='context',
                                   displayName=subscription.get('displayName', subscription.get('url'))
                                   )
                    ob['contexts'].append(context)
            if isContext:
                # When a context posts an activity it can be posted only
                # to itself, so add it directly
                    ob['contexts'] = [dict(url=self.data['actor']['url'],
                                   objectType='context',
                                   displayName=self.data['actor']['displayName'],
                                   )]
        self.update(ob)

    def addComment(self, comment):
        """
            Adds a comment to an existing activity and updates refering activity keywords and hashtags
        """
        self.addToList('replies', comment, allow_duplicates=True)

        activity_keywords = self.object.setdefault('_keywords',[])
        activity_keywords.extend(comment.get('_keywords',[]))
        activity_keywords = list(set(activity_keywords))

        activity_hashtags = self.object.setdefault('_hashtags',[])
        activity_hashtags.extend(comment.get('_hashtags',[]))
        activity_hashtags = list(set(activity_hashtags))

        self.mdb_collection.update({'_id': self['_id']},
                                      {'$set': {'object._keywords': activity_keywords,
                                                'object._hashtags': activity_hashtags}}
                                      )

    def _on_create_custom_validations(self):
        """
            Perform custom validations on the Activity Object

            * If the actor is a person, check wether can write in all contexts
            * If the actor is a context, check if the context is the same
        """
        # If we are updating, we already have all data on the object, so we read self directly
        result = True
        if isinstance(self.data['actor'], User):
            result = result and canWriteInContexts(self.data['actor'], self.data.get('contexts', []))
        if self.data.get('contexts', None) and isinstance(self.data['actor'], Context):
            result = result and self.data['actor']['url'] == self.data.get('contexts')[0]
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
                'following':    dict(default={'items': []}),
                'subscribedTo': dict(default={'items': []}),
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
        subscription = context.prepareUserSubscription()
        self.addToList('subscribedTo', subscription, safe=False)

    def removeSubscription(self, url):
        """
            Adds a comment to an existing activity
        """
        self.deleteFromList('subscribedTo', url)

    def modifyUser(self, properties):
        """Update the user object with the given properties"""

        self.updateFields(properties)
        self.save()

    def grantPermission(self, subscription, permission):
        """
        """
        criteria = {}
        criteria.update({'subscribedTo.items.urlHash': subscription['urlHash']})   # update object from "items" that matches urlHash
        criteria.update({'_id': self._id})                 # of collection entry with _id

         # Add permission to permissions array, of matched object of "items"
        what = {'$addToSet': {'subscribedTo.items.$.permissions': permission}}

        self.mdb_collection.update(criteria, what)

    def revokePermission(self, subscription, permission):
        """
        """
        criteria = {}
        criteria.update({'subscribedTo.items.urlHash': subscription['urlHash']})   # update object from "items" that matches urlHash
        criteria.update({'_id': self._id})                 # of collection entry with _id

         # deletes permission from permissions array, of matched object of "items"
        what = {'$pull': {'subscribedTo.items.$.permissions': permission}}

        self.mdb_collection.update(criteria, what)

    def getSubscriptionByURL(self, url):
        """
        """
        context_map = {context['url']: context for context in self.subscribedTo['items']}
        return context_map.get(url)


class Context(MADBase):
    """
        A max Context object representation
    """
    collection = 'contexts'
    unique = 'url'
    schema = {
                '_id':              dict(),
                'url':              dict(required=1),
                'urlHash':          dict(),
                'displayName':      dict(operations_mutable=1),
                'published':        dict(),
                'twitterHashtag':   dict(operations_mutable=1,
                                         formatters=['stripHash'],
                                         validators=['isValidHashtag'],
                                        ),
                'twitterUsername':  dict(operations_mutable=1,
                                         formatters=['stripTwitterUsername'],
                                         validators=['isValidTwitterUsername'],
                                       ),

                'twitterUsernameId':  dict(operations_mutable=1),
                'permissions':      dict(default={'read': DEFAULT_CONTEXT_PERMISSIONS['read'],
                                                  'write': DEFAULT_CONTEXT_PERMISSIONS['write'],
                                                  'join': DEFAULT_CONTEXT_PERMISSIONS['join'],
                                                  'invite': DEFAULT_CONTEXT_PERMISSIONS['invite']}),
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

        # If creating with the twitterUsername, get its Twitter ID
        if self.data.get('twitterUsername', None):
            ob['twitterUsernameId'] = getUserIdFromTwitter(self.data['twitterUsername'])

        ob.update(properties)
        self.update(ob)

    def modifyContext(self, properties):
        """Update the user object with the given properties"""
        # If updating the twitterUsername, get its Twitter ID
        if properties.get('twitterUsername', None):
            properties['twitterUsernameId'] = getUserIdFromTwitter(properties['twitterUsername'])

        self.updateFields(properties)

        if self.get('twitterUsername', None) == None and self.get('twitterUsernameId', None) != None:
            del self['twitterUsernameId']

        self.save()


    def subscribedUsers(self):
        """
        """
        criteria = {'subscribedTo.items.urlHash': self.urlHash}
        subscribed_users = self.mdb_collection.database.users.find(criteria)
        return [user for user in subscribed_users]

    def prepareUserSubscription(self):
        """
        """
        subscription = self.flatten()
        permissions = subscription['permissions']

        #If we are subscribing the user, read permission is granted
        user_permissions = ['read']

        #Set other permissions based on context defaults
        if permissions.get('write', DEFAULT_CONTEXT_PERMISSIONS['write']) in ['subscribed', 'public']:
            user_permissions.append('write')
        if permissions.get('invite', DEFAULT_CONTEXT_PERMISSIONS['invite']) in ['subscribed']:
            user_permissions.append('invite')

        #Assign permissions to the subscription object before adding it
        subscription['permissions'] = user_permissions
        return subscription

    def updateUsersSubscriptions(self):
        """
        """
        # XXX TODO For now only updates displayName
        ids = [user['_id'] for user in self.subscribedUsers()]

        for obid in ids:
            criteria = {'_id': obid, 'subscribedTo.items.urlHash': self.urlHash}

                 # deletes context from subcription list
            what = {'$set': {'subscribedTo.items.$.displayName': self.displayName}}
            self.mdb_collection.database.users.update(criteria, what)

    def removeUserSubscriptions(self):
        """
        """
        # update object from "items" that matches urlHash
        criteria = {'subscribedTo.items.urlHash': self.urlHash}

         # deletes context from subcription list
        what = {'$pull': {'subscribedTo.items': {'urlHash': self.urlHash}}}

