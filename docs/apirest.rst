API REST
========

Aquest document exposa els serveis web creats pel motor d'activitat i subscripcions. Tots els serveis web són de tipus REST i l'intercanvi d'informació es realitza en format JSON.

A l'espera d'un sistema d'autenticació basat en oAuth 2.0, i excepcionalment en periode beta i posteriors proves i pre-producció, els serveis no requereixen autenticació.

.. http:post:: /activity
    
    Genera una activitat en el sistema.

    Tipus d'activitat suportats:
     * `note` (estatus d'usuari)

(per un altre lloc!!, l'activitat només suporta 'notes', per ara...)
     * `comment` (comentari d'un usuari a una activitat)
     * `follow` (usuari comença a 'seguir' l'activitat d'un altre usuari)
     * `unfollow` (l'usuari deixa de 'seguir' l'activitat d'un altre usuari)
     * `share`
