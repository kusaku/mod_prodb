from collections import OrderedDict

import BigWorld

import GUI
from Event import Event
from PlayerEvents import g_playerEvents, defaultdict
from gui.InputHandler import g_instance
from gui.battle_control.arena_info.arena_vos import isObserver
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE, SHELL_SET_RESULT, VEHICLE_VIEW_STATE, \
    FEEDBACK_EVENT_ID
from helpers import dependency
from helpers.CallbackDelayer import CallbackDelayer
from skeletons.gui.battle_session import IBattleSessionProvider
from . import Log
from . import Channel

UPDATE_GUI_INTERVAL = 0.0
UPDATE_STATS_INTERVAL = 3.0
UPDATE_ARENA_INTERVAL = 1.0

class MSG_TYPE:
    ARENA = 'arena'
    STATS = 'stats'

class PlayerStats(defaultdict):
    DAMAGE_DONE = 'DAMAGE_DONE'
    DAMAGE_BLOCKED = 'DAMAGE_BLOCKED'
    DAMAGE_ASSIST = 'DAMAGE_ASSIST'
    SPOTTED_COUNT = 'SPOTTED_COUNT'
    SHOTS_COUNT = 'SHOTS_COUNT'
    HITS_COUNT = 'HITS_COUNT'
    KILLS_COUNT = 'KILLS_COUNT'


    def __init__(self):
        defaultdict.__init__(self, int)

    def updateStats(self, statsType, value):
        if statsType in (self.DAMAGE_DONE, self.DAMAGE_BLOCKED, self.DAMAGE_ASSIST):
            self[statsType] = value
        else:
            self[statsType] += value


class Tracking(CallbackDelayer):
    player = property(lambda self: BigWorld.player())
    arena = property(lambda self: getattr(self.player, 'arena', None))
    vehicle = property(lambda self: self.arena.vehicles.get(self.vid))
    aid = property(lambda self: getattr(self.player, 'arenaUniqueID', None))
    pid = property(lambda self: getattr(self.player, 'id', None))
    vid = property(lambda self: getattr(self.player, 'playerVehicleID', None))
    cid = property(lambda self: self.vehicle.get('accountDBID'))

    trackers = dict()
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    @property
    def gui(self):
        if self.__gui is None:
            self.__gui = GUI.Text()
            self.__gui.position = (-1, 0, 1)
            self.__gui.horizontalAnchor = 'LEFT'
            self.__gui.verticalAnchor = 'CENTER'
            self.__gui.colour = (255, 128, 0, 255)
            self.__gui.multiline = True
            self.__gui.font = 'default_small.font'
        return self.__gui


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
        self.statdata = PlayerStats()
        self.shells_qauntity = defaultdict(int)

    def send(self, type, data):
        Log.LOG_DEBUG('Send', type, data)
        self.channel.send({
            'prodb': True,
            'aid': self.aid,
            'cid': self.cid,
            'stime': BigWorld.stime(),
            'type': type,
            'data': data
        })

    def sendArena(self):
        if self.player.isObserver():
            self.send(MSG_TYPE.ARENA, self.arenadata)
        return UPDATE_ARENA_INTERVAL

    def sendStats(self):
        if not self.player.isObserver():
            self.send(MSG_TYPE.STATS, self.statdata)
        return UPDATE_STATS_INTERVAL

    def getAllEvents(self, name, ctrl):
        return {name + '.' + prop: getattr(ctrl, prop) for prop in dir(ctrl) if
                prop.startswith('on') and isinstance(getattr(ctrl, prop), Event)}

    def getAllControllersEvents(self):
        return (
            self.getAllEvents('g_playerEvents', g_playerEvents),
            self.getAllEvents('g_instance', g_instance),
            self.getAllEvents('player', self.player),
            self.getAllEvents('arena', self.arena),
            self.getAllEvents('ammo', self.sessionProvider.shared.ammo),
            self.getAllEvents('equipments', self.sessionProvider.shared.equipments),
            self.getAllEvents('optionalDevices', self.sessionProvider.shared.optionalDevices),
            self.getAllEvents('vehicleState', self.sessionProvider.shared.vehicleState),
            self.getAllEvents('hitDirection', self.sessionProvider.shared.hitDirection),
            self.getAllEvents('arenaLoad', self.sessionProvider.shared.arenaLoad),
            self.getAllEvents('arenaPeriod', self.sessionProvider.shared.arenaPeriod),
            self.getAllEvents('feedback', self.sessionProvider.shared.feedback),
            self.getAllEvents('chatCommands', self.sessionProvider.shared.chatCommands),
            self.getAllEvents('messages', self.sessionProvider.shared.messages),
            self.getAllEvents('drrScale', self.sessionProvider.shared.drrScale),
            self.getAllEvents('privateStats', self.sessionProvider.shared.privateStats),
            self.getAllEvents('crosshair', self.sessionProvider.shared.crosshair),
            self.getAllEvents('personalEfficiencyCtrl', self.sessionProvider.shared.personalEfficiencyCtrl),
            self.getAllEvents('battleCacheCtrl', self.sessionProvider.shared.battleCacheCtrl),
            self.getAllEvents('debug', self.sessionProvider.dynamic.debug),
            self.getAllEvents('teamBases', self.sessionProvider.dynamic.teamBases),
            self.getAllEvents('repair', self.sessionProvider.dynamic.repair),
            self.getAllEvents('respawn', self.sessionProvider.dynamic.respawn),
            self.getAllEvents('dynSquads', self.sessionProvider.dynamic.dynSquads),
            self.getAllEvents('gasAttack', self.sessionProvider.dynamic.gasAttack),
            self.getAllEvents('finishSound', self.sessionProvider.dynamic.finishSound)
        )

    def _onVehicleFeedbackReceived(self, eventID, vehicleID, value):
        if eventID in (FEEDBACK_EVENT_ID.VEHICLE_HIT, FEEDBACK_EVENT_ID.VEHICLE_ARMOR_PIERCED):
            self.statdata.updateStats(PlayerStats.HITS_COUNT, 1)
            self.sendStats()

    def _onPlayerFeedbackReceived(self, events):
        eventIDs = (event.getType() for event in events)
        for eventID in eventIDs:
            if eventID == FEEDBACK_EVENT_ID.PLAYER_KILLED_ENEMY:
                self.statdata.updateStats(PlayerStats.KILLS_COUNT, 1)
                self.sendStats()
            if eventID == FEEDBACK_EVENT_ID.PLAYER_SPOTTED_ENEMY:
                self.statdata.updateStats(PlayerStats.SPOTTED_COUNT, 1)
                self.sendStats()

    def _onTotalEfficiencyUpdated(self, diff):
        getTotalEfficiency = self.sessionProvider.shared.personalEfficiencyCtrl.getTotalEfficiency
        self.statdata.updateStats(PlayerStats.DAMAGE_DONE, getTotalEfficiency(PERSONAL_EFFICIENCY_TYPE.DAMAGE))
        self.statdata.updateStats(PlayerStats.DAMAGE_BLOCKED, getTotalEfficiency(PERSONAL_EFFICIENCY_TYPE.BLOCKED_DAMAGE))
        self.statdata.updateStats(PlayerStats.DAMAGE_ASSIST, getTotalEfficiency(PERSONAL_EFFICIENCY_TYPE.ASSIST_DAMAGE))

    def _onShellsAdded(self, intCD, descriptor, quantity, quantityInClip, gunSettings):
        self.shells_qauntity[intCD] = quantity

    def _onShellsUpdated(self, intCD, quantity, quantityInClip, result):
        shots_made = self.shells_qauntity[intCD] - quantity
        self.shells_qauntity[intCD] = quantity
        if result & SHELL_SET_RESULT.CURRENT:
            self.statdata.updateStats(PlayerStats.SHOTS_COUNT, shots_made)
            self.sendStats()

    def _onAvatarReady(self):
        self.sendArena()

    def _onArenaPeriodChange(self, period, periodEndTime, periodLength, periodAdditionalInfo):
        self.sendArena()

    def log(self, type, *args, **kwargs):
        if type == 'vehicleState.onVehicleStateUpdated':
            state = {
                1: 'FIRE',
                2: 'DEVICES',
                4: 'HEALTH',
                8: 'DESTROYED',
                16: 'CREW_DEACTIVATED',
                32: 'AUTO_ROTATION',
                64: 'SPEED',
                128: 'CRUISE_MODE',
                256: 'REPAIRING',
                512: 'PLAYER_INFO',
                1024: 'SHOW_DESTROY_TIMER',
                2048: 'HIDE_DESTROY_TIMER',
                4096: 'OBSERVED_BY_ENEMY',
                8192: 'RESPAWNING',
                16384: 'SWITCHING',
                32768: 'SHOW_DEATHZONE_TIMER',
                65536: 'HIDE_DEATHZONE_TIMER',
                131072: 'MAX_SPEED',
                262144: 'RPM',
                524288: 'VEHICLE_ENGINE_STATE',
                1048576: 'VEHICLE_MOVEMENT_STATE',
                2097152: 'DEATH_INFO',
                4194304: 'VEHICLE_CHANGED',
                8388608: 'SIEGE_MODE',
            }.get(args[0])

            Log.LOG_DEBUG(type, state, *args, **kwargs)

        elif type == 'feedback.onVehicleFeedbackReceived':

            state = {
                1: 'PLAYER_KILLED_ENEMY',
                2: 'PLAYER_DAMAGED_HP_ENEMY',
                3: 'PLAYER_DAMAGED_DEVICE_ENEMY',
                4: 'PLAYER_SPOTTED_ENEMY',
                5: 'PLAYER_ASSIST_TO_KILL_ENEMY',
                6: 'PLAYER_USED_ARMOR',
                7: 'PLAYER_CAPTURED_BASE',
                8: 'PLAYER_DROPPED_CAPTURE',
                9: 'VEHICLE_HEALTH',
                10: 'VEHICLE_HIT',
                11: 'VEHICLE_ARMOR_PIERCED',
                12: 'VEHICLE_DEAD',
                13: 'VEHICLE_SHOW_MARKER',
                14: 'VEHICLE_ATTRS_CHANGED',
                15: 'VEHICLE_IN_FOCUS',
                16: 'VEHICLE_HAS_AMMO',
                17: 'SHOW_VEHICLE_DAMAGES_DEVICES',
                18: 'HIDE_VEHICLE_DAMAGES_DEVICES',
                19: 'MINIMAP_SHOW_MARKER',
                20: 'MINIMAP_MARK_CELL',
                21: 'DAMAGE_LOG_SUMMARY',
                22: 'POSTMORTEM_SUMMARY',
                23: 'ENEMY_DAMAGED_HP_PLAYER',
                24: 'ENEMY_DAMAGED_DEVICE_PLAYER',
            }.get(args[0])

            Log.LOG_DEBUG(type, state, *args, **kwargs)

        elif type == 'feedback.onPlayerFeedbackReceived':
            states = [{
                          1: 'PLAYER_KILLED_ENEMY',
                          2: 'PLAYER_DAMAGED_HP_ENEMY',
                          3: 'PLAYER_DAMAGED_DEVICE_ENEMY',
                          4: 'PLAYER_SPOTTED_ENEMY',
                          5: 'PLAYER_ASSIST_TO_KILL_ENEMY',
                          6: 'PLAYER_USED_ARMOR',
                          7: 'PLAYER_CAPTURED_BASE',
                          8: 'PLAYER_DROPPED_CAPTURE',
                          9: 'VEHICLE_HEALTH',
                          10: 'VEHICLE_HIT',
                          11: 'VEHICLE_ARMOR_PIERCED',
                          12: 'VEHICLE_DEAD',
                          13: 'VEHICLE_SHOW_MARKER',
                          14: 'VEHICLE_ATTRS_CHANGED',
                          15: 'VEHICLE_IN_FOCUS',
                          16: 'VEHICLE_HAS_AMMO',
                          17: 'SHOW_VEHICLE_DAMAGES_DEVICES',
                          18: 'HIDE_VEHICLE_DAMAGES_DEVICES',
                          19: 'MINIMAP_SHOW_MARKER',
                          20: 'MINIMAP_MARK_CELL',
                          21: 'DAMAGE_LOG_SUMMARY',
                          22: 'POSTMORTEM_SUMMARY',
                          23: 'ENEMY_DAMAGED_HP_PLAYER',
                          24: 'ENEMY_DAMAGED_DEVICE_PLAYER',
                      }.get(a.getType()) for a in args[0]]

            Log.LOG_DEBUG(type, states, *args, **kwargs)

        else:
            Log.LOG_DEBUG(type, *args, **kwargs)

        if type == 'arena.onVehicleStatisticsUpdate':
            print repr(self.arena.statistics)

    def getLogger(self, type):
        return self.trackers.setdefault(type, lambda *args, **kwargs: self.log(type, *args, **kwargs))

    def update_gui(self):
        self.gui.text = 'STATS:\n\n' + '\n'.join('%s: %d' % (stat_name, stat_value) for stat_name, stat_value in self.statdata.iteritems())
        return UPDATE_GUI_INTERVAL

    def start(self):
        self.channel.init(self.config)

        self.statdata.clear()
        self.shells_qauntity.clear()

        if self.player.isObserver():
            g_playerEvents.onAvatarReady += self._onAvatarReady
            g_playerEvents.onArenaPeriodChange += self._onArenaPeriodChange
            self.delayCallback(UPDATE_ARENA_INTERVAL, self.sendArena)
        else:
            self.sessionProvider.shared.feedback.onVehicleFeedbackReceived += self._onVehicleFeedbackReceived
            self.sessionProvider.shared.feedback.onPlayerFeedbackReceived += self._onPlayerFeedbackReceived
            self.sessionProvider.shared.personalEfficiencyCtrl.onTotalEfficiencyUpdated += self._onTotalEfficiencyUpdated
            self.sessionProvider.shared.ammo.onShellsAdded += self._onShellsAdded
            self.sessionProvider.shared.ammo.onShellsUpdated += self._onShellsUpdated
            self.delayCallback(UPDATE_STATS_INTERVAL, self.sendStats)

        for ctrl_event in self.getAllControllersEvents():
            for name, event in ctrl_event.iteritems():
                Log.LOG_DEBUG('bound to %s' % name)
                event += self.getLogger(name)

        self.__gui = None

        GUI.roots()[-1].addChild(self.gui)
        self.delayCallback(UPDATE_GUI_INTERVAL, self.update_gui)

    def stop(self):
        self.clearCallbacks()

        GUI.roots()[-1].delChild(self.gui)

        for ctrl_event in self.getAllControllersEvents():
            for name, event in ctrl_event.iteritems():
                # Log.LOG_DEBUG('unbound from %s' % name)
                event -= self.getLogger(name)

        if self.player.isObserver():
            g_playerEvents.onAvatarReady -= self._onAvatarReady
            g_playerEvents.onArenaPeriodChange -= self._onArenaPeriodChange
        else:
            self.sessionProvider.shared.feedback.onVehicleFeedbackReceived -= self._onVehicleFeedbackReceived
            self.sessionProvider.shared.feedback.onPlayerFeedbackReceived -= self._onPlayerFeedbackReceived
            self.sessionProvider.shared.personalEfficiencyCtrl.onTotalEfficiencyUpdated -= self._onTotalEfficiencyUpdated
            self.sessionProvider.shared.ammo.onShellsAdded -= self._onShellsAdded
            self.sessionProvider.shared.ammo.onShellsUpdated -= self._onShellsUpdated

        for stat_name, stat_value in self.statdata.iteritems():
            Log.LOG_DEBUG('%s: %d' % (stat_name, stat_value))

        self.channel.fini()
