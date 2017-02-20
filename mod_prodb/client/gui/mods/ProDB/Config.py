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
    filepath = os.path.join(os.getcwd(), 'res_mods', 'ObsMod', 'server.json')
    is_caster = os.path.exists(os.path.join(os.getcwd(), 'res_mods', 'caster'))

    config = {
        'server_user': 'wot_observer_user',
        'server_pass': 'WoT123',
        'server_ip': '92.255.125.251',
        'server_port': '5672',
        'exchange_name': 'wot_observer_exchange',
        'is_caster': is_caster
    }

    try:
        config_keys = config.keys()
        with open(filepath, 'rt') as infile:
            loaded_config = json.load(infile)
            config = {key: loaded_config.get(key, config[key]) for key in config_keys}
            Log.LOG_DEBUG('Loaded config: %s' % filepath)
    except Exception as ex:
        Log.LOG_ERROR("'%s' exception: " % filepath, ex)

    return collections.namedtuple('Config', 'server_user,server_pass,server_ip,server_port,exchange_name,is_caster')(**config)
