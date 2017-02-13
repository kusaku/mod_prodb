import Queue
import json
import threading
import time

import pika
from . import Log

RETRY_DELAY = 0.5


class Channel:
    config = None
    queue = None
    thread = None
    connection = None
    channel = None

    def init(self, config):
        Log.LOG_DEBUG('Channel init')
        self.config = config

        self.queue = Queue.Queue()

        self.thread = threading.Thread(target=self.send_thread)
        self.thread.setDaemon(True)
        self.thread.start()

    def fini(self):
        Log.LOG_DEBUG('Channel fini')

        self.queue = None

        if self.thread.isAlive():
            Log.LOG_ERROR('Channel still running')

        self.thread = None

    def connect(self):
        Log.LOG_DEBUG('Channel connect')

        username = self.config.username
        password = self.config.password
        host = self.config.host
        port = int(self.config.port)
        exchange = self.config.exchange

        Log.LOG_DEBUG("Channel connect info: ExchangeName='%s' IP='%s' Port='%s' User='%s' len(Pass)=%d"
                      % (exchange, host, port, username, len(password)))
        self.exchange_name = exchange

        try:
            credentials = pika.PlainCredentials(username, password)
            connection_parameters = pika.ConnectionParameters(host=host, port=port, credentials=credentials)

            self.connection = pika.BlockingConnection(connection_parameters)
            self.channel = self.connection.channel()

            self.channel.exchange_declare(exchange=exchange, type='fanout')

        except Exception, ex:
            Log.LOG_ERROR('Channel connect exception:', ex)
            Log.LOG_CURRENT_EXCEPTION()

    def disconnect(self):
        Log.LOG_DEBUG('Channel disconnect')
        try:
            self.connection.close()
        except Exception, ex:
            Log.LOG_DEBUG('Channel fini exception:', ex)

        self.channel = None
        self.connection = None

    def send_message_try(self, message):
        try:
            self.channel.basic_publish(exchange=self.exchange_name, routing_key='', body=message)  # mandatory=True
            return True
        except Exception, ex:
            Log.LOG_ERROR('Channel send_message_try exception', ex)
            Log.LOG_CURRENT_EXCEPTION()
            return False

    def send_message(self, message):
        # This is send loop. If basic_publish throws exception,
        # we are trying to shutdown and reconnect
        while self.send_message_try(message) == False:
            self.disconnect()
            time.sleep(RETRY_DELAY)
            self.connect()

    def send_thread(self):
        Log.LOG_DEBUG('Channel send_thread start')

        self.connect()

        while self.queue is not None:
            message = self.queue.get()
            self.send_message(message)
            self.queue.task_done()

    def send(self, message):
        try:
            message_json = json.dumps(message, sort_keys=True)
            self.queue.put(message_json)
        except Exception, ex:
            Log.LOG_ERROR('Channel send exception:', ex)
            Log.LOG_ERROR('Channel send message:', message)
            Log.LOG_CURRENT_EXCEPTION()
