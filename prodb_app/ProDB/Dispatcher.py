import threading

from ProDB import App
from ProDB import Battle
from ProDB import Poller
from ProDB import logger

REFRESH_PERIOD = 3.0


class Dispatcher(object):
    def __init__(self):
        self.config = App.App().config
        self._inputq = App.App().inputq
        self._outputq = App.App().outputq
        self._pool = None
        self._stop_event = threading.Event()
        self._thread_in = None
        self._thread_out = None

    def start(self):
        self._pool = dict()
        self._stop_event.clear()
        self._thread_in = threading.Thread(target=self.thread_in, name='DispatchIn')
        self._thread_in.daemon = True
        self._thread_in.start()
        self._thread_out = threading.Thread(target=self.thread_out, name='DispatchOut')
        self._thread_out.daemon = True
        self._thread_out.start()

    def stop(self):
        self._stop_event.set()
        while len(self._pool):
            aid, battle = self._pool.popitem()
            battle.stop()
            logger.info('Battle {} stopped'.format(aid))
        self._thread_in = None
        self._thread_out = None

    def thread_in(self):
        logger.debug('Started')

        while not self._stop_event.isSet():
            msg = self._inputq.get()

            if msg is None:
                continue

            if msg.aid not in self._pool:
                battle = Battle.Battle(msg.aid, self._outputq)
                self._pool[msg.aid] = battle
                battle.start()
                logger.info('Battle {} started'.format(msg.aid))
            else:
                battle = self._pool[msg.aid]

            battle.queue.put(msg)

            self._inputq.task_done()

        logger.debug('Finished')

    def thread_out(self):
        logger.debug('Started')

        # poll_represh = 60.0

        while not self._stop_event.wait(0.01):

            for aid, battle in list(self._pool.items()):
                # if poll_represh < 0.0:
                #     battle.notify_update()

                if battle.is_post_updated:
                    post_data = battle.get_post()
                    msg = aid, post_data
                    self._outputq.put(msg)

                if battle.is_finished:
                    battle.stop()
                    logger.info('Battle {} stopped'.format(aid))
                    del self._pool[aid]

            # if poll_represh < 0.0:
            #     Poller.cache_clear_all()
            #     poll_represh = 60.0
            # else:
            #     poll_represh -= 0.01

        logger.debug('Finished')
