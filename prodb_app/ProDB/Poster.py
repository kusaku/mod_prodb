import asyncio
import json
import os
import queue
import threading

import jsonpatch

from .Logger import Logger
from .ProDBApi import postMatchRounds, postMatchRoundsСontestant, postMathcRoundStats


class POST_TYPE:
    POST_ROUND_STATUS = 1
    POST_ROUND_RESULT = 2
    POST_ROUND_STATISTICS = 3

class Poster(object):
    @property
    def config(self):
        from .App import App
        return App().config

    @property
    def outputq(self):
        from .App import App
        return App().outputq

    @property
    def executor(self):
        from .App import App
        return App().poster_executor

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread_lock = threading.Lock()
        self._thread = None
        self._loop = None
        self._futures = set()
        self._stats_storage = dict()

    def start(self):
        self._stop_event.clear()
        self._futures = set()
        self._stats_storage = dict()
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

    def _post_round_status(self, key, post):
        try:
            post_json = json.dumps(post)

            from .App import App

            if App().config.mockpost:
                if not os.path.exists('mockpost'):
                    os.makedirs('mockpost')
                fname = 'mockpost/status-{}.json'.format(key)
                with open(fname, 'at') as fh:
                    Logger.info('[mock] Round status data is written to {}'.format(fname))
                    fh.write('{}\n'.format(post_json))

            else:
                postMatchRounds(key, post_json)

        except Exception as ex:
            Logger.error('Exception in _post_round_status: {}'.format(repr(ex.args[0])))
            with self.outputq.mutex:
                self.outputq.queue.appendleft((POST_TYPE.POST_ROUND_STATUS, key, post))

    def _post_round_result(self, key, post):
        try:
            post_json = json.dumps(post)

            from .App import App

            if App().config.mockpost:
                if not os.path.exists('mockpost'):
                    os.makedirs('mockpost')
                fname = 'mockpost/result-{}.json'.format(key)
                with open(fname, 'at') as fh:
                    Logger.info('[mock] Round result data is written to {}'.format(fname))
                    fh.write('{}\n'.format(post_json))
            else:
                postMatchRoundsСontestant(key, post_json)

        except Exception as ex:
            Logger.error('Exception in _post_round_status: {}'.format(repr(ex.args[0])))
            with self.outputq.mutex:
                self.outputq.queue.appendleft((POST_TYPE.POST_ROUND_RESULT, key, post))


    def _post_round_statistics(self, key, post):
        try:
            with self._thread_lock:
                last_post = self._stats_storage.get(key)

            if last_post == post:
                return

            from .App import App

            if App().config.force_post or last_post is None:
                is_patch = False
                post_json = json.dumps(post)
            else:
                is_patch = True
                post_json = jsonpatch.make_patch(last_post, post).to_string()

            if App().config.mockpost:
                if not os.path.exists('mockpost'):
                    os.makedirs('mockpost')
                fname = 'mockpost/statistics-{}.json'.format(key)
                with open(fname, 'at') as fh:
                    Logger.info('[mock] Round statistics data is written to {}'.format(fname))
                    fh.write('{}\n'.format(post_json))

            else:
                postMathcRoundStats(key, post_json, is_patch)

            with self._thread_lock:
                self._stats_storage[key] = post

        except Exception as ex:
            Logger.error('Exception in _post_round_statistics: {}'.format(repr(ex.args[0])))
            with self.outputq.mutex:
                self.outputq.queue.appendleft((POST_TYPE.POST_ROUND_STATISTICS, key, post))

    async def _poster(self):
        while not self._stop_event.isSet():

            futures = set()

            while not self._stop_event.isSet() and len(futures) < self.config.max_poster_workers:
                try:
                    msg = self.outputq.get(block=False)

                    if msg is None:
                        continue

                    post_type, *args = msg

                    if post_type == POST_TYPE.POST_ROUND_STATUS:
                        futures.add(self._loop.run_in_executor(self.executor, self._post_round_status, *args))
                    elif post_type == POST_TYPE.POST_ROUND_RESULT:
                        futures.add(self._loop.run_in_executor(self.executor, self._post_round_result, *args))
                    elif post_type == POST_TYPE.POST_ROUND_STATISTICS:
                        futures.add(self._loop.run_in_executor(self.executor, self._post_round_statistics, *args))

                except queue.Empty:
                    pass

            gathered_future = asyncio.gather(*futures, return_exceptions=True)

            futures.clear()

            if not self._stop_event.isSet():
                await gathered_future
            else:
                gathered_future.cancel()
