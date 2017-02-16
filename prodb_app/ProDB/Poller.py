import asyncio
import json
import uuid

import functools
import requests

import names

mock_player = """
[
  {
    "key": "8acb69f3-ab39-458f-8677-4fb94bd5dcbe",
    "player": {
      "key": "",
      "name": "",
      "nameOriginal": "",
      "birthday": "1991-10-19",
      "gender": "m",
      "nick": "friberg",
      "nationality": "SE",
      "residence": "SE",
      "activityStatus": true
    },
    "gamePlatform": {
      "key": "3df8be21-dab3-4fe1-b792-59fa1a9f63c0",
      "platform": {
        "key": "pc",
        "label": "PC"
      }
    },
    "account": "1:1:",
    "validFrom": "2015-11-06T11:12:55.769",
    "validTo": null
  }
]
"""

mock_squad = """
[
  {
    "key": "3ff57e88-df4a-4d8e-9d1a-a4480ddbf727",
    "name": null,
    "team": {
      "key": "69cc29d8-0fa5-4039-93fd-ed2956182fa8",
      "name": "Ninjas in Pyjamas",
      "shortName": "NiP",
      "location": "SE",
      "activityStatus": true
    },
    "gamePlatform": {
      "key": "3df8be21-dab3-4fe1-b792-59fa1a9f63c0",
      "platform": {
        "key": "pc",
        "label": "PC"
      }
    },
    "location": null,
    "activityStatus": true,
    "description": "Ninjas in Pyjamas"
  }
]
"""

mock_match = """
[
  {
    "key": "c73b2efa-1730-43ac-ae66-d7a71d7930e2",
    "verticalPosition": 2,
    "startTime": "2016-08-02T18:00",
    "matchStatus": "live",
    "liveStatsStatus": "basic"
  },
  {
    "key": "cc9921d9-d3c3-4fab-8859-a8581151ec03",
    "verticalPosition": 1,
    "startTime": "2016-10-25T17:10",
    "matchStatus": "open",
    "liveStatsStatus": null
  },
]
"""

mock_round = """
{
  "match": {
    "key": "c73b2efa-1730-43ac-ae66-d7a71d7930e2",
    "verticalPosition": 2,
    "startTime": "2016-05-18T18:00",
    "matchStatus": "finished",
    "liveStatsStatus": "basic"
  },
  "tournament": {},
  "startTimeHistory": [],
  "matchStatusHistory": [],
  "comments": [],
  "metaDataMappings": [],
  "predecessors": [],
  "vods": [],
  "streams": [],
  "contestants": [],
  "rounds": [
    {
      "key": "68d661c3-f8e3-498c-a94e-8b83196fd7f7",
      "roundNumber": 1,
      "gameVersionMap": {
        "key": "402e9b66-7f07-4a67-9089-cc815847637f",
        "name": "de_mirage"
      },
      "roundStatus": "live",
      "startTime": "2016-05-18T18:05:09.013"
    }
  ]
}
"""


@functools.lru_cache()
def getPlayer(cid):
    url = 'https://prodb.tet.io/api/player-gameaccounts?' \
          'gamePlatform=3df8be21-dab3-4fe1-b792-59fa1a9f63c0&account=1:1:{}'.format(cid)
    resp = requests.get(url)
    return resp.json()


@functools.lru_cache()
def getSquads(players):
    players_keys = ','.join(players)
    url = 'https://prodb.tet.io/api/team-squads?' \
          'gamePlatform=3df8be21-dab3-4fe1-b792-59fa1a9f63c0&players={}'.format(players_keys)
    resp = requests.get(url)
    return resp.json()


@functools.lru_cache()
def getMatches(squads):
    squads_keys = ','.join(squad.get('team', {}).get('key') for squad in squads)
    url = 'https://prodb.tet.io/api/matches?' \
          'status=open,live&sort=startTime&squads={}'.format(squads_keys)
    resp = requests.get(url)
    return resp.json()


@functools.lru_cache()
def getMatchDetail(match_key):
    url = 'https://prodb.tet.io/api/matches/{}/detail'.format(match_key)
    match_info = requests.get(url).json()
    return match_info.get('rounds')


@functools.lru_cache()
def getRound(matches):
    for match_key in (match.get('key') for match in matches if match.get('matchStatus') in ('live', 'open')):
        for round_info in getMatchDetail(match_key):
            if round_info.get('roundStatus') in ('live', 'open'):
                return round_info


@asyncio.coroutine
def getRoundIdByPlayerCIDs(*cids, clearcache=False):
    if clearcache:
        getSquads.cache_clear()
        getMatches.cache_clear()
        getRound.cache_clear()
    squads_info = getSquads(cids)
    matches_info = getMatches(squads_info)
    round_info = getRound(matches_info)
    return round_info.get('key')


@asyncio.coroutine
def getTeamIdByPlayerCIDs(*cids, clearcache=False):
    if clearcache:
        getSquads.cache_clear()
    squads_info = getSquads(cids)
    return squads_info[0].get('team', {}).get('key')


@asyncio.coroutine
def getTeamNameByPlayerCIDs(*cids, clearcache=False):
    if clearcache:
        getSquads.cache_clear()
    squads_info = getSquads(cids)
    return squads_info[0].get('name', {}).get('key')


@asyncio.coroutine
def getPlayerIdByPlayerCID(cid, clearcache=False):
    if clearcache:
        getPlayer.cache_clear()
    player_info = getPlayer(cid)
    return player_info[0].get('player', {}).get('key')
