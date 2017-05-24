import asyncio
import copy
import datetime
import queue
import threading
import time

from ProDB import ProDBApi
from ProDB.Poller import Poller
from ProDB.Poster import POST_TYPE
from .Logger import Logger
from .ProxyTypes import ProxyPlayer, ProxyTeam


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
    def config(self):
        from .App import App
        return App().config

    @property
    def outputq(self):
        from .App import App
        return App().outputq

    @property
    def queue(self):
        return self._inputq

    @property
    def is_finished(self):
        return time.time() - self._last_atime > self.config.battle_finish_timeout

    @property
    def is_consistent(self):
        return len(self._data.get('players')) > 0
        # return len(self._data.get('stats')) > 0 and len(self._data.get('players')) > 0 and \
        #        set(self._data.get('stats').keys()) == set(self._data.get('players').keys())

    def force_update_all(self):
        self._round_info_needs_update = True
        self._round_status_needs_update = True
        self._round_results_needs_update = False  # sic!
        self._round_statistics_needs_update = True

    def __init__(self, aid):
        self._aid = aid
        self._inputq = queue.Queue()
        self._inputq_overflow = False
        self._stop_event = threading.Event()
        self._thread = None
        self._loop = None
        self._poller = None
        self._lock = threading.Lock()
        self._last_atime = time.time()
        self._counter = 0
        self._round_info = None
        self._round_info_needs_update = True
        self._round_status_needs_update = True
        self._round_results_needs_update = False  # sic!
        self._round_statistics_needs_update = True
        self._data = dict(period=dict(), stats=dict(), players=dict())
        self._start_time = datetime.datetime.now().isoformat() + 'Z'

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

        self._loop = asyncio.new_event_loop()
        self._loop.set_exception_handler(lambda *args: None)

        asyncio.set_event_loop(self._loop)

        self._poller = Poller()

        while not self._stop_event.wait(timeout=0.01):
            try:
                msg = self._inputq.get(block=False)

                if msg is None:
                    continue

                self._process(msg)

            except queue.Empty:
                pass

            qsize = self._inputq.qsize()

            if not self._inputq_overflow and qsize > 100:
                self._inputq_overflow = True
                Logger.error('Queue length is {}'.format(qsize))
            elif self._inputq_overflow and not qsize > 100:
                self._inputq_overflow = False
                Logger.info('Queue length is OK')

            with self._lock:
                if self._round_info_needs_update:
                    self._update_round_info()
                # if self._round_status_needs_update:
                #     self._update_round_status()
                # if self._round_results_needs_update:
                #     self._update_round_result()
                if self._round_statistics_needs_update:
                    self._update_round_statistics()

        self._loop.close()

        Logger.debug('Finished')

    def _process(self, msg):
        self._last_atime = time.time()

        if self.is_finished:
            return

        _old_data = copy.deepcopy(self._data)

        # update arena (can update player stats when battleresults received)
        if msg.type == MSG_TYPE.UPDATE_ARENA:
            self._data.update(msg.data)

        # do not receive players data after battle
        if self._data.get('period').get('period') != ARENA_PERIOD.AFTERBATTLE:
            # update player stats
            if msg.type in (MSG_TYPE.UPDATE_STATS, MSG_TYPE.UPDATE_BASE_STATE):
                stats = self._data.get('stats').setdefault(str(msg.cid), {})
                stats.update(msg.data.get('stats_data', {}))

        self._round_status_needs_update |= _old_data.get('period').get('period') != self._data.get('period').get('period')

        self._round_results_needs_update |=_old_data.get('period').get('period') == ARENA_PERIOD.BATTLE and \
                                           self._data.get('period').get('period') == ARENA_PERIOD.AFTERBATTLE

        self._round_statistics_needs_update |= _old_data != self._data

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
        #
        # self._round_info_needs_update = True
        # Logger.warn(json.dumps(self._data, indent=4))
        # Logger.warn('Is finished? {!r}'.format(self.is_finished))
        # Logger.warn('Is consistent? {!r}'.format(self.is_consistent))
        # Logger.warn('Does post need update? {!r}'.format(self._round_info_needs_update))
        # Logger.warn(('need_update', self._need_update_post))

    def _update_round_info(self):
        if not self.is_consistent:
            return

        team1_cids = [cid for cid, player in self._data.get('players', {}).items() if player.get('team') == 1]
        team2_cids = [cid for cid, player in self._data.get('players', {}).items() if player.get('team') == 2]

        try:
            round_info_task = self._poller.getMatchRoundByPlayerCIDs(team1_cids, team2_cids)
            self._round_info = self._loop.run_until_complete(round_info_task)
        except Exception as ex:
            Logger.error("Error '{}'".format(next(iter(ex.args), type(ex).__name__)))
        finally:
            self._round_info_needs_update = False

    def _update_round_status(self):
        if self._round_info is None:
            return

        arena_period = self._data.get('period').get('period')

        round_status = {
            ARENA_PERIOD.PREBATTLE: 'open',
            ARENA_PERIOD.BATTLE: 'live',
            ARENA_PERIOD.AFTERBATTLE: 'finished',
        }.get(arena_period)

        post = {
            'roundNumber': self._round_info.get('roundNumber'),
            'gameVersionMap': self._round_info.get('gameVersionMap').get('gameVersionKey'),
            'roundStatus': round_status,
            'startTime': self._start_time,
        }

        match_round_key = self._round_info.get('key')
        self.outputq.put((POST_TYPE.POST_ROUND_STATUS, match_round_key, post))
        self._round_status_needs_update = False

    def _update_round_result(self):
        if self._round_info is None:
            return

        # arena_period = self._data.get('period').get('period')
        # match_round_key = self._round_info.get('key')
        # winner_team, finish_reason = self._data.get('period').get('periodAdditionalInfo', (0, 0))

        winner_team = 1
        looser_team = winner_team % 2 + 1

        winner_team_cids = [cid for cid, player in self._data.get('players', {}).items() if player.get('team') == winner_team]
        looser_team_cids = [cid for cid, player in self._data.get('players', {}).items() if player.get('team') == looser_team]

        # mrdetails_task = self._poller.getMatchRoundDetailsByKey(match_round_key)

        from ProDB.App import App

        # mrdetails_task = self._poller.getMatchRoundDetailsByKey(match_round_key)
        mrdetails_task = self._loop.run_in_executor(App().poller_executor, ProDBApi.getMatchDetails, '21a987d6-7d73-46ba-aa0d-e08c3c2033b8')
        winner_team_key_task = self._poller.getTeamSquadKeyByPlayerCIDs(winner_team_cids)
        looser_team_key_task = self._poller.getTeamSquadKeyByPlayerCIDs(looser_team_cids)
        maintask = asyncio.gather(mrdetails_task, winner_team_key_task, looser_team_key_task)
        mrdetails, winner_team_key, looser_team_key = self._loop.run_until_complete(maintask)

        # rss = [ProDBApi.getMatchDetails(m.get('key')).get('rounds') for m in ProDBApi.getMatches(winner_team_key, looser_team_key)]
        #
        # def u(k):
        #     try:
        #         ProDBApi.getMatchRoundsDetails(k)
        #         return k
        #     except Exception as e:
        #         return e.args
        #
        # k = [u(r.get('key')) for rs in rss for r in rs]
        #
        # Logger.warn(k)
        #
        #

        contestants = mrdetails.get('contestants')

        winner_contestant_key = next(iter(c.get('key') for c in contestants if c.get('tournamentContestant').get('squad').get('key') == winner_team_key))
        looser_contestant_key = next(iter(c.get('key') for c in contestants if c.get('tournamentContestant').get('squad').get('key') == looser_team_key))

        self.outputq.put((POST_TYPE.POST_ROUND_RESULT, winner_contestant_key, {'gameResult': 'win', 'gameRole': None, 'score': 0}))
        self.outputq.put((POST_TYPE.POST_ROUND_RESULT, looser_contestant_key, {'gameResult': 'loss', 'gameRole': None, 'score': 0}))
        self._round_results_needs_update = False

    # utility to return tasks list from structure
    def _get_tasks_of(self, struct):
        if isinstance(struct, asyncio.Task):
            yield struct
        elif isinstance(struct, dict):
            for v in struct.values():
                yield from self._get_tasks_of(v)
        elif isinstance(struct, list):
            for v in struct:
                yield from self._get_tasks_of(v)

    # utility to set tasks result to structure
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

    def _update_round_statistics(self):
        if self._round_info is None:
            return

        match_round_key = self._round_info.get('key')

        proxy_team_1 = ProxyTeam(self._poller, 1, self._data)
        proxy_team_2 = ProxyTeam(self._poller, 2, self._data)

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

        for cid in sorted(self._data.get('players', {}).keys()):
            proxy_player = ProxyPlayer(self._poller, cid, self._data)
            players.append({
                'id': proxy_player.id,
                'vendorId': proxy_player.vendorId,
                'name': proxy_player.name,
                'teamId': proxy_player.teamId,
                'meta': {
                    'tank': {
                        'id': proxy_player.tank_name,
                        'name': proxy_player.tank_short_name,
                    }
                },
                'stats': {
                    'kills': proxy_player.kills,
                    'shots': proxy_player.shots,
                    'spotted': proxy_player.spotted,
                    'damageDealt': proxy_player.damageDealt,
                    'damageBlocked': proxy_player.damageBlocked,
                    'damageAssisted': proxy_player.damageAssisted,
                }
            })

        post = {
            'meta': {
                'arenaId': self._aid
            },
            'contestants': {
                'teams': teams,
                'players': players,
            },
            'timeline': list()
        }

        new_tasks = [v for v in self._get_tasks_of(post)]

        future = asyncio.wait(new_tasks, timeout=self.config.battle_poll_timeout, return_when=asyncio.FIRST_EXCEPTION)
        done_tasks, pending_tasks = self._loop.run_until_complete(future)

        if len(pending_tasks) > 0:
            is_timeout = True
            for task in done_tasks:
                if task.exception() is not None:
                    is_timeout = False
                    ex = task.exception()
                    Logger.error("Error '{}' in {}".format(next(iter(ex.args), type(ex).__name__), task._coro.__name__))
            for task in pending_tasks:
                task.cancel()
            if is_timeout:
                Logger.error('Timeout {}s querying all data'.format(self.config.battle_poll_timeout))

        else:
            try:
                self._set_result_to(post, done_tasks)
            except Exception as ex:
                Logger.error("Error '{}'".format(next(iter(ex.args), type(ex).__name__)))
            else:
                self.outputq.put((POST_TYPE.POST_ROUND_STATISTICS, match_round_key, post))
            finally:
                self._round_statistics_needs_update = False


