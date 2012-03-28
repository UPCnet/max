Instal·lació
============

En aquest apartat s’indiquen totes les passes per tal de posar en marxa una instància de tota la pila de software i serveis necessaris per al funcionament d’una instància del servei MAX.

Requisits
---------

Cal satisfer una sèrie de requisits previs que es detallen a continuació.

Sistema operatiu
----------------

Actualment, degut a limitacions tecnològiques, el entorn del projecte només pot executar-se sobre màquines \*nix. En aquests documents suposarem una màquina basada en una distribució Ubuntu Linux 11.04 (Natty). Per la instal·lació per altres distribucions cal substituïr els noms dels paquets pels corresponents a la distribució d'instal·lació.

Software base i llibreries:

    GCC i eines de compilació
    Python 2.7 (altres versions inferiors no són compatibles, mentre que superiors (>3) no han estat testades)
    Python Distribute (a.k.a setuptools)
    Git
    Erlang, xsltproc, zip (per la compilació del motor de cues)

Instal·lació de software base i llibreries
------------------------------------------

Presuposem que instal·lem el MAX i el software relacionat amb ell en la carpeta /var/pyramid::

    $ mkdir /var/pyramid
    $ cd /var/pyramid

Instal·lem els següents paquets base::

    $ sudo apt-get install wget build-essential git-core

Instal·lació de Python 2.7 (compilat), es recomana compilar-lo per partir d'una copia neta i sense llibreries de sistema innecessàries. Seguirem aquestes comandes per instal·lar-lo::

    $ sudo apt-get install libreadline5-dev libsqlite3-dev zlib1g-dev libbz2-dev
    $ wget http://python.org/ftp/python/2.7.2/Python-2.7.2.tgz
    $ tar xvfz Python-2.7.2.tgz
    $ cd Python-2.7.2
    $ ./configure --prefix=/var/pyramid/python2.7
    $ make
    $ make install

Instal·lació de Python Distribute::

    $ wget http://python-distribute.org/distribute_setup.py
    $ sudo python2.7 distribute_setup.py

Instal·lació de Erlang i llibreries::

    $ sudo apt-get install erlang xsltproc zip

Instal·lació de llibreries accés LDAP
-------------------------------------

És necessari les últimes llibreries de OpenLDAP de les distribucions corresponents, en cas d'Ubuntu::

    $ apt-get install libsasl2-dev libldap2-dev libssl-dev

Instal·lació de MAX
--------------------

El MAX utilitza un sistema de montatge (descàrrega, compilació i configuració) automàtic anomenat zc.buildout.

Aquest sistema utilitza un fitxer (buildout.cfg) de configuració que conté tota la informació necessària per a construir un entorn de MAX complet i configurat.

Per començar ens baixarem de Github el codi executant la següent ordre::

    $ git clone git://github.com/UPCnet/maxserver.git

Fet això, ens ha d’haver creat un nou directori maxserver. Accedim a ell::

    $ cd maxserver

Executem el muntatge amb aquestes ordres::

    $ /var/pyramid/python2.7/bin/python bootstrap.py
    $ ./bin/buildout

Esperem fins a que finalitzi. Un cop finalitzat, tindrem tots els serveis llestos per ser arrencats.
