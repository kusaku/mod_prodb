import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from ProDB import App
from ProDB import logger
from ProDB.ProDB import postStats

MAX_WORKERS = 4


class Poster(object):
    def __init__(self):
        self.config = App.App().config
        self._inputq = App.App().outputq
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
        logger.debug('Started')
        executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        # executor = ProcessPoolExecutor(max_workers=MAX_WORKERS)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_default_executor(executor)
        try:
            loop.run_until_complete(self._poster())
        finally:
            loop.close()
        logger.debug('Finished')

    async def _poster(self):
        loop = asyncio.get_event_loop()
        while not self._stop_event.isSet():
            futures = set()
            while not self._stop_event.isSet() and len(futures) < MAX_WORKERS:
                msg = self._inputq.get()
                if msg is None:
                    continue
                aid, post_data = msg
                try:
                    future = loop.run_in_executor(None, postStats, aid, post_data)
                except:
                    continue
                futures.add(future)
                self._inputq.task_done()
            gathered_future = asyncio.gather(*futures, return_exceptions=True)
            if not self._stop_event.isSet():
                # logger.warn(await gathered_future)
                await gathered_future
            else:
                gathered_future.cancel()
