import asyncio
import random
import threading
import time
import uuid

from .Logger import Logger
from .ProDBApi import getMatches, getPlayer, getRoundsInfo, getSquads

thread_lock = threading.Lock()


async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)


def getRoundKeyByPlayerCIDs_mock(*cids):
    time.sleep(random.random())
    result = str(uuid.uuid4())
    Logger.debug('[mock] getRoundKeyByPlayerCIDs [{}] = {}'.format(','.join(cids), result))
    return result


getRoundKeyByPlayerCIDs_cache = dict()


async def getRoundKeyByPlayerCIDs(team1_cids, team2_cids):
    assert len(team1_cids) > 0, 'getRoundKeyByPlayerCIDs - no players in team 1'
    assert len(team2_cids) > 0, 'getRoundKeyByPlayerCIDs - no players in team 2'

    cache_key = (tuple(sorted(team1_cids)), tuple(sorted(team2_cids)))
    with thread_lock:
        if cache_key in getRoundKeyByPlayerCIDs_cache:
            return getRoundKeyByPlayerCIDs_cache[cache_key]

    squads_keys = await asyncio.gather(*(getTeamKeyByPlayerCIDs(team1_cids), getTeamKeyByPlayerCIDs(team2_cids)))

    assert len(squads_keys) > 0, 'getRoundKeyByPlayerCIDs - no ProDB info for Squads'

    from ProDB.App import App
    if App().config.mockpoll:
        key = await run_in_executor(getRoundKeyByPlayerCIDs_mock, *sorted(team1_cids + team2_cids))
    else:
        matches_infos = await run_in_executor(getMatches, *sorted(squads_keys))
        matches_keys = [m_i.get('key') for m_i in matches_infos if m_i.get('matchStatus') in ('live', 'open')]

        assert len(matches_infos) > 0, 'getRoundKeyByPlayerCIDs - no ProDB info for Matches'

        rounds_infos = await asyncio.gather(*[run_in_executor(getRoundsInfo, m_k) for m_k in matches_keys])
        rounds_infos = [r_i for rs_i in rounds_infos for r_i in rs_i]

        assert len(rounds_infos) > 0, 'getRoundKeyByPlayerCIDs - no ProDB info for Rounds'

        # todo need to detect here most relevant round
        key = next(r_i.get('key') for r_i in rounds_infos if r_i.get('roundStatus') in ('live', 'open'))

    with thread_lock:
        if key is not None:
            getRoundKeyByPlayerCIDs_cache[cache_key] = key

    return key


def getTeamKeyByPlayerCIDs_mock(*cids):
    time.sleep(random.random())
    result = str(uuid.uuid4())
    Logger.debug('[mock] getTeamKeyByPlayerCIDs [{}] = {}'.format(','.join(cids), result))
    return result


getTeamKeyByPlayerCIDs_cache = dict()


async def getTeamKeyByPlayerCIDs(cids):
    assert len(cids) > 0, 'getTeamKeyByPlayerCIDs - no players in team'

    cache_key = tuple(sorted(cids))
    with thread_lock:
        if cache_key in getTeamKeyByPlayerCIDs_cache:
            return getTeamKeyByPlayerCIDs_cache[cache_key]

    player_keys = await asyncio.gather(*[getPlayerKeyByPlayerCID(cid) for cid in cids])

    assert all(player_keys), 'getTeamKeyByPlayerCIDs - no ProDB info for all players'

    from ProDB.App import App
    if App().config.mockpoll:
        key = await run_in_executor(getTeamKeyByPlayerCIDs_mock, *sorted(cids))
    else:
        squads_info = await run_in_executor(getSquads, *sorted(player_keys))
        key = next(iter(squads_info), {}).get('key')

    with thread_lock:
        if key is not None:
            getTeamKeyByPlayerCIDs_cache[cache_key] = key
            # clear round info cache
            for other_cache_key in set(getRoundKeyByPlayerCIDs_cache.keys()):
                if cache_key in other_cache_key:
                    del getRoundKeyByPlayerCIDs_cache[other_cache_key]

    return key


def getTeamNameByPlayerCIDs_mock(*cids):
    time.sleep(random.random())
    result = str(uuid.uuid4())
    Logger.debug('[mock] getTeamNameByPlayerCIDs [{}] = {}'.format(','.join(cids), result))
    return result


getTeamNameByPlayerCIDs_cache = dict()


async def getTeamNameByPlayerCIDs(cids):
    assert len(cids) > 0, 'getTeamNameByPlayerCIDs - no players in team'

    cache_key = tuple(sorted(cids))
    with thread_lock:
        if cache_key in getTeamNameByPlayerCIDs_cache:
            return getTeamNameByPlayerCIDs_cache[cache_key]

    player_keys = await asyncio.gather(*[getPlayerKeyByPlayerCID(cid) for cid in cids])

    assert all(player_keys), 'getTeamNameByPlayerCIDs - no ProDB info for all players'

    from ProDB.App import App
    if App().config.mockpoll:
        name = await run_in_executor(getTeamNameByPlayerCIDs_mock, *sorted(cids))
    else:
        squads_info = await run_in_executor(getSquads, *sorted(player_keys))
        name = next(iter(squads_info), {}).get('team', {}).get('name')

    with thread_lock:
        if name is not None:
            getTeamNameByPlayerCIDs_cache[cache_key] = name
            # clear round info cache
            for other_cache_key in set(getRoundKeyByPlayerCIDs_cache.keys()):
                if cache_key in other_cache_key:
                    del getRoundKeyByPlayerCIDs_cache[other_cache_key]

    return name


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

    from ProDB.App import App
    if App().config.mockpoll:
        key = await run_in_executor(getPlayerKeyByPlayerCID_mock, cid)
    else:
        player_info = await run_in_executor(getPlayer, cid)
        key = next(iter(player_info), {}).get('player', {}).get('key')

    with thread_lock:
        if key is not None:
            getPlayerKeyByPlayerCID_cache[cid] = key
            # clear team key cache
            for other_cache_key in set(getTeamKeyByPlayerCIDs_cache.keys()):
                if cache_key in other_cache_key:
                    del getTeamKeyByPlayerCIDs_cache[other_cache_key]
            # clear team name cache
            for other_cache_key in set(getTeamNameByPlayerCIDs_cache.keys()):
                if cache_key in other_cache_key:
                    del getTeamNameByPlayerCIDs_cache[other_cache_key]

    return key
