#!/var/plone/python2.6/bin/python

import os
os.system('cd en && make html LANG=en')
os.system('cd ca && make html LANG=ca')
