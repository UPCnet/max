Arquitectura
============

Aquest document explica la proposta d’arquitectura del servei MAX (Motor d’activitat i subscripcions) que s’engloba dins del projecte som.UPC. El servei es composa de diferents capes que comprenen des del servidor web públic fins a la capa de persistència. A continuació passem a descriure cadascun d’ells i les seves funcions.

Nginx
-----

Farem servir Nginx com a servidor web públic del servei. Per servir peticions aquest servidor utilitza l’aproximació asíncrona basada en events que proporciona un gran rendiment sota grans càrregues en contrast als servidors basats en fils de procés (threads) com Apache.

Serà la primera porta d’entrada al servei i proporcionarà robustesa a part de la capacitat d’absorbir grans quantitats de tràfic entrant.

.. image:: _static/DiagramaMAXServer.png

Gunicorn
--------

És el servidor d’aplicacions Python compatibles amb WSGI i el motor de la nostra aplicació. Està basat en un model semblant a l’utilitzat a Nginx, centrant-se amb donar un alt rendiment i ser molt lleuger.

Pyramid
-------

El codi base del MAX està implementat amb el framework de desenvolupament Pyramid que està basat en Python. Aquest framework també te fama de ser molt lleuger (no supera les 5000 línies de codi) i optimitzat per tenir un alt rendiment i traça de memòria molt petita.

MongoDB
-------

La capa de persistència està implementada amb una base de dades NoSQL anomenada MongoDB. Està optimitzada per a tindre un alt rendiment, no està lligada a la especificació prèvia d’un esquema i està orientada al document. Aquest documents que guarda són documents JSON. A més, aquesta base de dades permet la implementació molt senzilla d’alta disponibilitat i tolerància a fallides, així com balanceig de càrrega entre diferents nodes.

Celery
------

XXX

RabbitMQ
--------

XX

Escalabilitat horitzontal
-------------------------

L’arquitectura proposada i gràcies a les funcionalitats de clusterització de la MongoDB és extremadament escalable. A més, permet l’encapsulament d’aquesta en màquines virtuals molt petites i en cas de necessitat del servei, es poden aprovisionar tantes com es vulguin per poder dotar al servei de més potència de càrrega i augmentar el seu rendiment.
