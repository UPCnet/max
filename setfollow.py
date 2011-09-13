import httplib2
import json
import time
import datetime

# server = 'capricornius2.upc.es'
# server = 'macs.beta.upcnet.es'
server = 'localhost:6543'

follow = {
    "actor": {
        "objectType": "person",
        "id": "4e6f399aaceee9324c000000",
        "displayName": "victor"
    },
    "verb": "follow",
    "object": {
        "objectType": "person",
        "id": "4e6f4b7faceee9342c000000",
        "displayName": "javier"
    },
}

t0 = time.time()
h = httplib2.Http()
data = follow
data_json = json.dumps(data)
h.request("http://%s/follow" % server,
          "POST",
          data_json,
          headers={'Content-Type': 'application/json'})
print "%.3f segons" % (time.time()-t0)
