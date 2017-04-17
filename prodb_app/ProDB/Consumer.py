import json
import threading
import time
from collections import namedtuple
from datetime import datetime

import pika

from .Logger import Logger


class Consumer(object):
    msg_packet = namedtuple('msg_packet', 'aid,vid,cid,stime,type,data')

    @property
    def inputq(self):
        from ProDB.App import App
        return App().inputq

    @property
    def config(self):
        from ProDB.App import App
        return App().config

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self._connection = None
        self._counter = 0

    def callback(self, ch, method, properties, body):
        try:
            msg = self.msg_packet(**json.loads(body.decode('utf-8')))

            if self.config.rmq_session_dump is not None:
                with open(self.config.rmq_session_dump, 'a') as fh:
                    json.dump(msg._asdict(), fh, sort_keys=True)
                    fh.write('\n')

            # Logger.exception(json.dumps(msg, indent=4))
            self.inputq.put(msg)
        except Exception as ex:
            Logger.exception('Exception: {}'.format(type(ex).__name__))
            pass

    def consume(self):
        while not self._stop_event.isSet():
            try:
                Logger.debug('Connecting to {}:{}@{}:{}/{}'.format(
                    self.config.rmq_username,
                    '*' * len(self.config.rmq_password),
                    self.config.rmq_ip,
                    self.config.rmq_port,
                    self.config.rmq_exchange
                ))

                credentials = pika.PlainCredentials(self.config.rmq_username, self.config.rmq_password)

                self._connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.config.rmq_ip, port=self.config.rmq_port,
                                              credentials=credentials)
                )

                channel = self._connection.channel()
                channel.exchange_declare(exchange=self.config.rmq_exchange, type='fanout')

                queue_name = channel.queue_declare(exclusive=True).method.queue

                channel.queue_bind(exchange=self.config.rmq_exchange, queue=queue_name)
                channel.basic_consume(self.callback, queue=queue_name, no_ack=True)

                Logger.debug('Connected')

                while not self._stop_event.isSet():
                    self._connection.process_data_events(time_limit=0.01)

            except Exception as ex:
                Logger.exception('Exception: {}'.format(type(ex).__name__))

            finally:
                try:
                    if self._connection and self._connection.is_open:
                        Logger.debug('Closing connection')
                        self._connection.close()
                        self._connection = None
                except Exception as ex:
                    Logger.exception('Exception: {}'.format(type(ex).__name__))

    def mock(self):
        with open(self.config.mockrmq, 'rt') as fh:
            for line in fh:
                if len(line.strip()) == 0 or line.startswith('#'):
                    continue
                try:
                    msg = self.msg_packet(**json.loads(line))
                    # Logger.exception(json.dumps(msg, indent=4))
                    self.inputq.put(msg)
                    time.sleep(0.01)
                except Exception as ex:
                    Logger.exception('Exception: {}'.format(type(ex).__name__))

    def thread(self):
        Logger.debug('Started')
        if self.config.mockrmq is not None:
            Logger.debug('[mock] Reading mock file {}'.format(self.config.mockrmq))
            self.mock()
        else:
            self.consume()
        Logger.debug('Finished')

    def start(self):
        if self.config.rmq_session_dump:
            with open(self.config.rmq_session_dump, 'a') as fh:
                fh.write(datetime.now().strftime('# RMQ session started at %Y.%m.%d %H:%M:%S\n'))

        self._stop_event.clear()
        self._thread = threading.Thread(target=self.thread, name='Consumer')
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        if self.config.rmq_session_dump:
            with open(self.config.rmq_session_dump, 'a') as fh:
                fh.write(datetime.now().strftime('# RQM session stopped at %Y.%m.%d %H:%M:%S\n'))

        self._stop_event.set()
        self._thread = None
