BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "maxrabbit"
BROKER_PASSWORD = "operations"
BROKER_VHOST = "sneridagh"

CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = ("maxrules.tasks",)
