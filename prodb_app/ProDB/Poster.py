import asyncio
import json
import os
import random
import threading
import time

import jsonpatch

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
        self._thread_lock = threading.Lock()
        self._thread = None
        self._loop = None
        self._futures = set()
        self._storage = dict()

    def start(self):
        self._stop_event.clear()
        self._futures = set()
        self._storage = dict()
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

    def _post(self, key, post):
        try:
            with self._thread_lock:
                last_post = self._storage.get(key)

            if last_post is not None:
                is_patch = True
                post_json = jsonpatch.make_patch(last_post, post).to_string()
            else:
                is_patch = False
                post_json = json.dumps(post)

            time.sleep(random.random())
            assert random.random() > 0.3, 'azazaza!'

            from .App import App

            if App().config.mockpost:
                if not os.path.exists('mockpost'):
                    os.makedirs('mockpost')
                fname = 'mockpost/arena-{}.json'.format(key)
                with open(fname, 'at') as fh:
                    Logger.info('[mock] Post data is written to {}'.format(fname))
                    fh.write('{}\n'.format(post_json))

            else:
                postStats(key, post_json, is_patch)

            with self._thread_lock:
                self._storage[key] = post

        except Exception as ex:
            Logger.error('Exception: {}'.format(repr(ex.args[0])))
            with self.outputq.mutex:
                self.outputq.queue.appendLeft((key, post))

    async def _poster(self):
        from .App import App
        while not self._stop_event.isSet():
            futures = set()
            while not self._stop_event.isSet() and len(futures) < self.config.max_poster_workers:
                msg = self.outputq.get()
                if msg is None:
                    continue
                key, post = msg
                futures.add(self._loop.run_in_executor(App().poster_executor, self._post, key, post))
                self.outputq.task_done()
            gathered_future = asyncio.gather(*futures, return_exceptions=True)
            if not self._stop_event.isSet():
                await gathered_future
            else:
                gathered_future.cancel()
