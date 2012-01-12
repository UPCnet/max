import requests
import json


"""

Funcionament


Conectar

>>> from macsclient import MacsClient
>>> macs = MacsClient('http://max.beta.upcnet.es')

Afegir un usuari

>>> macs.addUser('test')
{u'displayName': u'test', u'subscribedTo': {u'items': []}, u'last_login': u'2012-01-11T12:14:52Z', u'published': u'2012-01-11T12:14:52Z', u'following': {u'items': []}, u'id': u'4f0d7d3c637e0325bc000000'}
>>>

Indicar l'usuari que firma les accions

>>> macs.setActor('test')

Afegir una activitat

>>> macs.addActivity('Hello world!')
{u'verb': u'post', u'object': {u'content': u'Hello world!', u'objectType': u'note'}, u'id': u'4f0d7e09637e0325bc000001', u'actor': {u'displayName': u'test', u'id': u'4f0d7d3c637e0325bc000000', u'objectType': u'person'}, u'published': u'2012-01-11T12:18:17Z'}

Obtenir la activitat per id

>>> macs.getActivity('4f0d7e09637e0325bc000001')
{u'verb': u'post', u'object': {u'content': u'Hello world!', u'objectType': u'note'}, u'id': u'4f0d7e09637e0325bc000001', u'actor': {u'displayName': u'test', u'id': u'4f0d7d3c637e0325bc000000', u'objectType': u'person'}, u'published': u'2012-01-11T12:18:17Z'}

Afegir un comentari a l'activitat

>>> macs.addComment('Hello moon!','4f0d7e09637e0325bc000001')
{u'verb': u'post', u'object': {u'content': u'Hello moon!', u'inReplyTo': [{u'id': u'4f0d7e09637e0325bc000001'}], u'objectType': u'comment'}, u'id': u'4f0d7fbe637e0325bc000002', u'actor': {u'displayName': u'test', u'id': u'4f0d7d3c637e0325bc000000', u'objectType': u'person'}, u'published': u'2012-01-11T12:25:34Z'}

Afagar el primer comentari de l'activitat

>>> macs.getActivity('4f0d7e09637e0325bc000001')['replies']['items'][0]
{u'content': u'Hello moon!', u'author': {u'displayName': u'test'}, u'id': u'4f0d7fbe637e0325bc000002', u'objectType': u'comment'}

Veure el timeline d'un usuari

>>> macs.getUserTimeline('test')
{u'totalItems': 2, u'items': [{u'verb': u'post', u'object': {u'content': u'Hello moon!', u'inReplyTo': [{u'id': u'4f0d7e09637e0325bc000001'}], u'objectType': u'comment'}, u'id': u'4f0d7fbe637e0325bc000002', u'actor': {u'displayName': u'test', u'id': u'4f0d7d3c637e0325bc000000', u'objectType': u'person'}, u'published': u'2012-01-11T12:25:34Z'}, {u'replies': {u'totalItems': 1, u'items': [{u'content': u'Hello moon!', u'author': {u'displayName': u'test'}, u'id': u'4f0d7fbe637e0325bc000002', u'objectType': u'comment'}]}, u'object': {u'content': u'Hello world!', u'objectType': u'note'}, u'actor': {u'displayName': u'test', u'id': u'4f0d7d3c637e0325bc000000', u'objectType': u'person'}, u'verb': u'post', u'published': u'2012-01-11T12:18:17Z', u'id': u'4f0d7e09637e0325bc000001'}]}
>>>


"""
ROUTES = dict(users='/people',
              user='/people/%(displayName)s',
              user_activities='/people/%(displayName)s/activities',
              timeline='/people/%(displayName)s/timeline',
              user_comments='/people/%(displayName)s/comments',
              user_shares='/people/%(displayName)s/shares',
              user_likes='/people/%(displayName)s/likes',
              follows='/people/%(displayName)s/follows',
              follow='/people/%(displayName)s/follows/%(followedDN)s',
              subscriptions='/people/%(displayName)s/subscriptions',
              activities='/activities',
              activity='/activities/%(activity)s',
              comments='/activities/%(activity)s/comments',
              comment='/activities/%(activity)s/comments/%(commentId)s',
              likes='/activities/%(activity)s/likes',
              like='/activities/%(activity)s/likes/%(likeId)s',
              shares='/activities/%(activity)s/shares',
              share='/activities/%(activity)s/shares/%(shareId)s')


class MacsClient(object):

    def __init__(self, url):
        """
        """
        self.url = url

    # def parse_list(self,key,item):
    #     return '&'.join([('%s=%s') % (key,value) for value in item])

    # def parse_str(self,key,item):
    #     return ('%s=%s') % (key,item)

    # def parse(self,key,item):
    #     parser = getattr(self,'parse_%s' % type(item).__name__)
    #     return parser(key,item)

    def examplePOSTCall(self, displayName):
        """
        """
        route = ROUTES['']

        query = {}
        rest_params = dict(displayName=displayName)

        (success, code, response) = self.POST(route % rest_params, query)
        return response

    def exampleGETCall(self, displayName):
        """
        """
        route = ROUTES['']
        query = {}
        rest_params = dict(displayName=displayName)
        (success, code, response) = self.GET(route % rest_params, query)
        return response

    def GET(self, route, query=None):
        """
        """
        resource_uri = '%s/%s' % (self.url, route)
        req = requests.get(resource_uri)

        isOk = req.status_code == 200
        isJson = 'application/json' in req.headers.get('content-type', '')
        if isOk:
            response = isJson and json.loads(req.content) or None
        else:
            print req.status_code
            response = ''
        return (isOk, req.status_code, response)

    def POST(self, route, query):
        """
        """
        resource_uri = '%s/%s' % (self.url, route)
        json_query = json.dumps(query)

        req = requests.post(resource_uri, data=json_query)
        isOk = req.status_code in [200, 201] and req.status_code or False
        isJson = 'application/json' in req.headers.get('content-type', '')
        if isOk:
            response = isJson and json.loads(req.content) or None
        else:
            print req.status_code
            response = ''

        return (isOk, req.status_code, response)

    def setActor(self, displayName):
        self.actor = dict(objectType='person', displayName=displayName)

    ###########################
    # USERS
    ###########################

    def addUser(self, displayName):
        """
        """
        route = ROUTES['user']

        query = {}
        rest_params = dict(displayName=displayName)

        (success, code, response) = self.POST(route % (rest_params), query)
        return response

    ###########################
    # ACTIVITIES
    ###########################

    def addActivity(self, content, otype='note', contexts=[]):
        """
        """
        route = ROUTES['user_activities']
        query = dict(verb='post',
                     object=dict(objectType=otype,
                                   content=content,
                                  ),
                    )
        if contexts:
            query['contexts'] = contexts

        rest_params = dict(displayName=self.actor['displayName'])

        (success, code, response) = self.POST(route % rest_params, query)
        return response

    def getActivity(self, activity):
        """
        """
        route = ROUTES['activity']
        rest_params = dict(activity=activity)
        (success, code, response) = self.GET(route % rest_params)
        return response

    def getUserTimeline(self, displayName):
        """
        """
        route = ROUTES['timeline']
        rest_params = dict(displayName=displayName)
        (success, code, response) = self.GET(route % rest_params)
        return response

    ###########################
    # COMMENTS
    ###########################

    def addComment(self, content, activity, otype='comment'):
        """
        """
        route = ROUTES['comments']
        query = dict(actor=self.actor,
                     verb='post',
                     object=dict(objectType=otype,
                                   content=content,
                                  ),
                    )
        rest_params = dict(activity=activity)
        (success, code, response) = self.POST(route % rest_params, query)
        return response

    def getComments(self, activity):
        """
        """
        query = {}
        route = ROUTES['comments']
        rest_params = dict(activity=activity)
        (success, code, response) = self.GET(route % rest_params, query)



    # def follow(self,displayName,oid,otype='person'):
    #     """
    #     """
    #     fn = sys._getframe().f_code.co_name
    #     query = dict(actor =  self.actor,
    #                  verb = 'follow',
    #                  object = dict(objectType=otype,
    #                                id=oid,
    #                                displayName=displayName,
    #                               ),
    #                 )
    #     (success, code, response) = self.POST(fn,query)
    #     return response

    # def unfollow(self,displayName,oid,otype='person'):
    #     """
    #     """
    #     fn = sys._getframe().f_code.co_name
    #     query = dict(actor =  self.actor,
    #                  verb = 'unfollow',
    #                  object = dict(objectType=otype,
    #                                id=oid,
    #                                displayName=displayName,
    #                               ),
    #                 )
    #     (success, code, response) = self.POST(fn,query)
    #     return response

    # def subscribe(self,url,otype='context'):
    #     """
    #     """
    #     route = 'people/%(displayName)s/subscriptions'
    #     rest_params=dict(displayName=self.actor['displayName'])
    #     query = dict(actor =  self.actor,
    #                  verb = 'follow',
    #                  object = dict(objectType=otype,
    #                                url=url,
    #                               ),
    #                 )
    #     (success, code, response) = self.POST(route % rest_params,query)
    #     return response

    # def unsubscribe(self,displayName,url,otype='service'):
    #     """
    #     """
    #     fn = sys._getframe().f_code.co_name
    #     query = dict(actor =  self.actor,
    #                  verb = 'unfollow',
    #                  object = dict(objectType=otype,
    #                                url=url,
    #                                displayName=displayName,
    #                               ),
    #                 )
    #     (success, code, response) = self.POST(fn,query)
    #     return response
