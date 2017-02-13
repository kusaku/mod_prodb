import json
import pprint
import queue
import threading

import time

from ProDB import logger, autodict
from ProDB.Poster import POST_TYPE
from ProDB.ProxyTypes import ProxyTeam, ProxyPlayer

BATTLE_FINISH_TIMEOUT = 20.0 # seconds


class MSG_TYPE:
    ARENA = 'arena'
    STATS = 'stats'

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
        return 'period' in self.data and \
               self.data['period']['period'] == ARENA_PERIOD.AFTERBATTLE or \
               time.time() - self._last_atime > BATTLE_FINISH_TIMEOUT

    def __init__(self, aid, outputq):
        self._aid = aid
        self._inputq = queue.Queue()
        self._outputq = outputq
        self._stop_event = threading.Event()
        self._thread = None
        self._last_atime = 0
        self._last_stime = 0
        self._counter = 0
        self.data = autodict()

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self.thread, name='Battle %s' % str(self._aid)[-5:])
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._inputq.put(None)
        self._thread = None
        self.data = autodict()

    def thread(self):
        logger.debug('Started')

        while not self._stop_event.isSet():
            msg = self._inputq.get()

            if msg is None:
                continue

            self._process(msg)

            self._inputq.task_done()

        logger.debug('Finished')

    def _process(self, msg):
        self._last_atime = time.time()
        if msg.type == MSG_TYPE.ARENA:
            self._last_stime = msg.stime
            self.data.update(msg.data)

        if self._last_stime == 0:
            return

        if msg.type == MSG_TYPE.STATS:
            self.data['stats'][str(msg.cid)].update(msg.data)

        logger.info(self._last_atime)
        # logger.info(json.dumps(self.data, indent=4))

    def generate_post(self, post_type):
        if post_type == POST_TYPE.STATS:
            proxy_team_1 = ProxyTeam(1, self.data)
            proxy_team_2 = ProxyTeam(2, self.data)

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

            for cid in self.data['players'].keys():
                proxy_player = ProxyPlayer(cid, self.data)
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

            return {
                'meta': dict(),
                'contestants': {
                    'teams': teams,
                    'players': players,
                },
                'timeline': list()
            }
