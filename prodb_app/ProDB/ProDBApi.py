import functools

import requests

from .Logger import Logger


def _get_app_config():
    from .App import App
    return App().config


@functools.lru_cache()
def getAuthToken():
    url = '{pro_db_url}login'.format(**_get_app_config()._asdict())
    Logger.debug('Query GET {}'.format(url))
    config = _get_app_config()
    data = {'name': config.pro_db_user, 'secret': config.pro_db_secret}
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    resp = requests.post(url, json=data, headers=headers)
    assert resp.text == '"OK"', 'getAuthToken - bad reply - {}'.format(resp.text)
    assert resp.status_code == 200, 'getAuthToken - bad status: {}'.format(resp.status_code)
    return resp.headers.get('X-Auth-Token')


@functools.lru_cache()
def getPlayer(cid):
    url = '{pro_db_url}player-gameaccounts?gamePlatform={pro_db_platform}&account={0}'.format(cid, **_get_app_config()._asdict())
    Logger.debug('Query GET {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getPlayer - bad status: {}'.format(resp.status_code)
    return resp.json()


@functools.lru_cache()
def getTeamSquads(*players_keys):
    assert len(players_keys) > 0, 'getTeamSquads - no cids passed'
    players_keys = ','.join(players_keys)
    url = '{pro_db_url}team-squads?gamePlatform={pro_db_platform}&players={0}'.format(players_keys, **_get_app_config()._asdict())
    Logger.debug('Query GET {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getTeamSquads - bad status: {}'.format(resp.status_code)
    return resp.json()


@functools.lru_cache()
def getMatches(*squads_keys):
    assert len(squads_keys) > 0, 'getMatche - no squads_keys passed'
    squads_keys = ','.join(squads_keys)
    url = '{pro_db_url}matches?status=open,live&sort=startTime&squads={0}'.format(squads_keys, **_get_app_config()._asdict())
    Logger.debug('Query GET {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getMatches - bad status: {}'.format(resp.status_code)
    return resp.json()


@functools.lru_cache()
def getMatchDetails(match_round_key):
    url = '{pro_db_url}matches/{0}/detail'.format(match_round_key, **_get_app_config()._asdict())
    Logger.debug('Query GET {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getMatchDetails - bad status: {}'.format(resp.status_code)
    return resp.json()


@functools.lru_cache()
def getMatchRounds(match_round_key):
    url = '{pro_db_url}match-rounds/{0}'.format(match_round_key, **_get_app_config()._asdict())
    Logger.debug('Query GET {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getMatchRounds - bad status: {}'.format(resp.status_code)
    return resp.json()


def postMatchRounds(match_round_key, post_json):
    url = '{pro_db_url}match-rounds/{0}'.format(match_round_key, **_get_app_config()._asdict())
    Logger.debug('Query POST {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Content-Type': 'application/json', 'Accept': 'application/json'}
    resp = requests.put(url, data=post_json, headers=headers)
    assert resp.status_code == 200, 'postMatchRounds - bad status: {}'.format(resp.status_code)


@functools.lru_cache()
def getMatchRoundsDetails(match_round_key):
    url = '{pro_db_url}match-rounds/{0}/details'.format(match_round_key, **_get_app_config()._asdict())
    Logger.debug('Query GET {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getMatchRoundsDetails - bad status: {}'.format(resp.status_code)
    return resp.json()


@functools.lru_cache()
def getMatchRoundsStats(match_round_key):
    url = '{pro_db_url}match-rounds/{0}/stats'.format(match_round_key, **_get_app_config()._asdict())
    Logger.debug('Query GET {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Accept': 'application/json'}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, 'getMatchRoundsStats - bad status: {}'.format(resp.status_code)
    return resp.json()


def postMathcRoundStats(match_round_key, post_json, is_patch):
    url = '{pro_db_url}match-rounds/{0}/stats'.format(match_round_key, **_get_app_config()._asdict())
    headers = {'X-Auth-Token': getAuthToken(), 'Content-Type': 'application/json', 'Accept': 'application/json'}
    if is_patch:
        Logger.debug('Query PATCH {}'.format(url))
        resp = requests.patch(url, data=post_json, headers=headers)
    else:
        Logger.debug('Query POST {}'.format(url))
        resp = requests.post(url, data=post_json, headers=headers)
    assert resp.status_code == 201, 'postMathcRoundStats - bad status: {}'.format(resp.status_code)


def postMatchRoundsСontestant(match_round_contestant_key, post_json):
    url = '{pro_db_url}match-round-contestants/{0}'.format(match_round_contestant_key, **_get_app_config()._asdict())
    Logger.debug('Query POST {}'.format(url))
    headers = {'X-Auth-Token': getAuthToken(), 'Content-Type': 'application/json', 'Accept': 'application/json'}
    resp = requests.put(url, data=post_json, headers=headers)
    assert resp.status_code == 200, 'postMatchСontestantRounds - bad status: {}'.format(resp.status_code)


def cache_clear_all():
    getPlayer.cache_clear()
    getTeamSquads.cache_clear()
    getMatches.cache_clear()
    getMatchDetails.cache_clear()
    getMatchRounds.cache_clear()
    getMatchRoundsDetails.cache_clear()
    getMatchRoundsStats.cache_clear()
    Logger.debug('ProDB data caches are cleared')


def cache_info_all():
    return {
        'getPlayer': getPlayer.cache_info(),
        'getTeamSquads': getTeamSquads.cache_info(),
        'getMatches': getMatches.cache_info(),
        'getMatchDetails': getMatchDetails.cache_info(),
        'getMatchRounds': getMatchRounds.cache_info(),
        'getMatchRoundsDetails': getMatchRoundsDetails.cache_info(),
        'getMatchRoundsStats': getMatchRoundsStats.cache_info(),
    }
