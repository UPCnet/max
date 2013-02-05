API REST
========

Aquest document exposa els serveis web públics creats pel motor d'activitat i
subscripcions. Aquests estan organitzats per recursos i les operacions sobre
ells. Tots els serveis web són de tipus RESTful i l'intercanvi d'informació es
realitza en format JSON.

Els paràmetres indicats a les seccions Query parameters, poden ser de 3 tipus:

:REST: Són obligatoris ja que formen part de la URI
:Requerits: Són obligatoris, però formen part de l'estructura JSON que s'envia
    amb el cos de la petició
:Opcionals: Com el nom indica, no son obligatoris, indiquen alguna funcionalitat
    extra

Tots els serveis requereixen autenticació oAuth en cas de que no s'especifiqui
el contrari.

Les respostes que retorna el sistema, en cas que siguin 1 o múltiples resultats
(Associats a col.leccions o entitats) seràn, o bé un sol objecte JSON en cas de
l'accés a una entitat concreta, o una estructura que englobi un conjunt de
resultats, indicant el total d'elements retornats::

    {
        "totalItems": 2,
        "items": [
                   { ... },
                   { ... }
                 ]
    }

.. this is some setup, it is hidden in a reST comment

    >>> from httpretty import HTTPretty
    >>> HTTPretty.enable()
    >>> HTTPretty.register_uri(HTTPretty.POST, "http://localhost:8080/checktoken", body="", status=200)
    >>> username = "messi"
    >>> utils = MaxTestBase(testapp)
    >>> utils.create_user(username)
    <201 Created application/json body='{"usernam...>
    >>> from max.tests.mockers import create_context, subscribe_context, context_query, user_status
    >>> utils.create_context(create_context)
    <201 Created application/json body='{"display...>
    >>> utils.subscribe_user_to_context(username, subscribe_context)
    <201 Created application/json body='{"replies...>

Usuaris
--------

Operacions sobre el recurs *usuari* del sistema.

.. http:get:: /people

    Retorna el resultat d'una cerca d'usuaris del sistema en forma de llista
    de noms d'usuaris per l'ús de la UI.

    :query username: El filtre de cerca d'usuaris.

    Cos de la petició

        .. code-block:: python

            {"username": "messi"}

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {"totalItems": 1, "items": [{"username": "messi", "id": "510fd582aceee925d0f1ecd1"}]}

        .. -> expected
            >>> response = testapp.get('/people', payload, oauth2Header(username), status=200)
            >>> response
            <200 OK application/json body='{"totalIt...>
            >>> response.json.get('displayName') == eval(expected).get('displayName')
            True
            >>> response.json.get('twitterUsername') == eval(expected).get('twitterUsername')
            True

    Success
        Retorna la llista d'usuaris que compleix la query especificada.

.. http:put:: /people/{username}

    Modifica un usuari del sistema pel seu posterior us si existeix. En cas de
    que l'usuari no existeixi retorna un error. La llista de paràmetres
    actualitzables de moment es limita a ``displayName`` i a
    ``twitterUsername``.

    :query username: (REST) L'identificador de l'usuari
    :query displayName: (Opcional) El nom real de l'usuari al sistema
    :query twitterUsername: (Opcional) El nom d'usuari de Twitter de l'usuari

    Cos de la petició

        .. code-block:: python

            {"displayName": "Lionel Messi", "twitterUsername": "messi10oficial"}

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "username": "messi",
                "displayName": "Lionel Messi",
                "subscribedTo": {
                    "totalItems": 0,
                    "items": []
                },
                "last_login": "2013-02-01T19:33:16Z",
                "published": "2013-02-01T19:33:16Z",
                "following": {
                    "totalItems": 0,
                    "items": []
                },
                "twitterUsername": "messi10oficial",
                "id": "510fd582aceee925d0f1ecd1"
            }

        .. -> expected
            >>> response = testapp.put('/people/{}'.format(username), payload, oauth2Header(username), status=200)
            >>> response
            <200 OK application/json body='{"usernam...>
            >>> response.json.get('displayName') == eval(expected).get('displayName')
            True
            >>> response.json.get('twitterUsername') == eval(expected).get('twitterUsername')
            True

    Success

        Retorna un objecte ``Person`` amb els paràmetres indicats modificats.

    Error

        .. code-block:: python

            {"error_description": "Unknown user: messi", "error": "UnknownUserError"}

.. http:get:: /people/{username}

    Retorna la informació d'un usuari del sistema. En cas de que l'usuari no
    existeixi retorna l'error especificat.

    :query username: (REST) L'identificador de l'usuari

    Cos de la petició

        Aquesta petició no necessita cos.

    Resposta esperada

        .. code-block:: python

            {
                "username": "messi",
                "displayName": "Lionel Messi",
                "subscribedTo": {
                    "totalItems": 0,
                    "items": []
                },
                "last_login": "2013-02-01T19:33:16Z",
                "published": "2013-02-01T19:33:16Z",
                "following": {
                    "totalItems": 0,
                    "items": []
                },
                "twitterUsername": "messi10oficial",
                "id": "510fd582aceee925d0f1ecd1"
            }

        .. -> expected
            >>> response = testapp.get('/people/{}'.format(username), "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json body='{"usernam...>
            >>> response.json.get('displayName') == eval(expected).get('displayName')
            True
            >>> response.json.get('twitterUsername') == eval(expected).get('twitterUsername')
            True

    Success

        Retorna un objecte ``Person``.

    Error

        .. code-block:: python

            {"error_description": "Unknown user: messi", "error": "UnknownUserError"}

.. http:get:: /people/{username}/avatar

    Retorna l'avatar (foto) de l'usuari del sistema. Aquest és un servei públic.

    :query username: (REST) L'identificador de l'usuari

    Success
        Retorna la imatge pel seu ús immediat.


Activitats de l'usuari
----------------------

Representa el conjunt d'activitats creades per un usuari i permet tant
llistar-les com crear-ne de noves.

.. http:post:: /people/{username}/activities

    Genera una activitat en el sistema. Els objectes d'aquesta activitat són els
    especificats en el protocol activitystrea.ms.

    :query username: (REST) Nom de l'usuari que crea l'activitat
    :query contexts: (Opcional) Per fer que una activitat estigui associada a un
        context determinat fa falta que enviem una llista d'objectes *context*
        (sota la clau ``contexts``) (ja que teòricament, podem fer que
        l'activitat estigui associada a varis contexts a l'hora), indicant com a
        ``objectType`` el tipus ``uri`` i les dades del context com a l'exemple.
    :query object: (Requerit) Per ara només suportat el tipus ``objectType``
        *note*. Ha de contindre les claus ``objectType`` i ``content`` el qual
        pot tractar-se d'un camp codificat amb HTML.

    Cos de la petició

        .. code-block:: python

            {
                "object": {
                    "objectType": "note",
                    "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
                }
            }

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "replies": {
                    "totalItems": 0,
                    "items": [

                    ]
                },
                "object": {
                    "content": "<p>[A] Testejant la creaci\\u00f3 d\'un canvi d\'estatus</p>",
                    "_keywords": [
                        "testejant",
                        "creaci\\u00f3",
                        "canvi",
                        "messi"
                    ],
                    "objectType": "note"
                },
                "actor": {
                    "username": "messi",
                    "displayName": "Lionel Messi",
                    "id": "510ec463e999fb129b5c4104",
                    "objectType": "person"
                },
                "verb": "post",
                "published": "2013-02-03T20:11:15Z",
                "id": "510fd582aceee925d0f1ecd1"
            }

        .. -> expected
            >>> response = testapp.post('/people/{}/activities'.format(username), payload, oauth2Header(username), status=201)
            >>> response
            <201 Created application/json body='{"replies...>
            >>> response.json.get('actor').get('displayName') == eval(expected).get('actor').get('displayName')
            True
            >>> response.json.get('object').get('objectType') == eval(expected).get('object').get('objectType')
            True

    Success

        Retorna un objecte del tipus ``Activity``.

    Error

        En cas de que l'usuari actor no sigui el mateix usuari que s'autentica via oAuth

            .. code-block:: python

                {u'error_description': u"You don't have permission to access xavi resources", u'error': u'Unauthorized'}

        En cas que l'usuari no existeixi

            .. code-block:: python

                {"error_description": "Unknown user: messi", "error": "UnknownUserError"}

    Tipus d'activitat suportats:
     * *note* (estatus d'usuari)

    Tipus d'activitat projectats:
     * *File*
     * *Event*
     * *Bookmark*
     * *Image*
     * *Video*
     * *Question*

En el cas que volguem lligar l'activitat a un context en concret, suposant que
l'usuari ha estat previament subscrit a aquest context.

    Cos de la petició

        .. code-block:: python

            {
                "contexts": [
                                {
                                    "url": "http://atenea.upc.edu",
                                    "objectType": "uri"
                                 }
                            ],
                "object": {
                    "objectType": "note",
                    "content": "<p>[A] Testejant la creació d'un canvi d'estatus a un context</p>"
                }
            }

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "contexts": [
                    {
                        "displayName": "Atenea",
                        "object": {
                            "url": "http://atenea.upc.edu",
                            "objectType": "uri"
                        },
                        "published": "2013-02-03T20:56:56Z",
                        "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                        "id": "510ecf18e999fb140d38f48e",
                        "permissions": [
                            "read",
                            "write",
                            "invite"
                        ]
                    }
                ],
                "object": {
                    "content": "<p>[A] Testejant la creaci\\u00f3 d\'un canvi d\'estatus a un context</p>",
                    "_keywords": [
                        "testejant",
                        "creaci\\u00f3",
                        "canvi",
                        "context",
                        "messi"
                    ],
                    "objectType": "note"
                },
                "actor": {
                    "username": "messi",
                    "displayName": "Lionel Messi",
                    "id": "510ecf18e999fb140d38f48d",
                    "objectType": "person"
                },
                "verb": "post",
                "replies": {
                    "totalItems": 0,
                    "items": [

                    ]
                },
                "id": "510ecf18e999fb140d38f491",
                "published": "2013-02-03T20:56:56Z"
            }

        .. -> expected
            >>> response = testapp.post('/people/{}/activities'.format(username), payload, oauth2Header(username), status=201)
            >>> response
            <201 Created application/json body='{"context...>
            >>> response.json.get('actor').get('displayName') == eval(expected).get('actor').get('displayName')
            True
            >>> response.json.get('object').get('objectType') == eval(expected).get('object').get('objectType')
            True
            >>> response.json.get('contexts')[0].get('object').get('url') == eval(expected).get('contexts')[0].get('object').get('url')
            True

.. http:get:: /people/{username}/activities

    Llista totes les activitats generades al sistema per part d'un usuari
    concret.

    :query username: (REST) Identificador d'usuari que crea l'activitat

    Cos de la petició

        Aquesta petició no necessita cos.

    Resposta esperada

        .. code-block:: python

            {
                "totalItems": 3,
                "items": [
                    {
                        "contexts": [
                            {
                                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                                "object": {
                                    "url": "http://atenea.upc.edu",
                                    "objectType": "uri"
                                },
                                "published": "2013-02-03T21:00:10Z",
                                "displayName": "Atenea",
                                "id": "510ecfdae999fb1424c14902",
                                "permissions": [
                                    "read",
                                    "write",
                                    "invite"
                                ]
                            }
                        ],
                        "object": {
                            "content": "<p>[A] Testejant la creaci\\u00f3 d\'un canvi d\'estatus a un context</p>",
                            "_keywords": [
                                "testejant",
                                "creaci\\u00f3",
                                "canvi",
                                "context",
                                "messi"
                            ],
                            "objectType": "note"
                        },
                        "actor": {
                            "username": "messi",
                            "displayName": "Lionel Messi",
                            "id": "510ecfdae999fb1424c14901",
                            "objectType": "person"
                        },
                        "verb": "post",
                        "replies": {
                            "totalItems": 0,
                            "items": [

                            ]
                        },
                        "id": "510ecfdae999fb1424c14905",
                        "published": "2013-02-03T21:00:10Z"
                    },
                    {
                        "replies": {
                            "totalItems": 0,
                            "items": [

                            ]
                        },
                        "object": {
                            "content": "<p>[A] Testejant la creaci\\u00f3 d\'un canvi d\'estatus</p>",
                            "_keywords": [
                                "testejant",
                                "creaci\\u00f3",
                                "canvi",
                                "messi"
                            ],
                            "objectType": "note"
                        },
                        "actor": {
                            "username": "messi",
                            "displayName": "Lionel Messi",
                            "id": "510ecfdae999fb1424c14901",
                            "objectType": "person"
                        },
                        "verb": "post",
                        "published": "2013-02-03T21:00:10Z",
                        "id": "510ecfdae999fb1424c14904"
                    },
                    {
                        "replies": {
                            "totalItems": 0,
                            "items": [

                            ]
                        },
                        "object": {
                            "url": "http://atenea.upc.edu",
                            "objectType": "uri"
                        },
                        "actor": {
                            "username": "messi",
                            "displayName": "messi",
                            "id": "510ecfdae999fb1424c14901",
                            "objectType": "person"
                        },
                        "verb": "subscribe",
                        "published": "2013-02-03T21:00:10Z",
                        "id": "510ecfdae999fb1424c14903"
                    }
                ]
            }

        .. -> expected
            >>> response = testapp.get('/people/{}/activities'.format(username), "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json body='{"totalIt...>
            >>> response.json.get('items')[0].get('actor').get('displayName') == eval(expected).get('items')[0].get('actor').get('displayName')
            True
            >>> response.json.get('totalItems') == eval(expected).get('totalItems')
            True

    .. note::

        En l'ultima resposta esperada hi han tres entrades les dues activitats
        que hem generat fins ara (amb context, i l'altre sense) i l'activitat
        que es genera quan es subscriu un usuari a un context, que es tracta com
        una activitat més.

    Success

        Retorna una col·lecció d'objectes del tipus ``Activity``.

    Error

        En cas de que l'usuari actor no sigui el mateix usuari que s'autentica
        via oAuth

            .. code-block:: python

                {u'error_description': u"You don't have permission to access xavi resources", u'error': u'Unauthorized'}

        En cas que l'usuari no existeixi

            .. code-block:: python

                {"error_description": "Unknown user: messi", "error": "UnknownUserError"}


Activitats globals
------------------

Torna el conjunt d'activitats generades pels usuaris del sistema a un context.
L'usuari que fa la petició ha de tindre permisos de lectura com a mínim en el
context requerit, de lo contrari se li denegarà l'accés. Típicament s'utilitza
per recuperar totes les activitats que els usuaris han associat a un context
concret.

.. http:get:: /activities

    Llistat de totes les activitats del sistema, filtrada sota algun criteri

    :query context: (Requerit) El hash (sha1) de la URL del context

    Cos de la petició

        .. code-block:: python

            {"context": "e6847aed3105e85ae603c56eb2790ce85e212997"}

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "totalItems": 1,
                "items": [
                    {
                        "contexts": [
                            {
                                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                                "object": {
                                    "url": "http://atenea.upc.edu",
                                    "objectType": "uri"
                                },
                                "published": "2013-02-03T22:14:50Z",
                                "displayName": "Atenea",
                                "id": "510ee15ae999fb15726fa1ec",
                                "permissions": [
                                    "read",
                                    "write",
                                    "invite"
                                ]
                            }
                        ],
                        "object": {
                            "content": "<p>[A] Testejant la creaci\\u00f3 d\'un canvi d\'estatus a un context</p>",
                            "_keywords": [
                                "testejant",
                                "creaci\\u00f3",
                                "canvi",
                                "context",
                                "messi"
                            ],
                            "objectType": "note"
                        },
                        "actor": {
                            "username": "messi",
                            "displayName": "Lionel Messi",
                            "id": "510ee15ae999fb15726fa1eb",
                            "objectType": "person"
                        },
                        "verb": "post",
                        "replies": {
                            "totalItems": 0,
                            "items": [

                            ]
                        },
                        "id": "510ee15ae999fb15726fa1ef",
                        "published": "2013-02-03T22:14:50Z"
                    }
                ],
                "context": {
                    "displayName": "Atenea",
                    "object": {
                        "url": "http://atenea.upc.edu",
                        "objectType": "uri"
                    },
                    "published": "2013-02-03T22:14:50Z",
                    "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                    "id": "510ee15ae999fb15726fa1ec",
                    "permissions": {
                        "write": "public",
                        "read": "public",
                        "join": "public",
                        "invite": "subscribed"
                    }
                }
            }

        .. -> expected
            >>> response = testapp.get('/activities', eval(payload), oauth2Header(username), status=200)
            >>> response
            <200 OK application/json body='{"totalIt...>
            >>> response.json.get('items')[0].get('actor').get('displayName') == eval(expected).get('items')[0].get('actor').get('displayName')
            True
            >>> response.json.get('totalItems') == eval(expected).get('totalItems')
            True

    Success
        Retorna una col·lecció d'objectes del tipus ``Activity``.


Timeline
--------

Representa el flux d'activitat global de l'usuari, que comprèn les activitats
que ha creat, les activitats de les persones a qui segueix i les activitats
generades sota els contexts concrets al qual està subscrit, directa o
indirectament.

.. http:get:: /people/{username}/timeline

    Llistat de totes les activitats del timeline de l'usuari. Actualment filtra
    les activitats i només mostra les de tipus *post*.

    :query username: (REST) Nom de l'usuari que del qual volem el llistat

    Cos de la petició

        Aquesta petició no necessita cos.

    Resposta esperada

        .. code-block:: python

            {
                "totalItems": 2,
                "items": [
                    {
                        "contexts": [
                            {
                                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                                "object": {
                                    "url": "http://atenea.upc.edu",
                                    "objectType": "uri"
                                },
                                "published": "2013-02-04T09:37:47Z",
                                "displayName": "Atenea",
                                "id": "510f816baceee9158ef3046c",
                                "permissions": [
                                    "read",
                                    "write",
                                    "invite"
                                ]
                            }
                        ],
                        "object": {
                            "content": "<p>[A] Testejant la creaci\\u00f3 d\'un canvi d\'estatus a un context</p>",
                            "_keywords": [
                                "testejant",
                                "creaci\\u00f3",
                                "canvi",
                                "context",
                                "messi"
                            ],
                            "objectType": "note"
                        },
                        "actor": {
                            "username": "messi",
                            "displayName": "Lionel Messi",
                            "id": "510f816baceee9158ef3046b",
                            "objectType": "person"
                        },
                        "verb": "post",
                        "replies": {
                            "totalItems": 0,
                            "items": [

                            ]
                        },
                        "id": "510f816baceee9158ef3046f",
                        "published": "2013-02-04T09:37:47Z"
                    },
                    {
                        "replies": {
                            "totalItems": 0,
                            "items": [

                            ]
                        },
                        "object": {
                            "content": "<p>[A] Testejant la creaci\\u00f3 d\'un canvi d\'estatus</p>",
                            "_keywords": [
                                "testejant",
                                "creaci\\u00f3",
                                "canvi",
                                "messi"
                            ],
                            "objectType": "note"
                        },
                        "actor": {
                            "username": "messi",
                            "displayName": "Lionel Messi",
                            "id": "510f816baceee9158ef3046b",
                            "objectType": "person"
                        },
                        "verb": "post",
                        "published": "2013-02-04T09:37:47Z",
                        "id": "510f816baceee9158ef3046e"
                    }
                ]
            }

        .. -> expected
            >>> response = testapp.get('/people/{}/timeline'.format(username), "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json body='{"totalIt...>
            >>> response.json.get('items')[0].get('actor').get('displayName') == eval(expected).get('items')[0].get('actor').get('displayName')
            True
            >>> response.json.get('totalItems') == eval(expected).get('totalItems')
            True

    Success

        Retorna una col·lecció d'objectes del tipus ``Activity``.


Comentaris d'una activitat
----------------------------

Representa el conjunt de comentaris fets a una activitat.

.. http:post:: /activities/{activity}/comments

    Afegeix un comentari a una activitat ja existent al sistema. Aquest servei
    crea el comentari pròpiament dit dins de l'activitat i genera una activitat
    nova del tipus *comment* (l'usuari ha comentat l'activitat... )

    :query activity: (REST) Ha de ser un identificador vàlid d'una activitat
        existent, per exemple: 4e6eefc5aceee9210d000004
    :query object: (Requerit) El tipus (``objectType``) d'una activitat
        comentari ha de ser *comment*. Ha de contindre les claus ``objectType``
        i ``content``.

    Cos de la petició

        .. code-block:: python

            {
                "object": {
                    "objectType": "comment",
                    "content": "<p>[C] Testejant un comentari nou a una activitat</p>"
                }
            }

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "replies": {
                    "totalItems": 0,
                    "items": []
                },
                "object": {
                    "content": "<p>[C] Testejant un comentari nou a una activitat</p>",
                    "inReplyTo": [
                        {
                            "id": "510f88e6aceee91b02bc5a91",
                            "objectType": "note"
                        }
                    ],
                    "_keywords": [
                        "testejant",
                        "comentari",
                        "nou",
                        "una",
                        "activitat",
                        "messi"
                    ],
                    "objectType": "comment"
                },
                "actor": {
                    "username": "messi",
                    "displayName": "Lionel Messi",
                    "id": "510f88e6aceee91b02bc5a8c",
                    "objectType": "person"
                },
                "verb": "comment",
                "published": "2013-02-04T10:09:42Z",
                "id": "510f88e6aceee91b02bc5a92"
            }

        .. -> expected
            >>> activity = utils.create_activity(username, user_status)
            >>> response = testapp.post('/activities/{}/comments'.format(activity.json.get('id')), payload, oauth2Header(username), status=201)
            >>> response
            <201 Created application/json body='{"replies...>
            >>> response.json.get('actor').get('displayName') == eval(expected).get('actor').get('displayName')
            True
            >>> response.json.get('verb') == eval(expected).get('verb')
            True

    Success

        Retorna l'objecte ``Activity`` del comentari.

.. http:get:: /activities/{activity}/comments

    Llista tots els comentaris d'una activitat

    :query activity: (REST) ha de ser un identificador vàlid d'una activitat
        existent, per exemple: 4e6eefc5aceee9210d000004

    Cos de la petició

         Aquesta petició no necessita cos.

    Resposta esperada

        .. code-block:: python

            {
                "totalItems": 1,
                "items": [
                    {
                        "_keywords": [
                            "testejant",
                            "comentari",
                            "nou",
                            "una",
                            "activitat",
                            "messi"
                        ],
                        "author": {
                            "username": "messi",
                            "displayName": "Lionel Messi",
                            "subscribedTo": {
                                "totalItems": 1,
                                "items": [
                                    {
                                        "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                                        "object": {
                                            "url": "http://atenea.upc.edu",
                                            "objectType": "uri"
                                        },
                                        "published": "2013-02-04T10:31:18Z",
                                        "displayName": "Atenea",
                                        "id": "510f8df6aceee91ead30bf2d",
                                        "permissions": [
                                            "read",
                                            "write",
                                            "invite"
                                        ]
                                    }
                                ]
                            },
                            "last_login": "2013-02-04T10:31:18Z",
                            "published": "2013-02-04T10:31:18Z",
                            "following": {
                                "totalItems": 0,
                                "items": []
                            },
                            "twitterUsername": "messi10oficial",
                            "id": "510f8df6aceee91ead30bf2c"
                        },
                        "content": "<p>[C] Testejant un comentari nou a una activitat</p>",
                        "published": "2013-02-04T10:31:18Z",
                        "id": "510f8df6aceee91ead30bf32",
                        "objectType": "comment"
                    }
                ]
            }

        .. -> expected
            >>> response = testapp.get('/activities/{}/comments'.format(activity.json.get('id')), payload, oauth2Header(username), status=200)
            >>> response
            <200 OK application/json body='{"totalIt...>
            >>> response.json.get('items')[0].get('author').get('displayName') == eval(expected).get('items')[0].get('author').get('displayName')
            True
            >>> response.json.get('totalItems') == eval(expected).get('totalItems')
            True

    Success

        Retorna una col·lecció d'objectes del tipus ``Comment``


Subscripcions
--------------

Representa el conjunt de contextes als quals esta subscrit un usuari.

.. http:get:: /people/{username}/subscriptions

    Torna totes les subscripcions d'un usuari

    :query username: (REST) L'identificador de l'usuari al sistema

    Cos de la petició

         Aquesta petició no necessita cos.

    Resposta esperada

        .. code-block:: python

            {
                "totalItems": 1,
                "items": [
                    {
                        "username": "messi",
                        "id": "51112aafaceee94e58dcf34d",
                        "subscribedTo": {
                            "totalItems": 1,
                            "items": [
                                {
                                    "displayName": "Atenea",
                                    "object": {
                                        "url": "http://atenea.upc.edu",
                                        "objectType": "uri"
                                    },
                                    "published": "2013-02-05T15:52:15Z",
                                    "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                                    "id": "51112aafaceee94e58dcf34e",
                                    "permissions": [
                                        "read",
                                        "write",
                                        "invite"
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }

        .. -> expected
            >>> response = testapp.get('/people/{}/subscriptions'.format(username), "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json body='{"totalIt...>
            >>> response.json.get('items')[0].get('subscribedTo').get('totalItems') == eval(expected).get('items')[0].get('subscribedTo').get('totalItems')
            True
            >>> response.json.get('totalItems') == eval(expected).get('totalItems')
            True




Missatges i converses
---------------------

El MAX implementa des de la seva versió 3.0 la funcionalitat de missatgeria
instantània asíncrona entre els seus usuaris. Aquests són els serveis associats.

.. setup other user for conversations interaction

    >>> username2 = 'xavi'
    >>> utils.create_user(username2)
    <201 Created application/json body='{"usernam...>

.. http:post:: /conversations

    Retorna totes les converses depenent de l'actor que faci la petició.

    :query contexts: (Requerit) Tipus d'objecte al qual ens volem subscriure (en
        aquest cas ``conversation``). Hem de proporcionar un objecte amb les claus
        ``objectType`` i el valor ``conversation``, i la llista de
        ``participants`` com a l'exemple
    :query object: (Requerit) Tipus d'objecte de la conversa. Hem de
        proporcionar un objecte (per ara només es permet el tipus `message`) i
        el contingut amb les dades ``content`` amb el cos del missatge
        propiament dit

    Cos de la petició

        .. code-block:: python

            {
                "contexts": [
                    {
                        "objectType":"conversation",
                        "participants": ["messi", "xavi"]
                    }
                ],
                "object": {
                    "objectType": "message",
                    "content": "Nos espera una gran temporada, no es cierto?"
                }
            }

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "contexts": [
                    {
                        "displayName": "messi, xavi",
                        "object": {
                            "participants": [
                                "messi",
                                "xavi"
                            ],
                            "objectType": "conversation"
                        },
                        "published": "2013-02-05T20:07:23Z",
                        "hash": "26a788ea21a872f14039da80a2a98831f2146c85",
                        "id": "5111667be999fb0d6a01d44b",
                        "permissions": [
                            "read",
                            "write"
                        ]
                    }
                ],
                "object": {
                    "content": "Nos espera una gran temporada, no es cierto?",
                    "_keywords": [
                        "nos",
                        "espera",
                        "una",
                        "gran",
                        "temporada",
                        "cierto",
                        "messi"
                    ],
                    "objectType": "message"
                },
                "actor": {
                    "username": "messi",
                    "displayName": "Lionel Messi",
                    "id": "5111667ae999fb0d6a01d443",
                    "objectType": "person"
                },
                "verb": "post",
                "replies": {
                    "totalItems": 0,
                    "items": []
                },
                "id": "5111667be999fb0d6a01d44c",
                "published": "2013-02-05T20:07:23Z"
            }

        .. -> expected
            >>> response = testapp.post('/conversations', payload, oauth2Header(username), status=201)
            >>> response
            <201 Created application/json body='{"context...>
            >>> response.json.get('object').get('objectType') == eval(expected).get('object').get('objectType')
            True
            >>> response.json.get('contexts')[0].get('displayName') == eval(expected).get('contexts')[0].get('displayName')
            True
            >>> conversation_hash = response.json.get('contexts')[0].get('hash')

    Success

        Retorna l'objecte ``Message`` (activitat).


.. http:get:: /conversations/{hash}/messages

    Retorna tots els missatges d'una conversa

    :query hash: (REST) El hash de la conversa en concret. Aquest hash es
        calcula fent una suma de verificació sha1 de la llista de participants
        (ordenada alfabèticament i sense espais) de la conversa

    Cos de la petició

        Aquesta petició no te cos.

    Resposta esperada

        .. code-block:: python

            {
                "totalItems": 1,
                "items": [
                    {
                        "contexts": [
                            {
                                "hash": "26a788ea21a872f14039da80a2a98831f2146c85",
                                "object": {
                                    "participants": [
                                        "messi",
                                        "xavi"
                                    ],
                                    "objectType": "conversation"
                                },
                                "published": "2013-02-05T20:21:07Z",
                                "displayName": "messi, xavi",
                                "id": "511169b3e999fb0dd75b20d4",
                                "permissions": [
                                    "read",
                                    "write"
                                ]
                            }
                        ],
                        "object": {
                            "content": "Nos espera una gran temporada, no es cierto?",
                            "_keywords": [
                                "nos",
                                "espera",
                                "una",
                                "gran",
                                "temporada",
                                "cierto",
                                "messi"
                            ],
                            "objectType": "message"
                        },
                        "actor": {
                            "username": "messi",
                            "displayName": "Lionel Messi",
                            "id": "511169b3e999fb0dd75b20cc",
                            "objectType": "person"
                        },
                        "verb": "post",
                        "replies": {
                            "totalItems": 0,
                            "items": []
                        },
                        "id": "511169b3e999fb0dd75b20d5",
                        "published": "2013-02-05T20:21:07Z"
                    }
                ]
            }

        .. -> expected
            >>> response = testapp.get('/conversations/{}/messages'.format(conversation_hash), "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json body='{"totalIt...>
            >>> response.json.get('items')[0].get('object').get('objectType') == eval(expected).get('items')[0].get('object').get('objectType')
            True
            >>> response.json.get('items')[0].get('contexts')[0].get('displayName') == eval(expected).get('items')[0].get('contexts')[0].get('displayName')
            True

    Success

        Retorna una llista d'objectes ``Message`

.. http:get:: /conversations

    Retorna totes les converses depenent de l'actor que faci la petició

    Cos de la petició

        Aquesta petició no te cos.

    Resposta esperada

        .. code-block:: python

            {
                "totalItems": 1,
                "items": [
                    {
                        "hash": "26a788ea21a872f14039da80a2a98831f2146c85",
                        "object": {
                            "participants": [
                                "messi",
                                "xavi"
                            ],
                            "messages": 1,
                            "lastMessage": {
                                "content": "Nos espera una gran temporada, no es cierto?",
                                "published": "2013-02-05T20:28:24Z"
                            },
                            "objectType": "conversation"
                        },
                        "published": "2013-02-05T20:28:24Z",
                        "displayName": "messi, xavi",
                        "id": "51116b68e999fb0e12a9cf9b",
                        "permissions": {
                            "read": "subscribed",
                            "write": "subscribed",
                            "join": "restricted",
                            "invite": "restricted"
                        }
                    }
                ]
            }

        .. -> expected
            >>> response = testapp.get('/conversations', "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json body='{"totalIt...>
            >>> response.json.get('items')[0].get('object').get('objectType') == eval(expected).get('items')[0].get('object').get('objectType')
            True
            >>> response.json.get('items')[0].get('displayName') == eval(expected).get('items')[0].get('displayName')
            True

    Success

        Retorna una llista d'objectes del tipus ``Conversation``.

.. http:post:: /conversations/{hash}/messages

    Crea un missatge nou a una conversa ja existent

    :query hash: (REST) El hash de la conversa en concret. Aquest hash es
        calcula fent una suma de verificació sha1 de la llista de participants
        (ordenada alfabèticament i sense espais) de la conversa

    Cos de la petició

        .. code-block:: python

            {
                "object": {
                    "objectType": "message",
                    "content": "M'agrada Taradell!"
                }
            }

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "contexts": [
                    {
                        "displayName": "messi, xavi",
                        "object": {
                            "participants": [
                                "messi",
                                "xavi"
                            ],
                            "objectType": "conversation"
                        },
                        "published": "2013-02-05T20:34:48Z",
                        "hash": "26a788ea21a872f14039da80a2a98831f2146c85",
                        "id": "51116ce8e999fb0e3f274d6a",
                        "permissions": [
                            "read",
                            "write"
                        ]
                    }
                ],
                "object": {
                    "content": "M\'agrada Taradell!",
                    "_keywords": [
                        "taradell",
                        "messi"
                    ],
                    "objectType": "message"
                },
                "actor": {
                    "username": "messi",
                    "displayName": "Lionel Messi",
                    "id": "51116ce8e999fb0e3f274d62",
                    "objectType": "person"
                },
                "verb": "post",
                "replies": {
                    "totalItems": 0,
                    "items": [

                    ]
                },
                "id": "51116ce8e999fb0e3f274d6c",
                "published": "2013-02-05T20:34:48Z"
            }

        .. -> expected
            >>> response = testapp.post('/conversations/{}/messages'.format(conversation_hash), payload, oauth2Header(username), status=201)
            >>> response
            <201 Created application/json body='{"context...>
            >>> response.json.get('object').get('objectType') == eval(expected).get('object').get('objectType')
            True
            >>> response.json.get('contexts')[0].get('displayName') == eval(expected).get('contexts')[0].get('displayName')
            True

    Success

        Retorna l'objecte ``Message`` (activitat).

.. doctests teardown (absolutelly needed)

    >>> HTTPretty.disable()
