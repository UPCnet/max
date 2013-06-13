BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "maxrabbit"
BROKER_PASSWORD = "operations"
BROKER_VHOST = "localhost"

CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = ("maxrules.tasks", "max.models")

# MongoDB config
mongodb_url = "mongodb://localhost"
mongodb_db_name = "max"

# Cluster config
mongodb_cluster = False
mongodb_hosts = "faiada.upcnet.es:27017,fajolpetit.upcnet.es:27017,finestrelles.upcnet.es:27017"
mongodb_replica_set = "maxcluster"
