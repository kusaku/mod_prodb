import asyncio
import functools
import time
import uuid

import requests

from ProDB import App
from ProDB import logger


@functools.lru_cache()
def getPlayer(cid):
    url = 'http://127.0.0.1:5000/api/player-gameaccounts?' \
          'gamePlatform=3df8be21-dab3-4fe1-b792-59fa1a9f63c0&account=1:1:{}'.format(cid)
    logger.debug(url)
    resp = requests.get(url)
    return resp.json()


@functools.lru_cache()
def getSquads(*players_keys):
    players_keys = ','.join(players_keys)
    url = 'http://127.0.0.1:5000/api/team-squads?' \
          'gamePlatform=3df8be21-dab3-4fe1-b792-59fa1a9f63c0&players = {}'.format(players_keys)
    logger.debug(url)
    resp = requests.get(url)
    return resp.json()


@functools.lru_cache()
def getMatches(*squads_keys):
    squads_keys = ','.join(squads_keys)
    url = 'http://127.0.0.1:5000/api/matches?' \
          'status=open,live&sort=startTime&squads = {}'.format(squads_keys)
    logger.debug(url)
    resp = requests.get(url)
    return resp.json()


@functools.lru_cache()
def getRoundsInfo(match_key):
    url = 'http://127.0.0.1:5000/api/matches/{}/detail'.format(match_key)
    logger.debug(url)
    match_info = requests.get(url).json()
    return match_info.get('rounds')


@functools.lru_cache()
def getRoundKeyByPlayerCIDs_mock(*cids):
    result = str(uuid.uuid4())
    logger.debug('[mock] getRoundKeyByPlayerCIDs [ {} ] = {}'.format(','.join(cids), result))
    time.sleep(0.5)
    return result


async def getRoundInfosAsync(match_key):
    return getRoundsInfo(match_key)


async def getRoundKeyByPlayerCIDs(team1_cids, team2_cids):
    if App.App().config.mockpoll:
        return getRoundKeyByPlayerCIDs_mock(*sorted(team1_cids + team2_cids))

    squads_keys = await asyncio.gather(
        (getTeamKeyByPlayerCIDs(team1_cids), getTeamKeyByPlayerCIDs(team2_cids))
    )

    matches_infos = getMatches(*sorted(squads_keys))

    matches_keys = [match_info.get('key') for match_info in matches_infos if
                    match_info.get('matchStatus') in ('live', 'open')]

    rounds_infos = await asyncio.gather(getRoundInfosAsync(match_key) for match_key in matches_keys)

    # todo need to detect here most relevant round
    return next(round_info.get('key') for round_info in rounds_infos if
                round_info.get('roundStatus') in ('live', 'open'))


@functools.lru_cache()
def getTeamKeyByPlayerCIDs_mock(*cids):
    result = str(uuid.uuid4())
    time.sleep(0.5)
    logger.debug('[mock] getTeamKeyByPlayerCIDs [ {} ] = {}'.format(','.join(cids), result))
    return result


async def getTeamKeyByPlayerCIDs(cids):
    if App.App().config.mockpoll:
        return getTeamKeyByPlayerCIDs_mock(*sorted(cids))

    player_keys = await asyncio.gather(getPlayerKeyByPlayerCID(cid) for cid in cids)
    squads_info = getSquads(*sorted(player_keys))
    return next(iter(squads_info), {}).get('key')


@functools.lru_cache()
def getTeamNameByPlayerCIDs_mock(*cids):
    result = str(uuid.uuid4())
    time.sleep(0.5)
    logger.debug('[mock] getTeamNameByPlayerCIDs [ {} ] = {}'.format(','.join(cids), result))
    return result


async def getTeamNameByPlayerCIDs(cids):
    if App.App().config.mockpoll:
        return getTeamNameByPlayerCIDs_mock(*sorted(cids))

    player_keys = await asyncio.gather(getPlayerKeyByPlayerCID(cid) for cid in cids)
    squads_info = getSquads(*sorted(player_keys))
    return next(iter(squads_info), {}).get('team', {}).get('name')


@functools.lru_cache()
def getPlayerKeyByPlayerCID_mock(cid):
    result = str(uuid.uuid4())
    time.sleep(0.5)
    logger.debug('[mock] getPlayerKeyByPlayerCID {} = {}'.format(cid, result))
    return result


async def getPlayerKeyByPlayerCID(cid):
    if App.App().config.mockpoll:
        return getPlayerKeyByPlayerCID_mock(cid)

    player_info = getPlayer(cid)

    return player_info[0].get('player', {}).get('key')


def cache_clear_all():
    logger.debug('All poller caches are cleared')
    getPlayer.cache_clear()
    getSquads.cache_clear()
    getMatches.cache_clear()
    getRoundsInfo.cache_clear()
    getRoundKeyByPlayerCIDs_mock.cache_clear()
    getTeamKeyByPlayerCIDs_mock.cache_clear()
    getTeamNameByPlayerCIDs_mock.cache_clear()
    getPlayerKeyByPlayerCID_mock.cache_clear()


def cache_info_all():
    return {
        'getPlayer': getPlayer.cache_info(),
        'getSquads': getSquads.cache_info(),
        'getMatches': getMatches.cache_info(),
        'getRoundsInfo': getRoundsInfo.cache_info(),
        'getRoundKeyByPlayerCIDs_mock': getRoundKeyByPlayerCIDs_mock.cache_info(),
        'getTeamKeyByPlayerCIDs_mock': getTeamKeyByPlayerCIDs_mock.cache_info(),
        'getTeamNameByPlayerCIDs_mock': getTeamNameByPlayerCIDs_mock.cache_info(),
        'getPlayerKeyByPlayerCID_mock': getPlayerKeyByPlayerCID_mock.cache_info(),
    }
