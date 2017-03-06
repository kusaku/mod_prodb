import asyncio
import copy
import json
import queue
import threading
import time

import jsonpatch

from . import BATTLE_FINISH_TIMEOUT, BATTLE_POST_TIMEOUT
from .Logger import Logger
from .ProxyTypes import ProxyPlayer, ProxyRound, ProxyTeam


class MSG_TYPE:
    UPDATE_ARENA = 'update_arena'
    UPDATE_STATS = 'update_stats'
    UPDATE_HEALTH = 'update_health'
    UPDATE_RELOAD = 'update_reload'
    UPDATE_DAMAGE = 'update_damage'
    UPDATE_SPOTTED = 'update_spotted'
    UPDATE_BASE_STATE = 'update_base_state'


class ARENA_PERIOD:
    IDLE = 0
    WAITING = 1
    PREBATTLE = 2
    BATTLE = 3
    AFTERBATTLE = 4


class Battle(object):
    @property
    def queue(self):
        return self._inputq

    @property
    def is_finished(self):
        return self._data.get('period').get('period') == ARENA_PERIOD.AFTERBATTLE or \
               time.time() - self._last_atime > BATTLE_FINISH_TIMEOUT

    @property
    def is_consistent(self):
        return self._data.get('stats') and self._data.get('players') and \
               set(self._data.get('stats').keys()) == set(self._data.get('players').keys())

    @property
    def is_post_updated(self):
        return self._post_is_updated

    @property
    def is_post_firsttime(self):
        return len(self._post_old) == 0

    def external_data_updated(self):
        self._post_needs_update = True

    def __init__(self, aid, outputq):
        self._aid = aid
        self._inputq = queue.Queue()
        self._outputq = outputq
        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._last_atime = time.time()
        self._counter = 0
        self._data = dict(period=dict(), stats=dict(), players=dict())
        self._post = dict()
        self._post_old = dict()
        self._post_key = str()
        self._post_needs_update = False
        self._post_is_updated = False

    def get_post(self):
        # Logger.warn('get_post')
        # deliver post data, clear updated status
        with self._lock:
            if self.is_post_firsttime:
                # return full post
                post = self._post_key, json.dumps(self._post), False
            else:
                # return json patch post - changes only
                post = self._post_key, jsonpatch.make_patch(self._post_old, self._post).to_string(), True

            self._post_old = copy.deepcopy(self._post)
            self._post_is_updated = False
            return post

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self.thread, name='Battle %s' % str(self._aid)[-5:])
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._inputq.put(None)
        self._thread = None

    def thread(self):
        Logger.debug('Started')

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.set_exception_handler(lambda *args: None)

        while not self._stop_event.wait(timeout=0.01):
            try:
                msg = self._inputq.get(block=False)

                if msg is None:
                    continue

                self._process(msg)
                self._inputq.task_done()

            except queue.Empty:
                pass

            if self._post_needs_update:
                with self._lock:
                    self._update_post()

        self.loop.close()

        Logger.debug('Finished')

    def _process(self, msg):
        self._last_atime = time.time()

        if self.is_finished:
            return

        _old_data = copy.deepcopy(self._data)

        if msg.type == MSG_TYPE.UPDATE_ARENA:
            self._data.update(msg.data)

        if msg.type in (MSG_TYPE.UPDATE_STATS, MSG_TYPE.UPDATE_BASE_STATE):
            stats = self._data.get('stats').setdefault(str(msg.cid), {})
            stats.update(msg.data.get('stats_data', {}))

        # Mock cids
        #
        # [542794177, 542794178, 542794179, 542794180, 542794181, 542793197, 542794182, 542794184, 542794185, 542794186, 542794188, 542794189, 542794190, 542794165]
        # Mock data
        #
        # self._data.update(
        #     {
        #         # 'attackingTeam': 1,
        #         # 'gameplayName': 'assault',
        #
        #         'stats': {
        #             '542794177': self._data['stats'].get('32377107', dict()),
        #             '542794178': dict(),
        #             '542794179': dict(),
        #             '542794180': dict(),
        #             '542794181': dict(),
        #             '542793197': dict(),
        #             '542794182': dict(),
        #             '542794184': dict(),
        #             '542794185': dict(),
        #             '542794186': dict(),
        #             '542794188': dict(),
        #             '542794189': dict(),
        #             '542794190': dict(),
        #             '542794165': dict(),
        #
        #         },
        #
        #         'players': {
        #             '542794177': self._data['players'].get('32377107', {'team': 1, 'name': 'WoT A1', 'vehicle_name': 'veh_t'}),
        #             '542794178': {'team': 1, 'name': 'WoT A2', 'vehicle_name': 'veh_t'},
        #             '542794179': {'team': 1, 'name': 'WoT A3', 'vehicle_name': 'veh_t'},
        #             '542794180': {'team': 1, 'name': 'WoT A4', 'vehicle_name': 'veh_t'},
        #             '542794181': {'team': 1, 'name': 'WoT A5', 'vehicle_name': 'veh_t'},
        #             '542793197': {'team': 1, 'name': 'WoT A6', 'vehicle_name': 'veh_t'},
        #             '542794182': {'team': 1, 'name': 'WoT A7', 'vehicle_name': 'veh_t'},
        #             '542794184': {'team': 2, 'name': 'WoT B1', 'vehicle_name': 'veh_t'},
        #             '542794185': {'team': 2, 'name': 'WoT B2', 'vehicle_name': 'veh_t'},
        #             '542794186': {'team': 2, 'name': 'WoT B3', 'vehicle_name': 'veh_t'},
        #             '542794188': {'team': 2, 'name': 'WoT B4', 'vehicle_name': 'veh_t'},
        #             '542794189': {'team': 2, 'name': 'WoT B5', 'vehicle_name': 'veh_t'},
        #             '542794190': {'team': 2, 'name': 'WoT B6', 'vehicle_name': 'veh_t'},
        #             '542794165': {'team': 2, 'name': 'WoT B7', 'vehicle_name': 'veh_t'},
        #         }
        #     }
        # )

        self._post_needs_update = self._post_needs_update or _old_data != self._data

        # self._post_needs_update = True
        # self._post_is_updated = True
        # Logger.warn(json.dumps(self._data, indent=4))
        # Logger.warn('Is finished? {!r}'.format(self.is_finished))
        # Logger.warn('Is consistent? {!r}'.format(self.is_consistent))
        # Logger.warn('Does post need update? {!r}'.format(self._post_needs_update))
        # Logger.warn(('need_update', self._need_update_post))

    # utulity to return tasks list from structure
    def _get_tasks_of(self, struct):
        if isinstance(struct, asyncio.Task):
            yield struct
        elif isinstance(struct, dict):
            for v in struct.values():
                yield from self._get_tasks_of(v)
        elif isinstance(struct, list):
            for v in struct:
                yield from self._get_tasks_of(v)

    # utulity to set tasks result to structure
    def _set_result_to(self, struct, completed):
        if isinstance(struct, dict):
            for k, v in struct.items():
                if isinstance(v, asyncio.Task):
                    struct[k] = v.result()
                else:
                    self._set_result_to(v, completed)
        elif isinstance(struct, list):
            for v in struct:
                self._set_result_to(v, completed)

    def _update_post(self):

        if not self.is_consistent:
            return

        # Logger.warn('update')

        proxy_team_1 = ProxyTeam(1, self._data)
        proxy_team_2 = ProxyTeam(2, self._data)

        teams = [
            {
                'id': proxy_team_1.id,
                'name': proxy_team_1.name,
                'meta': {
                    'ingameTeam': proxy_team_1.attack_defence
                }
            },
            {
                'id': proxy_team_2.id,
                'name': proxy_team_2.name,
                'meta': {
                    'ingameTeam': proxy_team_2.attack_defence
                }
            },
        ]

        players = list()

        for cid in self._data.get('players', {}).keys():
            proxy_player = ProxyPlayer(cid, self._data)
            players.append({
                'id': proxy_player.id,
                'vendorId': proxy_player.vendorId,
                'name': proxy_player.name,
                'teamId': proxy_player.teamId,
                'meta': {
                    'tank': {
                        'name': proxy_player.tank_name
                    }
                },
                'stats': {
                    'kills': proxy_player.kills,
                    'shots': proxy_player.shots,
                    'spotted': proxy_player.spotted,
                    'damageDealt': proxy_player.damageDealt,
                    'damageBlocked': proxy_player.damageBlocked,
                }
            })

        proxy_arena = ProxyRound(self._data)

        post = {
            'key': proxy_arena.id,
            'meta': dict(),
            'contestants': {
                'teams': teams,
                'players': players,
            },
            'timeline': list()
        }

        new_tasks = [v for v in self._get_tasks_of(post)]

        future = asyncio.wait(new_tasks, timeout=BATTLE_POST_TIMEOUT, return_when=asyncio.FIRST_EXCEPTION)
        done_tasks, pending_tasks = self.loop.run_until_complete(future)

        if len(pending_tasks) > 0:
            for task in done_tasks:
                if task.exception() is not None:
                    Logger.error('Error {} in {}'.format(repr(task.exception().args[0]), task._coro.__name__))

            for task in pending_tasks:
                task.cancel()

            # sleep?
            Logger.error('Generate post failed, sleepeng {} seconds'.format(BATTLE_POST_TIMEOUT))
            self.loop.run_until_complete(asyncio.sleep(BATTLE_POST_TIMEOUT))

        else:
            self._set_result_to(post, done_tasks)
            self._post_key = post.pop('key')
            self._post = post
            self._post_needs_update = False
            self._post_is_updated = self._post_is_updated or self._post_old != self._post
