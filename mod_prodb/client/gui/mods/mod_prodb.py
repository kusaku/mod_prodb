#
# mod_prodb entry point
#

from gui.mods.ProDB import Log, g_proDB


def init():
    Log.LOG_DEBUG('init')
    g_proDB.init()


def fini():
    Log.LOG_DEBUG('fini')
    g_proDB.fini()


def onAccountBecomeNonPlayer():
    Log.LOG_DEBUG('onAccountBecomeNonPlayer')


def onAccountBecomePlayer():
    Log.LOG_DEBUG('onAccountBecomePlayer')


def onAccountShowGUI(ctx):
    Log.LOG_DEBUG('onAccountShowGUI', ctx)


def onAvatarBecomePlayerdef():
    Log.LOG_DEBUG('onAvatarBecomePlayerdef')


