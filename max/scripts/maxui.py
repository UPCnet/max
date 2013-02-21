import sys
import json
from devel import load_settings


BASE_PRESET = 'src/max.ui.js/presets/base.json'


def main(argv=sys.argv):
    client, settings, path = load_settings()
    base = json.loads(open('%s/%s' % (path, BASE_PRESET)).read())
    base['username'] = settings['username']
    base['oAuthToken'] = settings['token']
    base['maxServerURL'] = settings['maxserver']
    base['maxServerURLAlias'] = settings['maxserver']
    base['maxTalkURL'] = settings['maxserver'] + '/max'
    base['avatarURLpattern'] = settings['maxserver'] + '/people/{0}/avatar'
    open('%s/%s' % (path, BASE_PRESET), 'w').write(json.dumps(base, indent=4, sort_keys=True))
