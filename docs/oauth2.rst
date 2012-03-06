Autenticació OAuth2
===================

Aquest document mostra quin és el flux oauth2 emprat per l'autenticació dels serveis webs del MAX, així com quin és el mecanisme triat per transportar els paràmetres oauth dins les peticions del servei.

Amb la implementació actual, els tokens generats per servidor OAuth no caduquen mai, i s'han d'invalidar manualment amb un webservice si és necessita.


Descripció del flux Oauth
--------------------------

A continuació una definició descriptiva del flux de petició de tokens:

* Obtenim el nom d'usuari i el password de l'usuari de qual volem obtenir el token
* Contactem amb el servei oauth, i li proporcionem les dades per obtenir el token
* El servei oauth ens proporciona un token per l'usuari indicat

Un cop tenim el token, per tal d'utilitzarlo:

* Fem una crida a un servei del MAX, indicant l'usuari i el token
* El MAX al rebre la petició, comprova al servidor oauth la validesa del token
* Si el token és valid, executa el servei i retorna la resposta


Crides al sistema oauth
------------------------

.. http:post:: /token/

    Demana un token per un usuari i un scope concrets segons els següents paràmetres passats en format 'application/form-url-encoded'

    :``grant_type`` : La cadena de text 'password', que indica que utilitzara un usuari LDAP per validar
    :``client_id`` : en el nostre cas, l'id és 'MAX'
    :``scope``: Cadena de text que indica desde on es genera l'activitat, de moment l'única permesa pel max és 'widgetcli', per tant hem d'usar aquesta
    :``username``: nom d'usuari pel que volem obtenir el token
    :``password``: contrasenya de l'usuari


    Retorna un codi de resposta HTTP 200 i una estructura JSON de la forma::

    {  "oauth_token": "4d53575d0d9582839c510b3302ac1f2c", "scope": "widgetcli", "fresh": false  }


    on 'fresh' ens indica si el token s'acava de generar o ja n'existia un de vàlid per aquest usuari i scope concrets. Davant d'un error, el servei retorna un codi d'error HTTP 400, i una estructura JSON indicant l'error, per exemple::

    {  "error": "invalid_grant"   }

.. http:post:: /checktoken

    Comprova la validesa d'un token per un usuari i un scope concrets segons els següents paràmetres passats en format 'application/form-url-encoded'

    :``oauth_token`` : El token que volem validar
    :``user_id`` : Nom d'usuari al que pertany el token
    :``scope``: Cadena de text que indica desde on es genera l'activitat, de moment l'única permesa pel max és 'widgetcli', per tant hem d'usar aquesta. Ha de ser la mateixa que es va especificar al moment de demanar el token.


    Retorna un codi de resposta HTTP 200 si el token és valid i un HTTP 401 si no ho és.


Us de OAuth amb MAX
--------------------

Per poder indicar al max que ens volem autenticar utilizant OAuth, ho farem a través de 3 capçaleres HTTP pròpies, amb les que proporcionarem les dades al MAX perquè pugui fer la validació del token. Tota petició a un servei del max que requereix de autenticació OAuth ha de contenir:

* ``X-Oauth-Token``: amb el valor del token que volem validar
* ``X-Oauth-Username``: amb el nom de l'usuari al qual pertany el token
* ``X-Oauth-Scope``: scope amb el que es va generar el token
