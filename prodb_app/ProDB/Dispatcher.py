import threading
import time

import ProDB.ProDB
from ProDB import App, CACHE_CLEAR_TIMEOUT
from ProDB import Battle
from ProDB import logger


class Dispatcher(object):
    def __init__(self):
        self._inputq = App.App().inputq
        self._outputq = App.App().outputq
        self._pool = None
        self._stop_event = threading.Event()
        self._thread_in = None
        self._thread_out = None
        self._thread_ctrl = None

    def start(self):
        self._pool = dict()
        self._stop_event.clear()
        self._thread_in = threading.Thread(target=self.thread_in, name='DispatchIn')
        self._thread_in.daemon = True
        self._thread_in.start()
        self._thread_out = threading.Thread(target=self.thread_out, name='DispatchOut')
        self._thread_out.daemon = True
        self._thread_out.start()
        self._thread_ctrl = threading.Thread(target=self.thread_ctrl, name='DispatchCtrl')
        self._thread_ctrl.daemon = True
        self._thread_ctrl.start()

    def stop(self):
        self._stop_event.set()
        while len(self._pool):
            aid, battle = self._pool.popitem()
            # logger.info('Finishing Battle {}'.format(str(aid)[-5:]))
            battle.stop()
        self._thread_in = None
        self._thread_out = None
        self._thread_ctrl = None

    def thread_in(self):
        logger.debug('Started')

        while not self._stop_event.isSet():
            msg = self._inputq.get()

            if msg is None:
                continue

            if msg.aid not in self._pool:
                # logger.info('Starting Battle {}'.format(str(msg.aid)[-5:]))
                battle = Battle.Battle(msg.aid, self._outputq)
                self._pool[msg.aid] = battle
                battle.start()
            else:
                battle = self._pool[msg.aid]

            battle.queue.put(msg)

            self._inputq.task_done()

        logger.debug('Finished')

    def thread_out(self):
        logger.debug('Started')

        while not self._stop_event.wait(0.01):

            for aid, battle in list(self._pool.items()):
                if battle.is_post_updated:
                    post_data = battle.get_post()
                    msg = aid, post_data
                    self._outputq.put(msg)

                if battle.is_finished:
                    # logger.info('Finishing Battle {}'.format(str(aid)[-5:]))
                    battle.stop()
                    del self._pool[aid]

        logger.debug('Finished')

    def thread_ctrl(self):
        logger.debug('Started')

        last_clear_cache_time = time.time()

        while not self._stop_event.wait(1.0):
            if len(self._pool) > 0 and time.time() - last_clear_cache_time > CACHE_CLEAR_TIMEOUT:
                ProDB.ProDB.cache_clear_all()
                last_clear_cache_time = time.time()
                for battle in self._pool.values():
                    battle.external_data_updated()

        logger.debug('Finished')
