import json
import threading
from collections import namedtuple
from datetime import datetime

import pika

from ProDB import App
from ProDB import logger

RESTART_TIMEOUT = 10.0
NEW_CASTER_TIMEOUT = 5.0

msg_packet = namedtuple('msg_packet', 'aid,vid,cid,stime,type,data')


class Consumer(object):
    def __init__(self):
        self._config = App.App().config
        self._queue = App.App().inputq
        self._stop_event = threading.Event()
        self._thread = None
        self._connection = None
        self._counter = 0

    def start(self):
        if self._config.rmq_session_dump:
            with open(self._config.rmq_session_dump, 'a') as outfile:
                outfile.write(datetime.now().strftime('# RMQ session started at %Y.%m.%d %H:%M:%S\n'))

        self._stop_event.clear()
        self._thread = threading.Thread(target=self.thread, name='Consumer')
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        if self._config.rmq_session_dump:
            with open(self._config.rmq_session_dump, 'a') as outfile:
                outfile.write(datetime.now().strftime('# RQM session stopped at %Y.%m.%d %H:%M:%S\n'))

        self._stop_event.set()
        self._thread = None

    def thread(self):
        logger.debug('Started')

        while not self._stop_event.isSet():
            try:
                logger.debug('Connecting to {}:{}@{}:{}/{}'.format(
                    self._config.rmq_username,
                    '*' * len(self._config.rmq_password),
                    self._config.rmq_ip,
                    self._config.rmq_port,
                    self._config.rmq_exchange
                ))

                credentials = pika.PlainCredentials(self._config.rmq_username, self._config.rmq_password)

                self._connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self._config.rmq_ip, port=self._config.rmq_port,
                                              credentials=credentials)
                )

                channel = self._connection.channel()
                channel.exchange_declare(exchange=self._config.rmq_exchange, type='fanout')

                queue_name = channel.queue_declare(exclusive=True).method.queue

                channel.queue_bind(exchange=self._config.rmq_exchange, queue=queue_name)
                channel.basic_consume(self.callback, queue=queue_name, no_ack=True)

                logger.debug('Connected')

                while not self._stop_event.isSet():
                    self._connection.process_data_events(time_limit=0.01)

            except Exception as ex:
                logger.exception('Exception: {}'.format(type(ex).__name__))

            finally:
                try:
                    if self._connection and self._connection.is_open:
                        logger.debug('Closing connection')
                        self._connection.close()
                        self._connection = None
                except Exception as ex:
                    logger.exception('Exception: {}'.format(type(ex).__name__))

        logger.debug('Finished')

    def callback(self, ch, method, properties, body):
        try:
            msg = msg_packet(**json.loads(body.decode('utf-8')))

            if self._config.rmq_session_dump is not None:
                with open(self._config.rmq_session_dump, 'a') as fh:
                    json.dump(msg._asdict(), fh, sort_keys=True)
                    fh.write('\n')

            # logger.exception(json.dumps(msg, indent=4))
            self._queue.put(msg)
        except Exception as e:
            logger.exception(body)
            pass
