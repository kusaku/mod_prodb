dataset_players = [
    {
        "player": {
            "key": "8acb69f3-ab39-458f-8677-4fb94bd5dcbe",
            "name": "kusaku",
            "nameOriginal": "kusaku",
            "birthday": "1991-10-19",
            "gender": "m",
            "nick": "friberg",
            "nationality": "SE",
            "residence": "SE",
            "activityStatus": True
        },
        "gamePlatform": {
            "key": "3df8be21-dab3-4fe1-b792-59fa1a9f63c0",
            "platform": {
                "key": "pc",
                "label": "PC"
            }
        },
        "account": "1:1:32377107",
        "validFrom": "2015-11-06T11:12:55.769",
        "validTo": None
    },
    {
        "player": {
            "key": "9c051e3f-6111-4599-ac96-d7ef08fd7d38",
            "name": "Sobaken81",
            "nameOriginal": "Sobaken81",
            "birthday": "1991-10-19",
            "gender": "m",
            "nick": "friberg",
            "nationality": "SE",
            "residence": "SE",
            "activityStatus": True
        },
        "gamePlatform": {
            "key": "3df8be21-dab3-4fe1-b792-59fa1a9f63c0",
            "platform": {
                "key": "pc",
                "label": "PC"
            }
        },
        "account": "1:1:45112428",
        "validFrom": "2015-11-06T11:12:55.769",
        "validTo": None
    }
]

dataset_squads = [
    {
        "players": ["8acb69f3-ab39-458f-8677-4fb94bd5dcbe"],
        "key": "3ff57e88-df4a-4d8e-9d1a-a4480ddbf727",
        "name": None,
        "team": {
            "key": "69cc29d8-0fa5-4039-93fd-ed2956182fa8",
            "name": "Ninjas in Pyjamas",
            "shortName": "NiP",
            "location": "SE",
            "activityStatus": True
        },
        "gamePlatform": {
            "key": "3df8be21-dab3-4fe1-b792-59fa1a9f63c0",
            "platform": {
                "key": "pc",
                "label": "PC"
            }
        },
        "location": None,
        "activityStatus": None,
        "description": "Ninjas in Pyjamas"
    },
    {
        "players": ["9c051e3f-6111-4599-ac96-d7ef08fd7d38"],
        "key": "e8b6c875-2e7c-45d0-85ee-76afd0ccda64",
        "name": None,
        "team": {
            "key": "9aaeb059-4c38-4baa-8535-fb4137c5b795",
            "name": "Pyjamas in Ninjas",
            "shortName": "PiN",
            "location": "SE",
            "activityStatus": True
        },
        "gamePlatform": {
            "key": "3df8be21-dab3-4fe1-b792-59fa1a9f63c0",
            "platform": {
                "key": "pc",
                "label": "PC"
            }
        },
        "location": None,
        "activityStatus": None,
        "description": "Pyjamas in Ninjas"
    }
]

dataset_matches = [
    {
        "squads": ["3ff57e88-df4a-4d8e-9d1a-a4480ddbf727", "e8b6c875-2e7c-45d0-85ee-76afd0ccda64"],
        "key": "3ff57e88-df4a-4d8e-9d1a-a4480ddbf727",
        "verticalPosition": 2,
        "startTime": "2016-08-02T18:00",
        "matchStatus": "live",
        "liveStatsStatus": "basic"
    },
    {
        "squads": ["3ff57e88-df4a-4d8e-9d1a-a4480ddbf727", "e8b6c875-2e7c-45d0-85ee-76afd0ccda64"],
        "key": "cc9921d9-d3c3-4fab-8859-a8581151ec03",
        "verticalPosition": 1,
        "startTime": "2016-10-25T17:10",
        "matchStatus": "open",
        "liveStatsStatus": None
    },
]

dataset_matches_details = [
    {
        "match": {
            "key": "3ff57e88-df4a-4d8e-9d1a-a4480ddbf727",
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
]
