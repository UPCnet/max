# -*- coding: utf-8 -*-


def CDATA(data):
    jsonified = json.dumps(data)
    wrap = '<![CDATA[%s]]>' % jsonified
    return wrap

activity = {
    'verb':'post',
    'object':{
        'objectType':'note',
        'content':'texthere'
    }
} 

import json
WADL = [
  {'base' : 'http://max.beta.upcnet.es',
   'docs' : 'http://max.beta.upcnet.es/docs',
   'resources' : [ 

                { 'route' : 'users',
                  'format' : '/people',
                  'methods' : [
                                { 'id' : 'getUsers',
                                  'name' : 'GET',
                                  'desc' : 'Llistat d''usuaris',
                                  'tags' : ['People'],
                                  'auth' : False,
                                  'doc' : 'Fa una llista de tots els usuaris donats d''alta al sistema',
                                },
                               ]
                  },
                { 'route' : 'user',
                  'format' : '/people/{displayName}',
                  'methods' : [
                                { 'id' : 'getUser',
                                  'name' : 'GET',
                                  'desc' : 'Dades de l''usuari',
                                  'tags' : ['People'],
                                  'auth' : False,
                                  'doc' : 'Obté les dades complertes d''un usuari del sistema',
                                },
                                { 'id' : 'addUser',
                                  'name' : 'POST',
                                  'desc' : 'Afegir un usuari',
                                  'tags' : ['People'],
                                  'auth' : False,
                                  'doc' : 'Afegeix un usuari amb nom segons {displayName}',
                                },
                                
                               ]
                  },
                { 'route' : 'user_activities',
                  'format' : '/people/{displayName}/activities',
                  'methods' : [
                                { 'id' : 'getUserActivities',
                                  'name' : 'GET',
                                  'desc' : 'Totes les activitats creades',
                                  'tags' : ['Activities'],
                                  'auth' : False,
                                  'doc' : 'Fa una llista de totes les activitats creades per un usuari',
                                },
                                { 'id' : 'addUserActivity',
                                  'name' : 'POST',
                                  'desc' : 'Afegir una activitat',
                                  'tags' : ['Activities'],
                                  'auth' : False,
                                  'doc' : 'Crea una nova activitat al sistema en nom de l''usuari indicat, utilitzant les dades del contingut de la petició',
                                  'request' : {'payload': CDATA(activity),
                                                'contenttype':'application/json'}
                                },
                                
                               ]
                  },
                { 'route' : 'timeline',
                  'format' : '/people/{displayName}/timeline',
                  'methods' : [
                                { 'id' : 'getUserTimeline',
                                  'name' : 'GET',
                                  'desc' : 'Timeline de l''usuari',
                                  'tags' : ['Activities'],
                                  'auth' : False,
                                  'doc' : 'Fa una llista de totes les activitats creades per un usuari, les activitats de la gent a qui segueix, i les activitats generades sota un context concret',
                                },
                               ]
                  },
                { 'route' : 'user_comments',
                  'format' : '/people/{displayName}/comments',
                  'methods' : [
                                { 'id' : 'getUserComments',
                                  'name' : 'GET',
                                  'desc' : 'Comentaris de l''usuari',
                                  'tags' : ['Comments'],
                                  'auth' : False,
                                  'doc' : 'Fa una llista dels comentaris a activitats fets per l''usuari especificat',
                                },
                               ]
                  },
                { 'route' : 'user_shares',
                  'format' : '/people/{displayName}/shares',
                  'methods' : [
                                { 'id' : 'getUserSharedActivities',
                                  'name' : 'GET',
                                  'desc' : 'Activitats compartides per l''usuari',
                                  'tags' : ['Shares'],
                                  'auth' : False,
                                  'doc' : 'Fa una llista de les activitats compartides per l''usuari',
                                },
                               ]
                  },
                { 'route' : 'user_likes',
                  'format' : '/people/{displayName}/likes',
                  'methods' : [
                                { 'id' : 'getUserLikedActivities',
                                  'name' : 'GET',
                                  'desc' : 'Activitats agradades per l''usuari',
                                  'tags' : ['Likes'],
                                  'auth' : False,
                                  'doc' : 'Fa una llista de totes les activitats que actualment estan marcades com a m''agrada',
                                },
                               ]
                  },
                { 'route' : 'follows',
                  'format' : '/people/{displayName}/follows',
                  'methods' : [
                                { 'id' : 'getFollowedUsers',
                                  'name' : 'GET',
                                  'desc' : 'Seguiments de l''usuari',
                                  'tags' : ['Follows'],
                                  'auth' : False,
                                  'doc' : 'Fa una llista de tothom a qui l''usuari esta seguint',
                                },
                               ]
                  },
                { 'route' : 'follow',
                  'format' : '/people/{displayName}/follows/{followedDN}',
                  'methods' : [
                                { 'id' : 'getFollowedUser',
                                  'name' : 'GET',
                                  'desc' : 'Mostra Seguidor',
                                  'tags' : ['Follows'],
                                  'auth' : False,
                                  'doc' : 'Obté les dades d''un seguidor',
                                },
                               ]
                  },
                { 'route' : 'subscriptions',
                  'format' : '/people/{displayName}/subscriptions',
                  'methods' : [
                                { 'id' : 'getUserSubscriptions',
                                  'name' : 'GET',
                                  'desc' : 'Subscripcions',
                                  'tags' : ['Subscriptions'],
                                  'auth' : False,
                                  'doc' : 'Fa una llista dels contextos als quals esta subscrit l''usuari',
                                },
                               ]
                  },
                { 'route' : 'subscription',
                  'format' : '/people/{displayName}/subscription/{subscrId}}',
                  'methods' : [
                                { 'id' : 'getUserSubscription',
                                  'name' : 'GET',
                                  'desc' : 'Subscripció',
                                  'tags' : ['Subscriptions'],
                                  'auth' : False,
                                  'doc' : 'Mostra les dades d''una subscripció',
                                },
                               ]
                  },
                { 'route' : 'activities',
                  'format' : '/activities',
                  'methods' : [
                                { 'id' : 'getActivities',
                                  'name' : 'GET',
                                  'desc' : 'Totes les activitats',
                                  'tags' : ['Activities'],
                                  'auth' : False,
                                  'doc' : 'Fa una llista de totes les activitats creades per tothom al sistema',
                                },
                               ]
                  },
                { 'route' : 'activity',
                  'format' : '/activities/{activity}',
                  'methods' : [
                                { 'id' : 'getActivity',
                                  'name' : 'GET',
                                  'desc' : 'Activitat',
                                  'tags' : ['Activities'],
                                  'auth' : False,
                                  'doc' : 'Mostra les dades d''una activitat concreta',
                                },
                               ]
                  },
                { 'route' : 'comments',
                  'format' : '/activities/{activity}/comments',
                  'methods' : [
                                { 'id' : 'getActivityComments',
                                  'name' : 'GET',
                                  'desc' : 'Comentaris',
                                  'tags' : ['Comments'],
                                  'auth' : False,
                                  'doc' : 'Fa una llista de tots els comentaris que s''han fet a una activitat',
                                },
                               ]
                  },
                { 'route' : 'comment',
                  'format' : '/activities/{activity}/comments/{commentId}',
                  'methods' : [
                                { 'id' : 'getActivityComment',
                                  'name' : 'GET',
                                  'desc' : 'Comentari',
                                  'tags' : ['Comments'],
                                  'auth' : False,
                                  'doc' : 'Mostra les dades d''un comentari concret',
                                },
                               ]
                  },
                { 'route' : 'likes',
                  'format' : '/activities/{activity}/likes',
                  'methods' : [
                                { 'id' : 'getActivityLikes',
                                  'name' : 'GET',
                                  'desc' : 'M''agrada d''una activitat',
                                  'tags' : ['Likes'],
                                  'auth' : False,
                                  'doc' : 'Fa una llista d''usuaris que han dit m''agrada a l''activitat',
                                },
                               ]
                  },
                { 'route' : 'likeId',
                  'format' : '/activities/{activity}/likes/{likeId}',
                  'methods' : [
                                { 'id' : 'getActivityLike',
                                  'name' : 'GET',
                                  'desc' : 'M''agrada d''una activitat',
                                  'tags' : ['Likes'],
                                  'auth' : False,
                                  'doc' : 'Mostra un m''agrada concret',
                                },
                               ]
                  },
                { 'route' : 'shares',
                  'format' : '/activities/{activity}/shares',
                  'methods' : [
                                { 'id' : 'getActivityShares',
                                  'name' : 'GET',
                                  'desc' : 'Compartits d''una activitat',
                                  'tags' : ['Shares'],
                                  'auth' : False,
                                  'doc' : 'Fa una llista de totes les vegades que s''ha compartit una activitat',
                                },
                               ]
                  },
                { 'route' : 'shareId',
                  'format' : '/activities/{activity}/shares/{shareId}',
                  'methods' : [
                                { 'id' : 'getActivityShare',
                                  'name' : 'GET',
                                  'desc' : 'Compartiment d''una activitat',
                                  'tags' : ['Shares'],
                                  'auth' : False,
                                  'doc' : 'Mostra les dades d''un compartiment concret',
                                },
                               ]
                  },
                                    
               ]
  }
]
