from maxclient import MaxClient
import threading
import json
import time
import datetime
from random import choice, randint

# server = 'capricornius2.upc.es'
# server = 'max.beta.upcnet.es'
server = 'http://147.83.193.90'

max = MaxClient(server)

# Afegim 30000 usuaris
numUsuaris = 3000
numActivitat = 10000
ALLOWED_CHARACTERS = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ0123456789'
MESSAGE_LENGTH = 140


class creaUsuaris(threading.Thread):
    def __init__(self, numUsuaris):
        self.numUsuaris = numUsuaris
        threading.Thread.__init__(self)

    def run(self):
        for usuari in range(self.numUsuaris):
            print "Creant usuari %s" % str(usuari)
            max.addUser('usuari' + str(usuari))


class creaActivitat(threading.Thread):
    def __init__(self, numUsuaris, numActivitat):
        self.numActivitat = numActivitat
        self.numUsuaris = numUsuaris
        self.allowed_chars = ALLOWED_CHARACTERS
        self.length = MESSAGE_LENGTH
        threading.Thread.__init__(self)

    def run(self):
        for i in range(self.numActivitat):
            usuariName = 'usuari' + str(randint(0, self.numUsuaris))
            max.setActor(usuariName)
            max.addActivity(''.join([choice(self.allowed_chars) for i in range(self.length)]))
            print "Creant activitat %s" % usuariName

t0 = time.time()
thread1 = creaUsuaris(numUsuaris)
thread1.start()
while thread1.isAlive():
    pass
print "%.3f segons: Fi de creacio usuaris" % (time.time() - t0)

t0 = time.time()
thread2 = creaActivitat(numUsuaris, numActivitat)
thread2.start()
while thread2.isAlive():
    pass
print "%.3f segons: Fi de creacio activitat" % (time.time() - t0)
