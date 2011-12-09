API REST
========

Aquest document exposa els serveis web creats pel motor d'activitat i subscripcions. Tots els serveis web són de tipus REST i l'intercanvi d'informació es realitza en format JSON.

A l'espera d'un sistema d'autenticació basat en oAuth 2.0, i excepcionalment en periode beta i posteriors proves i pre-producció, els serveis no requereixen autenticació.

Canvi d'estat
-------------

.. http:post:: /activity
    
    Genera una activitat en el sistema. Els objectes d'aquesta activitat són els especificats en el protocol activitystrea.ms.


    :query actor: (Requerit) Objecte diccionari. Ha de contindre les claus ``id`` i ``displayName``, i com a opcional, determinar el tipus d'objecte (``objectType``) i sent un usuari el valor serpa `person`.
    :query verb: (Requerit) Per ara només suportat el verb ``post``
    :query target: (Opcional) Per fer que una activitat estigui associada a un context determinat fa falta que enviem l'objecte target, indicant com a (``objectType``) el tipus 'service', i les dades del context com a l'exemple.
    :query object: (Requerit) Per ara només suportat el tipus (``objectType``) `note`. Ha de contindre les claus ``objectType`` i ``content`` que pot tractar-se d'un camp codificat amb HTML.

    Tipus d'activitat suportats:
     * `note` (estatus d'usuari)

    Tipus d'activitat projectats:
     * `File`
     * `Event`
     * `Bookmark`
     * `Image`
     * `Video`
     * `Question`

     Exemple::
        
        user_status = {
            "actor": {
                "objectType": "person",
                "id": "4e6e1243aceee91143000000",
                "displayName": "victor"
            },
            "verb": "post",
            "target": {
                "objectType": "service",
                "displayName": "Introduccio als computadors",
                "url": "http://atenea.upc.edu/introcomp"
            },            
            "object": {
                "objectType": "note",
                "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
            },
        }

Comentaris
----------

.. http:post:: /comment

    Afegeix un comentari a una activitat ja existent al sistema. Aquest servei crea el comentari pròpiament dit i genera una activitat nova (l'usuari ha comentat l'activitat... ).

    :query verb: (Requerit) Ha de ser el verb ``post``.
    :query actor: (Requerit) Objecte diccionari. Ha de contindre les claus ``id`` i ``displayName``, i com a opcional, determinar el tipus d'objecte (``objectType``) i sent un usuari el valor serà `person`.
    :query object: (Requerit) El tipus (``objectType``) d'una activitat comentari ha de ser `comment`. Ha de contindre les claus ``objectType`` i ``content`` que pot tractar-se d'un camp codificat amb HTML. Igualment, ha de contindre la clau ``inReplyTo`` del tipus llista (vector) de diccionaris, que ha de contindre a la seva vegada com a mínim un objecte diccionari que identifiqui a l'objecte (o objectes) al que fa referència el comentari, especificant com a mínim la clau ``id`` corresponent al número d'identificació únic de l'activitat (o activitats) en el sistema.

    Exemple::

        user_comment = {
            "actor": {
                "objectType": "person",
                "id": "4e6e1243aceee91143000000",
                "displayName": "javier"
            },
            "verb": "post",
            "object": {
                "objectType": "comment",
                "content": "<p>[C] Testejant un comentari nou a una activitat</p>",
                "inReplyTo": [
                  {
                    "id": "4e6eefc5aceee9210d000004",
                  }
                ]
            },
        }

Seguir (*follow*) a un usuari
-----------------------------

.. http:post:: /follow

    Guarda dins del sistema la voluntat de l'usuari de seguir a un altre usuari. Aquest servei guarda dins de l'objecte usuari la referència a l'usuari seguit i genera una activitat nova (l'usuari ara segueix a l'usuari...).

    :query verb: (Requerit) Ha de ser el verb ``follow``.
    :query actor: (Requerit) Objecte diccionari. Ha de contindre les claus ``id`` i ``displayName``, i com a opcional, determinar el tipus d'objecte (``objectType``) i sent un usuari el valor serà `person`.
    :query object: (Requerit) El tipus (``objectType``) d'una activitat follow ha de ser un altre usuari (`person`). Ha de contindre les claus ``objectType``, ``id`` i ``displayName`` que identifiquen unívocament a l'usuari en el sistema.

    Exemple::
        
        follow = {
            "actor": {
                "objectType": "person",
                "id": "4e6e1243aceee91143000000",
                "displayName": "victor"
            },
            "verb": "follow",
            "object": {
                "objectType": "person",
                "id": "4e6e1243aceee91143000001",
                "displayName": "javier"
            },
        }


Deixar de seguir (*unfollow*) a un usuari
-----------------------------------------

.. http:post:: /unfollow

    Guarda dins del sistema la voluntat de l'usuari de deixar de seguir a un altre usuari. Aquest servei esborra de l'objecte usuari la referència a l'usuari seguit i genera una activitat nova (l'usuari ha deixat de seguir a l'usuari...).

    :query verb: (Requerit) Ha de ser el verb ``unfollow``.
    :query actor: (Requerit) Objecte diccionari. Ha de contindre les claus ``id`` i ``displayName``, i com a opcional, determinar el tipus d'objecte (``objectType``) i sent un usuari el valor serà `person`.
    :query object: (Requerit) El tipus (``objectType``) d'una activitat follow ha de ser un altre usuari (`person`). Ha de contindre les claus ``objectType``, ``id`` i ``displayName`` que identifiquen unívocament a l'usuari en el sistema.

    Exemple::

        unfollow = {
            "actor": {
                "objectType": "person",
                "id": "4e6e1243aceee91143000000",
                "displayName": "victor"
            },
            "verb": "unfollow",
            "object": {
                "objectType": "person",
                "id": "4e6e1243aceee91143000001",
                "displayName": "javier"
            },
        }

Subscripció a un context
------------------------

.. http:post:: /follow_context

    Guarda dins del sistema la voluntat de l'usuari de subscriure's a un context i per extensió a totes les activitats que els usuaris del sistema generen sota aquest context. Aquest servei guarda dins de l'objecte usuari la referència al context seguit i genera una activitat nova (l'usuari ara està subscrit al context...).

    :query verb: (Requerit) Ha de ser el verb ``follow``.
    :query actor: (Requerit) Objecte diccionari. Ha de contindre les claus ``id`` i ``displayName``, i com a opcional, determinar el tipus d'objecte (``objectType``) i sent un usuari el valor serà `person`.
    :query object: (Requerit) El tipus (``objectType``) d'aquesta activitat serà del tipus `service`. Ha de contindre les claus ``displayName`` i ``url`` que identifiquen el context.

    Per ara, el sistema no manté una relació única de contexts seguits al sistema. Han de ser els mateixos contexts que han de mantindre una coherència al generar les seves activitats en els portlets, widgets o activitats autogenerades.
    
    Exemple::
        
        follow_context = {
            "actor": {
                "objectType": "person",
                "id": "4e6e1243aceee91143000000",
                "displayName": "victor"
            },
            "verb": "follow",
            "object": {
                "objectType": "service",
                "displayName": "Introduccio als computadors",
                "url": "http://atenea.upc.edu/introcomp"
            },
        }

Eliminar la subscripció a un context
------------------------------------

.. http:post:: /unfollow_context

    Guarda dins del sistema la voluntat de l'usuari de deixar d'estar subscrit a un context i per extensió a totes les activitats que els usuaris del sistema generen sota aquest context. Aquest servei elimina de l'objecte usuari la referència al context seguit i genera una activitat nova (l'usuari ja no està subscrit al context...).

    :query verb: (Requerit) Ha de ser el verb ``unfollow``.
    :query actor: (Requerit) Objecte diccionari. Ha de contindre les claus ``id`` i ``displayName``, i com a opcional, determinar el tipus d'objecte (``objectType``) i sent un usuari el valor serà `person`.
    :query object: (Requerit) El tipus (``objectType``) d'aquesta activitat serà del tipus `service`. Ha de contindre les claus ``displayName`` i ``url`` que identifiquen el context.

    Exemple::

        unfollow_context = {
            "actor": {
                "objectType": "person",
                "id": "4e6e1243aceee91143000000",
                "displayName": "victor"
            },
            "verb": "unfollow",
            "object": {
                "objectType": "service",
                "displayName": "Introduccio als computadors",
                "url": "http://atenea.upc.edu/introcomp"
            },
        }

Compartir (*share*) una activitat
---------------------------------

.. http:post:: /share

    Genera una activitat que republica un altre activitat.

    :query verb: (Requerit) Ha de ser el verb ``share``.
    :query actor: (Requerit) Objecte diccionari. Ha de contindre les claus ``id`` i ``displayName``, i com a opcional, determinar el tipus d'objecte (``objectType``) i sent un usuari el valor serà `person`.
    :query object: (Requerit) El tipus (``objectType``) d'aquesta activitat serà del tipus `activity`, doncs es comparteix o republica una activitat del sistema. Ha de contindre la clau ``id`` que identifica unívocament l'activitat que es vol compartir.

    Exemple::

        share = {
            "actor": {
                "objectType": "person",
                "id": "4e6e1243aceee91143000000",
                "displayName": "javier"
            },
            "verb": "share",
            "object": {
                "objectType": "activity",
                "id": "4e6eefc5aceee9210d000004",
            },
        }

Marcar l'activitat com *m'agrada* (`likes`)
-------------------------------------------

.. http:post:: /like

    Genera una activitat nova del tipus a l'usuari li agrada aquesta activitat. A més, actualitza l'objecte activitat a la que fa referència amb la informació del *m'agrada*.

    :query verb: (Requerit) Ha de ser el verb ``like``.
    :query actor: (Requerit) Objecte diccionari. Ha de contindre les claus ``id`` i ``displayName``, i com a opcional, determinar el tipus d'objecte (``objectType``) i sent un usuari el valor serà `person`.
    :query object: (Requerit) El tipus (``objectType``) d'aquesta activitat serà del tipus `activity`, doncs es comparteix o republica una activitat del sistema. Ha de contindre la clau ``id`` que identifica unívocament l'activitat que es vol compartir.

    Exemple::

        like = {
            "actor": {
                "objectType": "person",
                "id": "4e6e1243aceee91143000000",
                "displayName": "javier"
            },
            "verb": "like",
            "object": {
                "objectType": "activity",
                "id": "4e707f80aceee94f49000002"
            },
        }

Cerques
-------

.. http:get:: /user_activity

    Fa una cerca a la base de dades del sistema i retorna tota l'activitat de l'usuari així com l'activitat a la que està subscrit i l'activitat que generen els usuaris als que segueix.

    :query displayName: (Requerit) L'identificador de l'usuari al sistema.

    Exemple::
        
        query = {
            "displayName": "victor"
        }

.. http:get:: /user_activity_by_scope

    Fa una cerca a la base de dades del sistema i retorna tota l'activitat de l'usuari dins dels contexts especificats. No es retorna ni l'activitat a la que està subscrit ni l'activitat que generen els usuaris als que segueix.

    :query displayName: (Requerit) L'identificador de l'usuari al sistema.
    :query scopes: (Requerit) Els identificadors dels contexts sobre els que es vol fer la consulta.

    Exemple::
        
        query = {
            "displayName": "victor",
            "scopes": [
                'http://atenea.upc.edu/123123', 'http://atenea.upc.edu/456456'
                ]
        }

Creació d'un usuari del sistema
-------------------------------

.. http:post:: /add_user
    
    Si no existeix l'usuari especificats als paràmetres, crea un usuari remotament al sistema pel seu posterior us i retorna l'id únic de l'usuari al sistema en format JSON. Si ja existeix, només retorna l'id de l'usuari especificat.

    :query displayName: (Requerit) L'identificador del nou usuari al sistema.

    Retorna un objecte JSON amb l'id de l'usuari::

        {"$oid": "4e7b1d79aceee94bbd000009"}
