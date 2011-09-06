Serialitzacions i estructures JSON
==================================

En aquest document s'exposen una llista, a mode de manual de referència, de totes les serialitzacions JSON possibles que s'utilitzen en MACS.

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

Generació d'activitat sota un context
-------------------------------------

Un usuari pot generar una activitat sota un determinat context o ubicació. Per exemple, en una assignatura o en una carpeta d'un gestor de continguts.

Aleshores, posteriorment, es poden fer peticions de fil d'activitat per context, amb el web service XXX


Canvi d'estatus d'usuari sota un context
----------------------------------------

Aquesta seria la sintaxi d'aquest tipus d'activitat:

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
        }
        "published": "2011-09-06T13:45:55Z"
    }

