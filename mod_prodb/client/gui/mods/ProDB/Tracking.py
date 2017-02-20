import BigWorld

from PlayerEvents import g_playerEvents
from helpers import dependency
from helpers.CallbackDelayer import CallbackDelayer
from skeletons.gui.battle_session import IBattleSessionProvider
from . import Channel
from . import Log

UPDATE_ARENA_INTERVAL = 1.0


# shared with observer
class MSG_TYPE:
    UPDATE_ARENA = 'update_arena'
    UPDATE_STATS = 'update_stats'
    UPDATE_HEALTH = 'update_health'
    UPDATE_RELOAD = 'update_reload'
    UPDATE_DAMAGE = 'update_damage'
    UPDATE_SPOTTED = 'update_spotted'
    UPDATE_BASE_STATE = 'update_base_state'


class Tracking(CallbackDelayer):
    player = property(lambda self: BigWorld.player())
    arena = property(lambda self: getattr(self.player, 'arena', None))
    vehicle = property(lambda self: self.arena.vehicles.get(self.vid))
    aid = property(lambda self: getattr(self.player, 'arenaUniqueID', None))
    vid = property(lambda self: getattr(self.player, 'playerVehicleID', None))
    cid = property(lambda self: self.vehicle.get('accountDBID'))

    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    @property
    def players(self):
        players = (
            (
                vehicle.get('accountDBID'),
                {
                    'vid': vid,
                    'name': vehicle.get('name'),
                    'vehicle_name': vehicle.get('vehicleType').name.rpartition(':')[-1],
                    'team': vehicle.get('team'),
                    'isAlive': vehicle.get('isAlive'),
                }
            )
            for vid, vehicle in self.arena.vehicles.iteritems()
        )
        return {cid: data for cid, data in players if cid > 0 and data.get('vehicle_name') != 'Observer'}

    @property
    def attackingTeam(self):
        if self.arena.arenaType.gameplayName in ('assault', 'assault2'):
            if len(self.arena.arenaType.teamBasePositions[self.player.team - 1]) == 0:
                return self.player.team
            else:
                return self.player.team % 2 + 1
        else:
            return -1

    @property
    def arenadata(self):
        return {
            'players': self.players,
            'attackingTeam': self.attackingTeam,
            'bonusType': self.arena.bonusType,
            'gameplayName': self.arena.arenaType.gameplayName,
            'name': self.arena.arenaType.name,
            'period': {
                'period': self.arena.period,
                'periodEndTime': self.arena.periodEndTime,
                'periodLength': self.arena.periodLength,
                'periodAdditionalInfo': self.arena.periodAdditionalInfo
            }
        }

    def __init__(self, config):
        CallbackDelayer.__init__(self)
        self.__gui = None
        self.channel = Channel.Channel()
        self.config = config

    def start(self):
        self.channel.init(self.config)
        g_playerEvents.onAvatarReady += self._onAvatarReady
        g_playerEvents.onArenaPeriodChange += self._onArenaPeriodChange
        self.delayCallback(UPDATE_ARENA_INTERVAL, self.sendArena)

    def stop(self):
        self.clearCallbacks()
        g_playerEvents.onAvatarReady -= self._onAvatarReady
        g_playerEvents.onArenaPeriodChange -= self._onArenaPeriodChange
        self.channel.fini()

    def send(self, type, data):
        Log.LOG_DEBUG('Send', type, data)
        self.channel.send({
            'aid': self.aid,
            'vid': self.vid,
            'cid': self.cid,
            'stime': BigWorld.stime(),
            'type': type,
            'data': data
        })

    def sendArena(self):
        self.send(MSG_TYPE.UPDATE_ARENA, self.arenadata)
        return UPDATE_ARENA_INTERVAL

    def _onAvatarReady(self):
        self.sendArena()

    def _onArenaPeriodChange(self, period, periodEndTime, periodLength, periodAdditionalInfo):
        self.sendArena()
