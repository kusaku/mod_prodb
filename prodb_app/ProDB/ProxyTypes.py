import asyncio

from ProDB import ProDBPoller


class ProxyTeam:
    @property
    def id(self):
        cids = [cid for cid, player in self.data['players'].items() if player['team'] == self.index]
        loop = asyncio.get_event_loop()
        return loop.create_task(ProDBPoller.getTeamIdByPlayerCIDs(*cids))

    @property
    def name(self):
        # cids = [cid for cid, player in self.data['players'].items() if player['team'] == self.index]
        # return ProDBPoller.getTeamNameByPlayerCIDs(*cids)
        return 'Left Team' if self.index == 1 else 'Right Team'

    @property
    def attack_defence(self):
        if self.data['gameplayName'] in ('assault', 'assault2'):
            return 'attack' if self.index == self.data['attackingTeam'] else 'defense'
        else:
            return self.data['gameplayName']

    def __init__(self, index, data):
        self.index = index
        self.data = data


class ProxyPlayer:
    @property
    def id(self):
        loop = asyncio.get_event_loop()
        return loop.create_task(ProDBPoller.getPlayerIdByPlayerCID(self.cid))

    @property
    def vendorId(self):
        return int(self.cid)

    @property
    def name(self):
        return str(self.data['players'][self.cid]['name'])

    @property
    def teamId(self):
        team = self.data['players'][self.cid]['team']
        proxy_team = ProxyTeam(team, self.data)
        return proxy_team.id

    @property
    def tank_name(self):
        return str(self.data['players'][self.cid]['vehicle_name'])

    @property
    def kills(self):
        return self.data['stats'][self.cid].setdefault('KILLS_COUNT', 0)

    @property
    def shots(self):
        return self.data['stats'][self.cid].setdefault('SHOTS_COUNT', 0)

    @property
    def spotted(self):
        return self.data['stats'][self.cid].setdefault('SPOTTED_COUNT', 0)

    @property
    def damageDealt(self):
        return self.data['stats'][self.cid].setdefault('DAMAGE_DONE', 0)

    @property
    def damageBlocked(self):
        return self.data['stats'][self.cid].setdefault('DAMAGE_BLOCKED', 0)


    def __init__(self, cid, data):
        self.cid = cid # type(cid) is str!!!
        self.data = data