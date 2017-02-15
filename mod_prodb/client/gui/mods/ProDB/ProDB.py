from gui.shared import g_eventBus, events
from . import Config
from . import Tracking
from . import Log


class ProDB(object):
    config = None
    tracking = None

    def init(self):
        self.config = Config.Config()
        self.tracking = Tracking.Tracking(self.config)

        g_eventBus.addListener(events.AppLifeCycleEvent.INITIALIZED, self.onBattleAppInitialized)
        g_eventBus.addListener(events.AppLifeCycleEvent.DESTROYED, self.onBattleAppDestroyed)

    def fini(self):
        g_eventBus.removeListener(events.AppLifeCycleEvent.INITIALIZED, self.onBattleAppInitialized)
        g_eventBus.removeListener(events.AppLifeCycleEvent.DESTROYED, self.onBattleAppDestroyed)

    def onBattleAppInitialized(self, event):

        from gui.app_loader.settings import APP_NAME_SPACE as NS

        if event.ns != NS.SF_BATTLE:
            return

        Log.LOG_DEBUG('ProDB onBattleAppInitialized', event.ns)

        try:
            self.tracking.start()
        except Exception, ex:
            Log.LOG_ERROR('ProDB onBattleAppInitialized exception:', ex)
            Log.LOG_CURRENT_EXCEPTION()

    def onBattleAppDestroyed(self, event):
        from gui.app_loader.settings import APP_NAME_SPACE as NS

        if event.ns != NS.SF_BATTLE:
            return

        Log.LOG_DEBUG('ProDB onBattleAppDestroyed', event.ns)

        try:
            self.tracking.stop()
        except Exception, ex:
            Log.LOG_ERROR('ProDB onBattleAppDestroyed exception:', ex)
            Log.LOG_CURRENT_EXCEPTION()
