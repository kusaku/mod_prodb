import collections
import json

from ProDB import logger


def Config(args):
    config = {
        'rmq_username': 'wot_observer_user',
        'rmq_password': 'WoT123',
        'rmq_ip': '92.223.123.132',
        'rmq_port': 5672,
        'rmq_exchange': 'wot_observer_exchange',
        'rmq_session_dump': None,
        'mockpoll': bool(args.mockpoll),
        'mockpost': bool(args.mockpost),
    }

    config_keys = config.keys()

    filepath = str(args.config)

    try:
        with open(filepath, 'rt') as infile:
            loaded_config = json.load(infile)
            config = {key: loaded_config.get(key, config[key]) for key in config_keys}
    except Exception as ex:
        logger.error('Config file \'{}\' not loaded: {}, using defaults'.format(filepath, ex))
    else:
        logger.debug('Loaded config file \'{}\''.format(filepath))

    logger.debug('Config:\n{}\n{}\n{}'.format('*' * 80, json.dumps(config, indent=4, sort_keys=True), '*' * 80))

    return collections.namedtuple('Config', sorted(config_keys))(**config)
