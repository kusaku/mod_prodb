import asyncio
import functools

import requests

from ProDB import logger


@functools.lru_cache()
def getPlayer(cid):
    url = 'http://127.0.0.1:5000/api/player-gameaccounts?' \
          'gamePlatform=3df8be21-dab3-4fe1-b792-59fa1a9f63c0&account=1:1:{}'.format(cid)
    logger.error(url)
    resp = requests.get(url)
    return resp.json()


@functools.lru_cache()
def getSquads(*players_keys):
    players_keys = ','.join(players_keys)
    url = 'http://127.0.0.1:5000/api/team-squads?' \
          'gamePlatform=3df8be21-dab3-4fe1-b792-59fa1a9f63c0&players={}'.format(players_keys)
    logger.error(url)
    resp = requests.get(url)
    return resp.json()


@functools.lru_cache()
def getMatches(*squads_keys):
    squads_keys = ','.join(squads_keys)
    url = 'http://127.0.0.1:5000/api/matches?' \
          'status=open,live&sort=startTime&squads={}'.format(squads_keys)
    logger.error(url)
    resp = requests.get(url)
    return resp.json()


@functools.lru_cache()
def getMatchDetail(match_key):
    url = 'http://127.0.0.1:5000/api/matches/{}/detail'.format(match_key)
    logger.error(url)
    match_info = requests.get(url).json()
    return match_info.get('rounds')


@functools.lru_cache()
def getRound(*matches_keys):
    for match_key in matches_keys:
        for round_info in getMatchDetail(match_key):
            if round_info.get('roundStatus') in ('live', 'open'):
                return round_info


def cache_clear_all():
    getPlayer.cache_clear()
    getSquads.cache_clear()
    getMatches.cache_clear()
    getMatchDetail.cache_clear()
    getRound.cache_clear()


def cache_info_all():
    return {
        'getPlayer': getPlayer.cache_info(),
        'getSquads': getSquads.cache_info(),
        'getMatches': getMatches.cache_info(),
        'getMatchDetail': getMatchDetail.cache_info(),
        'getRound': getRound.cache_info()
    }


@asyncio.coroutine
def getRoundKeyByPlayerCIDs(team1_cids, team2_cids):
    squad1_key = yield from getTeamKeyByPlayerCIDs(team1_cids)
    squad2_key = yield from getTeamKeyByPlayerCIDs(team2_cids)

    matches_info = getMatches(squad1_key, squad2_key)
    matches_keys = [match_info.get('key') for match_info in matches_info if
                    match_info.get('matchStatus') in ('live', 'open')]
    round_info = getRound(*matches_keys)
    return round_info.get('key')


@asyncio.coroutine
def getTeamKeyByPlayerCIDs(cids):
    player_keys = []
    for cid in cids:
        player_key = yield from getPlayerKeyByPlayerCID(cid)
        player_keys.append(player_key)

    squads_info = getSquads(*player_keys)
    return next(iter(squads_info), {}).get('key')


@asyncio.coroutine
def getTeamNameByPlayerCIDs(cids):
    player_keys = []
    for cid in cids:
        player_key = yield from getPlayerKeyByPlayerCID(cid)
        player_keys.append(player_key)

    squads_info = getSquads(*player_keys)
    return next(iter(squads_info), {}).get('team', {}).get('name')


@asyncio.coroutine
def getPlayerKeyByPlayerCID(cid):
    player_info = getPlayer(cid)

    return player_info[0].get('player', {}).get('key')
