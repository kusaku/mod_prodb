import asyncio
import threading

from .Logger import Logger
from .ProDBApi import postStats


class Poster(object):
    @property
    def config(self):
        from .App import App
        return App().config

    @property
    def outputq(self):
        from .App import App
        return App().outputq

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self._loop = None
        self._futures = set()

    def start(self):
        self._stop_event.clear()
        self._futures = set()
        self._thread = threading.Thread(target=self.thread, name='Poster')
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread = None

    def thread(self):
        Logger.debug('Started')
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._poster())
        finally:
            self._loop.close()
        Logger.debug('Finished')

    async def _poster(self):
        from .App import App
        while not self._stop_event.isSet():
            futures = set()
            while not self._stop_event.isSet() and len(futures) < self.config.max_poster_workers:
                msg = self.outputq.get()
                if msg is None:
                    continue
                key, post_data, is_patch = msg
                try:
                    future = self._loop.run_in_executor(App().poster_executor, postStats, key, post_data, is_patch)
                except:
                    continue
                futures.add(future)
                self.outputq.task_done()
            gathered_future = asyncio.gather(*futures, return_exceptions=True)
            if not self._stop_event.isSet():
                await gathered_future
            else:
                gathered_future.cancel()
