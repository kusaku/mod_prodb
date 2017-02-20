from __future__ import print_function

import sys
import threading
import time
import traceback


def _makeMsgHeader(s, frame):
    filename = frame.f_code.co_filename
    return '[%s] (%s, %d):' % (s, filename, frame.f_lineno)


def LOG_CURRENT_EXCEPTION():
    with _logLock:
        print(_makeMsgHeader(time.strftime('%Y-%m-%d %H:%M:%S [EXCEPTION]'), sys._getframe(1)), file=_logFile)
        traceback.print_exc(file=_logFile)


def LOG_DEBUG(*args):
    with _logLock:
        args = (time.strftime('%Y-%m-%d %H:%M:%S [DEBUG]'),) + args
        print(' '.join(map(str, args)), file=_logFile)


def LOG_ERROR(*args):
    with _logLock:
        args = (time.strftime('%Y-%m-%d %H:%M:%S [ERROR]'),) + args
        print(' '.join(map(str, args)), file=_logFile)


_logLock = threading.Lock()
_logFile = open('ProDB.log', 'at', 0)
