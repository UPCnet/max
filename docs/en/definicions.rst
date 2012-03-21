Introducció a conceptes i convencions
=====================================

En aquest document introduïem alguns conceptes relacionats amb l'arquitectura REST, orientats a entendre la implementació dels serveis al MAX. Aquí s'expliquen conceptes que o bé son comuns a tots els serveis, o ajuden a entendre la filosofia i la estructura darrera d'aquests.

Conceptes previs
-------------------

La api REST està organitzada en recursos, identificats per una URI concreta. Cada recurs és capaç de subministrar diferents respostes en funció amb el mètode que utilitzem per accedir a ell. En termes generals, cada recurs exposa 4 mètodes que implementen el que es coneix com a UI (Uniform interface): GET, POST, PUT i DELETE. Aquests mètodes és poden interpretar sota l'acrònim que s'usa normalment de CRUD (Create, Read, Update, Delete), sent la correspondència la següent:

:GET: Llegir element(s) d'un recurs
:POST: Crear un element dins un recurs
:PUT: Modificar un element existent d'un recurs
:DELETE: Eliminar un element d'un recurs

Els recursos poden imlemenetar un o diversos dels mètodes de la UI, segons apliqui per el significat de cada recurs, complint sempre amb el significat genèric del mètode utilitzat. Els diferents serveis que hi han implementats, a part de la UI, comparteixen la forma en que expressen el resultat. Hi ha diferents codis d'estat , segons els estàndards HTTP, que es retornen com a codi d'estat en la resposta del servei, juntament amb les dades asociades a ca:

Codis d'estat
---------------

Tots els serveis indiquen el resultat de l'operació amb un codi d'estat de la resposta HTTP que pot ser un dels següents.

:200 OK: El servidor ha pogut processar el servei i donar una resposta correctament. Si estem fent un POST, i l'element que voliem crear ja existeix, aquest és el codi que rebrem.
:201 CREATED: S'ha creat una entitat nova al recurs
:400 BAD REQUEST: Alguns dels paràmetres requerits manquen o són erronis
:401 UNAUTHORIZED: Manca alguna paràmetre d'autenticació o aquesta no és vàlida
:404 NOT FOUND: El recurs solicitat no existeix, en aquest cas, comprovar la URI
:500 INTERNAL SERVER ERROR: Només en cas de apareixer algun bug o cas no tractat
:501 NOT IMPLEMENTED: En recursos existents, indica que aquell mètode encara no esta implementat o que no aplica per el tipus de recurs solicitat

Exceptuant els codis 200 i 201, que en el cos de la resposta es retorna l'object sobre el qual s'està actuant, en la resta de casos s'inclou un text descriptiu de l'error, que ens pot indicar la causa exacte del mateix.

Accés a recursos
------------------

Els recursos que anomenarem "arrel" (a partir d'ara col.leccions), són identificats per parts de la URI que no canvien, i són expresades en plural, o amb una paraula que impliqui un conjunt. Aquestes col·leccions contenen 1 o més elements (a partir d'ara entitats).

Per exemple::

    GET /people

Ens llista totes les entitats del recurs people i de la mateixa manera::

    GET /people/mindundi

Ens llista totes les dades de l'entitat mindundi. En aquest cas a la URI podem llegir un recurs arrel i una entitat concreta d'aquest recurs, però podem tenir altres recursos aniuats, representant un subconjunt d'entitats filtrades segons el recurs pare com per exemple::

    GET /people/mindundi/activities

Les URI's dels serveis REST les podem interpretar quasibé sempre llegint de dreta a esquerra, agrupant els diferents identificadors d'entitats concretes amb el seu recurs. D'aquesta manera, l'ultim exemple el podem interpretar com a::

    "Activitats de la persona amb nom mindundi"

Creació d'elements nous
--------------------------

Per afegir una entitat a un recurs concret, ens podem trobar dos casos, depenent del recurs. Ens podem trobar que necessitem indicar el paràmetre que es convertira en l'identificador únic de l'entitat, o que el sistema ja el generi automàticament i per tant no ens calgui proporcionar-lo. En ambdos casos, per afegir entitats a un recurs, sempre utilitzarem el mètode POST, per exemple::

    POST /users/mindundi

Ens afegirà l'usuari mindundi al recurs. Per altra banda::

    POST /users/mindundi/activities

Ens afegirà una activitat, generant l'identificador automàticament. En la documentació detallada de cada recurs, especifica quin cas aplica per cada un, i quins paràmetres i/o estructures de dades se li han de proporcionar.

Accedir a elements concrets
------------------------------

Les URI's per accedir a un element concret d'un recurs, coincidiran amb la sintaxis de les URI's per afegir un element especificant l'identificador. La diferència estarà en el mètode d'accés.

D'aquesta manera fent::

    GET /users/mindundi

Obtenim  l'usuari mindundi que en la secció anterior haviem creat. La URI és la mateixa, els paràmetres els mateixos (en aquest cas no n'hi han), només canvia el mètode HTTP usat.

Format dels paràmetres
----------------------

Els serveis accepten paràmetres en format JSON quan s'envien a través del cos de la resposta, cas en el qual s'ha de incloure la capçalera 'content-type' indicant el valor 'aplication/json'.

Els serveis també accepten pas de paràmentres en el format 'application/form-url-encoded', per exemple les peticions GET que no tenen cos, obligatòriament han de utilitzar aquest format.

Per estructures complexes amb més d'un nivell utilitzarem sempre JSON, mentre que per llistes de paràmetres clau=valor, podem utilitzar el tradicional 'application/form-url-encoded'

Per paràmetres que representen llistes de valors i que s'han de passar via GET, hem d'assegurar que el format en que es genera la llista de paràmentres compleixi el bàsic de HTTP, ja que hi han multiples convencions de com fer-ho. Per exemple:

    Si tenim el camp 'context' que té 2 valors 'A' i 'B', els paràmetres de la petició
    han repetir la clau 'context' tantes vegades com valors hi hagi::

    ?context=A&context=B

Adreces canòniques per recursos amb múltiples URI's
------------------------------------------------------

Hi a alguns casos en que un recurs te més d'una possible URI, majoritàriament determinat per que al crear l'element necessitem donar algun paràmetre que és coherent que estigui inclos en la URI, però que per posteriors accessos al recurs no te sentit. Posem un exemple a continuació per veure-ho més clar:

Per Afegir una activitat::

    POST /users/mindundi/activities

Pasant el contingut de l'activitat amb una estructura JSON. Aquesta activitat, tot i haver-la creat nosaltres, es pot donar el cas que algú que ens estigui seguint vulgui compartir aquesta activitat. Supsant que la activitat creada tingues un nom "activitat1", seguint la sintaxis del rest, podem accedir a la activitat a través de ::

    GET /users/mindundi/activities/activitat1

Tot i així si el que volem es compartir l'activitat amb algú altre, no te sentit indicar qui és el creador de l'activitat, ja que totes les activitats estan a la mateixa "saca". Podem accedir a la activitat de la següent manera::

    GET /activities/activitat1

que és equivalent a la forma anterior. Això ens dona una URI (canònica) simplificada per dur a terme accions com per exemple la de compartir, que seria de la següent forma::

    POST /activities/activitat1/shares

on shares representa el conjunt de vegades que s'ha compartit la activitat