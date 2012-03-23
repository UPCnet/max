Configuració
============

Python
------

Cal definir la codificació del Python que estem utilitzant per defecte::

    $ vi /var/pyramid/python2.7/lib/python2.7/sitecustomize.py

Afegir a aquest arxiu::

    import sys
    sys.setdefaultencoding('utf-8')

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
