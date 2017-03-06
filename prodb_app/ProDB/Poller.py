import asyncio
import itertools
import random

from .ProDBApi import getMatches, getPlayer, getRoundsInfo, getSquads
from .ProDBMock import getPlayerKeyByPlayerCID_mock, getRoundKeyByPlayerCIDs_mock, getTeamKeyByPlayerCIDs_mock, \
    getTeamNameByPlayerCIDs_mock


async def getRoundInfosAsync(match_key):
    return getRoundsInfo(match_key)


async def getRoundKeyByPlayerCIDs(team1_cids, team2_cids):
    # Logger.debug('getRoundKeyByPlayerCIDs')
    from ProDB.App import App
    if App().config.mockpoll:
        await asyncio.sleep(random.random())
        return getRoundKeyByPlayerCIDs_mock(*sorted(team1_cids + team2_cids))

    assert all(team1_cids), 'getRoundKeyByPlayerCIDs - no players in team 1'
    assert all(team2_cids), 'getRoundKeyByPlayerCIDs - no players in team 2'

    squads_keys = await asyncio.gather(*(getTeamKeyByPlayerCIDs(team1_cids), getTeamKeyByPlayerCIDs(team2_cids)))

    assert all(squads_keys), 'getRoundKeyByPlayerCIDs - no ProDB info for all Squads'

    matches_infos = getMatches(*sorted(squads_keys))
    matches_keys = [match_info.get('key') for match_info in matches_infos if
                    match_info.get('matchStatus') in ('live', 'open')]

    rounds_infos = await asyncio.gather(*[getRoundInfosAsync(match_key) for match_key in matches_keys])

    assert all(rounds_infos), 'getRoundKeyByPlayerCIDs - no ProDB info for all Rounds'

    # todo need to detect here most relevant round
    return next(round_info.get('key') for round_info in itertools.chain(*rounds_infos) if
                round_info.get('roundStatus') in ('live', 'open'))


async def getTeamKeyByPlayerCIDs(cids):
    # Logger.debug('getTeamKeyByPlayerCIDs')
    from ProDB.App import App
    if App().config.mockpoll:
        await asyncio.sleep(random.random())
        return getTeamKeyByPlayerCIDs_mock(*sorted(cids))

    assert len(cids) > 0, 'getTeamKeyByPlayerCIDs - no players in team'

    player_keys = await asyncio.gather(*[getPlayerKeyByPlayerCID(cid) for cid in cids])

    assert all(player_keys), 'getTeamKeyByPlayerCIDs - no ProDB info for all players'

    squads_info = getSquads(*sorted(player_keys))

    return next(iter(squads_info), {}).get('key')


async def getTeamNameByPlayerCIDs(cids):
    # Logger.debug('getTeamNameByPlayerCIDs')
    from ProDB.App import App
    if App().config.mockpoll:
        await asyncio.sleep(random.random())
        return getTeamNameByPlayerCIDs_mock(*sorted(cids))

    assert len(cids) > 0, 'getTeamNameByPlayerCIDs - no players in team'

    player_keys = await asyncio.gather(*[getPlayerKeyByPlayerCID(cid) for cid in cids])

    assert all(player_keys), 'getTeamNameByPlayerCIDs - no ProDB info for all players'

    squads_info = getSquads(*sorted(player_keys))
    return next(iter(squads_info), {}).get('team', {}).get('name')


async def getPlayerKeyByPlayerCID(cid):
    # Logger.debug('getPlayerKeyByPlayerCID')
    from ProDB.App import App
    if App().config.mockpoll:
        await asyncio.sleep(random.random())
        return getPlayerKeyByPlayerCID_mock(cid)

    player_info = getPlayer(cid)

    return next(iter(player_info), {}).get('player', {}).get('key')
