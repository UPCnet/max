import os
import sys
import re
import bigmax
import json
import getpass
from maxclient import MaxClient

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )


USAGE = """

usage: %s add|list user|context|subscription

"""


def usage(argv):
    cmd = os.path.basename(argv[0])
    print(USAGE % (cmd))
    sys.exit(1)


def login():
    username = raw_input("Max Username: ")
    password = getpass.getpass()
    return username, password


def doAction(client, action, target, *args):
    if action not in ['add', 'get']:
        print "Unknwon action '%s'" % action
        sys.exit(1)
    if target not in ['user', 'context', 'subscription']:
        print "Unknwon target '%s'" % target
        sys.exit(1)

    action_function = globals().get('_%s_%s' % (action, target))
    if not action_function:
        print 'Not implemented'
        sys.exit()

    action_function(client, *args)


def _add_subscription(client, *args):
    if len(args) == 0:
        username = raw_input('User to subscribe: ')
    if len(args) < 2:
        url = raw_input('Context url: ')
    if len(args) > 0:
        username = args[0]
    if len(args) > 1:
        url = args[1]

    if username and url:
        req = client.subscribe(url, username=username)
        if isinstance(req, dict):
            print 'Done'
        else:
            print 'Oops! An error occurred...'


def _add_user(client, *args):
    if len(args) == 0:
        username = raw_input('New User username: ')
    else:
        username = args[0]
    if username:
        req = client.addUser(username)
        if req[0] not in [200, 201]:
            print 'Oops! An error occurred...'
        else:
            print 'Done.'


def _add_context(client, *args):
    if len(args) == 0:
        url = raw_input('Context URL: ')
    if len(args) < 2:
        displayName = raw_input('Display Name: ')
    if len(args) > 0:
        url = args[0]
    if len(args) > 1:
        displayName = args[1]

    if url and displayName:
        req = client.addContext(url, displayName)
        if isinstance(req, dict):
            print 'Done'
        else:
            print 'Oops! An error occurred...'


def load_settings():
    save_settings = False
    buildout_path = re.search(r'^(.*?)/src.*', bigmax.__path__[0]).groups()[0]
    settings_file = '%s/.max_settings' % buildout_path

    if os.path.exists(settings_file):
        settings = json.loads(open(settings_file).read())
    else:
        settings = {}

    if 'maxserver' not in settings:
        url = raw_input("MAX server URL: ")
        settings['maxserver'] = url
        save_settings = True

    client = MaxClient(settings['maxserver'])

    if 'token' not in settings or 'username' not in settings:
        username, password = login()
        settings['username'] = username
        settings['token'] = client.getToken(username, password)
        save_settings = True

    client.setToken(settings['token'])
    client.setActor(settings['username'])

    if save_settings:
        open(settings_file, 'w').write(json.dumps(settings, indent=4, sort_keys=True))
    return client, settings, buildout_path


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)

    client, settings, path = load_settings()
    doAction(client, argv[1], argv[2], *argv[3:])
