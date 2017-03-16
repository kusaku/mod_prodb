import asyncio

from . import Poller


class ProxyTeam:
    @property
    def id(self):
        cids = [cid for cid, player in self.data.get('players', {}).items() if player.get('team') == self.index]
        return asyncio.ensure_future(Poller.getTeamKeyByPlayerCIDs(cids))

    @property
    def name(self):
        cids = [cid for cid, player in self.data.get('players', {}).items() if player.get('team') == self.index]
        return asyncio.ensure_future(Poller.getTeamNameByPlayerCIDs(cids))

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
        return asyncio.ensure_future(Poller.getPlayerKeyByPlayerCID(self.cid))

    @property
    def vendorId(self):
        return str(self.cid)

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

    @property
    def damageAssisted(self):
        return self.data.get('stats', {}).get(self.cid, {}).get('DAMAGE_ASSIST', 0)

    def __init__(self, cid, data):
        self.cid = cid  # type(cid) is str!!!
        self.data = data


class ProxyRound:
    def __init__(self, data):
        self.data = data

    @property
    def id(self):
        team1_cids = [cid for cid, player in self.data.get('players', {}).items() if player.get('team') == 1]
        team2_cids = [cid for cid, player in self.data.get('players', {}).items() if player.get('team') == 2]
        return asyncio.ensure_future(Poller.getRoundKeyByPlayerCIDs(team1_cids, team2_cids))
