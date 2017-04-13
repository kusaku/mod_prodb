import logging
import os
import sys
from logging import handlers as handlers

import colorlog

stream_handler = logging.StreamHandler(stream=sys.stderr)
stream_handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s %(thread)-5d %(threadName)-12s %(message_log_color)s%(message)s',
    datefmt='%H:%M:%S',
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={
        'message': {
            'DEBUG': 'bold_cyan',
            'INFO': 'bold_green',
            'WARNING': 'bold_yellow',
            'ERROR': 'bold_red',
            'CRITICAL': 'red,bg_white',
        }
    }
))

Logger = logging.getLogger(__name__)
Logger.addHandler(stream_handler)


class FileLogger(object):
    debug = lambda *args, **kwargs: None
    info = lambda *args, **kwargs: None
    warning = lambda *args, **kwargs: None
    error = lambda *args, **kwargs: None
    exception = lambda *args, **kwargs: None
    critical = lambda *args, **kwargs: None
    warn = warning

    file_logger = None

    @classmethod
    def enable(cls, level=logging.DEBUG):
        try:
            os.makedirs('logs')
        except:
            pass
        finally:
            file_path = os.path.join('logs', 'prodb_mod_server.log')
            if os.path.exists(file_path):
                for i in range(99, 0, -1):
                    sfn = '%s.%d' % (file_path, i)
                    dfn = '%s.%d' % (file_path, i + 1)
                    if os.path.exists(sfn):
                        if os.path.exists(dfn):
                            os.remove(dfn)
                        os.rename(sfn, dfn)
                os.rename(file_path, file_path + '.1')

        file_handler = handlers.RotatingFileHandler(file_path)

        file_handler.setFormatter(
            logging.Formatter('%(asctime)s %(thread)-5d %(threadName)-12s %(name)-33s [%(levelname)-5s] %(message)s'))

        cls.file_logger = logging.getLogger()
        cls.file_logger.addHandler(file_handler)
        cls.file_logger.setLevel(level)
        cls.debug = cls.file_logger.debug
        cls.info = cls.file_logger.info
        cls.warning = cls.file_logger.warning
        cls.error = cls.file_logger.error
        cls.exception = cls.file_logger.exception
        cls.critical = cls.file_logger.critical
