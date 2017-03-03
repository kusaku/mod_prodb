import argparse
import logging
import queue
import signal
import sys
import threading

from .Config import Config
from .Consumer import Consumer
from .Dispatcher import Dispatcher
from .Logger import FileLogger, Logger
from .Poster import Poster
from .Singleton import Singleton


class App(metaclass=Singleton):
    _args = None
    _instance = None
    _publisher = None
    _consumer = None
    _dispatcher = None
    _poster = None

    _restart_event = threading.Event()
    _stop_event = threading.Event()

    _config = None
    config = property(lambda self: self._config)

    _inputq = queue.Queue()
    _outputq = queue.Queue()

    def __init__(self):
        signal.signal(signal.SIGBREAK, lambda *args: self._restart_event.set())
        signal.signal(signal.SIGINT, lambda *args: self._stop_event.set())

        parser = argparse.ArgumentParser()
        parser.add_argument('--verbose', dest='verbose', action='store_true', help='verbose mode')
        parser.add_argument('--filelog', dest='filelog', action='store_true', help='enable log to files')
        parser.add_argument('--mockpoll', dest='mockpoll', action='store_true', help='mock ProDB service poll')
        parser.add_argument('--mockpost', dest='mockpost', action='store_true', help='mock ProDB service post')
        parser.add_argument('--config', dest='config', default='prodb_mod_server.cfg', help='configuration file')
        args = parser.parse_args()

        if args.filelog:
            FileLogger.enable()

        Logger.info('Command line is {}'.format(' '.join(sys.argv)))

        if args.verbose:
            Logger.setLevel(logging.DEBUG)
        else:
            Logger.setLevel(logging.INFO)
            # suppress traces
            Logger.exception = Logger.error

        Logger.info('Press Ctrl+C to stop, Ctrl+Break to reload')

        self._args = args

    def mainloop(self):
        self.start()
        while not self._stop_event.wait(0.1):
            self.check_restart()
        self.stop()
        self._restart_event.wait(0.1)  # wait other threads
        Logger.info('Normal exit')

    def start(self):
        self._config = Config(self._args)
        self._consumer = Consumer(self._config, self._inputq)
        self._consumer.start()
        self._dispatcher = Dispatcher(self._inputq, self._outputq)
        self._dispatcher.start()
        self._poster = Poster(self._config, self._outputq)
        self._poster.start()

    def stop(self):
        self._consumer.stop()
        self._consumer = None
        self._inputq.put(None)
        self._outputq.put(None)
        self._dispatcher.stop()
        self._dispatcher = None
        self._poster.stop()
        self._poster = None

    def check_restart(self):
        if self._restart_event.isSet():
            Logger.info('Restarting workers')
            self.stop()
            self.start()
            self._restart_event.clear()
