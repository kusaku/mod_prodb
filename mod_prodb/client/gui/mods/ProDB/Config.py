import collections
import json
import os

from . import Log


def convert_to_utf8(data):
    if isinstance(data, dict):
        return {convert_to_utf8(key): convert_to_utf8(value) for key, value in data.iteritems()}
    if isinstance(data, (tuple, list)):
        return [convert_to_utf8(value) for value in data]
    if isinstance(data, unicode):
        return data.encode('utf8')
    return data


def Config():
    filepath = os.path.join(os.getcwd(), 'res_mods', 'server.json')

    config = {
        'username': 'wot_observer_user',
        'password': 'WoT123',
        'host': '92.255.125.251',
        'port': 5672,
        'exchange': 'wot_ventuz_exchange'
    }

    try:
        with open(filepath, 'rt') as infile:
            config = convert_to_utf8(json.load(infile))
            Log.LOG_DEBUG('Loaded config: %s\n%s' % (filepath, repr(config)))
    except Exception as ex:
        Log.LOG_ERROR("'%s' exception: " % filepath, ex)

    return collections.namedtuple('Config', ('username', 'password', 'host', 'port', 'exchange'))(**config)
