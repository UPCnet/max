API REST (restringida)
======================

Aquesta és la llista de serveis REST que queda fora de la operativa d'usuari i
de la UI. Està dissenyada per l'ús d'un usuari restringit d'aplicació pel qual
prèviament se li ha d'haver donat permisos al sistema. Aquest usuari no te cap
privilegi addicional sobre el sistema que el que s'exposa en la descripció de
cada servei.

.. test fixtures
    >>> from httpretty import HTTPretty
    >>> import json
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
                "iosDevices": [],
                "displayName": "messi",
                "talkingIn": [],
                "creator": "test_manager",
                "androidDevices": [],
                "following": [],
                "subscribedTo": [],
                "last_login": "2000-01-01T00:01:00Z",
                "published": "2000-01-01T00:01:00Z",
                "owner": "test_manager",
                "id": "519b00000000000000000000",
                "objectType": "person"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.post('/people/{}'.format(username), "", oauth2Header(test_manager), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('displayName') == expected.get('displayName')
            True
            >>> response.json.get('twitterUsername') == expected.get('twitterUsername')
            True

    Success

        Retorna un objecte ``Person``.


Contexts
--------

.. http:post:: /contexts

    Crea un context al sistema.

    :query objectType: (Obligatori) De moment se suporta el tipus ``context``
    :query url: La URL amb la qual s'identifica el context.
    :query displayName: (Opcional) El nom per mostrar a la UI. Si no s'especifica, es
        mostrarà la url
    :query twitterHashtag: (Opcional) El hashtag (#) que identifica els posts
        a Twitter com a posts del context. Tots els posts d'usuaris del
        sistema i amb permisos al context amb compta de twitter informada
        s'importaran i apareixeran a l'activitat del context.
    :query twitterUsername: (Opcional) El nom d'usuari de Twitter que aquest
        context té assignat. Qualsevol post fet a Twitter amb aquest usuari
        s'importarà i apareixerà a l'activitat del context com activitat
        (impersonat) del propi context.
    :query permissions: (Opcional) Els permisos i parametrització de seguretat
        relacionada amb el context. Per defecte els contextos són públics a tots
        els efectes.
    :query tags: (Opcional) Llista de tags per categoritzar un contexte

    Cos de la petició

        .. code-block:: python

            {
                "url": "http://atenea.upc.edu",
                "objectType": "context",
                "displayName": "Atenea",
                "tags": ["Assignatura"]
            }

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "displayName": "Atenea",
                "creator": "test_manager",
                "url": "http://atenea.upc.edu",
                "tags": [
                    "Assignatura"
                ],
                "published": "2000-01-01T00:01:00Z",
                "owner": "test_manager",
                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                "permissions": {
                    "read": "public",
                    "write": "public",
                    "invite": "public",
                    "subscribe": "public"
                },
                "id": "519b00000000000000000000",
                "objectType": "context"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.post('/contexts', payload, oauth2Header(test_manager), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('displayName') == expected.get('displayName')
            True
            >>> response.json.get('hash') == expected.get('hash')
            True
            >>> context_hash = response.json.get('hash')

    Success

        Retorna l'objecte ``Context``.

.. http:get:: /contexts

    Cerca un context al sistema

    :tags: (Opcional)

    Cos de la petició

        .. code-block:: python

            {
                "tags": "Assignatura"
            }

        .. -> payload

    Resposta esperada

        .. code-block:: python

            [
                {
                    "displayName": "Atenea",
                    "creator": "test_manager",
                    "url": "http://atenea.upc.edu",
                    "tags": [
                        "Assignatura"
                    ],
                    "published": "2000-01-01T00:01:00Z",
                    "owner": "test_manager",
                    "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                    "objectType": "context",
                    "id": "519b00000000000000000000",
                    "permissions": {
                        "read": "public",
                        "write": "public",
                        "invite": "public",
                        "subscribe": "public"
                    }
                }
            ]

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.get('/contexts', payload, oauth2Header(test_manager), status=200)
            >>> response
            <200 OK application/json ...
            >>> len(response.json) == len(expected)
            True

.. http:put:: /contexts/{hash}

    Modifica un context al sistema. Els camps que es poden modificar queden descrits a continuació

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
    :query tags: (Opcional) Llista de tags per categoritzar un contexte

    Cos de la petició

        .. code-block:: python

            { "twitterHashtag": "assignatura1" }

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "twitterHashtag": "assignatura1",
                "displayName": "Atenea",
                "creator": "test_manager",
                "url": "http://atenea.upc.edu",
                "tags": [
                    "Assignatura"
                ],
                "published": "2000-01-01T00:01:00Z",
                "owner": "test_manager",
                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                "objectType": "context",
                "id": "519b00000000000000000000",
                "permissions": {
                    "read": "public",
                    "write": "public",
                    "invite": "public",
                    "subscribe": "public"
                }
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.put('/contexts/{}'.format(context_hash), payload, oauth2Header(test_manager), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json.get('displayName') == expected.get('displayName')
            True
            >>> response.json.get('hash') == expected.get('hash')
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
                "displayName": "Atenea",
                "creator": "test_manager",
                "url": "http://atenea.upc.edu",
                "tags": [
                    "Assignatura"
                ],
                "published": "2000-01-01T00:01:00Z",
                "owner": "test_manager",
                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                "permissions": {
                    "read": "public",
                    "write": "public",
                    "invite": "public",
                    "subscribe": "public"
                },
                "id": "519b00000000000000000000",
                "objectType": "context"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.get('/contexts/{}'.format(context_hash), "", oauth2Header(test_manager), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json.get('displayName') == expected.get('displayName')
            True
            >>> response.json.get('hash') == expected.get('hash')
            True

    Success

        Retorna un objecte del tipus ``Context``.

.. http:delete:: /contexts/{hash}

    Esborra un objecte ``Context`` i les subscripcions de tots els usuaris subscrits a aquell contexte
    NO esborra les activitats que s'hagin creat previament al context esborrat. Tot i que les activitats que queden
    a la base de dades no es poden consultar directament, en el timeline de un usuari coninuarà veient les activitats que va crear ell.

    :query hash: (REST) El hash del context en concret. Aquest hash es calcula
        fent una suma de verificació sha1 dels paràmetres del context

    Cos de la petició

        Aquesta petició no te cos.

.. Create the context to delete in this test

    >>> create_context = {"url": "http://atenea.upc.edu/delete", "objectType": "context" }
    >>> resp = utils.create_context(create_context)
    >>> context_hash_for_deleting = resp.json.get('hash')

    Resposta esperada

        Retorna un codi HTTP 204 (deleted) amb el cos buit

        .. actual test
            >>> resp = testapp.delete('/contexts/{}'.format(context_hash_for_deleting), "", oauth2Header(test_manager), status=204)
            >>> resp
            <204 No Content ...

    Success

        Retorna un codi HTTP 204 (deleted) amb el cos buit


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
                    "objectType": "context",
                    "url": "http://atenea.upc.edu"
                }
            }

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "generator": null,
                "creator": "test_manager",
                "replies": [],
                "object": {
                    "url": "http://atenea.upc.edu",
                    "objectType": "context"
                },
                "actor": {
                    "username": "messi",
                    "displayName": "messi",
                    "objectType": "person"
                },
                "commented": "2000-01-01T00:01:00Z",
                "verb": "subscribe",
                "published": "2000-01-01T00:01:00Z",
                "owner": "messi",
                "id": "519b00000000000000000000",
                "objectType": "activity"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.post('/people/{}/subscriptions'.format(username), payload, oauth2Header(test_manager), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('displayName') == expected.get('displayName')
            True
            >>> response.json.get('verb') == expected.get('verb')
            True

    Success

        Retorna un objecte del tipus ``Activity``.

    Error

        En cas que l'usuari no existeixi

            .. code-block:: python

                { "error_description": "Unknown user: messi", "error": "UnknownUserError" }

.. http:delete:: /people/{username}/subscriptions/{hash}

    Elimina la subscripció d'un usuari Esborra un objecte ``Context`` i les subscripcions de tots els usuaris subscrits a aquell contexte.
    NO esborra les activitats que s'hagin creat previament al context del qual ens hem dessubscrit. Tot i que les activitats que queden a la base de dades no es poden consultar directament, en el timeline de un usuari coninuarà veient les activitats que va crear ell.

    :query username: (REST) L'identificador de l'usuari al sistema.
    :query hash: (REST) El hash del context la subscripció al qual es vol esborrar. Aquest hash es calcula
        fent una suma de verificació sha1 dels paràmetres del context

    Cos de la petició

        Aquesta petició no te cos.

.. Create the context to delete in this test

    >>> create_context_d = {"url": "http://atenea.upc.edu/C", "objectType": "context" }
    >>> subscribe_context_d = { "object": {"url": "http://atenea.upc.edu/C", "objectType": "context" } }
    >>> resp = utils.create_context(create_context_d)
    >>> context_hash_for_deleting = resp.json.get('hash')
    >>> utils.admin_subscribe_user_to_context(username, subscribe_context_d)
    <201 Created application/json ...

    Resposta esperada

        Retorna un codi HTTP 204 (deleted) amb el cos buit

        .. actual test
            >>> resp = testapp.delete('/people/{}/subscriptions/{}'.format(username, context_hash_for_deleting), "", oauth2Header(test_manager), status=204)
            >>> resp
            <204 No Content ...

    Success

        Retorna un codi HTTP 204 (deleted) amb el cos buit

Permisos a contexts
-------------------

Sobre els objectes context es poden otorgar o revocar permisos a usuaris del
sistema. Aquests permisos són qualsevol dels permisos definitsen profunditat
en l'apartat de permisos. Els permisos otorgats amb aquest sistema són persistents,
per tant un canvi de permisos en els valors per defecte del context no afecta als permisos afegits/denegats.

Per tornar un usuari am permisos afegits/denegats als valors per defecte del contexte, haurem de resetejar els
permisos d'aquell usuari en aquell contexte.

Un usuari pot tenir un permis per defecte, i tot i aixi otorgar-li el permis de manera persistent, de manera
que a partir de llavors, no el pot perdre exepte per eliminació explícita.

.. http:put:: /contexts/{hash}/permissions/{username}/{permission}

    Afegeix els permisos per un context donat un identificador d'usuari i el
    permís que li vols donar, de forma persistent.

    :query hash: (REST) El hash del context en concret. Aquest hash es calcula
        fent una suma de verificació sha1 de la URL del context.
    :query username: (REST) L'identificador del nou usuari al sistema
    :query permission: (REST) El permís que li volem otorgar a l'usuari

    Cos de la petició

        Aquesta petició no te cos.

    Resposta esperada

        .. code-block:: python

            {
                "twitterHashtag": "assignatura1",
                "displayName": "Atenea",
                "url": "http://atenea.upc.edu",
                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                "permissions": [
                    "read",
                    "write",
                    "unsubscribe"
                ],
                "objectType": "context"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.put('/contexts/{}/permissions/{}/write'.format(context_hash, username), "", oauth2Header(test_manager), status=201)
            >>> response
            <201 Created application/json ...

    Success

        Si el permís ja estava otorgat, el codi HTTP de resposta és 200, si no, torna un 201.
        En el cos, torna la subscripció modificada.

.. http:delete:: /contexts/{hash}/permissions/{username}/{permission}

    Denega els permis per un context donat un identificador d'usuari i el
    permís que li vols donar de manera persistent

    :query hash: (REST) El hash del context en concret. Aquest hash es calcula
        fent una suma de verificació sha1 de la URL del context.
    :query username: (REST) L'identificador del nou usuari al sistema
    :query permission: (REST) El permís que li volem otorgar a l'usuari

    Cos de la petició

        Aquesta petició no te cos.

    Resposta esperada

        .. code-block:: python

            {
                "twitterHashtag": "assignatura1",
                "displayName": "Atenea",
                "url": "http://atenea.upc.edu",
                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                "permissions": [
                    "read",
                    "unsubscribe"
                ],
                "objectType": "context"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.delete('/contexts/{}/permissions/{}/write'.format(context_hash, username), "", oauth2Header(test_manager), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('displayName') == expected.get('displayName')
            True
            >>> response.json.get('permissions') == expected.get('permissions')
            True

.. put the write permissions of the test user back for further testing :)

    >>> testapp.put('/contexts/{}/permissions/{}/write'.format(context_hash, username), "", oauth2Header(test_manager), status=201)
    <201 Created application/json ...

    Success
        Si el permís ja estava denegat, el codi HTTP de resposta és 200, si no, torna un 201.
        Torna la subscripció modificada.

.. http:post:: /contexts/{hash}/permissions/{username}/defaults

    Reseteja els permisos d'un usuari en un contexte als per defecte d'aquell contexte. Això elimina
    qualsevol permis persistent afegit o denegat anteriorment.

    :query hash: (REST) El hash del context en concret. Aquest hash es calcula
        fent una suma de verificació sha1 de la URL del context.
    :query username: (REST) L'identificador del nou usuari al sistema

    Cos de la petició

        Aquesta petició no te cos.

    Resposta esperada

        .. code-block:: python

            {
                "twitterHashtag": "assignatura1",
                "displayName": "Atenea",
                "url": "http://atenea.upc.edu",
                "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                "permissions": [
                    "read",
                    "write",
                    "unsubscribe"
                ],
                "objectType": "context"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.post('/contexts/{}/permissions/{}/defaults'.format(context_hash, username), "", oauth2Header(test_manager), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json.get('displayName') == expected.get('displayName')
            True
            >>> response.json.get('permissions') == expected.get('permissions')
            True

.. put the write permissions of the test user back for further testing :)

    >>> testapp.put('/contexts/{}/permissions/{}/write'.format(context_hash, username), "", oauth2Header(test_manager), status=201)
    <201 Created application/json ...

    Success
        Si el permís ja estava denegat, el codi HTTP de resposta és 200, si no, torna un 201.
        Torna la subscripció modificada.


Activitats
----------

.. http:post:: /people/{username}/activities

    Afegeix una activitat en nom d'un usuari qualsevol

    :query username: (REST) El nom d'usuari en nom del qual es crearà
        l'activitat
    :query contexts: (Opcional) Per fer que una activitat estigui associada a un
        context determinat fa falta que enviem una llista d'objectes *context*
        (sota la clau ``contexts``) (ja que teòricament, podem fer que
        l'activitat estigui associada a varis contexts a l'hora), indicant com a
        ``objectType`` el tipus ``context`` i les dades del context com a l'exemple
    :query object: (Requerit) Per ara només suportat el tipus (``objectType``)
        *note*. Ha de contindre les claus ``objectType`` i ``content`` que pot
        tractar-se d'un camp codificat amb HTML

    Cos de la petició

        .. code-block:: python

            {
                "contexts": [
                                {
                                    "url": "http://atenea.upc.edu",
                                    "objectType": "context"
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
                "generator": null,
                "creator": "test_manager",
                "contexts": [
                    {
                        "url": "http://atenea.upc.edu",
                        "twitterHashtag": "assignatura1",
                        "displayName": "Atenea",
                        "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                        "objectType": "context"
                    }
                ],
                "object": {
                    "content": "[A] Testejant la creaci\u00f3 d'un canvi d'estatus a un context",
                    "objectType": "note"
                },
                "replies": [],
                "actor": {
                    "username": "messi",
                    "displayName": "messi",
                    "objectType": "person"
                },
                "commented": "2000-01-01T00:01:00Z",
                "verb": "post",
                "published": "2000-01-01T00:01:00Z",
                "owner": "messi",
                "id": "519b00000000000000000000",
                "objectType": "activity"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.post('/people/{}/activities'.format(username), payload, oauth2Header(test_manager), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('displayName') == expected.get('displayName')
            True
            >>> response.json.get('verb') == expected.get('verb')
            True

.. http:post:: /contexts/{hash}/activities

    Afegeix una activitat en nom d'un context qualsevol

    :query hash: (REST) El hash del context en nom del qual es crearà
        l'activitat
    :query contexts: (Requerit) Per fer que una activitat estigui associada a un
        context determinat fa falta que enviem una llista d'objectes *context*
        (sota la clau ``contexts``) (ja que teòricament, podem fer que
        l'activitat estigui associada a varis contexts a l'hora), indicant com a
        ``objectType`` el tipus ``context`` i les dades del context com a l'exemple.
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
                                    "objectType": "context"
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
                "generator": null,
                "creator": "test_manager",
                "contexts": [
                    {
                        "twitterHashtag": "assignatura1",
                        "displayName": "Atenea",
                        "creator": "test_manager",
                        "url": "http://atenea.upc.edu",
                        "tags": [
                            "Assignatura"
                        ],
                        "published": "2000-01-01T00:01:00Z",
                        "owner": "test_manager",
                        "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                        "objectType": "context",
                        "id": "519b00000000000000000000",
                        "permissions": {
                            "read": "public",
                            "write": "public",
                            "invite": "public",
                            "subscribe": "public"
                        }
                    }
                ],
                "object": {
                    "content": "[A] Testejant la creaci\u00f3 d'un canvi d'estatus a un context",
                    "keywords": [
                        "testejant",
                        "creaci\u00f3",
                        "canvi",
                        "estatus",
                        "context"
                    ],
                    "objectType": "note"
                },
                "replies": [],
                "actor": {
                    "url": "http://atenea.upc.edu",
                    "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                    "displayName": "Atenea",
                    "objectType": "uri"
                },
                "commented": "2000-01-01T00:01:00Z",
                "verb": "post",
                "published": "2000-01-01T00:01:00Z",
                "owner": "test_manager",
                "id": "519b00000000000000000000",
                "objectType": "activity"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.post('/contexts/{}/activities'.format(context_hash), payload, oauth2Header(test_manager), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('displayName') == expected.get('displayName')
            True
            >>> response.json.get('verb') == expected.get('verb')
            True


.. doctests teardown (absolutelly needed)

    >>> HTTPretty.disable()
