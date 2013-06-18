Max UI
=====================================

En aquest document descriurem els passos per integrar el widget del max,
anomenat MaxUI, en aplicacions de tercers. MaxUI proporciona una interfície
d'usuari configurable per a clients finals a través de la qual accedir a les
funcionalitats del MAX.

El widget esta dissenyat per incorporar-se en qualsevol pagina html com a un
contingut més, sense iframes, i sense interferir ni amb el comportament de la
pàgina ni amb la càrrega d'aquesta. Si per la raó que sigui el widget no esta
disponible o tarda molt en carregar, la pàgina que el conté no s'en veurà
perjudicada. Al ser un component implementat en javascript, la càrrega de
renderitzar-lo i de les peticions als serveis del max que realitza està
suportada al 100% pel navegador.

Prerequisits
------------

Per poder utilitzar el widget cal:

* Tenir instal·lat a l'entorn web jQuery 1.7.x o superior.

Si no disposem de jQuery, el podem instal·lar localment o bé agafar-lo de
qualsevol CDN disponible a la xarxa, per exemple:

.. code-block:: html

    <script src="//ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js"></script>

* Disposar d'algun mecanisme per generar javascript dinàmic:

Com a mínim hi haurà un paràmetre que s'ha de configurar, que depèn de l'usuari
autenticat a la web on es mostrarà el widget. Es per això que el nostre sistema
ha de disposar d'algun mètode per incorporar fitxers *.js* generats partir de
plantilles.

* Disposar d'algun mecanisme per interceptar la autenticació de l'usuari a
  l'aplicació hoste.

* Els usuaris del sistema ha de ser usuaris de l'LDAP UPC.

El servidor de OAUTH que s'utilitza per autenticar els usuaris del widget, te de
base els usuaris del LDAP.


Instal·lació del widget
-----------------------

La instal·lació del widget consisteix en les següents parts:

* Incorporació del *contenidor* html on es renderitzadà el widget
* Incorporació del *loader* que descarregarà i inicialitzarà el widget
* Incorporació dels *css* del widget


Contenidor
+++++++++++

El *contenidor* és l'element del DOM de la pàgina destí on es vol mostrar el
widget. Hem de reservar un espai amb un element ``<div>`` al qual li hem de
fixar la amplada en pixels ja sigui a través dels css existents en la pàgina, o
bé amb un ``style`` *inline*. L'amplada pot ser qualsevol, però per una millor
experiència d'usuari es recomana d'un mínim de 300px:

.. code-block:: html

    <div id="container" style="width:300px"> </div>


Aconsellem proporcionar identificar inequívocament el contenidor amb un
``id=nom``, per facilitar la inicialització del widget. Si no es proporciona un
identificador directament al contenidor, s'ha de poder construir un selector
apropiat que retorni únicament el contenidor, per exemple:

.. code-block:: html

    <div id="principal">
      <div class="columna primera">
       XXXX
      </div>
      <div class="columna segona"></div>
    </div>


Suposant que l'exemple és codi html ja existent, que volem aprofitar i no
podem/volem inserir nous elements html, podríem referenciar el contenidor de
manera única amb el selector css ``#principal .columna.segona``

Loader
+++++++

El *loader* és el següent codi javascript encarregat de instanciar de manera
asíncrona el widget en la nostra aplicació:

.. code-block:: js

    // 1 - Inicialitzar variable global
    window._MAXUI = window._MAXUI || {}

    // 2 -  Inicialitzar widget, quan estigui disponible
    window._MAXUI.onReady = function() {
        var settings = {  }

        intervalID = setInterval(function(event) {
            if ($().maxUI) {
                clearInterval(intervalID)
                $('#activityStream').maxUI(settings)
            }
        }, 30)
    }


    // 3 - Descarregar codi del widget
    (function(d){
        var mui_location = 'http://rocalcom.upc.edu/maxui/maxui.js'
        var mui = d.createElement('script'); mui.type = 'text/javascript'; mui.async = true;
        mui.src = mui_location
        var s = d.getElementsByTagName('script')[0]; s.parentNode.insertBefore(mui, s);
    }(document))

i consta de 3 porcions de codi que s'han d'incorporar a la resta de javascript
de la nostra pàgina. Passem a descriure les diferents parts:

1. **Inicialitzar variable global**

El widget utilitza aquest variable, de tipus ``Object`` de javascript, on es
poden emmagatzemar dades en format *clau-valor*. Aquesta variable és accessible
com a global, a través de ``_MAXUI`` o ``window._MAXUI`` indistintament, i
proporciona un lloc on emmagatzemar altres variables globals o configuracions,
sense risc d'entrar en conflicte de noms amb altres variables existents. Aquesta
primera part s'assegura de crear la variable si no existeix i donar-li un valor
per defecte

2. **Inicialitzar widget**

Aquí definim una funció ``onReady``, que el propi widget s'encarrega d'executar
un cop s'ha completat la descàrrega en el següent pas. Dins d'aquesta funció és
on definirem sobre quin *contenidor* hem d'inicialitzar el widget
(``#activityStream`` a l'exemple), i li passarem els paràmetres de configuració
oportuns.

3. **Descarregar codi del widget**

Per últim, injectem en el codi de la pàgina l'ordre per descarregar de manera
asíncrona el codi del maxui. La ubicació d'aquest codi pot ser remota com a
l'exemple, que el descarrega de ``http://rocalcom.upc.edu/maxui/maxui.js``, o bé
el podeu ubicar als vostres servidors. **ULL!** Si l'ubiqueu als vostres
servidors, les imatges que utilitza el widget les continuara agafant del
servidor del qual heu descarregat el maxui.js. En cas que volguéssiu hostatjar
les imatges, haureu de substituir manualment la url al maxui.js.

.. note::

    **IMPORTANT** S'ha de respectar l'ordre de les 3 parts quan incorporem el
    codi als fitxers javascripts de la pagina.

CSS
---

Cal incorporar els css dels qual depèn el widget a cadascuna de les pàgines on
se'l vulgui renderitzar. Per fer-ho, inclourem el següent codi al ``<head>`` de
la pàgina:

.. code-block:: html

    <link rel="stylesheet" type="text/css" href="http://rocalcom.upc.edu/maxui/maxui.css">

o bé, tal com hem explicat anteriorment amb el ``maxui.js``,  el podem hostatjar
localment en els nostres servidors, i de mateixa manera, haurem de tenir en
compte la reescriptura de les urls de les imatges que hi ha al css.

Configuració del widget
-----------------------

Per configurar el widget, prepararem una variable javascript, on especificarem
els paràmetres amb els quals volem inicialitzar el widget. Aquí tenim una
mostra, a tall d'exemple per veure una representació dels diversos valors que
pot prendre, en mode timeline:

.. code-block:: js

    var settings = {
           'language': 'ca',
           'username' : 'nom.cognom',
           'oAuthToken' : '01234567890abcdef01234567890abcd',
           'oAuthGrantType' : 'password',
           'maxServerURL' : 'https://rocalcom.upc.edu',
           'activitySource': 'timeline'
           }

i un altra exemple en mode context:

.. code-block:: js

    var settings = {
           'language': 'ca',
           'username' : 'nom.cognom',
           'oAuthToken' : '01234567890abcdef01234567890abcd',
           'oAuthGrantType' : 'password',
           'maxServerURL' : 'https://rocalcom.upc.edu',
           'readContext': 'http://foo.com/bar',
           'writeContexts': ['http://foo.com/bar/cel', 'http://foo.com/bar/cel/ona]''
           'activitySource': 'activities'
           }


A continuació detallarem els diferents paràmetres que es poden utilitzar, quins
són obligatoris, i el tipus de valor que s'espera en cada un d'ells:

Paràmetres referents al MAX

* ``username`` (obligatori) - Nom d'usuari del MAX (El mateix que el LDAP
  *nom.cognom*)
* ``oauthToken`` (obligatori) - token oAuth de l'usuari del MAX
* ``maxServerURL`` (obligatori) - URL absoluta del servidor max a utilitzar
* ``maxTalkURL`` (obligatori) - Si desde el servei MAX no s'indica el contrari,
  és el mateix que ``maxServerURL`` acavat amb ``/max``
* ``readContext`` (obligatori) - URI del context del qual volem mostrar-ne les
  activitats.
* ``writeContexts`` - ``default: []`` - Llista d'URIS de contextos alternatius
  on es publicaran les activitats. El context especificat a * ``readContext``,
  formara sempre part automàticament d'aquesta llista.
* ``activitySource`` (obligatori)-  Font de l'activitat. Pot ser ``timeline`` o
  ``activities``.
* ``activitySortOrder`` - ``default: activities`` - Ordre que s'aplicarà a les activitats
  tant en mode timeline com en mode activities. Si és ``activities`` la ultima activitat
  generada sortirà la primera. SI és ``comments`` la ultima activitat on s'hagi fet
  un comentari sortirà la primera.
* ``generatorName`` (obligatori) - Nom que s'adjuntarà a les activitats
  generades des del widget, representant l'orígen de les activitats. Típicament
  serà el nom de l'aplicació on s'ha instal·lat el widget.

Paràmetres de la UI

* ``UISection`` - ``default: timeline`` - Secció a mostrar al inicialitzar el
  widget. Hi han dues opcions ``timeline`` per mostrar el fil d'activitat, i
  ``conversations`` per mostrar les converses privades.
* ``avatarURLpattern`` - Si no està especificat, el widget intentarà obtenir les
  imatges dels usuaris del propi max. Si l'aplicació vol utilitzar les seves
  propies imatges, pot proporcionar una url on es pugui proporcionar un
  paràmetre ``{1}`` amb el nom d'usuari, i que retorni la imatge de l'usuari o
  una imatge genèrica si no existeix l'usuari, d'una forma similar a algun
  d'aquests exemples::

    http://laMevaAplicacio.com/fotos/{1}
    http://laMevaAplicacio.com/fotos?usuari={1}

* ``disableTimeline`` - ``default: false`` - Posar-ho a ``true`` per
  deshabilitar el fil d'activitat
* ``disableConversations`` - ``default: false`` - Posar-ho a ``true`` per
  deshabilitar les converses
* ``language`` - ``default: en`` - Idioma de la interfície, disposa dels
  literals traduïts en Català (ca), Anglès (en) i  Castellà(es).
* ``literals`` - Objecte javascript per definir literals personalitzats per
  l'aplicació. Hi ha dos casos d'ús:

    - Literals per un idioma que no *existeix per defecte*: S'han d'especificar
      **tots**
    - Literals per un idioma que *ja existeix*: S'han d'especificar només els
      que es volen sobreescriure. Els literals disponibles són:

    .. code-block:: js

        {'new_activity_text': 'Escriu alguna cosa...',
         'activity': 'activitat',
         'conversations': 'converses',
         'conversations_list': 'llista de converses',
         'new_conversation_text': 'Cita a @algú per iniciar una conversa',
         'new_activity_post': "Publica",
         'toggle_comments': "comentaris",
         'new_comment_text': "Comenta alguna cosa...",
         'new_comment_post': "Comenta",
         'load_more': "Carrega'n més",
         'context_published_in': "Publicat a",
         'generator_via': "via",
         'search_text': "Busca...",
         'and_more': "i més...",
         'new_message_post':'Envia el missatge',
         'post_permission_unauthorized': 'No estàs autoritzat a publicar en aquest contexte',
         'post_permission_not_here': "No estas citant a @ningú"
        }

Altres Paràmetres

* ``maxRequestsAPI`` - ``default: jquery`` - Api a utilitzar per les peticions
  al servidor MAX. Actualment només suporta jquery en aquesta versió.
* ``enableAlerts`` - ``default: false`` - Booleà per activar finestres emergents
  d'alerta quan succeeixi algun error. Útil per a depurar errors.


La lectura/escriptura de les activitats d'un contexte, venen donades pels
permisos de subscripcio atorgats en el moment de subscriure l'usuari, i dels
permisos per defecte del context.

Autenticació
------------

La autenticació del widget es fa mitjançant un token oauth que s'ha de demanar
al servidor https://oauth.upc.edu. Per demanar aquest token s'ha de fer la
petició corresponent al servidor, i injectar el token juntament amb el nom
d'usuari als paràmetres de configuració explicats anteriorment.

Com que es necessita tenir accés a les credencials de l'usuari per sol·licitar
el token oauth, actualment el mètode vigent, implica que l'aplicació ha de
implementar en el seu procés de login les següent accions en el moment que
disposa del password de l'usuari:

* Demanar el token oAuth i emmagatzemar-lo en les bases de dades pròpies de
  l'aplicació, amb l'objectiu de només demanar-lo la primera vegada que un
  usuari es connecta a l'aplicació.
* Crear l'usuari al max, i subscriure'l als contextes oportuns si s'escau.


CORS - Cross Origin Resource Sharing
-------------------------------------

Les crides al MAX que es fan des del widget es van via peticions XHR des del
navegador. Degut a restriccions de seguretat, per defecte els navegadors no
permeten que una crida XHR interactuï amb dominis diferents del qual s'ha
accedit. Per exemple, si hem carregat l'aplicació a ``http://www.foo.com``, no
podrem fer crides XHR a ``http://www.bar.com``.

Per superar aquest obstacle, s'ha implementat l'estàndar CORS que permet fer
aquestes accions, però no tots els navegadors ho suporten. De moment el sistema
de reserva per tal d'assegurar el funcionament del widget en navegadors antics,
necessita de dues coses:

* Definir una url continguda en el servidor de l'aplicació que fagi proxy de les
  peticions cap a la url del servidor MAX: Per exemple::

  - Aplicació a http://www.foo.bar
  - Servidor  MAX http://www.max.com
  - http://www.foo.bar/max --> http://www.max.com

* Configurar el widget perquè utilitzi el redireccionament en casos que el
  navegador no suporti CORS:

.. code-block:: js

    {
     'maxServerURLAlias' : 'http://www.foo.bar/max'
    }


Depuració d'errors
------------------

A part del paràmetre ``enableAlerts`` de la configuració, per poder esbrinar la
causa de que no s'inicialitzi el widget, recomanem utilitzar les eines de
desenvolupament natives disponibles en algunes navegadors com *Google Chrome* o
plugins com *firebug* pe al *Firefox*. Bàsicament ens haurem de fixar en
possibles errors javascript que aparegui a la consola d'errors, i a peticions
XHR fallides. En aquest segon cas, ens interessara fixar-nos el el missatge
d'error en format JSON que haurà retornat la petició fallida.
