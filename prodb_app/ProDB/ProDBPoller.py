import asyncio
import functools
import json
import pprint
import uuid

import names
from ProDB import logger

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

def getPlayer(pid):
    player = json.loads(mock_player)
    guid = str(uuid.uuid4())
    name = names.get_full_name()
    player[0]['player']['key'] = guid
    player[0]['player']['name'] = name
    player[0]['player']['nameOriginal'] = name
    player[0]['account'] = '1:1:%d' % pid
    return player

def getSquad(players):
    return json.loads(mock_squad)

def getMatch(squad):
    return json.loads(mock_match)

def getRound(match):
    return json.loads(mock_round)

def getRoundGUID(round):
    return round['rounds'][0]['key']


# @functools.lru_cache()
async def getTeamIdByPlayerCIDs(*cids):
    await asyncio.sleep(5)
    return str(uuid.uuid4())

# @functools.lru_cache()
async def getTeamNameByPlayerCIDs(*cids):
    await asyncio.sleep(0.5)
    return names.get_last_name()

# @functools.lru_cache()
async def getPlayerIdByPlayerCID(cid):
    await asyncio.sleep(0.5)
    return str(uuid.uuid4())

