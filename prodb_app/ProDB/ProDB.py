import functools
import json
import os

import requests

from ProDB import logger, App, PRO_DB_USER, PRO_DB_SECRET
from ProDB.ProDBMock import getRoundKeyByPlayerCIDs_mock, getTeamKeyByPlayerCIDs_mock, getTeamNameByPlayerCIDs_mock, \
    getPlayerKeyByPlayerCID_mock


@functools.lru_cache()
def getAuthTocken():
    url = 'https://prodb.tet.io/api/login'
    logger.debug('Query {}'.format(url))
    data = {'name': PRO_DB_USER, 'secret': PRO_DB_SECRET}
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    resp = requests.post(url, json=data, headers=headers)
    assert resp.text == '"OK"', 'getAuthTocken bad reply - {}'.format(resp.text)
    assert resp.status_code == 200, 'getAuthTocken bad status: {}'.format(resp.status_code)
    return resp.headers.get('X-Auth-Token')


@functools.lru_cache()
def getPlayer(cid):
    url = 'https://prodb.tet.io/api/player-gameaccounts?' \
          'gamePlatform=3df8be21-dab3-4fe1-b792-59fa1a9f63c0&account=1:1:{}'.format(cid)
    logger.debug('Query {}'.format(url))
    headers = {'X-Auth-Token': getAuthTocken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getPlayer bad status: {}'.format(resp.status_code)
    return resp.json()


@functools.lru_cache()
def getSquads(*players_keys):
    players_keys = ','.join(players_keys)
    url = 'https://prodb.tet.io/api/team-squads?' \
          'gamePlatform=3df8be21-dab3-4fe1-b792-59fa1a9f63c0&players={}'.format(players_keys)
    logger.debug('Query {}'.format(url))
    headers = {'X-Auth-Token': getAuthTocken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getSquads bad status: {}'.format(resp.status_code)
    return resp.json()


@functools.lru_cache()
def getMatches(*squads_keys):
    squads_keys = ','.join(squads_keys)
    url = 'https://prodb.tet.io/api/matches?' \
          'status=open,live&sort=startTime&squads={}'.format(squads_keys)
    logger.debug('Query {}'.format(url))
    headers = {'X-Auth-Token': getAuthTocken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getMatches bad status: {}'.format(resp.status_code)
    return resp.json()


@functools.lru_cache()
def getRoundsInfo(match_key):
    url = 'https://prodb.tet.io/api/matches/{}/detail'.format(match_key)
    logger.debug('Query {}'.format(url))
    headers = {'X-Auth-Token': getAuthTocken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getRoundsInfo bad status: {}'.format(resp.status_code)
    return resp.json().get('rounds')


def postStats(aid: int, post_data: dict):
    try:
        key = post_data.pop('key')
        data = json.dumps(post_data, indent=4)

        if App.App().config.mockpost:
            if not os.path.exists('mockpost'):
                os.makedirs('mockpost')
            fname = 'mockpost/arena-{}.json'.format(aid)
            with open(fname, 'wt') as fp:
                logger.info('[mock] Post data is written to {}'.format(fname))
                fp.write('{}\n'.format(data))
        else:
            url = 'https://prodb.tet.io/api/match-rounds/{}/stats'.format(key)
            headers = {'X-Auth-Token': getAuthTocken(), 'Accept': 'application/json'}
            resp = requests.patch(url, data=data, headers=headers)
            # logger.info('Post data : {}'.format(resp.text))
            assert resp.status_code == 200, 'post bad status: {}'.format(resp.status_code)

    except Exception as ex:
        logger.exception('Exception: {}'.format(type(ex).__name__))


def cache_clear_all():
    getPlayer.cache_clear()
    getSquads.cache_clear()
    getMatches.cache_clear()
    getRoundsInfo.cache_clear()
    getRoundKeyByPlayerCIDs_mock.cache_clear()
    getTeamKeyByPlayerCIDs_mock.cache_clear()
    getTeamNameByPlayerCIDs_mock.cache_clear()
    getPlayerKeyByPlayerCID_mock.cache_clear()
    logger.debug('ProDB data caches are cleared')


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
