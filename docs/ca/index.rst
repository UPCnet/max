.. max documentation master file, created by
   sphinx-quickstart on Tue Aug 30 13:52:33 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Benvinguts a la documentació del motor d'activitat i subscripcions (MAX)
=========================================================================

MAX és un sistema de recollida i visualització de registres d'activitat generada
per usuaris i aplicacions així com les interactuacions entre usuaris i entre
usuaris i aplicacions.

El MAX registra l'activitat de dues maneres: Activa i passiva. Quan ho fa de
manera passiva, els usuaris i aplicacions que generen activitat, usen l'API del
MAX per registrar-hi activitat. Quan ho fa de manera activa, el MAX va a buscar
l’activitat al sistema que la genera a través d'unes regles predefinides, per
exemple, l’activitat generada per un compte de Twitter i un hashtag associat.

Tant els usuaris com les aplicacions que puguin interactuar amb el MAX poden ser
d’origen en escenaris corporatius (interns) o en canvi ser totalment externs al
sistema.


Continguts
----------

.. toctree::
   :maxdepth: 2

   instalacio.rst
   configuracio.rst
   funcionalitats.rst
   arquitectura.rst
   definicions.rst
   permisos.rst
   oauth2.rst
   apirest.rst
   apioperations.rst
   maxui.rst

.. En la nevera: serialitzacions.rst
