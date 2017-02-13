#
# ventuz_mod entry point
#

from gui.mods.ProDB import g_logger, Log

def init():
    Log.LOG_DEBUG('init')
    g_logger.init()


def fini():
    Log.LOG_DEBUG('fini')
    g_logger.fini()


def onAccountBecomeNonPlayer():
    Log.LOG_DEBUG('onAccountBecomeNonPlayer')


def onAccountBecomePlayer():
    Log.LOG_DEBUG('onAccountBecomePlayer')


def onAccountShowGUI(ctx):
    Log.LOG_DEBUG('onAccountShowGUI', ctx)


def onAvatarBecomePlayerdef():
    Log.LOG_DEBUG('onAvatarBecomePlayerdef')


