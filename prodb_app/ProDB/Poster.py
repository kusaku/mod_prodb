import asyncio
import threading
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor

import requests

from ProDB import App
from ProDB import logger


class POST_TYPE:
    STATS = 'stats'


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

        # executor = ProcessPoolExecutor(max_workers=3)
        executor = ThreadPoolExecutor(max_workers=3)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._poster(executor))
        finally:
            loop.close()

        logger.debug('Finished')

    async def _poster(self, executor):
        futures = set()
        loop = asyncio.get_event_loop()

        while not self._stop_event.wait(0.1):
            post_data = 'aaaa'  # self._inputq.get()
            if post_data is None:
                continue

            future = loop.run_in_executor(executor, _post, post_data)
            futures.add(future)
            # self._inputq.task_done()

        for future in futures:
            future.cancel()
            await future


def _post(data):
    requests.post('127.0.0.1', data)
