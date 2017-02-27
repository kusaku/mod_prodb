import asyncio

from ProDB import Poller


class ProxyTeam:
    @property
    def id(self):
        cids = [cid for cid, player in self.data.get('players', {}).items() if player.get('team') == self.index]
        loop = asyncio.get_event_loop()
        return loop.create_task(Poller.getTeamKeyByPlayerCIDs(cids))

    @property
    def name(self):
        cids = [cid for cid, player in self.data.get('players', {}).items() if player.get('team') == self.index]
        loop = asyncio.get_event_loop()
        return loop.create_task(Poller.getTeamNameByPlayerCIDs(cids))

    @property
    def attack_defence(self):
        if self.data.get('gameplayName') in ('assault', 'assault2'):
            return 'attack' if self.index == self.data.get('attackingTeam') else 'defense'
        else:
            return self.data.get('gameplayName')

    def __init__(self, index, data):
        self.index = index
        self.data = data


class ProxyPlayer:
    @property
    def id(self):
        loop = asyncio.get_event_loop()
        return loop.create_task(Poller.getPlayerKeyByPlayerCID(self.cid))

    @property
    def vendorId(self):
        return int(self.cid)

    @property
    def name(self):
        return str(self.data.get('players', {}).get(self.cid, {}).get('name'))

    @property
    def teamId(self):
        team = self.data.get('players', {}).get(self.cid, {}).get('team')
        proxy_team = ProxyTeam(team, self.data)
        return proxy_team.id

    @property
    def tank_name(self):
        return str(self.data.get('players', {}).get(self.cid, {}).get('vehicle_name'))

    @property
    def kills(self):
        return self.data.get('stats', {}).get(self.cid, {}).get('KILLS_COUNT', 0)

    @property
    def shots(self):
        return self.data.get('stats', {}).get(self.cid, {}).get('SHOTS_COUNT', 0)

    @property
    def spotted(self):
        return self.data.get('stats', {}).get(self.cid, {}).get('SPOTTED_COUNT', 0)

    @property
    def damageDealt(self):
        return self.data.get('stats', {}).get(self.cid, {}).get('DAMAGE_DONE', 0)

    @property
    def damageBlocked(self):
        return self.data.get('stats', {}).get(self.cid, {}).get('DAMAGE_BLOCKED', 0)

    def __init__(self, cid, data):
        self.cid = cid  # type(cid) is str!!!
        self.data = data


class ProxyRound:
    def __init__(self, data):
        self.data = data

    @property
    def id(self):
        loop = asyncio.get_event_loop()
        team1_cids = [cid for cid, player in self.data.get('players', {}).items() if player.get('team') == 1]
        team2_cids = [cid for cid, player in self.data.get('players', {}).items() if player.get('team') == 2]
        return loop.create_task(Poller.getRoundKeyByPlayerCIDs(team1_cids, team2_cids))
