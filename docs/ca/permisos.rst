Permisos
========

Es defineixen una serie de permisos i comportaments per defecte en relació als
permisos del sistema i de les entitats del sistema.

Contextos
---------

Els permisos dels contextos serveixen per assignar permis de
lectura/escriptura als usuaris en el moment de la subscripció. El permís que
s'utilitza és el que queda assignat a la subscripció de l'usuari, segons el
criteri escollit:

READ
~~~~
    - subscribed - Tots els usuaris subscrits al context poden llegir
    - public -  Qualsevol usuari sense esta subscrit al context el pot llegir

WRITE
~~~~~

    - subscribed - Tots els usuaris subscrits al context poden escriure al context
    - restricted - Només el usuaris subscrits i autoritzats explicitament
      poden escriure al context
    - public -  Qualsevol usuari sense esta subscrit al context poden escriure
      al context

SUBSCRIBE
~~~~~~~~~

    - restricted - Només els usuaris administradors poden efectuar subscripcions al context
    - public - Qualsevol usuari pot subscriure's al context (i dessubscriure's)

Si no s'especifiquen en la creació del context, els permisos per defecte són:

    read='public', write='public', subscribe='public', invite='public'
