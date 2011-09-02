Introducció ràpida
==================

El sistema utilitza com enmagatzamatge una base de dades orientada a objectes (MongoDB) i conté una interfície REST per accedir a ella. Aquests són els web services que té:

.. http:post:: /activity
    
    http://macs.beta.upcnet.es/activity (via POST)

    Permet la creació de un objecte nou en la BBDD amb el format activitystrea.ms (http://activitystrea.ms/specs/json/1.0/).
    De fet, a hores d'ara permet la creació de qualsevol objecte JSON (en un futur hauria de permetre només objectes que complissin la especificació activitystrea.ms).

En el request que se li faci al web service, se li ha d'especificar el content-type ('application/json') i el contingut ha de ser JSON vàlid.

A mode d'exemple, aquí teniu aquest script Python que realitza una prova de càrrega al servidor (fa un insert de 1000 objectes)::

    import httplib2
    import json
    import time
    import datetime

    server = 'macs.beta.upcnet.es'
    # server = 'capricornius2.upc.es'
    # server = 'localhost:6543'

    t0 = time.time()
    h = httplib2.Http()
    for i in range(1000):
        data={"published": i,"actor": {"url": "http://example.org/martin","objectType" : "person","id": "victor","image": {"url": "http://example.org/martin/image","width": 250,"height": 250}, "displayName": "Victor Fernandez de Alba"},"verb": "post","object" : {"url": "http://example.org/blog/2011/02/entry","id": "tag:example.org,2011:abc123/xyz"},"target" : {"url": "http://example.org/blog/","objectType": "blog","id": "tag:example.org,2011:abc123","displayName": "Martin's Blog"}}
        data_json = json.dumps(data)
        h.request("http://%s/activity" % server,
                  "POST",
                  data_json,
                  headers={'Content-Type': 'application/json'})
    print "%.3f segons" % (time.time()-t0)

.. http:get:: /user_activity

    http://macs.beta.upcnet.es/user_activity (via GET)

    Pren un objecte JSON amb el contingut de la consulta a realitzar i retorna un objecte JSON, amb tots els resultats de la query especificada en el request.

Per ara la query només funciona amb una cerca per autor de l'activitat, aquest és un script que mostra com funciona::

    import httplib2
    import json
    import time

    server = 'macs.beta.upcnet.es'
    # server = 'capricornius2.upc.es'
    # server = 'localhost:6543'

    t0 = time.time()
    req = httplib2.Http()
    data = {'actor.id': 'victor'}
    data_json = json.dumps(data)
    resp = req.request("http://%s/user_activity" % server,
              "GET",
              data_json,
              headers={'Content-Type': 'application/json'})

    resultats = json.loads(resp[1])

    print resultats
    print "%.3f segons" % (time.time() - t0)
