API REST
========

Aquest document exposa els serveis web públics creats pel motor d'activitat i
subscripcions. Aquests estan organitzats per recursos i les operacions sobre
ells. Tots els serveis web són de tipus RESTful i l'intercanvi d'informació es
realitza en format JSON.

Els paràmetres indicats a les seccions Query parameters, poden ser de 3 tipus:

:REST: Són obligatoris ja que formen part de la URI
:Requerits: Són obligatoris, però formen part de l'estructura JSON que s'envia
    amb el cos de la petició. En el cas de peticions GET, aquesta estructura equival
    a paràmetres de la URL. (i.e. ?context=ab0012313...)
:Opcionals: Com el nom indica, no son obligatoris, indiquen alguna funcionalitat
    extra

Tots els serveis requereixen autenticació oAuth en cas de que no s'especifiqui
el contrari.

Les respostes que retorna el sistema, en cas que siguin 1 o múltiples resultats
(Associats a col.leccions o entitats) seràn, o bé un sol objecte JSON en cas de
l'accés a una entitat concreta, o una llista o array de resultats::

    [
       { ... },
       { ... }
    ]

.. this is some setup, it is hidden in a reST comment

    >>> from httpretty import HTTPretty
    >>> from max.tests import test_manager
    >>> import json
    >>> HTTPretty.enable()
    >>> HTTPretty.register_uri(HTTPretty.POST, "http://localhost:8080/checktoken", body="", status=200)
    >>> username = "messi"
    >>> username2 = "neymar"
    >>> utils = MaxTestBase(testapp)
    >>> utils.create_user(username)
    <201 Created application/json ...
    >>> from max.tests.mockers import create_context, create_contextA, subscribe_context, context_query, user_status
    >>> utils.create_context(create_context)
    <201 Created application/json ...
    >>> utils.create_context(create_contextA)
    <201 Created application/json ...

Usuaris
--------

Operacions sobre el recurs *usuari* del sistema.

.. http:get:: /people

    Retorna el resultat d'una cerca d'usuaris del sistema en forma de llista
    de noms d'usuaris per l'ús de la UI.

    **Paràmetres JSON**
        - ``username``: El filtre de cerca d'usuaris.

    **Exemple de petició**:

        .. code-block:: python

            {"username": "messi"}

        .. -> payload

    **Resposta esperada**:

        .. code-block:: python

            [
                {
                    "username": "messi",
                    "displayName": "messi",
                    "id": "519b00000000000000000000",
                    "objectType": "person"
                }
            ]

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.get('/people', payload, oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json[0].get('displayName') == expected[0].get('displayName')
            True
            >>> response.json[0].get('twitterUsername') == expected[0].get('twitterUsername')
            True

    **Codis d'error**:
        * 200 petició executada correctament

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

    **Exemple de petició**

        .. code-block:: python

            {"displayName": "Lionel Messi", "twitterUsername": "messi10oficial"}

        .. -> payload

    **Resposta esperada**:

        .. code-block:: python

            {
                "username": "messi",
                "iosDevices": [],
                "displayName": "Lionel Messi",
                "talkingIn": [],
                "creator": "test_manager",
                "androidDevices": [],
                "following": [],
                "subscribedTo": [],
                "last_login": "2000-01-01T00:01:00Z",
                "published": "2000-01-01T00:01:00Z",
                "owner": "test_manager",
                "twitterUsername": "messi10oficial",
                "id": "519b00000000000000000000",
                "objectType": "person"
            }

        .. -> expected
            >>> response = testapp.put('/people/{}'.format(username), payload, oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json.get('displayName') == eval(expected).get('displayName')
            True
            >>> response.json.get('twitterUsername') == eval(expected).get('twitterUsername')
            True

    Success

        Retorna un objecte ``Person`` amb els paràmetres indicats modificats.

    Error

        .. code-block:: python

            {"error_description": "Unknown user: messi", "error": "UnknownUserError"}

.. http:post:: /people/{username}

    Crea el perfil propi (el de l'usuari que executa) d'usuari remotament al
    sistema pel seu posterior ús si no existeix. En cas de que l'usuari ja
    existis, el retorna canviant el codi d'estat HTTP en funció de l'acció
    realitzada.

    :query username: (REST) L'identificador del nou usuari al sistema
    :query displayName: (Opcional) El nom real (de pantalla) de l'usuari al
        sistema

    Cos de la petició

        .. code-block:: python

            {"username": "neymar", "displayName": "Neymar JR"}

        .. -> payload

    Resposta esperada

        .. code-block:: python

            {
                "username": "neymar",
                "iosDevices": [],
                "displayName": "Neymar JR",
                "talkingIn": [],
                "creator": "neymar",
                "androidDevices": [],
                "following": [],
                "subscribedTo": [],
                "last_login": "2000-01-01T00:01:00Z",
                "published": "2000-01-01T00:01:00Z",
                "owner": "neymar",
                "id": "519b00000000000000000000",
                "objectType": "person"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.post('/people/{}'.format(username2), payload, oauth2Header(username2), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('displayName') == expected.get('displayName')
            True

    Success

        Retorna un objecte ``Person``.

.. http:get:: /people/{username}

    Retorna la informació d'un usuari del sistema. En cas de que l'usuari no
    existeixi retorna l'error especificat.

    :query username: (REST) L'identificador de l'usuari

    **Exemple de petició**

        Aquesta petició no necessita cos.

    **Resposta esperada**:

        .. code-block:: python

            {
                "username": "messi",
                "iosDevices": [],
                "displayName": "Lionel Messi",
                "talkingIn": [],
                "creator": "test_manager",
                "androidDevices": [],
                "following": [],
                "subscribedTo": [],
                "last_login": "2000-01-01T00:01:00Z",
                "published": "2000-01-01T00:01:00Z",
                "owner": "test_manager",
                "twitterUsername": "messi10oficial",
                "id": "519b00000000000000000000",
                "objectType": "person"
            }

        .. -> expected
            >>> response = testapp.get('/people/{}'.format(username), "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
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

.. http:post:: /people/{username}/avatar

    Permet a l'usuari del sistema pujar la seva imatge del seu perfil (avatar).

    :query username: (REST) L'identificador de l'usuari

    Cos de la petició

        La petició ha d'estar feta mitjançant multipart/form-data amb les
        capçaleres corresponents d'oAuth en aquest endpoint.

    Success
        Retorna un codi **201** (Created)

.. http:post:: /people/{username}/device/{platform}/{token}

    Afegeix un token de dispositiu al perfil de l'usuari. Aquest token és el que
    identifica el dispositiu per a que se li puguin enviar notificacions push.

    :query username: (REST) L'identificador del nou usuari al sistema
    :query platform: (REST) El tipus de plataforma
    :query token: (REST) La cadena de text que representa el token

    Cos de la petició

        Aquesta petició no necessita cos.

    Resposta esperada

        .. code-block:: python

            {
                "username": "messi",
                "iosDevices": [
                    "12345678901234567890123456789012"
                ],
                "displayName": "Lionel Messi",
                "talkingIn": [],
                "creator": "test_manager",
                "androidDevices": [],
                "following": [],
                "subscribedTo": [],
                "last_login": "2000-01-01T00:01:00Z",
                "published": "2000-01-01T00:01:00Z",
                "owner": "test_manager",
                "twitterUsername": "messi10oficial",
                "id": "519b00000000000000000000",
                "objectType": "person"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> platform = 'ios'
            >>> token = '12345678901234567890123456789012'
            >>> response = testapp.post('/people/{}/device/{}/{}'.format(username, platform, token), "", oauth2Header(username), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('displayName') == expected.get('displayName')
            True

    Success

        Retorna un objecte ``Person``.

.. http:delete:: /people/{username}/device/{platform}/{token}

    Esborra un token de dispositiu al perfil de l'usuari. Aquest token és el que
    identifica el dispositiu per a que se li puguin enviar notificacions push.

    :query username: (REST) L'identificador del nou usuari al sistema
    :query platform: (REST) El tipus de plataforma
    :query token: (REST) La cadena de text que representa el token

    Cos de la petició

        Aquesta petició no necessita cos.

    Resposta esperada

        Retorna un codi HTTP 204 (deleted) amb el cos buit

        .. actual test
            >>> platform = 'ios'
            >>> token = '12345678901234567890123456789012'
            >>> response = testapp.delete('/people/{}/device/{}/{}'.format(username, platform, token), "", oauth2Header(username), status=204)
            >>> response
            <204 No Content ...

    Success

        Retorna un objecte ``Person``.

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
        pot tractar-se d'un camp codificat amb HTML, amb tags restringits.

    **Exemple de petició**

        .. code-block:: python

            {
                "object": {
                    "objectType": "note",
                    "content": "<p[A] Testejant la creació d'un canvi d'estatus</p>"
                }
            }

        .. -> payload

    **Resposta esperada**:

        .. code-block:: python

            {
                "generator": null,
                "creator": "messi",
                "replies": [],
                "object": {
                    "content": "",
                    "objectType": "note"
                },
                "actor": {
                    "username": "messi",
                    "displayName": "Lionel Messi",
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
            >>> response = testapp.post('/people/{}/activities'.format(username), payload, oauth2Header(username), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('actor').get('displayName') == expected.get('actor').get('displayName')
            True
            >>> response.json.get('object').get('objectType') == expected.get('object').get('objectType')
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

    .. Subscribe the user to the context
        >>> utils.admin_subscribe_user_to_context(username, subscribe_context)
        <201 Created application/json ...


    **Exemple de petició**

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

    **Resposta esperada**:

        .. code-block:: python

            {
                "generator": null,
                "creator": "messi",
                "contexts": [
                    {
                        "url": "http://atenea.upc.edu",
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
                    "displayName": "Lionel Messi",
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
            >>> response = testapp.post('/people/{}/activities'.format(username), payload, oauth2Header(username), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('actor').get('displayName') == expected.get('actor').get('displayName')
            True
            >>> response.json.get('object').get('objectType') == expected.get('object').get('objectType')
            True
            >>> response.json.get('contexts')[0].get('url') == expected.get('contexts')[0].get('url')
            True

.. http:get:: /people/{username}/activities

    Llista totes les activitats de tipus post generades al sistema per part d'un usuari
    concret.

    :query username: (REST) Identificador d'usuari que crea l'activitat

    **Exemple de petició**

        Aquesta petició no necessita cos.

    **Resposta esperada**:

        .. code-block:: python

            [
                {
                    "generator": null,
                    "contexts": [
                        {
                            "url": "http://atenea.upc.edu",
                            "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                            "displayName": "Atenea",
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
                        "displayName": "Lionel Messi",
                        "objectType": "person"
                    },
                    "id": "519b00000000000000000000",
                    "verb": "post",
                    "deletable": true,
                    "published": "2000-01-01T00:01:00Z",
                    "commented": "2000-01-01T00:01:00Z",
                    "objectType": "activity"
                },
                {
                    "generator": null,
                    "replies": [],
                    "object": {
                        "content": "",
                        "objectType": "note"
                    },
                    "actor": {
                        "username": "messi",
                        "displayName": "Lionel Messi",
                        "objectType": "person"
                    },
                    "id": "519b00000000000000000000",
                    "verb": "post",
                    "deletable": true,
                    "published": "2000-01-01T00:01:00Z",
                    "commented": "2000-01-01T00:01:00Z",
                    "objectType": "activity"
                }
            ]

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.get('/people/{}/activities'.format(username), "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json[0].get('actor').get('displayName') == expected[0].get('actor').get('displayName')
            True
            >>> len(response.json) == len(expected)
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


Activitats d'un contexte
-------------------------

Torna el conjunt d'activitats generades pels usuaris del sistema a un context.
L'usuari que fa la petició ha de tindre permisos de lectura com a mínim en el
context requerit, de lo contrari se li denegarà l'accés. Típicament s'utilitza
per recuperar totes les activitats que els usuaris han associat a un context
concret.

.. http:get:: /contexts/{hash}/activities

    Llistat de totes les activitats del sistema, filtrada sota algun criteri

    :query hash: (REST) El hash (sha1) de la URL del context
    :query sortBy: (Opcional) Tipus d'ordenació que s'aplicarà als resultats. Per defecte és
        ``activities``, i te en compte la data de publicació de l'activitat. L'altre valor
        possible és ``comments`` i ordena per la data de l'últim comentari a l'activitat.

        .. code-block:: python

            {"context": "e6847aed3105e85ae603c56eb2790ce85e212997"}

        .. -> payload

    **Resposta esperada**:

        .. code-block:: python

            [
                {
                    "generator": null,
                    "contexts": [
                        {
                            "url": "http://atenea.upc.edu",
                            "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                            "displayName": "Atenea",
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
                        "displayName": "Lionel Messi",
                        "objectType": "person"
                    },
                    "id": "519b00000000000000000000",
                    "verb": "post",
                    "deletable": true,
                    "published": "2000-01-01T00:01:00Z",
                    "commented": "2000-01-01T00:01:00Z",
                    "objectType": "activity"
                }
            ]

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.get('/contexts/%s/activities'% (eval(payload)['context']), '', oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json[0].get('actor').get('displayName') == expected[0].get('actor').get('displayName')
            True
            >>> len(response.json) == len(expected)
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
    :query sortBy: (Opcional) Tipus d'ordenació que s'aplicarà als resultats. Per defecte és
        ``activities``, i te en compte la data de publicació de l'activitat. L'altre valor
        possible és ``comments`` i ordena per la data de l'últim comentari a l'activitat.

    **Exemple de petició**

        Aquesta petició no necessita cos.

    **Resposta esperada**:

        .. code-block:: python

            [
                {
                    "generator": null,
                    "contexts": [
                        {
                            "url": "http://atenea.upc.edu",
                            "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                            "displayName": "Atenea",
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
                        "displayName": "Lionel Messi",
                        "objectType": "person"
                    },
                    "id": "519b00000000000000000000",
                    "verb": "post",
                    "deletable": true,
                    "published": "2000-01-01T00:01:00Z",
                    "commented": "2000-01-01T00:01:00Z",
                    "objectType": "activity"
                },
                {
                    "generator": null,
                    "replies": [],
                    "object": {
                        "content": "",
                        "objectType": "note"
                    },
                    "actor": {
                        "username": "messi",
                        "displayName": "Lionel Messi",
                        "objectType": "person"
                    },
                    "id": "519b00000000000000000000",
                    "verb": "post",
                    "deletable": true,
                    "published": "2000-01-01T00:01:00Z",
                    "commented": "2000-01-01T00:01:00Z",
                    "objectType": "activity"
                }
            ]

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.get('/people/{}/timeline'.format(username), "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json[0].get('actor').get('displayName') == expected[0].get('actor').get('displayName')
            True
            >>> len(response.json) == len(expected)
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

    **Exemple de petició**

        .. code-block:: python

            {
                "object": {
                    "objectType": "comment",
                    "content": "<p>[C] Testejant un comentari nou a una activitat</p>"
                }
            }

        .. -> payload

    **Resposta esperada**:

        .. code-block:: python

            {
                "generator": null,
                "creator": "messi",
                "replies": [],
                "object": {
                    "content": "[C] Testejant un comentari nou a una activitat",
                    "inReplyTo": [
                        {
                            "id": "519b00000000000000000000",
                            "objectType": "note"
                        }
                    ],
                    "keywords": [
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
                    "objectType": "person"
                },
                "commented": "2000-01-01T00:01:00Z",
                "verb": "comment",
                "published": "2000-01-01T00:01:00Z",
                "owner": "messi",
                "id": "519b00000000000000000000",
                "objectType": "activity"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> activity = utils.create_activity(username, user_status)
            >>> response = testapp.post('/activities/{}/comments'.format(activity.json.get('id')), payload, oauth2Header(username), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('actor').get('displayName') == expected.get('actor').get('displayName')
            True
            >>> response.json.get('verb') == expected.get('verb')
            True

    Success

        Retorna l'objecte ``Activity`` del comentari.

.. http:get:: /activities/{activity}/comments

    Llista tots els comentaris d'una activitat

    :query activity: (REST) ha de ser un identificador vàlid d'una activitat
        existent, per exemple: 4e6eefc5aceee9210d000004

    **Exemple de petició**

         Aquesta petició no necessita cos.

    **Resposta esperada**:

        .. code-block:: python

            [
                {
                    "actor": {
                        "username": "messi",
                        "displayName": "Lionel Messi",
                        "objectType": "person"
                    },
                    "content": "[C] Testejant un comentari nou a una activitat",
                    "deletable": true,
                    "published": "2000-01-01T00:01:00Z",
                    "id": "519b00000000000000000000",
                    "objectType": "comment"
                }
            ]

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.get('/activities/{}/comments'.format(activity.json.get('id')), payload, oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json[0].get('actor').get('displayName') == expected[0].get('actor').get('displayName')
            True
            >>> len(response.json) == len(expected)
            True

    Success

        Retorna una col·lecció d'objectes del tipus ``Comment``


Subscripcions
-------------


.. http:get:: /contexts/public

    Dona una llista de tots els contextes als qual un usuari es pot subscriure lliurement

    **Exemple de petició**

        Aquesta petició no necessita cos.

    **Resposta esperada**:

        .. code-block:: python

            [
                {
                    "displayName": "Atenea",
                    "tags": [
                        "Assignatura"
                    ],
                    "url": "http://atenea.upc.edu",
                    "published": "2000-01-01T00:01:00Z",
                    "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                    "permissions": {
                        "write": "public",
                        "subscribe": "public",
                        "read": "public",
                        "invite": "subscribed"
                    },
                    "id": "519b00000000000000000000",
                    "objectType": "context"
                },
                {
                    "displayName": "Atenea A",
                    "tags": [
                        "Assignatura"
                    ],
                    "url": "http://atenea.upc.edu/A",
                    "published": "2000-01-01T00:01:00Z",
                    "hash": "90c8f28a7867fbad7a2359c6427ae8798a37ff07",
                    "permissions": {
                        "write": "public",
                        "subscribe": "public",
                        "read": "public",
                        "invite": "subscribed"
                    },
                    "id": "519b00000000000000000000",
                    "objectType": "context"
                }
            ]

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.get('/contexts/public', payload, oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> len(response.json) == len(expected)
            True
            >>> response.json[0]['objectType'] == expected[0]['objectType']
            True


    Success

        Retorna un objecte del tipus ``Activity``.


.. http:post:: /people/{username}/subscriptions

    Subscriu l'usuari a un context determinat. El context al qual es vol subscriure l'usuari ha de ser de tipus
    public, sinó obtindrem un error d'autorització ``401 Unauthorized``

    :query username: (REST) L'identificador de l'usuari al sistema.
    :query contexts: (Requerit) Tipus d'objecte al qual ens volem subscriure, en
        aquest cas del tipus `context`. Hem de proporcionar un objecte amb les
        claus ``objectType`` i el valor *context*, i la dada ``url`` del context.

    **Exemple de petició**

        .. code-block:: python

            {
                "object": {
                    "objectType": "context",
                    "url": "http://atenea.upc.edu/A"
                }
            }

        .. -> payload

    **Resposta esperada**:

        .. code-block:: python

            {
                "generator": null,
                "creator": "messi",
                "replies": [],
                "object": {
                    "url": "http://atenea.upc.edu/A",
                    "objectType": "context"
                },
                "actor": {
                    "username": "messi",
                    "displayName": "Lionel Messi",
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
            >>> response = testapp.post('/people/{}/subscriptions'.format(username), payload, oauth2Header(username), status=201)
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

Representa el conjunt de contextes als quals esta subscrit un usuari.

.. http:get:: /people/{username}/subscriptions

    Torna totes les subscripcions d'un usuari

    :query username: (REST) L'identificador de l'usuari al sistema

    **Exemple de petició**

         Aquesta petició no necessita cos.

    **Resposta esperada**:

        .. code-block:: python

            [
                {
                    "url": "http://atenea.upc.edu",
                    "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                    "objectType": "context",
                    "displayName": "Atenea",
                    "permissions": [
                        "read",
                        "write",
                        "unsubscribe",
                        "invite"
                    ]
                },
                {
                    "url": "http://atenea.upc.edu/A",
                    "hash": "90c8f28a7867fbad7a2359c6427ae8798a37ff07",
                    "objectType": "context",
                    "displayName": "Atenea A",
                    "permissions": [
                        "read",
                        "write",
                        "unsubscribe",
                        "invite"
                    ]
                }
            ]

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.get('/people/{}/subscriptions'.format(username), "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> len(response.json) == len(expected)
            True

.. http:delete:: /people/{username}/subscriptions/{hash}

    Elimina la subscripció d'un usuari, si l'usuari té permis per dessubscriure's.
    NO esborra les activitats que s'hagin creat previament al context del qual ens hem dessubscrit. Tot i que les activitats que queden a la base de dades no es poden consultar directament, en el timeline de un usuari coninuarà veient les activitats que va crear ell.

    :query username: (REST) L'identificador de l'usuari al sistema.
    :query hash: (REST) El hash del context la subscripció al qual es vol esborrar. Aquest hash es calcula
        fent una suma de verificació sha1 dels paràmetres del context

    **Exemple de petició**

        Aquesta petició no te cos.

.. Create the context unsubscribe and subcribe user to it

    >>> create_context_d = {"url": "http://atenea.upc.edu/C", "objectType": "context" }
    >>> subscribe_context_d = {"object": {"url": "http://atenea.upc.edu/C", "objectType": "context" } }
    >>> resp = utils.create_context(create_context_d)
    >>> context_hash_for_deleting = resp.json.get('hash')
    >>> utils.admin_subscribe_user_to_context(username, subscribe_context_d)
    <201 Created application/json ...


    **Resposta esperada**:

        Retorna un codi HTTP 204 (deleted) amb el cos buit

        .. actual test
            >>> resp = testapp.delete('/people/{}/subscriptions/{}'.format(username, context_hash_for_deleting), "", oauth2Header(username), status=204)
            >>> resp
            <204 No Content ...

    Success

        Retorna un codi HTTP 204 (deleted) amb el cos buit


Missatges i converses
---------------------

El MAX implementa des de la seva versió 3.0 la funcionalitat de missatgeria
instantània asíncrona entre els seus usuaris.

* Les converses tenen un limit de 20 participants.
* Les converses tenen un propietari, que és l'usuari que va crear la conversa.
* El propietari de la conversa pot afegir més gent a la conversa.
* El propietari de la conversa pot fer fora usuaris de la conversa.
* El propietari de la conversa *NO* pot marxar d'una conversa
* Els participants d'una conversa poden marxar sempre que vulguin de la conversa, els seus missatges no s'esborren

Aquests són els serveis associats.

.. setup other user for conversations interaction

    >>> username2 = 'xavi'
    >>> utils.create_user(username2)
    <201 Created application/json ...

.. http:post:: /conversations

    Crea una conversa nova, hi subscriu tots els participants especificats, i afegeix el
    missatge a la conversa.

    :query contexts: (Requerit) Tipus d'objecte al qual ens volem subscriure (en
        aquest cas ``conversation``). Hem de proporcionar un objecte amb les claus
        ``objectType`` i el valor ``conversation``, i la llista de
        ``participants`` com a l'exemple
    :query object: (Requerit) Tipus d'objecte de la conversa. Hem de
        proporcionar un objecte (per ara només es permet el tipus `note`) i
        el contingut amb les dades ``content`` amb el cos del missatge
        propiament dit

    **Exemple de petició**

        .. code-block:: python

            {
                "contexts": [
                    {
                        "objectType":"conversation",
                        "participants": ["messi", "xavi"]
                    }
                ],
                "object": {
                    "objectType": "note",
                    "content": "Nos espera una gran temporada, no es cierto?"
                }
            }

        .. -> payload

    **Resposta esperada**:

        .. code-block:: python

            {
                "generator": null,
                "creator": "messi",
                "contexts": [
                    {
                        "participants": [
                            "messi",
                            "xavi"
                        ],
                        "displayName": "messi, xavi",
                        "id": "519b00000000000000000000",
                        "objectType": "conversation"
                    }
                ],
                "object": {
                    "content": "Nos espera una gran temporada, no es cierto?",
                    "keywords": [
                        "nos",
                        "espera",
                        "una",
                        "gran",
                        "temporada",
                        "cierto",
                        "messi"
                    ],
                    "objectType": "note"
                },
                "replies": [],
                "actor": {
                    "username": "messi",
                    "displayName": "Lionel Messi",
                    "objectType": "person"
                },
                "commented": "2000-01-01T00:01:00Z",
                "verb": "post",
                "published": "2000-01-01T00:01:00Z",
                "owner": "messi",
                "id": "519b00000000000000000000",
                "objectType": "message"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.post('/conversations', payload, oauth2Header(username), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('object').get('objectType') == expected.get('object').get('objectType')
            True
            >>> response.json.get('contexts')[0].get('displayName') == expected.get('contexts')[0].get('displayName')
            True
            >>> conversation_id = response.json.get('contexts')[0].get('id')

    Success

        Retorna l'objecte ``Message`` (activitat).


.. http:get:: /conversations/{hash}/messages

    Retorna tots els missatges d'una conversa

    :query hash: (REST) El hash de la conversa en concret. Aquest hash es
        calcula fent una suma de verificació sha1 de la llista de participants
        (ordenada alfabèticament i sense espais) de la conversa

    **Exemple de petició**

        Aquesta petició no te cos.

    **Resposta esperada**:

        .. code-block:: python

            [
                {
                    "generator": null,
                    "contexts": [
                        {
                            "participants": [
                                "messi",
                                "xavi"
                            ],
                            "displayName": "messi, xavi",
                            "id": "519b00000000000000000000",
                            "objectType": "conversation"
                        }
                    ],
                    "object": {
                        "content": "Nos espera una gran temporada, no es cierto?",
                        "objectType": "note"
                    },
                    "replies": [],
                    "actor": {
                        "username": "messi",
                        "displayName": "Lionel Messi",
                        "objectType": "person"
                    },
                    "id": "519b00000000000000000000",
                    "verb": "post",
                    "published": "2000-01-01T00:01:00Z",
                    "commented": "2000-01-01T00:01:00Z",
                    "objectType": "message"
                }
            ]

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.get('/conversations/{}/messages'.format(conversation_id), "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json[0].get('object').get('objectType') == expected[0].get('object').get('objectType')
            True
            >>> response.json[0].get('contexts')[0].get('displayName') == expected[0].get('contexts')[0].get('displayName')
            True

    Success

        Retorna una llista d'objectes ``Message``

.. http:get:: /conversations

    Retorna totes les converses de l'actor que faci la petició

    **Exemple de petició**

        Aquesta petició no te cos.

    **Resposta esperada**:

        .. code-block:: python

            [
                {
                    "displayName": "messi, xavi",
                    "creator": "messi",
                    "messages": 1,
                    "participants": [
                        "messi",
                        "xavi"
                    ],
                    "lastMessage": {
                        "content": "Nos espera una gran temporada, no es cierto?",
                        "published": "2000-01-01T00:01:00Z"
                    },
                    "published": "2000-01-01T00:01:00Z",
                    "owner": "messi",
                    "permissions": {
                        "read": "subscribed",
                        "write": "subscribed",
                        "unsubscribe": "public",
                        "invite": "restricted",
                        "subscribe": "restricted"
                    },
                    "id": "519b00000000000000000000",
                    "objectType": "conversation"
                }
            ]

        .. -> expected
            >>> response = testapp.get('/conversations', "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json[0].get('objectType') == eval(expected)[0].get('objectType')
            True
            >>> response.json[0].get('displayName') == eval(expected)[0].get('displayName')
            True

    Success

        Retorna una llista d'objectes del tipus ``Conversation``.

.. http:get:: /conversations/{id}

    Retorna una conversa

    :query id: (REST) L'identificador d'una conversa. el podem obtenir en la resposta al crear una conversa nova,
        o en la llista de converses d'un usuari.

    **Exemple de petició**

        Aquesta petició no te cos.

    **Resposta esperada**:

        .. code-block:: python

            {
                "displayName": "xavi",
                "creator": "messi",
                "participants": [
                    "messi",
                    "xavi"
                ],
                "published": "2000-01-01T00:01:00Z",
                "owner": "messi",
                "permissions": {
                    "read": "subscribed",
                    "write": "subscribed",
                    "unsubscribe": "public",
                    "invite": "restricted",
                    "subscribe": "restricted"
                },
                "id": "519b00000000000000000000",
                "objectType": "conversation"
            }

        .. -> expected
            >>> response = testapp.get('/conversations/{}'.format(conversation_id), "", oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json['objectType'] == 'conversation'
            True

    Success

        Retorna un objecte del tipus ``Conversation``.


.. http:put:: /conversations/{id}

    Modifica una conversa

    :query id: (REST) L'identificador d'una conversa. el podem obtenir en la resposta al crear una conversa nova,
        o en la llista de converses d'un usuari.
    :query displayName: El nom visible de la conversa, només visible en converses de més de 2 participants.

    **Exemple de petició**

        .. code-block:: python

            {
                displayName: 'Nou nom'
            }

        .. -> payload


    **Resposta esperada**:

        .. code-block:: python

            {
                "displayName": "xavi",
                "creator": "messi",
                "participants": [
                    "messi",
                    "xavi"
                ],
                "published": "2000-01-01T00:01:00Z",
                "owner": "messi",
                "permissions": {
                    "read": "subscribed",
                    "write": "subscribed",
                    "unsubscribe": "public",
                    "invite": "restricted",
                    "subscribe": "restricted"
                },
                "id": "519b00000000000000000000",
                "objectType": "conversation"
            }

        .. -> expected


            >>> response = testapp.get('/conversations/{}'.format(conversation_id), json.dumps(payload), oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> response.json['objectType'] == 'conversation'
            True

    Success

        Retorna un objecte del tipus ``Conversation``.


.. http:post:: /conversations/{hash}/messages

    Crea un missatge nou a una conversa ja existent

    :query hash: (REST) El hash de la conversa en concret. Aquest hash es
        calcula fent una suma de verificació sha1 de la llista de participants
        (ordenada alfabèticament i sense espais) de la conversa

    **Exemple de petició**

        .. code-block:: python

            {
                "object": {
                    "objectType": "note",
                    "content": "M'agrada Taradell!"
                }
            }

        .. -> payload

    **Resposta esperada**:

        .. code-block:: python

            {
                "generator": null,
                "creator": "messi",
                "contexts": [
                    {
                        "participants": [
                            "messi",
                            "xavi"
                        ],
                        "displayName": "messi, xavi",
                        "id": "519b00000000000000000000",
                        "objectType": "conversation"
                    }
                ],
                "object": {
                    "content": "M'agrada Taradell!",
                    "keywords": [
                        "agrada",
                        "taradell",
                        "messi"
                    ],
                    "objectType": "note"
                },
                "replies": [],
                "actor": {
                    "username": "messi",
                    "displayName": "Lionel Messi",
                    "objectType": "person"
                },
                "commented": "2000-01-01T00:01:00Z",
                "verb": "post",
                "published": "2000-01-01T00:01:00Z",
                "owner": "messi",
                "id": "519b00000000000000000000",
                "objectType": "message"
            }

        .. -> expected
            >>> expected = json.loads(expected)
            >>> response = testapp.post('/conversations/{}/messages'.format(conversation_id), payload, oauth2Header(username), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('object').get('objectType') == expected.get('object').get('objectType')
            True
            >>> response.json.get('contexts')[0].get('displayName') == expected.get('contexts')[0].get('displayName')
            True

    Success

        Retorna l'objecte ``Message`` (activitat).


.. http:post:: /people/{username}/conversations/{id}

    Afegeix un usuari a una conversa. L'usuari propietari de la conversa és l'únic que ho pot fer.
    Hi ha un limit de 20 participants per conversa.

    :query username: (REST) L'usuari que es vol afegir a la conversa
    :query id: (REST) L'identificador d'una conversa. el podem obtenir en la resposta al crear una conversa nova,
        o en la llista de converses d'un usuari.

    **Exemple de petició**

        Aquesta petició no te cos.

    **Resposta esperada**:

        .. code-block:: python

            {
                "generator": null,
                "creator": "messi",
                "replies": [],
                "object": {
                    "participants": [
                        "messi",
                        "xavi",
                        "nouusuari"
                    ],
                    "id": "519b00000000000000000000",
                    "objectType": "conversation"
                },
                "actor": {
                    "username": "nouusuari",
                    "displayName": "nouusuari",
                    "objectType": "person"
                },
                "commented": "2000-01-01T00:01:00Z",
                "verb": "subscribe",
                "published": "2000-01-01T00:01:00Z",
                "owner": "nouusuari",
                "id": "519b00000000000000000000",
                "objectType": "activity"
            }

        .. -> expected

            >>> expected = json.loads(expected)
            >>> utils.create_user('nouusuari')
            <201 Created application/json ...
            >>> response = testapp.post('/people/{}/conversations/{}'.format('nouusuari', conversation_id), payload, oauth2Header(username), status=201)
            >>> response
            <201 Created application/json ...
            >>> response.json.get('object').get('objectType') == expected.get('object').get('objectType')
            True

        Retorna un codi HTTP 201 (created) amb la subscripció, o un HTTP 401 (Unauthorized) si l'usuari no és el propietari.
        Si sobrepassem el límit obtindrem un HTTP 403 (Forbidden)

.. http:delete:: /people/{username}/conversations/{id}

    Treu un usuari d'una conversa. Ho pot fer qualsevol participant de la conversa excepte el propietari.

    :query username: (REST) L'usuari que es vol afegir a la conversa
    :query id: (REST) L'identificador d'una conversa. el podem obtenir en la resposta al crear una conversa nova,
        o en la llista de converses d'un usuari.

    **Exemple de petició**

        Aquesta petició no te cos.

    **Resposta esperada**:

        Retorna un codi HTTP 204 (deleted) amb el cos buit, o un HTTP 401 (Unauthorized) si l'usuari no és el propietari

        .. actual test
            >>> resp = testapp.delete('/people/{}/conversations/{}'.format('nouusuari', conversation_id), "", oauth2Header(username), status=204)
            >>> resp
            <204 No Content ...

.. http:delete:: /conversations/{id}

    Elimina una conversa

    Elimina una conversa i tots els seus missatges de forma permanent. L'usuari propietari de la conversa és
    ĺ'únic que pot eliminarla.

    :query id: (REST) L'identificador d'una conversa. el podem obtenir en la resposta al crear una conversa nova,
        o en la llista de converses d'un usuari.

    **Exemple de petició**

        Aquesta petició no te cos.

    **Resposta esperada**:

        Retorna un codi HTTP 204 (deleted) amb el cos buit, o un HTTP 401 (Unauthorized) si l'usuari no és el propietari

        .. actual test
            >>> resp = testapp.delete('/conversations/{}'.format(conversation_id), "", oauth2Header(username), status=204)
            >>> resp
            <204 No Content ...


Contextos
---------

Tot i que els serveis associats a contextos són majoritàriament d'accés restringit, els
que són accessibles per usuaris normals estàn documentats aquí

.. http:get:: /contexts/public

    Dona una llista de tots els contextes als qual un usuari es pot subscriure lliurement

    **Exemple de petició**

        Aquesta petició no necessita cos.

    **Resposta esperada**:

        .. code-block:: python

            [
                {
                    "displayName": "Atenea",
                    "tags": [
                        "Assignatura"
                    ],
                    "url": "http://atenea.upc.edu",
                    "published": "2000-01-01T00:01:00Z",
                    "hash": "e6847aed3105e85ae603c56eb2790ce85e212997",
                    "permissions": {
                        "write": "public",
                        "subscribe": "public",
                        "read": "public",
                        "invite": "subscribed"
                    },
                    "id": "519b00000000000000000000",
                    "objectType": "context"
                },
                {
                    "displayName": "Atenea A",
                    "tags": [
                        "Assignatura"
                    ],
                    "url": "http://atenea.upc.edu/A",
                    "published": "2000-01-01T00:01:00Z",
                    "hash": "90c8f28a7867fbad7a2359c6427ae8798a37ff07",
                    "permissions": {
                        "write": "public",
                        "subscribe": "public",
                        "read": "public",
                        "invite": "subscribed"
                    },
                    "id": "519b00000000000000000000",
                    "objectType": "context"
                }
            ]

        .. -> expected
            >>> testapp.delete('/contexts/{}'.format(context_hash_for_deleting), '', oauth2Header(test_manager), status=204)
            <204 No Content ...
            >>> expected = json.loads(expected)
            >>> response = testapp.get('/contexts/public', '', oauth2Header(username), status=200)
            >>> response
            <200 OK application/json ...
            >>> len(response.json) == len(expected)
            True
            >>> response.json[0]['objectType'] == expected[0]['objectType']
            True


    Success

        Retorna un objecte del tipus ``Context``.


.. http:get:: /contexts/{hash}/avatar

    Retorna la imatge que li correspon al context depenent del usuari de
    Twitter que te assignat. Si no en te cap, retorna una imatge estàndar. Per
    ara només està implementada la integració amb Twitter i dissenyat per quan
    un context vol *parlar* impersonat a l'activitat del seu propi context.
    Per exemple, una assignatura.

    Aquest és un servei públic, no és necessaria la autenticació oauth.

    :query hash: (REST) El hash del context en concret. Aquest hash es calcula
        fent una suma de verificació sha1 de la URL del context.

    Success

        Retorna la imatge del context.

.. doctests teardown (absolutelly needed)

    >>> HTTPretty.disable()
