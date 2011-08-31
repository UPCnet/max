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
        }
        "published": "2011-08-31T13:45:55Z"
    }

Es representa amb un tipus "note" (http://activitystrea.ms/head/activity-schema.html#note) que s'utilitza com a objecte base per a tots els status en l-especificació.
Aquests són els camps imprescindibles per a complir amb l'especificació, podent-se afegir d'altres opcionals.