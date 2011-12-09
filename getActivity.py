import httplib2
import json
import time

# server = 'capricornius2.upc.es'
server = 'max.beta.upcnet.es'
# server = 'localhost:6543'

t0 = time.time()
req = httplib2.Http()
data = {'actor.id': 'victor'}
data_json = json.dumps(data)
resp = req.request("http://%s/activity" % server,
          "GET",
          data_json,
          headers={'Content-Type': 'application/json'})

# print resp

resultats = json.loads(resp[1])

print resultats
print "%.3f segons" % (time.time() - t0)
