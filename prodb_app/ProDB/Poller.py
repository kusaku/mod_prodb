import asyncio

from .ProDBApi import getMatches, getPlayer, getRoundsInfo, getSquads
from .ProDBMock import getPlayerKeyByPlayerCID_mock, getRoundKeyByPlayerCIDs_mock, getTeamKeyByPlayerCIDs_mock, \
    getTeamNameByPlayerCIDs_mock


async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)


async def getRoundKeyByPlayerCIDs(team1_cids, team2_cids):
    # Logger.debug('getRoundKeyByPlayerCIDs')

    assert len(team1_cids) > 0, 'getRoundKeyByPlayerCIDs - no players in team 1'
    assert len(team2_cids) > 0, 'getRoundKeyByPlayerCIDs - no players in team 2'

    squads_keys = await asyncio.gather(*(getTeamKeyByPlayerCIDs(team1_cids), getTeamKeyByPlayerCIDs(team2_cids)))

    assert len(squads_keys) > 0, 'getRoundKeyByPlayerCIDs - no ProDB info for Squads'

    from ProDB.App import App
    if App().config.mockpoll:
        return await run_in_executor(getRoundKeyByPlayerCIDs_mock, *sorted(team1_cids + team2_cids))

    matches_infos = await run_in_executor(getMatches, *sorted(squads_keys))
    matches_keys = [match_info.get('key') for match_info in matches_infos if
                    match_info.get('matchStatus') in ('live', 'open')]

    rounds_infos = await asyncio.gather(*[run_in_executor(getRoundsInfo, match_key) for match_key in matches_keys])
    rounds_infos = [round_info for rounds_info in rounds_infos for round_info in rounds_info]

    assert len(rounds_infos) > 0, 'getRoundKeyByPlayerCIDs - no ProDB info for Rounds'

    # todo need to detect here most relevant round
    return next(round_info.get('key') for round_info in rounds_infos if
                round_info.get('roundStatus') in ('live', 'open'))


async def getTeamKeyByPlayerCIDs(cids):
    # Logger.debug('getTeamKeyByPlayerCIDs')
    assert len(cids) > 0, 'getTeamKeyByPlayerCIDs - no players in team'

    player_keys = await asyncio.gather(*[getPlayerKeyByPlayerCID(cid) for cid in cids])

    assert all(player_keys), 'getTeamKeyByPlayerCIDs - no ProDB info for all players'

    from ProDB.App import App
    if App().config.mockpoll:
        return await run_in_executor(getTeamKeyByPlayerCIDs_mock, *sorted(cids))

    squads_info = await run_in_executor(getSquads, *sorted(player_keys))

    return next(iter(squads_info), {}).get('key')


async def getTeamNameByPlayerCIDs(cids):
    # Logger.debug('getTeamNameByPlayerCIDs')

    assert len(cids) > 0, 'getTeamNameByPlayerCIDs - no players in team'

    player_keys = await asyncio.gather(*[getPlayerKeyByPlayerCID(cid) for cid in cids])

    assert all(player_keys), 'getTeamNameByPlayerCIDs - no ProDB info for all players'

    from ProDB.App import App
    if App().config.mockpoll:
        return await run_in_executor(getTeamNameByPlayerCIDs_mock, *sorted(cids))

    squads_info = await run_in_executor(getSquads, *sorted(player_keys))

    return next(iter(squads_info), {}).get('team', {}).get('name')


async def getPlayerKeyByPlayerCID(cid):
    # Logger.debug('getPlayerKeyByPlayerCID')

    from ProDB.App import App
    if App().config.mockpoll:
        return await run_in_executor(getPlayerKeyByPlayerCID_mock, cid)

    player_info = await run_in_executor(getPlayer, cid)

    return next(iter(player_info), {}).get('player', {}).get('key')
