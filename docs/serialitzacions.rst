Serialitzacions i estructures JSON
==================================

En aquest document s'exposa una llista, a mode de manual de referència, de totes les serialitzacions JSON possibles utilitzades en MACS.

.. note::

    Aquestes serialitzacions són les dades JSON que s'afegeixen finalment en la base de dades de la aplicació. Encara que poden ser similars, en cap moment es refereixen al cos JSON que s'utilitza en les crides a serveis REST.

Canvi d'estatus d'usuari
------------------------

L'activitat generada per l'usuari més simple i comú::

    {
        "actor": {
            "objectType" : "person",
            "id":"victor"
        },
        "verb": "post",
        "object": {
            "objectType": "note",
            "content": "Avui sera un gran dia!"
        },
        "published": "2011-08-31T13:45:55Z"
    }

Es representa amb un tipus "note" (http://activitystrea.ms/head/activity-schema.html#note) que s'utilitza com a objecte base per a tots els status en l-especificació.
Aquests són els camps imprescindibles per a complir amb l'especificació, podent-se afegir d'altres opcionals.

Comentaris a una activitat
--------------------------

Quan es genera un comentari han de passar dues coses: La primera, crear un registre d'activitat nou que guardi els detalls de la nova activitat (comentari). Després, cal actualitzar el registre original a la que fa referència el comentari.

Per més informació, veure la especificació encara en draft: http://activitystrea.ms/specs/json/replies/1.0/

Aquest és l'esquema de la nova activitat comentari::

    {
        "actor": {
            "objectType" : "person",
            "id":"victor"
        },
        "verb": "post",
        "object": {
            "objectType": "comment",
            "content": "<p>This is a comment</p>",
            "inReplyTo": [
              {
                "objectType": "note",
                "id": "http://example.org/objects/123",
                "displayName": "A simple note"
              }
            ]
        },
        "published": "2011-08-31T13:45:55Z"
    }

Aquest és l'esquema de l'objecte al que fa referència::

    {
        "actor": {
            "objectType" : "person",
            "id":"victor"
        },
        "verb": "post",
        "object": {
            "objectType": "note",
            "content": "Avui sera un gran dia!"
        },
        "replies": {
            "totalItems": 2,
            "items": [
                {
                    "_id":"4134231423412344",
                    "objectType": "comment",
                    "author": {
                        "objectType" : "person",
                        "id":"victor"
                    },
                    "content": "<p>This is a comment</p>",
                    "published": "2011-08-31T13:45:55Z"
                },
                {
                    "_id":"4134231423412346",
                    "objectType": "comment",
                    "author": {
                        "objectType" : "person",
                        "id":"victor"
                    },
                    "content": "<p>This is another comment</p>",
                    "published": "2011-08-31T13:50:55Z"
                }        
            ]
        },
        "published": "2011-08-31T13:45:55Z"
    }

Seguir (*follow*) a un usuari
-----------------------------

Un usuari pot decidir seguir a un altre usuari i així l'activitat d'aquest usuari passarà a aparèixer en el timeline de l'usuari que te la voluntat d'iniciar l'acció de seguiment.

.. note::

    Hi han dos timelines públics que es poden demanar al sistema: el timeline d'activitat d'usuari (sovint anomenada home_timeline i que només mostra directament l'activitat generada per ell) i el que aglutina tota l'activitat adreçada a l'usuari (inclou l'activitat del home_timeline, l'activitat a la que està subscrita l'usuari).

Cada cop que un usuari segueix a un altre, es genera una activitat informant d'aquest canvi i es guarda la relació a la base de dades. Aquest és l'esquema de l'objecte activitat::

    {
        "actor": {
            "objectType" : "person",
            "id":"victor"
        },
        "verb": "follow",
        "object": {
            "objectType" : "person",
            "id":"javier"
        },
        "published": "2011-08-31T13:45:55Z"
    }

Subscriure's (*follow*) a un context
------------------------------------

Un usuari pot decidir seguir l'activitat generada per un context (veure apartat següent). Cada context ha de tindre una URI (o IRI) que l'identifiqui unívocament.

Cada cop que un usuari es subscriu a un context, es genera una activitat informant d'aquest canvi i es guarda la relació a la base de dades. Aquest és l'esquema de l'objecte activitat::

    {
        "actor": {
            "objectType" : "person",
            "id":"victor"
        },
        "verb": "follow",
        "object": {
            "objectType": "service"
            "id": "ASSIG123456",
            "displayName": "Introduccio als computadors",
            "url": "http://atenea.upc.edu/introcomp"
        },
        "published": "2011-08-31T13:45:55Z"
    }

.. note:

    No s'ha pogut trobar un tipus d'objecte més adient que el de "service" per identificar a un context. En tot cas és susceptible de que es pugui determinar un altre més adient en posteriors revisions.


Generació d'activitat sota un context
-------------------------------------

Un usuari pot generar una activitat sota un determinat context o ubicació. Per exemple, en una assignatura o en una carpeta d'un gestor de continguts.

Aleshores, posteriorment, es poden fer peticions de fil d'activitat per context, amb el web service XXX


Canvi d'estatus d'usuari sota un context
----------------------------------------

Aquesta seria la sintaxi d'aquest tipus d'activitat::

    {
        "actor": {
            "objectType" : "person",
            "id":"victor"
        },
        "verb": "post",
        "object": {
            "objectType": "note",
            "content": "Avui sera un gran dia!"
        },
        "target": {
            "objectType": "service"
            "id": "ASSIG123456",
            "displayName": "Introduccio als computadors",
            "url": "http://atenea.upc.edu/introcomp"
        },
        "published": "2011-09-06T13:45:55Z"
    }

