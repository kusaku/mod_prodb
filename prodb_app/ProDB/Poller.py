import asyncio
import functools
import random
import threading
import time
import uuid

from .Logger import Logger
from .ProDBApi import getMatches, getPlayer, getMatchDetails, getSquads

thread_lock = threading.Lock()


async def run_in_executor(func, *args):
    from .App import App
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(App().poller_executor, func, *args)


@functools.lru_cache()
def getRoundKeyByPlayerCIDs_mock(*cids):
    time.sleep(random.random())
    result = str(uuid.uuid4())
    Logger.debug('[mock] getRoundKeyByPlayerCIDs [{}] = {}'.format(','.join(cids), result))
    return result


getRoundKeyByPlayerCIDs_cache = dict()


async def getRoundKeyByPlayerCIDs(team1_cids, team2_cids):
    assert len(team1_cids) > 0, 'No Players in Team 1'
    assert len(team2_cids) > 0, 'No Players in Team 2'

    cache_key = (tuple(sorted(team1_cids)), tuple(sorted(team2_cids)))
    with thread_lock:
        if cache_key in getRoundKeyByPlayerCIDs_cache:
            return getRoundKeyByPlayerCIDs_cache[cache_key]

    squads_keys = await asyncio.gather(getSquadKeyByPlayerCIDs(team1_cids), getSquadKeyByPlayerCIDs(team2_cids))

    assert all(squads_keys), 'No ProDB info for Squads [{}] vs [{}]'.format(','.join(team1_cids), ','.join(team1_cids))

    from .App import App
    if App().config.mockpoll:
        key = await run_in_executor(getRoundKeyByPlayerCIDs_mock, *sorted(team1_cids + team2_cids))
    else:
        matches_keys = [m_i.get('key') for m_i in await run_in_executor(getMatches, *sorted(squads_keys))]

        assert len(matches_keys) > 0, 'No ProDB info for open Matches [{}] vs [{}]'.format(','.join(team1_cids), ','.join(team1_cids))

        mdetails_tasks = [run_in_executor(getMatchDetails, m_k) for m_k in matches_keys]
        rounds_infos = [r_i for md_i in await asyncio.gather(*mdetails_tasks) for r_i in md_i.get('rounds')]

        assert len(rounds_infos) > 0, 'No ProDB info for open Rounds [{}] vs [{}]'.format(','.join(team1_cids), ','.join(team1_cids))

        # todo need to detect here most relevant round
        key = next((r_i.get('key') for r_i in rounds_infos if r_i.get('roundStatus') in ('live', 'open')), None)

        assert key is not None, 'No ProDB info for open Rounds [{}] vs [{}]'.format(','.join(team1_cids), ','.join(team1_cids))

    with thread_lock:
        if key is not None:
            getRoundKeyByPlayerCIDs_cache[cache_key] = key

    return key


getSquadInfoByPlayerCIDs_cache = dict()


async def getSquadInfoByPlayerCIDs(cids):
    assert len(cids) > 0, 'No Players in Team'

    cache_key = tuple(sorted(cids))
    with thread_lock:
        if cache_key in getSquadInfoByPlayerCIDs_cache:
            return getSquadInfoByPlayerCIDs_cache[cache_key]

    player_keys = await asyncio.gather(*[getPlayerKeyByPlayerCID(cid) for cid in cids])

    assert all(player_keys), 'No ProDB info for every Player [{}]'.format(','.join(cids))

    squads_info = await run_in_executor(getSquads, *sorted(player_keys))
    squads_info = [s_i for s_i in squads_info if s_i.get('activityStatus') is True]

    assert len(squads_info) > 0, 'No ProDB info for Squad [{}]'.format(','.join(cids))

    with thread_lock:
        getSquadInfoByPlayerCIDs_cache[cache_key] = squads_info
        # clear round info cache
        for other_cache_key in set(getRoundKeyByPlayerCIDs_cache.keys()):
            if cache_key in other_cache_key:
                del getRoundKeyByPlayerCIDs_cache[other_cache_key]

    return squads_info


@functools.lru_cache()
def getSquadKeyByPlayerCIDs_mock(*cids):
    time.sleep(random.random())
    result = str(uuid.uuid4())
    Logger.debug('[mock] getSquadKeyByPlayerCIDs [{}] = {}'.format(','.join(cids), result))
    return result


async def getSquadKeyByPlayerCIDs(cids):
    from .App import App
    if App().config.mockpoll:
        key = await run_in_executor(getSquadKeyByPlayerCIDs_mock, *sorted(cids))
    else:
        key = next(iter(await getSquadInfoByPlayerCIDs(cids)), {}).get('key')

        assert key is not None, 'No ProDB info for Squad [{}]'.format(','.join(cids))

    return key


@functools.lru_cache()
def getSquadNameByPlayerCIDs_mock(*cids):
    time.sleep(random.random())
    result = str(uuid.uuid4())
    Logger.debug('[mock] getSquadNameByPlayerCIDs [{}] = {}'.format(','.join(cids), result))
    return result


async def getSquadNameByPlayerCIDs(cids):
    from .App import App
    if App().config.mockpoll:
        name = await run_in_executor(getSquadNameByPlayerCIDs_mock, *sorted(cids))
    else:
        name = next(iter(await getSquadInfoByPlayerCIDs(cids)), {}).get('team', {}).get('name')

        assert name is not None, 'No ProDB info for Squad [{}]'.format(','.join(cids))

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
            for other_cache_key in set(getSquadInfoByPlayerCIDs_cache.keys()):
                if cache_key in other_cache_key:
                    del getSquadInfoByPlayerCIDs_cache[other_cache_key]

    return key
