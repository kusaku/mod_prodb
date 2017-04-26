import collections
import json

from .Logger import Logger


def Config(args):
    config = {
        'rmq_username': 'wot_observer_user',
        'rmq_password': 'WoT123',
        'rmq_ip': '92.223.123.132',
        'rmq_port': 5672,
        'rmq_exchange': 'wot_observer_exchange',
        'rmq_session_dump': None,
        'cache_clear_timeout': 60.0,
        'battle_finish_timeout': 20.0,
        'battle_poll_timeout': 10.0,
        'pro_db_url': 'https://prodb.tet.io/api/',
        'pro_db_platform': 'a5480e62-61e4-4091-83ca-2ab364f1d645',
        'pro_db_user': 'wot-stats',
        'pro_db_secret': '38o5diufjfqct6gm2chg1hnmncociqf0leg8qq8',
        'max_poster_workers': 4,
        'max_poller_workers': 4,
        'mockpoll': bool(args.mockpoll),
        'mockpost': bool(args.mockpost),
        'mockrmq': args.mockrmq,
    }

    config_keys = config.keys()

    filepath = str(args.config)

    try:
        with open(filepath, 'rt') as fh:
            loaded_config = json.load(fh)
            config = {key: loaded_config.get(key, config[key]) for key in config_keys}
    except Exception as ex:
        Logger.error('Config file \'{}\' not loaded: {}, using defaults'.format(filepath, ex))
    else:
        Logger.debug('Loaded config file \'{}\''.format(filepath))

    Logger.debug('Config:\n{}\n{}\n{}'.format('*' * 80, json.dumps(config, indent=4, sort_keys=True), '*' * 80))

    return collections.namedtuple('Config', sorted(config_keys))(**config)
