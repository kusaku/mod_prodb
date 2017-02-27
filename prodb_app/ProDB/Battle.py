import asyncio
import copy
import queue
import threading
import time

from ProDB import logger
from ProDB.ProxyTypes import ProxyTeam, ProxyPlayer, ProxyRound

BATTLE_FINISH_TIMEOUT = 20.0  # seconds


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
    def is_data_updated(self):
        return self._data != self._old_data

    @property
    def is_post_updated(self):
        return self._post != self._old_post

    def notify_update(self):
        self._need_update_post = True

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
        self._old_data = dict(period=dict(), stats=dict(), players=dict())
        self._need_update_post = True
        self._post = dict()
        self._old_post = dict()

    def get_post(self):
        # logger.warn('get_post')
        with self._lock:
            if self.is_post_updated:
                self._old_post = copy.deepcopy(self._post)
            return copy.deepcopy(self._post)

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
        logger.debug('Started')

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        while not self._stop_event.wait(timeout=0.01):
            try:
                msg = self._inputq.get(block=False)

                if msg is None:
                    continue

                self._process(msg)
                self._inputq.task_done()

            except queue.Empty:
                pass

            if self._need_update_post:
                with self._lock:
                    self._update_post()

        self.loop.close()

        logger.debug('Finished')

    def _process(self, msg):
        self._last_atime = time.time()

        self._old_data = copy.deepcopy(self._data)

        if msg.type == MSG_TYPE.UPDATE_ARENA:
            self._data.update(msg.data)

        if msg.type in (MSG_TYPE.UPDATE_STATS, MSG_TYPE.UPDATE_BASE_STATE):
            stats = self._data.get('stats').setdefault(str(msg.cid), {})
            stats.update(msg.data.get('stats_data', {}))

        self._need_update_post = self._need_update_post or self.is_data_updated

        # logger.warn(('need_update', self._need_update_post))

    def _update_post(self):

        if not self.is_consistent:
            return

        # logger.warn('update')

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

        def get_tasks_of(struct):
            if isinstance(struct, asyncio.Task):
                yield struct
            elif isinstance(struct, dict):
                for v in struct.values():
                    yield from get_tasks_of(v)
            elif isinstance(struct, list):
                for v in struct:
                    yield from get_tasks_of(v)

        tasks = [v for v in get_tasks_of(post)]

        done, pending = self.loop.run_until_complete(asyncio.wait(tasks))

        def set_result_to(struct, completed):
            if isinstance(struct, dict):
                for k, v in struct.items():
                    if isinstance(v, asyncio.Task):
                        struct[k] = v.result()
                    else:
                        set_result_to(v, completed)
            elif isinstance(struct, list):
                for v in struct:
                    set_result_to(v, completed)

        set_result_to(post, done)

        self._post = post
        self._need_update_post = False
