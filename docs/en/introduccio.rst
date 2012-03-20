Introducció ràpida
==================

El sistema utilitza com enmagatzamatge una base de dades orientada a objectes (MongoDB) i conté una interfície REST per accedir a ella. Aquests són els web services que té:

.. note::
    
    En l'apartat API REST es detalla més extensament tots els serveis web que te el sistema. Si us plau adreceu-vos a aquest apartat per més informació.

.. http:post:: /activity
    
    http://max.beta.upcnet.es/activity (via POST)

    Permet la creació de un objecte nou en la BBDD amb el format activitystrea.ms (http://activitystrea.ms/specs/json/1.0/).
    De fet, a hores d'ara permet la creació de qualsevol objecte JSON (en un futur hauria de permetre només objectes que complissin la especificació activitystrea.ms).

En el request que se li faci al web service, se li ha d'especificar el content-type ('application/json') i el contingut ha de ser JSON vàlid.

A mode d'exemple, aquí teniu aquest script Python que realitza una prova de càrrega al servidor (fa un insert de 1000 objectes)::

    import httplib2
    import json
    import time
    import datetime

    server = 'max.beta.upcnet.es'
    # server = 'capricornius2.upc.es'
    # server = 'localhost:6543'

    t0 = time.time()
    h = httplib2.Http()
    for i in range(1000):
        data = {
            "actor": {
                "objectType": "person",
                "id": "4e6e1243aceee91143000000",
                "displayName": "victor"
            },
            "verb": "post",
            "object": {
                "objectType": "note",
                "content": "Avui sera un gran dia!"
            },
        }
        data_json = json.dumps(data)
        h.request("http://%s/activity" % server,
                  "POST",
                  data_json,
                  headers={'Content-Type': 'application/json'})
    print "%.3f segons" % (time.time()-t0)

.. http:get:: /user_activity

    http://max.beta.upcnet.es/user_activity (via GET)

    Pren un objecte JSON amb el contingut de la consulta a realitzar i retorna un objecte JSON, amb tots els resultats de la query especificada en el request.

Per ara la query només funciona amb una cerca per autor de l'activitat, aquest és un script que mostra com funciona::

    import httplib2
    import json
    import time

    server = 'max.beta.upcnet.es'
    # server = 'capricornius2.upc.es'
    # server = 'localhost:6543'

    t0 = time.time()
    req = httplib2.Http()
    data = {'displayName': 'victor'}
    data_json = json.dumps(data)
    resp = req.request("http://%s/user_activity" % server,
              "GET",
              data_json,
              headers={'Content-Type': 'application/json'})

    resultats = json.loads(resp[1])

    print resultats
    print "%.3f segons" % (time.time() - t0)
