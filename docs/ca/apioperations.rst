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

    Success

        Retorna l'objecte ``Context``.

.. http:put:: /contexts/{hash}

    Modifica un context al sistema.

    :query url: (Requerit) La URL del context.
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

            {
                "object": {
                    "url": "http://atenea.upc.edu",
                    "objectType": "uri"
                },
                "displayName": "Context arrel del servei Atenea"
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
            .. >>> response = testapp.post('/contexts', payload, oauth2Header(test_manager), status=201)
            .. >>> response
            .. <201 Created application/json body='{"display...>
            .. >>> response.json.get('displayName') == eval(expected).get('displayName')
            .. True
            .. >>> response.json.get('hash') == eval(expected).get('hash')
            .. True

    Success
        Retorna l'objecte ``Context`` modificat.

.. http:get:: /contexts/{hash}

    Retorna la informació d'un objecte ``Context``.

    :query hash: (REST) El hash del context en concret. Aquest hash es calcula
        fent una suma de verificació sha1 de la URL del context.

    Success
        Retorna un objecte del tipus ``Context``.

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
        claus ``objectType`` i el valor `context`, i la dada ``url`` del context.

    Cos de la petició

        .. code-block:: python

            {
                "object": {
                    "objectType": "context",
                    "url": "http://atenea.upc.edu/4127368123"
                }
            }

    Success
        Retorna un objecte del tipus ``Activity``.

    Error
        En cas que l'usuari no existeixi::

            {"error_description": "Unknown user: messi", "error": "UnknownUserError"}

Activitats
----------

.. http:post:: /admin/people/{username}/activities

    Afegeix una activitat en nom d'un usuari qualsevol

    :query username: (REST) El nom d'usuari en nom del qual es crearà l'activitat
    :query contexts: (Opcional) Per fer que una activitat estigui associada a un
        context determinat fa falta que enviem una llista d'objectes contexts,
        indicant com a (``objectType``) el tipus 'context', i les dades del
        context com a l'exemple.
    :query object: (Requerit) Per ara només suportat el tipus (``objectType``)
        `note`. Ha de contindre les claus ``objectType`` i ``content`` que pot
        tractar-se d'un camp codificat amb HTML.

    Cos de la petició::

        {
            "contexts": [
                "http://atenea.upc.edu/4127368123"
            ],
            "object": {
                "objectType": "note",
                "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
            },
        }


.. http:post:: /admin/contexts/{hash}/activities

    Afegeix una activitat en nom d'un context qualsevol

    :query hash: (REST) El hash del context en nom del qual es crearà l'activitat
    :query contexts: (Requerit) Per fer que una activitat estigui associada a un
        context determinat fa falta que enviem una llista d'objectes contexts,
        indicant com a (``objectType``) el tipus 'context', i les dades del
        context com a l'exemple. En aquest cas d'ús el contexte especificat aquí ha de ser el mateix que l'especificat al paràmetre {hash}
    :query object: (Requerit) Per ara només suportat el tipus (``objectType``)
        `note`. Ha de contindre les claus ``objectType`` i ``content`` que pot
        tractar-se d'un camp codificat amb HTML.

    Cos de la petició::

        {
            "contexts": [
                "http://atenea.upc.edu/4127368123"
            ],
            "object": {
                "objectType": "note",
                "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
            },
        }

.. doctests teardown (absolutelly needed)

    >>> HTTPretty.disable()
