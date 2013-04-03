Permisos
========

Es defineixen una serie de permisos i comportaments per defecte en relació als
permisos del sistema i de les entitats del sistema.

General
-------

Els permisos de modificació de camps i d'eliminació d'objectes estan subjectes a la propietat dels objectes.
La propietat

* creator
* actor
* owner

- El creator te el mateix comportament a tots els objectes i identifica l'usuari que estava autenticat via oauth en el moment
de la creació de l'objecte. Aquest camp no es pot modificar
- L'actor identifica la persona real que està creant un objecte, i que podria ser diferent del creator, en el cas que un administrador
estés creant activitat en nom d'una altra persona. L'actor tampoc es pot modificar.
- El owner identifica qui és el propietari, és a dir qui té el poder per poder-lo modificar i eliminar. En el moment de creació de l'objecte l'owner és el mateix que el creador, excepte el el cas de crear activitats, que serà l'actor. L'owner pot canviar en determinades ocasions, com per exemple al marxar l'owner original d'una conversa, l'owner passarà a ser un altre dels components de la conversa.

Contextos
---------

Els permisos dels contextos serveixen per assignar permis de
lectura/escriptura als usuaris en el moment de la subscripció. El permís que
s'utilitza és el que queda assignat a la subscripció de l'usuari, segons el
criteri escollit:

READ
~~~~
Defineix qui pot llegir l'activitat escrita sota el context

    - subscribed - Tots els usuaris subscrits al context poden llegir
    - public -  Qualsevol usuari sense esta subscrit al context el pot llegir

WRITE
~~~~~
Defineix qui pot afegir activitat al context

    - subscribed - Tots els usuaris subscrits al context poden escriure al context
    - restricted - Només el usuaris subscrits i autoritzats explicitament
      poden escriure al context
    - public -  Qualsevol usuari sense esta subscrit al context poden escriure
      al context

SUBSCRIBE
~~~~~~~~~
Defineix qui es pot subscriure al context

    - restricted - Només els usuaris administradors poden efectuar subscripcions al context
    - public - Qualsevol usuari pot subscriure's al context (i dessubscriure's)

UNSUBSCRIBE
~~~~~~~~~~~
Defineix qui es pot dessubscriure d'un context. Aquest permís es dona automàticament en cas que el permís subscribe sigui public.Només cal especificar-lo si es vol modificar el compartament per defecte.
    - restricted - Només els usuaris administradors poden dessubscriure usuaris del context
    - public - Qualsevol usuari pot dessubscriure's del context previament subscrit


Si no s'especifiquen en la creació del context, els permisos per defecte són:

    read='public', write='public', subscribe='public', invite='public'
