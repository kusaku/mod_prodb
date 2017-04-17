import functools
import os

import requests

from .Logger import Logger


@functools.lru_cache()
def getAuthToken():
    url = 'https://prodb.tet.io/api/login'
    Logger.debug('Query GET {}'.format(url))
    from .App import App
    data = {'name': App().config.pro_db_user, 'secret': App().config.pro_db_secret}
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    resp = requests.post(url, json=data, headers=headers)
    assert resp.text == '"OK"', 'getAuthToken - bad reply - {}'.format(resp.text)
    assert resp.status_code == 200, 'getAuthToken - bad status: {}'.format(resp.status_code)
    return resp.headers.get('X-Auth-Token')


@functools.lru_cache()
def getPlayer(cid):
    url = 'https://prodb.tet.io/api/player-gameaccounts?gamePlatform=a5480e62-61e4-4091-83ca-2ab364f1d645&account={}'.format(cid)
    Logger.debug('Query GET {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getPlayer - bad status: {}'.format(resp.status_code)
    ret = resp.json()
    return ret


@functools.lru_cache()
def getSquads(*players_keys):
    assert len(players_keys) > 0, 'getSquads - no cids passed'
    players_keys = ','.join(players_keys)
    url = 'https://prodb.tet.io/api/team-squads?gamePlatform=a5480e62-61e4-4091-83ca-2ab364f1d645&players={}'.format(players_keys)
    Logger.debug('Query GET {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getSquads - bad status: {}'.format(resp.status_code)
    ret = resp.json()
    return ret


@functools.lru_cache()
def getMatches(*squads_keys):
    assert len(squads_keys) > 0, 'getMatche - no squads_keys passed'
    squads_keys = ','.join(squads_keys)
    url = 'https://prodb.tet.io/api/matches?status=open,live&sort=-startTime&squads,verticalPosition&squads={}'.format(squads_keys)
    Logger.debug('Query GET {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getMatches - bad status: {}'.format(resp.status_code)
    ret = resp.json()
    return ret


@functools.lru_cache()
def getRoundsInfo(match_key):
    url = 'https://prodb.tet.io/api/matches/{}/detail'.format(match_key)
    Logger.debug('Query GET {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getRoundsInfo - bad status: {}'.format(resp.status_code)
    ret = resp.json().get('rounds')
    return ret


def getStats(round_match_key):
    url = 'https://prodb.tet.io/api/match-rounds/{}/stats'.format(round_match_key)
    Logger.debug('Query GET {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getStats - bad status: {}'.format(resp.status_code)
    return resp.json()


def postStats(key, post_data, is_patch):
    try:
        from .App import App

        if App().config.mockpost:
            if not os.path.exists('mockpost'):
                os.makedirs('mockpost')
            fname = 'mockpost/arena-{}.json'.format(key)
            with open(fname, 'at') as fh:
                Logger.info('[mock] Post data is written to {}'.format(fname))
                fh.write('{}\n'.format(post_data))

        else:
            url = 'https://prodb.tet.io/api/match-rounds/{}/stats'.format(key)
            headers = {'X-Auth-Token': getAuthToken(), 'Content-Type': 'application/json', 'Accept': 'application/json'}

            if is_patch:
                Logger.debug('Query PATCH {}'.format(url))
                resp = requests.patch(url, data=post_data, headers=headers)
            else:
                Logger.debug('Query POST {}'.format(url))
                resp = requests.post(url, data=post_data, headers=headers)

            assert resp.status_code == 201, 'postStats - bad status: {}'.format(resp.status_code)

    except Exception as ex:
        Logger.exception('Exception: {}'.format(repr(ex.args[0])))


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
