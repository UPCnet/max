API REST
========

Aquest document exposa els serveis web creats pel motor d'activitat i subscripcions. Organitzats per recursos. Tots els serveis web són de tipus RESTful i l'intercanvi d'informació es realitza en format JSON.

Els paràmetres indicats a les seccions Query parameters, poden ser de 3 tipus:

:REST: Són obligatoris ja que formen part de la URI
:Requerits: Són obligatoris, però formen part de l'estructura JSON que s'envia amb el cos de la petició
:Opcionals: Com el nom indica, no son obligatoris, indiquen alguna funcionalitat extra

Tots els serveis requereixen autenticació oAuth en cas de que no s'especifiqui el contrari.

Les respostes que retorna el sistema, en cas que siguin 1 o múltiples resultats (Associats a col.leccions o entitats) seràn, o bé un sol objecte JSON en cas de l'accés a una entitat concreta, o una estructura que englobi un conjunt de resultats, indicant el total d'elements retornats::

    {

        "totalItems": 2,
        "items": [
                   { ... }
                   { ... }
                 ]
    }

Usuaris
--------

Representa el conjunt d'usuaris del sistema.

.. http:post:: /people/{username}

    Crea un usuari remotament al sistema pel seu posterior us, si no existeix. En cas de que l'usuari ja existis, el retorna canviant el codi d'estat HTTP en funció de l'acció realitzada.

    :query username: (REST) L'identificador del nou usuari al sistema.
    :query displayName: (Opcional) El nom real de l'usuari al sistema

    Success
        Retorna un objecte ``Person``.

.. http:put:: /people/{username}

    Modifica un usuari del sistema pel seu posterior us, si no existeix. En cas de que l'usuari no existis, retorna un error. La llista de paràmetres actualitzables de moment és limita a 1 'displayName'.

    :query username: (REST) L'identificador de l'usuari
    :query displayName: (Opcional) El nom real de l'usuari al sistema

    Success
        Retorna un objecte ``Person`` amb els paràmetres indicats modificats.

    Error
        {"error_description": "Unknown user: messi", "error": "UnknownUserError"}

.. http:get:: /people/{username}

    Retorna la informació d'un usuari del sistema. En cas de que l'usuari no existis, retorna l'error especificat.

    :query username: (REST) L'identificador de l'usuari

    Success
        Retorna un objecte ``Person``.

    Error
        {"error_description": "Unknown user: messi", "error": "UnknownUserError"}


Activitats de l'usuari
----------------------

Representa el conjunt d'activitats creades per un usuari i permet tant llistarles com crear-ne de noves.

.. http:get:: /people/{username}/activities

    Llistat totes les activitats generades al sistema d'un usuari concret.

    :query username: (REST) Nom de l'usuari que crea l'activitat

    Success
        Retorna una col·lecció d'objecte del tipus ``Activity``.

    Error
        En cas de que l'usuari actor no sigui el mateix usuari que s'autentica via oAuth::

            {u'error_description': u"You don't have permission to access xavi resources", u'error': u'Unauthorized'}

        En cas que l'usuari no existeixi::

            {"error_description": "Unknown user: messi", "error": "UnknownUserError"}

.. http:post:: /people/{username}/activities

    Genera una activitat en el sistema. Els objectes d'aquesta activitat són els especificats en el protocol activitystrea.ms.

    :query username: (REST) Nom de l'usuari que crea l'activitat
    :query contexts: (Opcional) Per fer que una activitat estigui associada a un context determinat fa falta que enviem una llista d'objectes contexts, indicant com a (``objectType``) el tipus 'context', i les dades del context com a l'exemple.
    :query object: (Requerit) Per ara només suportat el tipus (``objectType``) `note`. Ha de contindre les claus ``objectType`` i ``content`` que pot tractar-se d'un camp codificat amb HTML.

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

    Success
        Retorna un objecte del tipus ``Activity``.

    Error
        En cas de que l'usuari actor no sigui el mateix usuari que s'autentica via oAuth::

            {u'error_description': u"You don't have permission to access xavi resources", u'error': u'Unauthorized'}

        En cas que l'usuari no existeixi::

            {"error_description": "Unknown user: messi", "error": "UnknownUserError"}

    Tipus d'activitat suportats:
     * `note` (estatus d'usuari)

    Tipus d'activitat projectats:
     * `File`
     * `Event`
     * `Bookmark`
     * `Image`
     * `Video`
     * `Question`


Activitats globals
------------------

Representa el conjunt d'activitats generades pels usuaris del sistema. L'accés a algunes de les activitats vindrà limitada per les subscripcions a contexts de l'usuari que fa la petició.

.. http:get:: /activities

    Llistat de totes les activitats del sistema, filtrada sota algun criteri

    :query contexts: (Requerit) una llista de urls representant cadascuna un context

    Success
        Retorna una col·lecció d'objectes del tipus ``Activity``.


Timeline
----------

Representa el flux d'activitat global de l'usuari, que comprèn les activitats que ha creat, les activitats de les persones a qui segueix i les activitats generades sota un context concret al qual esta subscrit.

.. http:get:: /people/{username}/timeline

    Llistat totes les activitats del timeline de l'usuari.

    :query username: (REST) Nom de l'usuari que del qual volem el llistat

    Success
        Retorna una col·lecció d'objectes del tipus ``Activity``.


Comentaris d'una activitat
----------------------------

Representa el conjunt de comentaris fets a una activitat.

.. http:post:: /activities/{activity}/comments

    Afegeix un comentari a una activitat ja existent al sistema. Aquest servei crea el comentari pròpiament dit dins de l'activitat i genera una activitat nova (l'usuari ha comentat l'activitat... )

    :query activity: (REST) ha de ser un identificador vàlid d'una activitat existent, per exemple: 4e6eefc5aceee9210d000004
    :query actor: (Requerit) Objecte diccionari. Ha de contindre les claus ``username`` i ``objectType`` sent l'unic valor suportat d'aquesta ultima `person`.
    :query object: (Requerit) El tipus (``objectType``) d'una activitat comentari ha de ser `comment`. Ha de contindre les claus ``objectType`` i ``content``.

    Cos de la petició::

        {
            "actor": {
                "objectType": "person",
                "username": "javier"
            },
            "object": {
                "objectType": "comment",
                "content": "<p>[C] Testejant un comentari nou a una activitat</p>"
            }
        }

.. http:get:: /activities/{activity}/comments

    Llistat de tots els comentaris d'una activitat

    :query activity: (REST) ha de ser un identificador vàlid d'una activitat existent, per

    Retorna una col·lecció d'objectes del tipus ``Comment``


Subscripcions
--------------

Representa el conjunt de contextes als quals esta subscrit un usuari.

.. http:post:: /people/{username}/subscriptions

    Subscriu l'usuari a un context determinat.

    ..note::
        Aquest servei requereix autenticació basicAuth amb l'usuari d'operacions del MAX.

    :query username: (REST) L'identificador de l'usuari al sistema.
    :query contexts: (Requerit) Tipus d'object al qual ens volem subscriure. De moment només està suportat el tipus `context`. Hem de proporcionar un objecte amb les claus ``objectType`` i el valor 'context', i les dades del context com a l'exemple::

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
