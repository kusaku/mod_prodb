import asyncio
import functools
import random
import threading
import time
import uuid

from .Logger import Logger
from .ProDBApi import getMatchDetails, getMatches, getPlayer, getTeamSquads

thread_lock = threading.Lock()


async def run_in_executor(func, *args):
    from .App import App
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(App().poller_executor, func, *args)


async def getMatchRoundDetailsByKey(match_round_key):
    # mrdetails = await run_in_executor(getMatchRoundsDetails, match_round_key)
    # return mrdetails
    return 'getMatchRoundDetailsByKey() result'


@functools.lru_cache()
def getMatchRoundByPlayerCIDs_mock(*cids):
    time.sleep(random.random())
    round_info = {'roundNumber': 1, 'gameVersionMap': {'gameVersionKey': str(uuid.uuid4())}, 'key': str(uuid.uuid4())}
    Logger.debug('[mock] getMatchRoundKeyByPlayerCIDs [{}] = {}'.format(','.join(cids), repr(round_info)))
    return round_info


getMatchRoundByPlayerCIDs_cache = dict()


async def getMatchRoundByPlayerCIDs(team1_cids, team2_cids):
    assert len(team1_cids) > 0, 'No Players in Team 1'
    assert len(team2_cids) > 0, 'No Players in Team 2'

    cache_key = (tuple(sorted(team1_cids)), tuple(sorted(team2_cids)))
    with thread_lock:
        if cache_key in  getMatchRoundByPlayerCIDs_cache:
            return getMatchRoundByPlayerCIDs_cache[cache_key]

    from .App import App
    if App().config.mockpoll:
        rounds_info = await run_in_executor(getMatchRoundByPlayerCIDs_mock, *sorted(team1_cids + team2_cids))

    else:
        squads_keys = await asyncio.gather(getTeamSquadKeyByPlayerCIDs(team1_cids), getTeamSquadKeyByPlayerCIDs(team2_cids))

        assert all(squads_keys), 'No ProDB info for Squads [{}] vs [{}]'.format(','.join(team1_cids), ','.join(team2_cids))

        matches_keys = [m_i.get('key') for m_i in await run_in_executor(getMatches, *sorted(squads_keys))]

        assert len(matches_keys) > 0, 'No ProDB info for open Matches [{}] vs [{}]'.format(','.join(team1_cids), ','.join(team2_cids))

        mdetails_tasks = [run_in_executor(getMatchDetails, m_k) for m_k in matches_keys]
        rounds_infos = [r_i for md_i in await asyncio.gather(*mdetails_tasks) for r_i in md_i.get('rounds')]

        assert len(rounds_infos) > 0, 'No ProDB info for open Rounds [{}] vs [{}]'.format(','.join(team1_cids), ','.join(team2_cids))

        # todo: todo need to detect here most relevant round
        rounds_info = next((r_i for r_i in rounds_infos if r_i.get('roundStatus') in ('live', 'open')), None)

        assert rounds_info is not None, 'No ProDB info for open Rounds [{}] vs [{}]'.format(','.join(team1_cids), ','.join(team2_cids))

    with thread_lock:
        if rounds_info is not None:
            getMatchRoundByPlayerCIDs_cache[cache_key] = rounds_info

    return rounds_info


async def getMatchRoundKeyByPlayerCIDs(team1_cids, team2_cids):
    round_info = await getMatchRoundByPlayerCIDs(team1_cids, team2_cids)
    key = round_info.get('key')
    return key


@functools.lru_cache()
def getTeamSquadInfoByPlayerCIDs_mock(*cids):
    time.sleep(random.random())
    squads_info = [{'key': str(uuid.uuid4()), 'team': {'name': 'Team ' + ''.join(random.choice('prodb') for _ in range(5))}}]
    Logger.debug('[mock] getTeamSquadInfoByPlayerCIDs [{}] = {}'.format(','.join(cids), repr(squads_info)))
    return squads_info


getTeamSquadInfoByPlayerCIDs_cache = dict()


async def getTeamSquadInfoByPlayerCIDs(cids):
    assert len(cids) > 0, 'No Players in Team'

    cache_key = tuple(sorted(cids))
    with thread_lock:
        if cache_key in getTeamSquadInfoByPlayerCIDs_cache:
            return getTeamSquadInfoByPlayerCIDs_cache[cache_key]

    from .App import App
    if App().config.mockpoll:
        squads_info = await run_in_executor(getTeamSquadInfoByPlayerCIDs_mock, *sorted(cids))

    else:
        player_keys = await asyncio.gather(*[getPlayerKeyByPlayerCID(cid) for cid in cids])

        assert all(player_keys), 'No ProDB info for every Player [{}]'.format(','.join(cids))

        squads_info = await run_in_executor(getTeamSquads, *sorted(player_keys))
        # squads_info = [s_i for s_i in squads_info if s_i.get('activityStatus') is True]

        assert len(squads_info) > 0, 'No ProDB info for Squad [{}]'.format(','.join(cids))

    with thread_lock:
        getTeamSquadInfoByPlayerCIDs_cache[cache_key] = squads_info
        # clear round info cache
        for other_cache_key in set(getMatchRoundByPlayerCIDs_cache.keys()):
            if cache_key in other_cache_key:
                del getMatchRoundByPlayerCIDs_cache[other_cache_key]

    return squads_info


async def getTeamSquadKeyByPlayerCIDs(cids):
    key = next(iter(await getTeamSquadInfoByPlayerCIDs(cids)), {}).get('key')

    assert key is not None, 'No ProDB key for Squad [{}]'.format(','.join(cids))

    return key


async def getTeamSquadNameByPlayerCIDs(cids):
    name = next(iter(await getTeamSquadInfoByPlayerCIDs(cids)), {}).get('team', {}).get('name')

    assert name is not None, 'No ProDB name for Squad [{}]'.format(','.join(cids))

    return name


@functools.lru_cache()
def getPlayerKeyByPlayerCID_mock(cid):
    time.sleep(random.random())
    result = str(uuid.uuid4())
    Logger.debug('[mock] getPlayerKeyByPlayerCID {} = {}'.format(cid, result))
    return result


getPlayerKeyByPlayerCID_cache = dict()


async def getPlayerKeyByPlayerCID(cid):
    cache_key = cid
    with thread_lock:
        if cid in getPlayerKeyByPlayerCID_cache:
            return getPlayerKeyByPlayerCID_cache[cid]

    from .App import App
    if App().config.mockpoll:
        key = await run_in_executor(getPlayerKeyByPlayerCID_mock, cid)
    else:
        player_info = await run_in_executor(getPlayer, cid)
        key = next(iter(player_info), {}).get('player', {}).get('key')

        assert key is not None, 'No ProDB info for Player {}'.format(cid)

    with thread_lock:
        if key is not None:
            getPlayerKeyByPlayerCID_cache[cid] = key
            # clear team info cache
            for other_cache_key in set(getTeamSquadInfoByPlayerCIDs_cache.keys()):
                if cache_key in other_cache_key:
                    del getTeamSquadInfoByPlayerCIDs_cache[other_cache_key]

    return key
