API REST (restringida)
======================

Aquesta és la llista de serveis REST que queda fora de la operativa d'usuari i
de la UI. Està dissenyada per l'ús d'un usuari restringit d'aplicació pel qual
prèviament se li ha d'haver donat permisos al sistema. Aquest usuari no te cap
privilegi addicional sobre el sistema que el que s'exposa en la descripció de
cada servei.

.. test fixtures
    >>> from httpretty import HTTPretty
    >>> HTTPretty.enable()
    >>> HTTPretty.register_uri(HTTPretty.POST, "http://localhost:8080/checktoken", body="", status=200)
    >>> from max.tests import test_manager
    >>> username = "messi"
    >>> utils = MaxTestBase(testapp)

Usuaris
-------

.. http:post:: /people/{username}

    Crea un usuari remotament al sistema pel seu posterior ús si no existeix.
    En cas de que l'usuari ja existis, el retorna canviant el codi d'estat HTTP
    en funció de l'acció realitzada.

    :query username: (REST) L'identificador del nou usuari al sistema
    :query displayName: (Opcional) El nom real (de pantalla) de l'usuari al
        sistema

    Cos de la petició

        .. code-block:: python

            {"username": "messi", "displayName": "Lionel Messi"}

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "username": "messi",
                "displayName": "messi",
                "subscribedTo": {
                    "totalItems": 0,
                    "items": []
                },
                "last_login": "2013-02-04T15:36:34Z",
                "published": "2013-02-04T15:36:34Z",
                "following": {
                    "totalItems": 0,
                    "items": []
                },
                "id": "510fd582aceee925d0f1ecd1"
            }

        .. -> expected
            >>> response = testapp.post('/people/{}'.format(username), "", oauth2Header(test_manager), status=201)
            >>> response
            <201 Created application/json body='{"usernam...>
            >>> response.json.get('displayName') == eval(expected).get('displayName')
            True
            >>> response.json.get('twitterUsername') == eval(expected).get('twitterUsername')
            True

    Success

        Retorna un objecte ``Person``.


Contexts
--------

.. http:post:: /contexts

    Crea un context al sistema.

    :query url: (Requerit) Una clau de tipus ``object`` que identifica al
        context indicant com a ``objectType`` el tipus ``uri`` i la URL del
        context com a l'exemple.
    :query displayName: (Opcional) El nom per mostrar a la UI.
    :query twitterHashtag: (Opcional) El hashtag (#) que identifica els posts
        a Twitter com a posts del context. Tots els posts d'usuaris del
        sistema i amb permisos al context amb compta de twitter informada
        s'importaran i apareixeran a l'activitat del context.
    :query twitterUsername: (Opcional) El nom d'usuari de Twitter que aquest
        context té assignat. Qualsevol post fet a Twitter amb aquest usuari
        s'importarà i apareixerà a l'activitat del context com activitat
        (impersonat) del propi context.
    :query permissions: (Opcional) Els permisos i parametrització de seguretat
        relacionada amb el context.

    Cos de la petició

        .. code-block:: python

            {
                "object": {
                    "url": "http://atenea.upc.edu",
                    "objectType": "uri"
                },
                "displayName": "Atenea"
            }

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "displayName": "Atenea",
                "object": {
                    "url": "http://atenea.upc.edu",
                    "objectType": "uri"
                },
                "published": "2013-02-04T16:28:03Z",
                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                "id": "510fe193aceee92cc82408cb",
                "permissions": {
                    "read": "public",
                    "write": "public",
                    "join": "public",
                    "invite": "public"
                }
            }

        .. -> expected
            >>> response = testapp.post('/contexts', payload, oauth2Header(test_manager), status=201)
            >>> response
            <201 Created application/json body='{"display...>
            >>> response.json.get('displayName') == eval(expected).get('displayName')
            True
            >>> response.json.get('hash') == eval(expected).get('hash')
            True
            >>> context_hash = response.json.get('hash')

    Success

        Retorna l'objecte ``Context``.

.. http:put:: /contexts/{hash}

    Modifica un context al sistema.

    :query hash: (REST) El hash del context en concret. Aquest hash es calcula
        fent una suma de verificació sha1 de la URL del context.
    :query displayName: (Opcional) El nom per mostrar a la UI.
    :query twitterHashtag: (Opcional) El hashtag (#) que identifica els posts
        a Twitter com a posts del context. Tots els posts d'usuaris del
        sistema i amb permisos al context amb compta de twitter informada
        s'importaran i apareixeran a l'activitat del context.
    :query twitterUsername: (Opcional) El nom d'usuari de Twitter que aquest
        context té assignat. Qualsevol post fet a Twitter amb aquest usuari
        s'importarà i apareixerà a l'activitat del context com activitat
        (impersonat) del propi context.

    Cos de la petició

        .. code-block:: python

            { "twitterHashtag": "assignatura1" }

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "twitterHashtag": "assignatura1",
                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                "object": {
                    "url": "http://atenea.upc.edu",
                    "objectType": "uri"
                },
                "published": "2013-02-05T14:55:23Z",
                "displayName": "Atenea",
                "id": "51111d5baceee9464d989908",
                "permissions": {
                    "read": "public",
                    "write": "public",
                    "join": "public",
                    "invite": "public"
                }
            }

        .. -> expected
            >>> response = testapp.put('/contexts/{}'.format(context_hash), payload, oauth2Header(test_manager), status=200)
            >>> response
            <200 OK application/json body='{"twitter...>
            >>> response.json.get('displayName') == eval(expected).get('displayName')
            True
            >>> response.json.get('hash') == eval(expected).get('hash')
            True

    Success

        Retorna l'objecte ``Context`` modificat.

.. http:get:: /contexts/{hash}

    Retorna la informació d'un objecte ``Context``.

    :query hash: (REST) El hash del context en concret. Aquest hash es calcula
        fent una suma de verificació sha1 de la URL del context.

    Cos de la petició

        Aquesta petició no te cos.

    Resposta esperada

        .. code-block:: python

            {
                "twitterHashtag": "assignatura1",
                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                "object": {
                    "url": "http://atenea.upc.edu",
                    "objectType": "uri"
                },
                "published": "2013-02-05T14:55:23Z",
                "displayName": "Atenea",
                "id": "51111d5baceee9464d989908",
                "permissions": {
                    "read": "public",
                    "write": "public",
                    "join": "public",
                    "invite": "public"
                }
            }

        .. -> expected
            >>> response = testapp.get('/contexts/{}'.format(context_hash), "", oauth2Header(test_manager), status=200)
            >>> response
            <200 OK application/json body='{"twitter...>
            >>> response.json.get('displayName') == eval(expected).get('displayName')
            True
            >>> response.json.get('hash') == eval(expected).get('hash')
            True

    Success

        Retorna un objecte del tipus ``Context``.

.. http:delete:: /contexts/{hash}

    Esborra un objecte ``Context`` i les subscripcions de tots els usuaris subscrits a aquell contexte
    NO esborra les activitats que s'hagin creat previament a l'esborrat. Tot i que les activitats que queden
    a la base de dades no es poden consultar direcatament, en el timeline de un usuari coninuarà veient les activitats que va crear ell.

    :query hash: (REST) El hash del context en concret. Aquest hash es calcula
        fent una suma de verificació sha1 dels paràmetres del context

    Cos de la petició

        Aquesta petició no te cos.

.. Create the context to delete in this test

    >>> create_context = { "object": {"url": "http://atenea.upc.edu", "objectType": "uri" } }
    >>> resp = utils.create_context(create_context)
    >>> context_hash_for_deleting = resp.json.get('hash')

    Resposta esperada

        Retorna un codi HTTP 204 (deleted) amb el cos buit

        .. actual test
            >>> response = testapp.delete('/contexts/{}'.format(context_hash_for_deleting), "", oauth2Header(test_manager), status=204)
            >>> response
            <204 No Content no body>

    Success

        Retorna un codi HTTP 204 (deleted) amb el cos buit


.. http:get:: /contexts/{hash}/avatar

    Retorna la imatge que li correspon al context depenent del usuari de
    Twitter que te assignat. Si no en te cap, retorna una imatge estàndar. Per
    ara només està implementada la integració amb Twitter i dissenyat per quan
    un context vol *parlar* impersonat a l'activitat del seu propi context.
    Per exemple, una assignatura.

    Aquest és un servei públic.

    :query hash: (REST) El hash del context en concret. Aquest hash es calcula
        fent una suma de verificació sha1 de la URL del context.

    Success

        Retorna la imatge del context.


Subscripcions
-------------

.. http:post:: /people/{username}/subscriptions

    Subscriu l'usuari a un context determinat.

    :query username: (REST) L'identificador de l'usuari al sistema.
    :query contexts: (Requerit) Tipus d'objecte al qual ens volem subscriure, en
        aquest cas del tipus `context`. Hem de proporcionar un objecte amb les
        claus ``objectType`` i el valor *context*, i la dada ``url`` del context.

    Cos de la petició

        .. code-block:: python

            {
                "object": {
                    "objectType": "uri",
                    "url": "http://atenea.upc.edu"
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
                    "url": "http://atenea.upc.edu",
                    "objectType": "uri"
                },
                "actor": {
                    "username": "messi",
                    "displayName": "messi",
                    "id": "511121f6aceee949e9da50d4",
                    "objectType": "person"
                },
                "verb": "subscribe",
                "published": "2013-02-05T15:15:02Z",
                "id": "511121f6aceee949e9da50d6"
            }

        .. -> expected
            >>> response = testapp.post('/people/{}/subscriptions'.format(username), payload, oauth2Header(test_manager), status=201)
            >>> response
            <201 Created application/json body='{"replies...>
            >>> response.json.get('displayName') == eval(expected).get('displayName')
            True
            >>> response.json.get('verb') == eval(expected).get('verb')
            True

    Success

        Retorna un objecte del tipus ``Activity``.

    Error

        En cas que l'usuari no existeixi

            .. code-block:: python

                { "error_description": "Unknown user: messi", "error": "UnknownUserError" }


Permisos a contexts
-------------------

Sobre els objectes context es poden otorgar o revocar permisos a usuaris del
sistema. Aquests permisos són bàsicament de lectura/escriptura, tal i com
s'explica amb profunditat en l'apartat de permisos.

.. http:put:: /contexts/{hash}/permissions/{username}/{permission}

    Afegeix els permisos per un context donat un identificador d'usuari i el
    permís que li vols donar.

    :query hash: (REST) El hash del context en concret. Aquest hash es calcula
        fent una suma de verificació sha1 de la URL del context.
    :query username: (REST) L'identificador del nou usuari al sistema
    :query permission: (REST) El permís que li volem otorgar a l'usuari

    Cos de la petició

        Aquesta petició no te cos.

    Resposta esperada

        .. code-block:: python

            {
                "displayName": "http://atenea.upc.edu",
                "object": {
                    "url": "http://atenea.upc.edu",
                    "objectType": "uri"
                },
                "published": "2013-02-05T19:38:25Z",
                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                "id": "51115fb1e999fb0cabd43ba8",
                "permissions": [
                    "read",
                    "write",
                    "invite"
                ]
            }

        .. -> expected
            >>> response = testapp.put('/contexts/{}/permissions/{}/write'.format(context_hash, username), "", oauth2Header(test_manager), status=200)
            >>> response
            <200 OK application/json body='{"display...>

    Success

        Si el permís ja estava otorgat, el codi HTTP de resposta és 200, si no, torna un 201.
        En el cos, torna l'objecte ``Context`` modificat.

.. http:delete:: /contexts/{hash}/permissions/{username}/{permission}

    Esborra els permisos per un context donat un identificador d'usuari i el
    permís que li vols donar.

    :query hash: (REST) El hash del context en concret. Aquest hash es calcula
        fent una suma de verificació sha1 de la URL del context.
    :query username: (REST) L'identificador del nou usuari al sistema
    :query permission: (REST) El permís que li volem otorgar a l'usuari

    Cos de la petició

        Aquesta petició no te cos.

    Resposta esperada

        .. code-block:: python

            {
                "displayName": "http://atenea.upc.edu",
                "object": {
                    "url": "http://atenea.upc.edu",
                    "objectType": "uri"
                },
                "published": "2013-02-05T19:40:25Z",
                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                "id": "51116029e999fb0cb57338b3",
                "permissions": [
                    "read",
                    "invite"
                ]
            }

        .. -> expected
            >>> response = testapp.delete('/contexts/{}/permissions/{}/write'.format(context_hash, username), "", oauth2Header(test_manager), status=200)
            >>> response
            <200 OK application/json body='{"display...>
            >>> response.json.get('displayName') == eval(expected).get('displayName')
            True
            >>> response.json.get('permissions') == eval(expected).get('permissions')
            True

.. put the write permissions of the test user back for further testing :)

    >>> testapp.put('/contexts/{}/permissions/{}/write'.format(context_hash, username), "", oauth2Header(test_manager), status=201)
    <201 Created application/json body='{"hash": ...>

    Success

        Torna l'objecte ``Context`` modificat.


Activitats
----------

.. http:post:: /admin/people/{username}/activities

    Afegeix una activitat en nom d'un usuari qualsevol

    :query username: (REST) El nom d'usuari en nom del qual es crearà
        l'activitat
    :query contexts: (Opcional) Per fer que una activitat estigui associada a un
        context determinat fa falta que enviem una llista d'objectes *context*
        (sota la clau ``contexts``) (ja que teòricament, podem fer que
        l'activitat estigui associada a varis contexts a l'hora), indicant com a
        ``objectType`` el tipus ``uri`` i les dades del context com a l'exemple
    :query object: (Requerit) Per ara només suportat el tipus (``objectType``)
        *note*. Ha de contindre les claus ``objectType`` i ``content`` que pot
        tractar-se d'un camp codificat amb HTML

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
                        "twitterHashtag": "assignatura1",
                        "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                        "object": {
                            "url": "http://atenea.upc.edu",
                            "objectType": "uri"
                        },
                        "published": "2013-02-05T15:24:38Z",
                        "displayName": "Atenea",
                        "id": "51112436aceee94b85795c13",
                        "permissions": [
                            "read",
                            "write"
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
                    "displayName": "messi",
                    "id": "51112436aceee94b85795c12",
                    "objectType": "person"
                },
                "verb": "post",
                "replies": {
                    "totalItems": 0,
                    "items": [

                    ]
                },
                "id": "51112436aceee94b85795c15",
                "published": "2013-02-05T15:24:38Z"
            }

        .. -> expected
            >>> response = testapp.post('/admin/people/{}/activities'.format(username), payload, oauth2Header(test_manager), status=201)
            >>> response
            <201 Created application/json body='{"context...>
            >>> response.json.get('displayName') == eval(expected).get('displayName')
            True
            >>> response.json.get('verb') == eval(expected).get('verb')
            True

.. http:post:: /admin/contexts/{hash}/activities

    Afegeix una activitat en nom d'un context qualsevol

    :query hash: (REST) El hash del context en nom del qual es crearà
        l'activitat
    :query contexts: (Requerit) Per fer que una activitat estigui associada a un
        context determinat fa falta que enviem una llista d'objectes *context*
        (sota la clau ``contexts``) (ja que teòricament, podem fer que
        l'activitat estigui associada a varis contexts a l'hora), indicant com a
        ``objectType`` el tipus ``uri`` i les dades del context com a l'exemple.
        En aquest cas d'ús el contexte especificat aquí ha de ser el mateix que
        l'especificat al paràmetre {hash}
    :query object: (Requerit) Per ara només suportat el tipus (``objectType``)
        `note`. Ha de contindre les claus ``objectType`` i ``content`` que pot
        tractar-se d'un camp codificat amb HTML.

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
                        "twitterHashtag": "assignatura1",
                        "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                        "object": {
                            "url": "http://atenea.upc.edu",
                            "objectType": "uri"
                        },
                        "published": "2013-02-05T15:24:38Z",
                        "displayName": "Atenea",
                        "id": "51112436aceee94b85795c13",
                        "permissions": [
                            "read",
                            "write"
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
                    "displayName": "messi",
                    "id": "51112436aceee94b85795c12",
                    "objectType": "person"
                },
                "verb": "post",
                "replies": {
                    "totalItems": 0,
                    "items": [

                    ]
                },
                "id": "51112436aceee94b85795c15",
                "published": "2013-02-05T15:24:38Z"
            }

        .. -> expected
            >>> response = testapp.post('/admin/contexts/{}/activities'.format(context_hash), payload, oauth2Header(test_manager), status=201)
            >>> response
            <201 Created application/json body='{"context...>
            >>> response.json.get('displayName') == eval(expected).get('displayName')
            True
            >>> response.json.get('verb') == eval(expected).get('verb')
            True


.. doctests teardown (absolutelly needed)

    >>> HTTPretty.disable()
