import argparse
import logging
import queue
import signal
import sys
import threading

from ProDB import logger, file_logger
from ProDB.Config import Config
from ProDB.Consumer import Consumer
from ProDB.Dispatcher import Dispatcher
from ProDB.Poster import Poster
from ProDB.Singleton import Singleton

restart_event = threading.Event()
stop_event = threading.Event()


class App(metaclass=Singleton):
    _args = None
    _instance = None
    _publisher = None
    _consumer = None
    _dispatcher = None
    _poster = None

    config = None
    inputq = queue.Queue()
    outputq = queue.Queue()

    def __init__(self):
        signal.signal(signal.SIGBREAK, lambda *args: restart_event.set())
        signal.signal(signal.SIGINT, lambda *args: stop_event.set())

        parser = argparse.ArgumentParser()
        parser.add_argument('--verbose', dest='verbose', action='store_true', help='verbose mode')
        parser.add_argument('--filelog', dest='filelog', action='store_true', help='enable log to files')
        parser.add_argument('--config', dest='config', default='prodb_mod_server.cfg', help='configuration file')
        args = parser.parse_args()

        if args.filelog:
            file_logger.enable()

        logger.info('Command line is {}'.format(' '.join(sys.argv)))

        if args.verbose:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
            # suppress traces
            logger.exception = logger.error

        logger.info('Press Ctrl+C to stop, Ctrl+Break to reload')

        self._args = args

    def mainloop(self):
        self.start()
        while not stop_event.wait(0.1):
            self.check_restart()
        self.stop()
        restart_event.wait(0.1)  # wait other threads
        logger.info('Normal exit')

    def start(self):
        self.config = Config(self._args.config)
        self._consumer = Consumer()
        self._consumer.start()
        self._dispatcher = Dispatcher()
        self._dispatcher.start()
        self._poster = Poster()
        self._poster.start()

    def stop(self):
        self._consumer.stop()
        self._consumer = None
        self.inputq.put(None)
        self.outputq.put(None)
        self._dispatcher.stop()
        self._dispatcher = None
        self._poster.stop()
        self._poster = None

    def check_restart(self):
        if restart_event.isSet():
            logger.info('Restarting workers')
            self.stop()
            self.start()
            restart_event.clear()
