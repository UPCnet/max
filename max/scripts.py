import os
import sys
import pymongo

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

default_security = {'roles': {"Manager": ["victor.fernandez",
                                           "carles.bruguera",
                                           "usuari.atenea",
                                           "usuari.somupc"
                                           ]
                               }
                    }


def init_security(settings):
    db_uri = settings['mongodb.url']
    conn = pymongo.Connection(db_uri)
    db = conn[settings['mongodb.db_name']]
    if not [items for items in db.security.find({})]:
        db.security.insert(default_security)
        print("Created default security info in MAXDB.")


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    init_security(settings)
