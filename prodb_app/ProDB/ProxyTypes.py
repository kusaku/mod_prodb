import asyncio


class ProxyTeam:
    @property
    def id(self):
        cids = [cid for cid, player in self._data.get('players', {}).items() if player.get('team') == self._index]
        return asyncio.ensure_future(self._poller.getTeamSquadKeyByPlayerCIDs(cids))

    @property
    def name(self):
        cids = [cid for cid, player in self._data.get('players', {}).items() if player.get('team') == self._index]
        return asyncio.ensure_future(self._poller.getTeamSquadNameByPlayerCIDs(cids))

    @property
    def attack_defence(self):
        if self._data.get('gameplayName') in ('assault', 'assault2'):
            return 'attack' if self._index == self._data.get('attackingTeam') else 'defense'
        else:
            return self._data.get('gameplayName')

    def __init__(self, poller, index, data):
        self._poller = poller
        self._index = index
        self._data = data


class ProxyPlayer:
    @property
    def config(self):
        from .App import App
        return App().config

    @property
    def id(self):
        return asyncio.ensure_future(self._poller.getPlayerKeyByPlayerCID(self._cid))

    @property
    def vendorId(self):
        return str(self._cid)

    @property
    def name(self):
        name = str(self._data.get('players', {}).get(self._cid, {}).get('name'))
        for tag in self.config.remove_player_tags:
            name = name.replace(tag, '')
        return name

    @property
    def teamId(self):
        team = self._data.get('players', {}).get(self._cid, {}).get('team')
        proxy_team = ProxyTeam(self._poller, team, self._data)
        return proxy_team.id

    @property
    def tank_name(self):
        return str(self._data.get('players', {}).get(self._cid, {}).get('vehicle_name'))

    @property
    def tank_short_name(self):
        return str(self._data.get('players', {}).get(self._cid, {}).get('vehicle_short_name'))

    @property
    def kills(self):
        return self._data.get('stats', {}).get(self._cid, {}).get('KILLS_COUNT', 0)

    @property
    def shots(self):
        return self._data.get('stats', {}).get(self._cid, {}).get('SHOTS_COUNT', 0)

    @property
    def spotted(self):
        return self._data.get('stats', {}).get(self._cid, {}).get('SPOTTED_COUNT', 0)

    @property
    def damageDealt(self):
        return self._data.get('stats', {}).get(self._cid, {}).get('DAMAGE_DONE', 0)

    @property
    def damageBlocked(self):
        return self._data.get('stats', {}).get(self._cid, {}).get('DAMAGE_BLOCKED', 0)

    @property
    def damageAssisted(self):
        return self._data.get('stats', {}).get(self._cid, {}).get('DAMAGE_ASSIST', 0)

    def __init__(self, poller, cid, data):
        self._poller = poller
        self._cid = cid  # type(_cid) is str!!!
        self._data = data


class ProxyRound:
    def __init__(self, poller, data):
        self._poller = poller
        self._data = data

    @property
    def id(self):
        team1_cids = [cid for cid, player in self._data.get('players', {}).items() if player.get('team') == 1]
        team2_cids = [cid for cid, player in self._data.get('players', {}).items() if player.get('team') == 2]
        return asyncio.ensure_future(self._poller.getMatchRoundKeyByPlayerCIDs(team1_cids, team2_cids))
