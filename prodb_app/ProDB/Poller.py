import asyncio
import random
import threading
import time
import uuid

from .Logger import Logger
from .ProDBApi import getMatchDetails, getMatches, getPlayer, getTeamSquads


def round_info_mock(*cids):
    time.sleep(random.random())
    round_info = {'roundNumber': 1, 'gameVersionMap': {'gameVersionKey': str(uuid.uuid4())}, 'key': str(uuid.uuid4())}
    Logger.debug('[mock] getMatchRoundKeyByPlayerCIDs [{}] = {}'.format(','.join(cids), repr(round_info)))
    return round_info


def squads_info_mock(*cids):
    time.sleep(random.random())
    squads_info = [{'key': str(uuid.uuid4()), 'team': {'name': 'Team {}'.format(sum(map(int, cids)))}}]
    Logger.debug('[mock] getTeamSquadInfoByPlayerCIDs [{}] = {}'.format(','.join(cids), repr(squads_info)))
    return squads_info


def player_info_mock(cid):
    time.sleep(random.random())
    player_info = [{'key': str(uuid.uuid4()), 'name': 'Player {}'.format(cid)}]
    Logger.debug('[mock] getPlayerKeyByPlayerCID {} = {}'.format(cid, player_info))
    return player_info


class Poller(object):
    @property
    def config(self):
        from .App import App
        return App().config
    
    @property
    def executor(self):
        from .App import App
        return App().poller_executor

    # shared caches
    squads_info_cache = dict()
    player_info_cache = dict()

    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self._thread_lock = threading.Lock()
        # unique cache
        self.rounds_info_cache = dict()

    async def run_in_executor(self, func, *args):
        return await self._loop.run_in_executor(self.executor, func, *args)
    
    async def getMatchRoundDetailsByKey(self, match_round_key):
        # mrdetails = await run_in_executor(getMatchRoundsDetails, match_round_key)
        # return mrdetails
        return 'getMatchRoundDetailsByKey() result'
    
    async def getMatchRoundByPlayerCIDs(self, team1_cids, team2_cids):
        assert len(team1_cids) > 0, 'No Players in Team 1'
        assert len(team2_cids) > 0, 'No Players in Team 2'
    
        cache_key = (tuple(sorted(team1_cids)), tuple(sorted(team2_cids)))

        with self._thread_lock:
            if cache_key in self.rounds_info_cache:
                return self.rounds_info_cache[cache_key]
    
        if self.config.mockpoll:
            rounds_info = await self.run_in_executor(round_info_mock, *sorted(team1_cids + team2_cids))
    
        else:
            squads_keys = await asyncio.gather(self.getTeamSquadKeyByPlayerCIDs(team1_cids), self.getTeamSquadKeyByPlayerCIDs(team2_cids))
    
            assert all(squads_keys), 'No ProDB info for Squads [{}] vs [{}]'.format(','.join(team1_cids), ','.join(team2_cids))
    
            matches_keys = [m_i.get('key') for m_i in await self.run_in_executor(getMatches, *sorted(squads_keys))]
    
            assert len(matches_keys) > 0, 'No ProDB info for open Matches [{}] vs [{}]'.format(','.join(team1_cids), ','.join(team2_cids))
    
            mdetails_tasks = [self.run_in_executor(getMatchDetails, m_k) for m_k in matches_keys]
            rounds_infos = [r_i for md_i in await asyncio.gather(*mdetails_tasks) for r_i in md_i.get('rounds')]
    
            assert len(rounds_infos) > 0, 'No ProDB info for open Rounds [{}] vs [{}]'.format(','.join(team1_cids), ','.join(team2_cids))
    
            # todo: todo need to detect here most relevant round
            rounds_info = next((r_i for r_i in rounds_infos if r_i.get('roundStatus') in ('live', 'open')), None)
    
            assert rounds_info is not None, 'No ProDB info for open Rounds [{}] vs [{}]'.format(','.join(team1_cids), ','.join(team2_cids))
    
        with self._thread_lock:
            if rounds_info is not None:
                self.rounds_info_cache[cache_key] = rounds_info
    
        return rounds_info
    
    async def getMatchRoundKeyByPlayerCIDs(self, team1_cids, team2_cids):
        round_info = await self.getMatchRoundByPlayerCIDs(team1_cids, team2_cids)
        key = round_info.get('key')
        return key

    async def getTeamSquadInfoByPlayerCIDs(self, cids):
        assert len(cids) > 0, 'No Players in Team'
    
        cache_key = tuple(sorted(cids))

        with self._thread_lock:
            if cache_key in self.squads_info_cache:
                return self.squads_info_cache[cache_key]
    
        if self.config.mockpoll:
            squads_info = await self.run_in_executor(squads_info_mock, *sorted(cids))
    
        else:
            player_keys = await asyncio.gather(*[self.getPlayerKeyByPlayerCID(cid) for cid in cids])
    
            assert all(player_keys), 'No ProDB info for every Player [{}]'.format(','.join(cids))
    
            squads_info = await self.run_in_executor(getTeamSquads, *sorted(player_keys))
            # squads_info = [s_i for s_i in squads_info if s_i.get('activityStatus') is True]
    
            assert len(squads_info) > 0, 'No ProDB info for Squad [{}]'.format(','.join(cids))
    
        with self._thread_lock:
            self.squads_info_cache[cache_key] = squads_info
            # clear round info cache
            for other_cache_key in set(self.rounds_info_cache.keys()):
                if cache_key in other_cache_key:
                    del self.rounds_info_cache[other_cache_key]
    
        return squads_info
    
    async def getTeamSquadKeyByPlayerCIDs(self, cids):
        key = next(iter(await self.getTeamSquadInfoByPlayerCIDs(cids)), {}).get('key')
        assert key is not None, 'No ProDB key for Squad [{}]'.format(','.join(cids))
        return key
    
    async def getTeamSquadNameByPlayerCIDs(self, cids):
        name = next(iter(await self.getTeamSquadInfoByPlayerCIDs(cids)), {}).get('team', {}).get('name')
        assert name is not None, 'No ProDB name for Squad [{}]'.format(','.join(cids))
        return name
    
    async def getPlayerInfoByPlayerCID(self, cid):

        cache_key = cid

        with self._thread_lock:
            if cid in self.player_info_cache:
                return self.player_info_cache[cid]
    
        if self.config.mockpoll:
            player_info = await self.run_in_executor(player_info_mock, cid)
        else:
            player_info = await self.run_in_executor(getPlayer, cid)

            assert player_info is not None, 'No ProDB info for Player {}'.format(cid)
    
        with self._thread_lock:
            if player_info is not None:
                self.player_info_cache[cid] = player_info
                # clear team info cache
                for other_cache_key in set(self.squads_info_cache.keys()):
                    if cache_key in other_cache_key:
                        del self.squads_info_cache[other_cache_key]
    
        return player_info

    async def getPlayerKeyByPlayerCID(self, cid):
        key = next(iter(await self.getPlayerInfoByPlayerCID(cid)), {}).get('key')
        assert key is not None, 'No ProDB key for Player {}'.format(cid)
        return key

    async def getPlayerNameByPlayerCID(self, cid):
        name = next(iter(await self.getPlayerInfoByPlayerCID(cid)), {}).get('name')
        assert name is not None, 'No ProDB name for Player {}'.format(cid)
        return name
