import threading
import time

from .Battle import Battle
from .Logger import Logger
from .ProDBApi import cache_clear_all as api_cache_clear_all
from .ProDBMock import cache_clear_all as mock_cache_clear_all


class Dispatcher(object):
    @property
    def config(self):
        from ProDB.App import App
        return App().config

    @property
    def inputq(self):
        from ProDB.App import App
        return App().inputq

    @property
    def outputq(self):
        from ProDB.App import App
        return App().outputq

    def __init__(self):
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
            # Logger.info('Finishing Battle {}'.format(str(aid)[-5:]))
            battle.stop()
        self._thread_in = None
        self._thread_out = None
        self._thread_ctrl = None

    def thread_in(self):
        Logger.debug('Started')

        while not self._stop_event.isSet():
            msg = self.inputq.get()

            if msg is None:
                continue

            if msg.aid not in self._pool:
                # Logger.info('Starting Battle {}'.format(str(msg.aid)[-5:]))
                battle = Battle(msg.aid)
                self._pool[msg.aid] = battle
                battle.start()
            else:
                battle = self._pool[msg.aid]

            battle.queue.put(msg)

            self.inputq.task_done()

        Logger.debug('Finished')

    def thread_out(self):
        Logger.debug('Started')

        while not self._stop_event.wait(0.01):

            for aid, battle in list(self._pool.items()):
                if battle.is_post_updated:
                    msg = battle.get_post()
                    self.outputq.put(msg)

                if battle.is_finished:
                    # Logger.info('Finishing Battle {}'.format(str(aid)[-5:]))
                    battle.stop()
                    del self._pool[aid]

        Logger.debug('Finished')

    def thread_ctrl(self):
        Logger.debug('Started')

        last_clear_cache_time = time.time()

        while not self._stop_event.wait(1.0):
            if len(self._pool) > 0 and time.time() - last_clear_cache_time > self.config.cache_clear_timeout:
                api_cache_clear_all()
                mock_cache_clear_all()
                last_clear_cache_time = time.time()
                for battle in self._pool.values():
                    battle.external_data_updated()

        Logger.debug('Finished')
