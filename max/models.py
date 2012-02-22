from max.MADObjects import MADBase
import datetime
from max.rest.utils import formatMessageEntities


class Activity(MADBase):
    """
        An activitystrea.ms Activity object representation
    """
    collection = 'activity'
    unique = '_id'
    schema = {
                '_id':         dict(required=0, request=0),
                'actor':       dict(required=0, request=1),
                'verb':        dict(required=0, request=1),
                'object':      dict(required=0, request=1),
                'published':   dict(required=0, request=0),
                'contexts':    dict(required=0, request=0),
                'replies':    dict(required=0, request=0),
             }

    def buildObject(self):
        """
            Updates the dict content with the activity structure,
            with data parsed from the request
        """
        ob = {'actor': {
                    'objectType': 'person',
                    '_id': self.data['actor']['_id'],
                    'displayName': self.data['actor']['displayName']
                    },
                'verb': self.data['verb'],
                'object': None,
                }
        wrapper = self.getObjectWrapper(self.data['object']['objectType'])
        subobject = wrapper(self.data['object'])
        subobject['content'] = formatMessageEntities(subobject['content'])
        ob['object'] = subobject

        if 'contexts' in self.data:
            ob['contexts'] = self.data['contexts']

        self.update(ob)

    def addComment(self, comment):
        """
            Adds a comment to an existing activity
        """
        self.addToList('replies', comment, allow_duplicates=True)


class User(MADBase):
    """
        An activitystrea.ms User object representation
    """
    collection = 'users'
    unique = 'displayName'
    schema = {
                '_id':          dict(required=0),
                'displayName':  dict(required=1, request=1),
                'last_login':   dict(required=0),
                'following':    dict(required=0),
                'subscribedTo': dict(required=0),
                'published':    dict(required=0),
             }

    def buildObject(self):
        """
            Updates the dict content with the user structure,
            with data from the request
        """
        ob = {'displayName': self.data['displayName'],
                   'last_login': datetime.datetime.utcnow(),
                   'following': {'items': [], },
                   'subscribedTo': {'items': [], }
                   }
        self.update(ob)

    def addFollower(self, person):
        """
            Adds a follower to the list
        """
        self.addToList('following', person)

    def addSubscription(self, url):
        """
            Adds a comment to an existing activity
        """
        self.addToList('subscribedTo', url, safe=False)

    def removeSubscription(self, url):
        """
            Adds a comment to an existing activity
        """
        self.deleteFromList('subscribedTo', url)
