Configuració
============

Python
------

Cal definir la codificació del Python que estem utilitzant per defecte::

    $ vi /var/pyramid/python2.7/lib/python2.7/sitecustomize.py

Afegir a aquest arxiu::

    import sys
    sys.setdefaultencoding('utf-8')

Gunicorn
--------

Cal crear l'usuari **pyramid** al sistema, que serà l'usuari amb el que s'executi els processos de Gunicorn::

    $ adduser pyramid

RabbitMQ
--------

El servidor de cues s'ha de configurar creant un usuari amb el que farem les operacions, creant un vhost per les nostres cues i assignant-li els permissos necessaris a l'usuari sota el context d'aquest vhost::

    $ ./bin/rabbitmq-server -detached
    $ ./bin/rabbitmqctl add_user  ``username`` ``password``
    $ ./bin/rabbitmqctl add_vhost ``nom_maquina``
    $ ./bin/rabbitmqctl set_permissions -p ``nom_maquina`` ``username`` ".*" ".*" ".*"

Celery
------

El procés que s'ocupa de llençar els workers de les tasques de les cues (``celeryd``), es configura a través d'un módul de Python que es troba directament en el directori src/max/maxrules::

    BROKER_HOST = "localhost"
    BROKER_PORT = 5672
    BROKER_USER = ""
    BROKER_PASSWORD = ""
    BROKER_VHOST = ""

    CELERY_RESULT_BACKEND = "amqp"
    CELERY_IMPORTS = ("maxrules.tasks",)

    # MongoDB config
    mongodb_url = "mongodb://localhost"
    mongodb_db_name = "max"

També conté la configuració de la base de dades MongoDB ja que els workers han de poder accedir-hi.

Ajustos de sistema
------------------

Per tal d'optimitzar el sistema cal ajustar alguns paràmetres de funcionament.

Pujar el número de file descriptors (FDs)::

    $ vi /etc/security/limits.conf

i posar la següent configuració::

    # /etc/security/limits.conf
    #
    root soft nofile 10000
    root hard nofile 10000

    # Nginx
    www-data soft nofile 10000
    www-data hard nofile 10000

    # Gunicorn/Pyramid
    pyramid soft nofile 10000
    pyramid hard nofile 10000

La base de dades ha d'estar en una partició ext4.

(http://www.mongodb.org/display/DOCS/Production+Notes)

General Unix Notes

    Turn off atime for the data volume
    Set file descriptor limit and user process limit to 4k+ (see etc/limits and ulimit)
    Do not use large VM pages with Linux (more info)
    Use dmesg to see if box is behaving strangely
    Try to disable NUMA in your BIOS. If that is not possible see NUMA
    Minimize clock skew between your hosts by using ntp; linux distros usually include this by default, but check and install the ntpd package if it isn't already installed
