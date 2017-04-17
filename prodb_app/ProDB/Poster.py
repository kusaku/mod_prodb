import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from ProDB import MAX_POSTER_WORKERS
from ProDB.Logger import Logger
from .ProDBApi import postStats


class Poster(object):
    @property
    def config(self):
        from ProDB.App import App
        return App().config

    @property
    def outputq(self):
        from ProDB.App import App
        return App().outputq

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
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
        executor = ThreadPoolExecutor(max_workers=MAX_POSTER_WORKERS)
        # executor = ProcessPoolExecutor(max_workers=MAX_POSTER_WORKERS)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(executor)
        try:
            loop.run_until_complete(self._poster())
        finally:
            loop.close()
        Logger.debug('Finished')

    async def _poster(self):
        loop = asyncio.get_event_loop()
        while not self._stop_event.isSet():
            futures = set()
            while not self._stop_event.isSet() and len(futures) < MAX_POSTER_WORKERS:
                msg = self.outputq.get()
                if msg is None:
                    continue
                key, post_data, is_patch = msg
                try:
                    future = loop.run_in_executor(None, postStats, key, post_data, is_patch)
                except:
                    continue
                futures.add(future)
                self.outputq.task_done()
            gathered_future = asyncio.gather(*futures, return_exceptions=True)
            if not self._stop_event.isSet():
                await gathered_future
            else:
                gathered_future.cancel()
