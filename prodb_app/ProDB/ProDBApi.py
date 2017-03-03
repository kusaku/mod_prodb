import functools
import json
import os

import requests

from . import PRO_DB_SECRET, PRO_DB_USER
from .Logger import Logger


@functools.lru_cache()
def getAuthToken():
    url = 'https://prodb.tet.io/api/login'
    Logger.debug('Query {}'.format(url))
    data = {'name': PRO_DB_USER, 'secret': PRO_DB_SECRET}
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    resp = requests.post(url, json=data, headers=headers)
    assert resp.text == '"OK"', 'getAuthToken bad reply - {}'.format(resp.text)
    assert resp.status_code == 200, 'getAuthToken bad status: {}'.format(resp.status_code)
    return resp.headers.get('X-Auth-Token')


@functools.lru_cache()
def getPlayer(cid):
    url = 'https://prodb.tet.io/api/player-gameaccounts?' \
          'gamePlatform=3df8be21-dab3-4fe1-b792-59fa1a9f63c0&account=1:1:{}'.format(cid)
    Logger.debug('Query {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getPlayer bad status: {}'.format(resp.status_code)
    return resp.json()


@functools.lru_cache()
def getSquads(*players_keys):
    players_keys = ','.join(players_keys)
    url = 'https://prodb.tet.io/api/team-squads?' \
          'gamePlatform=3df8be21-dab3-4fe1-b792-59fa1a9f63c0&players={}'.format(players_keys)
    Logger.debug('Query {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getSquads bad status: {}'.format(resp.status_code)
    return resp.json()


@functools.lru_cache()
def getMatches(*squads_keys):
    squads_keys = ','.join(squads_keys)
    url = 'https://prodb.tet.io/api/matches?' \
          'status=open,live&sort=startTime&squads={}'.format(squads_keys)
    Logger.debug('Query {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getMatches bad status: {}'.format(resp.status_code)
    return resp.json()


@functools.lru_cache()
def getRoundsInfo(match_key):
    url = 'https://prodb.tet.io/api/matches/{}/detail'.format(match_key)
    Logger.debug('Query {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getRoundsInfo bad status: {}'.format(resp.status_code)
    return resp.json().get('rounds')


def postStats(aid: int, post_data: dict):
    try:
        key = post_data.pop('key')
        data = json.dumps(post_data, indent=4)

        from ProDB.App import App

        if App().config.mockpost:
            if not os.path.exists('mockpost'):
                os.makedirs('mockpost')
            fname = 'mockpost/arena-{}.json'.format(aid)
            with open(fname, 'wt') as fp:
                Logger.info('[mock] Post data is written to {}'.format(fname))
                fp.write('{}\n'.format(data))
        else:
            url = 'https://prodb.tet.io/api/match-rounds/{}/stats'.format(key)
            headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
            resp = requests.patch(url, data=data, headers=headers)
            # Logger.info('Post data : {}'.format(resp.text))
            assert resp.status_code == 200, 'post bad status: {}'.format(resp.status_code)

    except Exception as ex:
        Logger.exception('Exception: {}'.format(type(ex).__name__))


def cache_clear_all():
    getPlayer.cache_clear()
    getSquads.cache_clear()
    getMatches.cache_clear()
    getRoundsInfo.cache_clear()
    Logger.debug('ProDB data caches are cleared')


def cache_info_all():
    return {
        'getPlayer': getPlayer.cache_info(),
        'getSquads': getSquads.cache_info(),
        'getMatches': getMatches.cache_info(),
        'getRoundsInfo': getRoundsInfo.cache_info(),
    }
