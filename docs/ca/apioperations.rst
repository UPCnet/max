API REST (restringida)
======================

Aquesta és la llista de serveis REST que queda fora de la operativa d'usuari i
de la UI. Si no s'indica el contrari, aquests serveis s'autentiquen via HTTP
BasicAuth i està dissenyada per ĺ'ús d'un usuari restringit d'aplicació.
Aquest usuari no te cap privilegi addicional sobre el sistema que el que
s'exposa en la descripció de cada servei.


Contexts
--------

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

.. http:post:: /contexts

    Afegeix un context al sistema.

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
    :query permissions: (Opcional) Els permisos i parametrització de seguretat
        relacionada amb el context.

    Cos de la petició::

        {
            'url': 'http://atenea.upc.edu',
            'displayName': 'Atenea',
            'twitterHashtag': 'atenea',
            'twitterUsername': 'atenaupc',
            'permissions': {
                                'read':'subscribed',
                                'write':'subscribed'
                            }
            }

    Success
        Retorna l'objecte ``Context``.

.. http:put:: /contexts

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

    Success
        Retorna l'objecte ``Context`` modificat.

