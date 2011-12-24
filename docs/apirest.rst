API REST
========

Aquest document exposa els serveis web creats pel motor d'activitat i subscripcions. Organitzats per recursos. Tots els serveis web són de tipus RESTful i l'intercanvi d'informació es realitza en format JSON.

Els paràmetres indicats a les seccions Query parameters, poden ser de 3 tipus:

:REST: Són obligatoris ja que formen part de la URI
:Requerits: Són obligatoris, però formen part de l'estructura JSON que s'envia amb el cos de la petició
:Opcionals: Com el nom indica, no son obligatoris, indiquen alguna funcionalitat extra

Les respostes que retorna el sistema, en cas que siguin 1 o múltiples resultats (Associats a col.leccions o entitats) seràn, o bé un sol objecte JSON en cas de l'accés a una entiat concreta, o una estructura que englobi un conjunt de resultats, indicant el total d'elements retornats::

    {

        "totalItems": 2,
        "items": [
                   { ... }
                   { ... }                 
                 ]
    }

A l'espera d'un sistema d'autenticació basat en oAuth 2.0, i excepcionalment en periode beta i posteriors proves i pre-producció, els serveis no requereixen autenticació.




Usuaris
--------

Representa el conjunt d'usuaris del sistema

.. http:post:: /people/{displayName}
    
    Crea un usuari remotament al sistema pel seu posterior us, si no existeix. En cas de que l'usuari ja existis, el retorna canviant el codi d'estat HTTP en funció de l'accó realitzada.

    :query displayName: (REST) L'identificador del nou usuari al sistema.

    Retorna un objecte ``Person``


Timeline
----------

Representa el flux d'activitat global de l'usuari, que comprèn les activitats que ha creat, les activitats de les persones a qui segueix, i les activitats generades sota un context concret


.. http:get:: /people/{displayName}/timeline

    Llistat totes les activitats del timeline de l'usuari

    :query displayName: (REST) Nom de l'usuari que del qual volem el llistat

    Retorna una col·lecció d'objectes del tipus ``Activity``

Activitats de l'usuari
------------------------

Representa el conjunt d'activitats creades per un usuari, i permet llistarles i crear-ne de noves


.. http:get:: /people/{displayName}/activities

    Llistat totes les activitats generades al sistema d'un usuari concret

    :query displayName: (REST) Nom de l'usuari que crea l'activitat

    Retorna una col·lecció d'objecte del tipus ``Activity``

.. http:post:: /people/{displayName}/activities
    
    Genera una activitat en el sistema. Els objectes d'aquesta activitat són els especificats en el protocol activitystrea.ms.

    :query displayName: (REST) Nom de l'usuari que crea l'activitat
    :query verb: (Requerit) Per ara només suportat el verb ``post``
    :query contexts: (Opcional) Per fer que una activitat estigui associada a un context determinat fa falta que enviem l'objecte contexts, indicant com a (``objectType``) el tipus 'context', i les dades del context com a l'exemple.
    :query object: (Requerit) Per ara només suportat el tipus (``objectType``) `note`. Ha de contindre les claus ``objectType`` i ``content`` que pot tractar-se d'un camp codificat amb HTML.

    Cos de la petició::
        
       {
            "verb": "post",
            "target": {
                "objectType": "service",
                "url": "http://atenea.upc.edu/introcomp"
            },            
            "object": {
                "objectType": "note",
                "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
            },
        }

    Retorna un objecte del tipus ``Activity``

    Tipus d'activitat suportats:
     * `note` (estatus d'usuari)

    Tipus d'activitat projectats:
     * `File`
     * `Event`
     * `Bookmark`
     * `Image`
     * `Video`
     * `Question`


Comentaris d'una activitat
----------------------------

Representa el conjunt de comentaris realitzats sobre una activitat concreta

.. http:post:: /activities/{activity}/comments

    Afegeix un comentari a una activitat ja existent al sistema. Aquest servei crea el comentari pròpiament dit dins de l'activitat i genera una activitat nova (l'usuari ha comentat l'activitat... )

    :query activity: (REST) ha de ser un identificador vàlid d'una activitat existent, per exemple: 4e6eefc5aceee9210d000004
    :query verb: (Requerit) Ha de ser el verb ``post``.
    :query actor: (Requerit) Objecte diccionari. Ha de contindre les claus ``id`` i ``displayName``, i com a opcional, determinar el tipus d'objecte (``objectType``) i sent un usuari el valor serà `person`.
    :query object: (Requerit) El tipus (``objectType``) d'una activitat comentari ha de ser `comment`. Ha de contindre les claus ``objectType`` i ``content`` que pot tractar-se d'un camp codificat amb HTML. 

    Cos de la petició::

        {
            "actor": {
                "objectType": "person",
                "displayName": "javier"
            },
            "verb": "post",
            "object": {
                "objectType": "comment",
                "content": "<p>[C] Testejant un comentari nou a una activitat</p>",
            },
        }


